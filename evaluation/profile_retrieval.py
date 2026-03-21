"""
Retrieval profiling for DocuMind evaluation plan
"""

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

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import torch
import torch.nn.functional as F
import config
from src.doc_processing.late_chunking import LateChunking
from src.doc_processing.ragpipeline  import RAGPipeline
from src.doc_processing.vector_store import VectorStore
from src.doc_processing.text_extraction import Extraction


def build_pipeline():
    print("[init] Loading model and tokenizer...")
    lc = LateChunking(model_name=config.MODEL, tokenizer_name=config.TOKENIZER)
    db_path = PROJECT_ROOT / "chroma_db"
    vs = VectorStore(persist_dir=str(db_path))
    api_key = os.getenv("GROQ_API_KEY", "dummy")
    pipeline = RAGPipeline(late_chunking=lc, api_key=api_key, vector_store=vs)
    print("[init] Ready.\n")
    return pipeline


def find_pdf(pdf_dir: Path, filename: str):
    matches = list(pdf_dir.rglob(filename))
    return matches[0] if matches else None


def load_document(pipeline, pdf_path: str):
    if not pipeline.vector_store.is_indexed(pdf_path):
        print(f"  [warn] not in ChromaDB — indexing now...")
        pages = Extraction.extract_text(pdf_path)
        pipeline.index(pages, pdf_path=pdf_path)
    else:
        pages = Extraction.extract_text(pdf_path)
        pipeline.index(pages, pdf_path=pdf_path)


def embed_query(pipeline, query: str) -> torch.Tensor:
    prefixed = "search_query: " + query
    tokens = pipeline.lc.tokenizer(
        prefixed,
        return_tensors="pt",
        return_offsets_mapping=False,
        truncation=True,
        max_length=8192,
    )
    tokens = {k: v.to(pipeline.lc.device) for k, v in tokens.items()}
    with torch.inference_mode():
        outputs = pipeline.lc.model(
            input_ids=tokens["input_ids"],
            attention_mask=tokens["attention_mask"],
        )
    return outputs.last_hidden_state[0].mean(dim=0)


def retrieve_with_scores(pipeline, query: str, top_k: int):
    query_emb = embed_query(pipeline, query)
    similarities = []
    for i, chunk_emb in enumerate(pipeline.chunk_embeddings):
        if not isinstance(chunk_emb, torch.Tensor):
            chunk_emb = torch.tensor(chunk_emb, dtype=torch.float32).to(pipeline.lc.device)
        score = F.cosine_similarity(query_emb.unsqueeze(0), chunk_emb.unsqueeze(0))
        similarities.append((score.item(), i))
    similarities.sort(reverse=True)
    top = similarities[:top_k]
    return [(score, pipeline.lc.chunks[i], pipeline.lc.chunk_pages[i]) for score, i in top]


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


def keyword_hit_count(retrieved, keywords):
    return sum(1 for chunk, _ in retrieved
               if any(kw.lower() in chunk.lower() for kw in keywords))


def main():
    parser = argparse.ArgumentParser(
        description="Profile retrieval stage — no LLM calls, pure embedding + cosine search"
    )
    parser.add_argument("--eval_set", required=True,
                        help="Path to eval_set.json")
    parser.add_argument("--pdf_dir", required=True,
                        help="Root directory containing PDFs (searched recursively)")
    parser.add_argument("--out", default="evaluation/retrieval_results.json",
                        help="Output JSON file (default: evaluation/retrieval_results.json)")
    parser.add_argument("--top_k", type=int, default=None,
                        help="Number of chunks to retrieve (default: config.TOP_K)")
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

    pipeline = build_pipeline()
    results  = []
    last_pdf = None

    print(f"Running {len(eval_set)} queries  top_k={top_k}\n{'─'*70}")

    for item in eval_set:
        found = find_pdf(pdf_dir, item["document"])
        if found is None:
            print(f"[skip] {item['document']} not found under {pdf_dir}")
            continue

        pdf_path = str(found)

        if pdf_path != last_pdf:
            print(f"\n[doc] {item['document']}  ({found.parent.name})")
            load_document(pipeline, pdf_path)
            last_pdf = pdf_path

        query        = item["question"]
        keywords     = item.get("keywords", [])
        correct_page = item.get("correct_page")

        t0 = time.perf_counter()
        scored = retrieve_with_scores(pipeline, query, top_k)
        retrieval_time = round(time.perf_counter() - t0, 3)

        retrieved       = [(chunk, page) for _, chunk, page in scored]
        scores          = [round(s, 4) for s, _, _ in scored]
        retrieved_pages = [page for _, page in retrieved]

        rec   = recall_at_k(retrieved, keywords)
        prec  = precision_at_k(retrieved, keywords)
        mrr_v = mrr(retrieved, keywords)
        rank  = rank_of_correct_page(retrieved, correct_page)
        hits  = keyword_hit_count(retrieved, keywords)
        avg_sim = round(sum(scores) / len(scores), 4) if scores else 0.0

        row = {
            "id":                    item["id"],
            "document":              item["document"],
            "query":                 query,
            "correct_page":          correct_page,
            "keywords":              keywords,
            "chunks_retrieved":      top_k,
            "retrieved_pages":       retrieved_pages,
            "retrieval_time_s":      retrieval_time,
            "recall":                rec,
            "precision":             prec,
            "mrr":                   mrr_v,
            "rank_of_correct_page":  rank,
            "keyword_hit_count":     hits,
            "avg_cosine_similarity": avg_sim,
            "cosine_scores":         scores,
            "_top_chunk_preview":    retrieved[0][0][:120] if retrieved else "",
            "_top_chunk_page":       retrieved_pages[0] if retrieved_pages else None,
        }

        results.append(row)

        hit_str = f"rank={rank}" if rank else "MISS"
        print(f"  [Q{item['id']:03d}] recall={rec:.0f}  prec={prec:.2f}  "
              f"mrr={mrr_v:.3f}  {hit_str}  sim={avg_sim:.3f}  "
              f"time={retrieval_time}s")

    n = len(results)

    def avg(key):
        vals = [r[key] for r in results if r.get(key) is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    rank_hits = [r["rank_of_correct_page"] for r in results
                 if r["rank_of_correct_page"] is not None]

    recall_avg = avg("recall")
    prec_avg   = avg("precision")

    aggregate = {
        "n_queries":              n,
        "top_k":                  top_k,
        "recall_pct":             round(recall_avg * 100, 1) if recall_avg is not None else None,
        "precision_pct":          round(prec_avg   * 100, 1) if prec_avg   is not None else None,
        "mrr":                    avg("mrr"),
        "avg_retrieval_time_s":   avg("retrieval_time_s"),
        "avg_cosine_similarity":  avg("avg_cosine_similarity"),
        "correct_page_found_pct": round(len(rank_hits) / n * 100, 1) if n else 0,
        "rank_distribution": {
            "rank_1":    sum(1 for r in rank_hits if r == 1),
            "rank_2":    sum(1 for r in rank_hits if r == 2),
            "rank_3":    sum(1 for r in rank_hits if r == 3),
            "rank_4_5":  sum(1 for r in rank_hits if r in (4, 5)),
            "not_found": n - len(rank_hits),
        },
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

    w = 60
    print(f"\n{'═'*w}")
    print(f"  Saved to            : {out_path}")
    print(f"{'─'*w}")
    print(f"  Queries run         : {n}  (skipped: {len(eval_set)-n})")
    print(f"  Top-k               : {top_k}")
    print(f"{'─'*w}")
    print(f"  Recall@{top_k}            : {aggregate['recall_pct']}%")
    print(f"  Precision@{top_k}         : {aggregate['precision_pct']}%")
    print(f"  MRR                 : {aggregate['mrr']}")
    print(f"  Avg retrieval time  : {aggregate['avg_retrieval_time_s']}s")
    print(f"  Avg cosine sim      : {aggregate['avg_cosine_similarity']}")
    print(f"  Correct page found  : {aggregate['correct_page_found_pct']}%")
    print(f"{'─'*w}")
    d = aggregate["rank_distribution"]
    print(f"  Rank 1              : {d['rank_1']} queries")
    print(f"  Rank 2              : {d['rank_2']} queries")
    print(f"  Rank 3              : {d['rank_3']} queries")
    print(f"  Rank 4-5            : {d['rank_4_5']} queries")
    print(f"  Not found           : {d['not_found']} queries")
    print(f"{'═'*w}\n")


if __name__ == "__main__":
    main()
