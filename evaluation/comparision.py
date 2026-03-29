import os
import sys
import json
import time
import platform
import argparse
from pathlib import Path
from datetime import datetime
 
if platform.system() == "Windows":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
 
PROJECT_ROOT = Path(__file__).parent.parent  # evaluation/ -> project root
sys.path.insert(0, str(PROJECT_ROOT))
 
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
 
import torch
import torch.nn.functional as F
import config
from src.doc_processing.text_extraction import Extraction
from src.doc_processing.late_chunking   import LateChunking
from src.doc_processing.naive_chunking  import NaiveChunking
 
 
# ---------------------------------------------------------------------------
# retrieval helpers  (no RAGPipeline dependency — we go direct)
# ---------------------------------------------------------------------------
 
def embed_query(chunker, query: str) -> torch.Tensor:
    prefixed = "search_query: " + query
    tokens = chunker.tokenizer(
        prefixed,
        return_tensors="pt",
        truncation=True,
        max_length=8192,
    )
    tokens = {k: v.to(chunker.device) for k, v in tokens.items()}
    with torch.inference_mode():
        outputs = chunker.model(
            input_ids=tokens["input_ids"],
            attention_mask=tokens["attention_mask"],
        )
    return outputs.last_hidden_state[0].mean(dim=0)
 
 
def retrieve(chunker, query: str, top_k: int):
    """Return top_k (score, chunk_text, pages) tuples."""
    q_emb = embed_query(chunker, query)
    sims  = []
    for i, emb in enumerate(chunker.chunk_embeddings):
        if not isinstance(emb, torch.Tensor):
            emb = torch.tensor(emb, dtype=torch.float32).to(chunker.device)
        score = F.cosine_similarity(q_emb.unsqueeze(0), emb.unsqueeze(0))
        sims.append((score.item(), i))
    sims.sort(reverse=True)
    top = sims[:top_k]
    return [(s, chunker.chunks[i], chunker.chunk_pages[i]) for s, i in top]
 
 
# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------
 
def recall_at_k(retrieved, keywords):
    for chunk, _ in retrieved:
        if any(kw.lower() in chunk.lower() for kw in keywords):
            return 1.0
    return 0.0
 
 
def precision_at_k(retrieved, keywords):
    if not retrieved:
        return 0.0
    hits = sum(1 for chunk, _ in retrieved
               if any(kw.lower() in chunk.lower() for kw in keywords))
    return round(hits / len(retrieved), 3)
 
 
def mrr(retrieved, keywords):
    for rank, (chunk, _) in enumerate(retrieved, start=1):
        if any(kw.lower() in chunk.lower() for kw in keywords):
            return round(1.0 / rank, 3)
    return 0.0
 
 
def rank_of_correct_page(retrieved, correct_page):
    for rank, (_, page) in enumerate(retrieved, start=1):
        if page == correct_page:
            return rank
    return None
 
 
# ---------------------------------------------------------------------------
# build chunkers (shared model weights)
# ---------------------------------------------------------------------------
 
def build_chunkers():
    print("[init] Loading model and tokenizer (shared weights)...")
    lc = LateChunking(model_name=config.MODEL, tokenizer_name=config.TOKENIZER)
 
    nc = NaiveChunking(model_name=config.MODEL, tokenizer_name=config.TOKENIZER)
    # share the already-loaded model so we don't double RAM usage
    nc.model     = lc.model
    nc.tokenizer = lc.tokenizer
    nc.device    = lc.device
 
    print("[init] Ready.\n")
    return lc, nc
 
 
def find_pdf(pdf_dir: Path, filename: str):
    matches = list(pdf_dir.rglob(filename))
    return matches[0] if matches else None
 
 
# ---------------------------------------------------------------------------
# per-query evaluation
# ---------------------------------------------------------------------------
 
def eval_query(chunker, query, keywords, correct_page, top_k):
    t0     = time.perf_counter()
    scored = retrieve(chunker, query, top_k)
    elapsed = round(time.perf_counter() - t0, 4)
 
    retrieved = [(chunk, page) for _, chunk, page in scored]
    scores    = [s for s, _, _ in scored]
 
    return {
        "recall":                recall_at_k(retrieved, keywords),
        "precision":             precision_at_k(retrieved, keywords),
        "mrr":                   mrr(retrieved, keywords),
        "rank_of_correct_page":  rank_of_correct_page(retrieved, correct_page),
        "avg_cosine_sim":        round(sum(scores) / len(scores), 4) if scores else 0.0,
        "retrieval_time_s":      elapsed,
        "top_chunk_preview":     retrieved[0][0][:100] if retrieved else "",
        "retrieved_pages":       [p for _, p in retrieved],
    }
 
 
# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
 
def main():
    parser = argparse.ArgumentParser(
        description="Late Chunking vs Naive Chunking — head-to-head retrieval eval"
    )
    parser.add_argument("--eval_set", required=True,
                        help="Path to eval_set.json")
    parser.add_argument("--pdf_dir", required=True,
                        help="Root directory containing PDFs (searched recursively)")
    parser.add_argument("--out", default="evaluation/comparison_results.json",
                        help="Output JSON (default: evaluation/comparison_results.json)")
    parser.add_argument("--top_k", type=int, default=None,
                        help="Chunks to retrieve (default: config.TOP_K)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only run first N queries (smoke-test)")
    args = parser.parse_args()
 
    top_k = args.top_k or config.TOP_K
 
    with open(args.eval_set) as f:
        eval_set = json.load(f)
    if args.limit:
        eval_set = eval_set[:args.limit]
 
    pdf_dir  = Path(args.pdf_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
 
    lc, nc = build_chunkers()
 
    results  = []
    last_pdf = None
 
    print(f"Queries: {len(eval_set)}   top_k: {top_k}")
    print(f"{'─'*80}")
 
    for item in eval_set:
        found = find_pdf(pdf_dir, item["document"])
        if found is None:
            print(f"[skip] {item['document']} not found")
            continue
 
        pdf_path = str(found)
 
        # re-index both chunkers whenever the document changes
        if pdf_path != last_pdf:
            print(f"\n[doc] {item['document']}")
 
            pages = Extraction.extract_text(pdf_path)
 
            print(f"  [late]  indexing...")
            t0 = time.perf_counter()
            lc.run(pages)
            lc_index_time = round(time.perf_counter() - t0, 2)
            print(f"  [late]  {len(lc.chunks)} chunks in {lc_index_time}s")
 
            print(f"  [naive] indexing...")
            t0 = time.perf_counter()
            nc.run(pages)
            nc_index_time = round(time.perf_counter() - t0, 2)
            print(f"  [naive] {len(nc.chunks)} chunks in {nc_index_time}s\n")
 
            last_pdf = pdf_path
 
        query        = item["question"]
        keywords     = item.get("keywords", [])
        correct_page = item.get("correct_page")
 
        lc_m = eval_query(lc, query, keywords, correct_page, top_k)
        nc_m = eval_query(nc, query, keywords, correct_page, top_k)
 
        # who won each metric
        recall_winner = (
            "late"  if lc_m["recall"]    > nc_m["recall"]    else
            "naive" if nc_m["recall"]    > lc_m["recall"]    else "tie"
        )
        mrr_winner = (
            "late"  if lc_m["mrr"]       > nc_m["mrr"]       else
            "naive" if nc_m["mrr"]       > lc_m["mrr"]       else "tie"
        )
 
        row = {
            "id":            item["id"],
            "document":      item["document"],
            "query":         query,
            "correct_page":  correct_page,
            "keywords":      keywords,
            "late_chunking": lc_m,
            "naive_chunking": nc_m,
            "winner_recall": recall_winner,
            "winner_mrr":    mrr_winner,
        }
        results.append(row)
 
        lc_rank  = lc_m["rank_of_correct_page"]
        nc_rank  = nc_m["rank_of_correct_page"]
        lc_rank_str = f"rank={lc_rank}" if lc_rank else "MISS"
        nc_rank_str = f"rank={nc_rank}" if nc_rank else "MISS"
 
        print(
            f"  [Q{item['id']:03d}] "
            f"LATE  rec={lc_m['recall']:.0f} mrr={lc_m['mrr']:.3f} "
            f"sim={lc_m['avg_cosine_sim']:.3f} {lc_rank_str:>8}  |  "
            f"NAIVE rec={nc_m['recall']:.0f} mrr={nc_m['mrr']:.3f} "
            f"sim={nc_m['avg_cosine_sim']:.3f} {nc_rank_str:>8}  "
            f"=> {recall_winner.upper()}"
        )
 
    # -----------------------------------------------------------------------
    # aggregate
    # -----------------------------------------------------------------------
    n = len(results)
 
    def avg_metric(method, key):
        vals = [r[method][key] for r in results if r[method].get(key) is not None]
        return round(sum(vals) / len(vals), 3) if vals else None
 
    def win_pct(winner_key):
        late  = sum(1 for r in results if r[winner_key] == "late")
        naive = sum(1 for r in results if r[winner_key] == "naive")
        ties  = sum(1 for r in results if r[winner_key] == "tie")
        return {"late": late, "naive": naive, "ties": ties}
 
    def rank_found_pct(method):
        found = [r[method]["rank_of_correct_page"] for r in results
                 if r[method]["rank_of_correct_page"] is not None]
        return round(len(found) / n * 100, 1) if n else 0
 
    aggregate = {
        "n_queries": n,
        "top_k":     top_k,
        "late_chunking": {
            "recall_pct":         round((avg_metric("late_chunking", "recall") or 0) * 100, 1),
            "precision_pct":      round((avg_metric("late_chunking", "precision") or 0) * 100, 1),
            "mrr":                avg_metric("late_chunking", "mrr"),
            "avg_cosine_sim":     avg_metric("late_chunking", "avg_cosine_sim"),
            "avg_retrieval_time": avg_metric("late_chunking", "retrieval_time_s"),
            "correct_page_found_pct": rank_found_pct("late_chunking"),
        },
        "naive_chunking": {
            "recall_pct":         round((avg_metric("naive_chunking", "recall") or 0) * 100, 1),
            "precision_pct":      round((avg_metric("naive_chunking", "precision") or 0) * 100, 1),
            "mrr":                avg_metric("naive_chunking", "mrr"),
            "avg_cosine_sim":     avg_metric("naive_chunking", "avg_cosine_sim"),
            "avg_retrieval_time": avg_metric("naive_chunking", "retrieval_time_s"),
            "correct_page_found_pct": rank_found_pct("naive_chunking"),
        },
        "wins_by_recall": win_pct("winner_recall"),
        "wins_by_mrr":    win_pct("winner_mrr"),
    }
 
    output = {
        "meta": {
            "run_at":   datetime.now().isoformat(),
            "eval_set": args.eval_set,
            "pdf_dir":  str(pdf_dir),
            "top_k":    top_k,
            "n_total":  len(eval_set),
            "n_run":    n,
        },
        "aggregate": aggregate,
        "results":   results,
    }
 
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
 
    # -----------------------------------------------------------------------
    # pretty summary
    # -----------------------------------------------------------------------
    lc_a = aggregate["late_chunking"]
    nc_a = aggregate["naive_chunking"]
 
    def delta(lc_val, nc_val, higher_is_better=True):
        if lc_val is None or nc_val is None:
            return "   n/a"
        d = lc_val - nc_val
        if higher_is_better:
            arrow = "+" if d >= 0 else ""
        else:
            arrow = "-" if d >= 0 else "+"
        return f"{arrow}{d:+.1f}" if isinstance(d, float) else f"{arrow}{d:+d}"
 
    w = 70
    print(f"\n{'='*w}")
    print(f"  RESULTS -> {out_path}")
    print(f"{'─'*w}")
    print(f"  {'Metric':<28} {'Late':>10} {'Naive':>10} {'Delta (L-N)':>12}")
    print(f"  {'─'*28} {'─'*10} {'─'*10} {'─'*12}")
 
    rows = [
        ("Recall @ k (%)",          lc_a["recall_pct"],          nc_a["recall_pct"],          True),
        ("Precision @ k (%)",        lc_a["precision_pct"],       nc_a["precision_pct"],       True),
        ("MRR",                      lc_a["mrr"],                 nc_a["mrr"],                 True),
        ("Avg cosine similarity",    lc_a["avg_cosine_sim"],      nc_a["avg_cosine_sim"],      True),
        ("Correct page found (%)",   lc_a["correct_page_found_pct"], nc_a["correct_page_found_pct"], True),
        ("Avg retrieval time (s)",   lc_a["avg_retrieval_time"],  nc_a["avg_retrieval_time"],  False),
    ]
    for label, lv, nv, hib in rows:
        lv_s = f"{lv}" if lv is not None else "n/a"
        nv_s = f"{nv}" if nv is not None else "n/a"
        d_s  = delta(lv, nv, hib) if (lv is not None and nv is not None) else "n/a"
        print(f"  {label:<28} {lv_s:>10} {nv_s:>10} {d_s:>12}")
 
    print(f"{'─'*w}")
    wr = aggregate["wins_by_recall"]
    wm = aggregate["wins_by_mrr"]
    print(f"  Win by Recall   ->  Late: {wr['late']}  Naive: {wr['naive']}  Ties: {wr['ties']}")
    print(f"  Win by MRR      ->  Late: {wm['late']}  Naive: {wm['naive']}  Ties: {wm['ties']}")
    print(f"{'='*w}\n")
 
 
if __name__ == "__main__":
    main()
