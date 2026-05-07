import os
import sys
import json
import time
import platform
import argparse
from pathlib import Path
from datetime import datetime, timedelta

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
# progress bar (no external dependencies)
# ---------------------------------------------------------------------------

class Progress:
    """
    Rolling terminal progress bar.

    Layout (overwrites the same line each query):
      [████████░░░░░░░░░░░░░░░░░░░░░░]  42/200 (21%)  ETA 0:14:32  elapsed 0:03:51
        Q042 report.pdf           rec L=1/N=0  mrr L=0.50/N=0.25  LATE▲
    """

    BAR_WIDTH = 32

    def __init__(self, total: int):
        self.total      = total
        self.done       = 0          # set externally for resume offset
        self.start_time = time.perf_counter()
        self._last_len  = 0

    def _eta(self) -> str:
        if self.done == 0:
            return "--:--:--"
        elapsed   = time.perf_counter() - self.start_time
        remaining = (self.total - self.done) / (self.done / elapsed)
        return str(timedelta(seconds=int(remaining)))

    def _elapsed(self) -> str:
        return str(timedelta(seconds=int(time.perf_counter() - self.start_time)))

    def update(self, q_id, doc_name, lc_recall, nc_recall, lc_mrr, nc_mrr, winner):
        self.done += 1
        pct    = self.done / self.total
        filled = int(self.BAR_WIDTH * pct)
        bar    = "█" * filled + "░" * (self.BAR_WIDTH - filled)
        tag    = {"late": "LATE▲", "naive": "NAIVE▲", "tie": "TIE"}.get(winner, winner)

        line = (
            f"\r  [{bar}] {self.done}/{self.total} ({pct*100:.0f}%)  "
            f"ETA {self._eta()}  elapsed {self._elapsed()}  "
            f"Q{q_id:03d} {doc_name[:16]:<16}  "
            f"rec L={lc_recall:.0f}/N={nc_recall:.0f}  "
            f"mrr L={lc_mrr:.2f}/N={nc_mrr:.2f}  {tag}"
        )
        pad = max(0, self._last_len - len(line))
        sys.stdout.write(line + " " * pad)
        sys.stdout.flush()
        self._last_len = len(line)

    def println(self, msg: str):
        """Print a static line above the progress bar (newline before, not after)."""
        sys.stdout.write(f"\n  {msg}\n")
        sys.stdout.flush()
        self._last_len = 0

    def finish(self):
        sys.stdout.write("\n")
        sys.stdout.flush()
        self._last_len = 0


# ---------------------------------------------------------------------------
# retrieval helpers
# ---------------------------------------------------------------------------

def embed_query(chunker, query: str) -> torch.Tensor:
    prefixed = "search_query: " + query
    tokens = chunker.tokenizer(
        prefixed, return_tensors="pt", truncation=True, max_length=8192,
    )
    tokens = {k: v.to(chunker.device) for k, v in tokens.items()}
    with torch.inference_mode():
        out = chunker.model(
            input_ids=tokens["input_ids"],
            attention_mask=tokens["attention_mask"],
        )
    return out.last_hidden_state[0].mean(dim=0)


def retrieve(chunker, query: str, top_k: int):
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
    if correct_page is None:
        return None
    target = str(correct_page)
    for rank, (_, page) in enumerate(retrieved, start=1):
        if str(page) == target:
            return rank
    return None


# ---------------------------------------------------------------------------
# build chunkers (shared model weights)
# ---------------------------------------------------------------------------

def build_chunkers():
    print("[init] Loading model and tokenizer (shared weights)...")
    lc = LateChunking(model_name=config.MODEL, tokenizer_name=config.TOKENIZER)

    nc = NaiveChunking.__new__(NaiveChunking)
    nc.model     = lc.model
    nc.tokenizer = lc.tokenizer
    nc.device    = lc.device
    if hasattr(NaiveChunking, "_init_state"):
        NaiveChunking._init_state(nc)
    else:
        nc.chunks           = []
        nc.chunk_embeddings = []
        nc.chunk_pages      = []

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
        "recall":               recall_at_k(retrieved, keywords),
        "precision":            precision_at_k(retrieved, keywords),
        "mrr":                  mrr(retrieved, keywords),
        "rank_of_correct_page": rank_of_correct_page(retrieved, correct_page),
        "avg_cosine_sim":       round(sum(scores) / len(scores), 4) if scores else 0.0,
        "retrieval_time_s":     elapsed,
        "top_chunk_preview":    retrieved[0][0][:100] if retrieved else "",
        "retrieved_pages":      [p for _, p in retrieved],
    }


# ---------------------------------------------------------------------------
# checkpoint helpers — auto-resume if the run is interrupted
# ---------------------------------------------------------------------------

def load_checkpoint(ckpt_path: Path):
    if ckpt_path.exists():
        try:
            with open(ckpt_path) as f:
                data = json.load(f)
            ids = {r["id"] for r in data}
            print(f"[resume] Checkpoint found — {len(data)} queries already done, "
                  f"skipping those IDs.\n")
            return data, ids
        except Exception:
            pass
    return [], set()


def save_checkpoint(ckpt_path: Path, results: list):
    with open(ckpt_path, "w") as f:
        json.dump(results, f)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Late Chunking vs Naive Chunking — head-to-head retrieval eval"
    )
    parser.add_argument("--eval_set",  required=True,
                        help="Path to eval_set.json")
    parser.add_argument("--pdf_dir",   required=True,
                        help="Root directory containing PDFs (searched recursively)")
    parser.add_argument("--out",       default="evaluation/comparison_results.json",
                        help="Output JSON (default: evaluation/comparison_results.json)")
    parser.add_argument("--top_k",     type=int, default=None,
                        help="Chunks to retrieve (default: config.TOP_K)")
    parser.add_argument("--limit",     type=int, default=None,
                        help="Only run first N queries (smoke-test)")
    parser.add_argument("--no_resume", action="store_true",
                        help="Ignore any existing checkpoint and start fresh")
    args = parser.parse_args()

    top_k = args.top_k or config.TOP_K

    with open(args.eval_set) as f:
        eval_set = json.load(f)
    if args.limit:
        eval_set = eval_set[:args.limit]

    pdf_dir   = Path(args.pdf_dir)
    out_path  = Path(args.out)
    ckpt_path = out_path.with_suffix(".checkpoint.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # resume from checkpoint if available
    # ------------------------------------------------------------------
    if args.no_resume:
        results, done_ids = [], set()
    else:
        results, done_ids = load_checkpoint(ckpt_path)

    remaining = [item for item in eval_set if item["id"] not in done_ids]

    print(f"Total queries : {len(eval_set)}")
    if done_ids:
        print(f"Already done  : {len(done_ids)}  —  running {len(remaining)} remaining")
    print(f"top_k         : {top_k}")
    print(f"{'─'*80}\n")

    if not remaining:
        print("[info] All queries already completed. Re-run with --no_resume to redo.")
    else:
        lc, nc   = build_chunkers()
        last_pdf = None
        progress = Progress(total=len(eval_set))
        progress.done = len(done_ids)   # offset bar for already-completed queries

        for item in remaining:
            found = find_pdf(pdf_dir, item["document"])
            if found is None:
                progress.println(f"[skip] {item['document']} — PDF not found")
                progress.done += 1
                continue

            pdf_path = str(found)

            # re-index when document changes
            if pdf_path != last_pdf:
                progress.println(f"[doc] {item['document']}")
                try:
                    pages = Extraction.extract_text(pdf_path)

                    t0 = time.perf_counter()
                    lc.run(pages)
                    lc_t = round(time.perf_counter() - t0, 2)
                    progress.println(f"  [late]  {len(lc.chunks)} chunks in {lc_t}s")

                    t0 = time.perf_counter()
                    nc.run(pages)
                    nc_t = round(time.perf_counter() - t0, 2)
                    progress.println(f"  [naive] {len(nc.chunks)} chunks in {nc_t}s")

                    last_pdf = pdf_path
                except Exception as exc:
                    progress.println(f"  [error] indexing failed: {exc}")
                    continue

            query        = item["question"]
            keywords     = item.get("keywords", [])
            correct_page = item.get("correct_page")

            try:
                lc_m = eval_query(lc, query, keywords, correct_page, top_k)
                nc_m = eval_query(nc, query, keywords, correct_page, top_k)
            except Exception as exc:
                progress.println(f"[error] Q{item['id']:03d} failed: {exc}")
                continue

            recall_winner = (
                "late"  if lc_m["recall"] > nc_m["recall"] else
                "naive" if nc_m["recall"] > lc_m["recall"] else "tie"
            )
            mrr_winner = (
                "late"  if lc_m["mrr"] > nc_m["mrr"] else
                "naive" if nc_m["mrr"] > lc_m["mrr"] else "tie"
            )

            results.append({
                "id":             item["id"],
                "document":       item["document"],
                "query":          query,
                "correct_page":   correct_page,
                "keywords":       keywords,
                "late_chunking":  lc_m,
                "naive_chunking": nc_m,
                "winner_recall":  recall_winner,
                "winner_mrr":     mrr_winner,
            })

            progress.update(
                q_id=item["id"],
                doc_name=item["document"],
                lc_recall=lc_m["recall"], nc_recall=nc_m["recall"],
                lc_mrr=lc_m["mrr"],       nc_mrr=nc_m["mrr"],
                winner=recall_winner,
            )

            # checkpoint after every query — crash loses at most 1 result
            save_checkpoint(ckpt_path, results)

        progress.finish()

    if not results:
        print("[warn] No results collected — nothing to aggregate.")
        return

    # -----------------------------------------------------------------------
    # aggregate
    # -----------------------------------------------------------------------
    n = len(results)

    def avg_metric(method, key):
        vals     = [r[method][key] for r in results if r[method].get(key) is not None]
        excluded = n - len(vals)
        if excluded:
            print(f"[warn] {method}/{key}: {excluded}/{n} None values excluded from average")
        return round(sum(vals) / len(vals), 3) if vals else None

    def win_counts(winner_key):
        late  = sum(1 for r in results if r[winner_key] == "late")
        naive = sum(1 for r in results if r[winner_key] == "naive")
        ties  = sum(1 for r in results if r[winner_key] == "tie")
        return {
            "late": late, "naive": naive, "ties": ties,
            "late_pct":  round(late  / n * 100, 1),
            "naive_pct": round(naive / n * 100, 1),
            "tie_pct":   round(ties  / n * 100, 1),
        }

    def rank_found_pct(method):
        found = [r[method]["rank_of_correct_page"] for r in results
                 if r[method]["rank_of_correct_page"] is not None]
        return round(len(found) / n * 100, 1) if n else 0

    aggregate = {
        "n_queries": n,
        "top_k":     top_k,
        "late_chunking": {
            "recall_pct":             round((avg_metric("late_chunking", "recall")    or 0) * 100, 1),
            "precision_pct":          round((avg_metric("late_chunking", "precision") or 0) * 100, 1),
            "mrr":                    avg_metric("late_chunking", "mrr"),
            "avg_cosine_sim":         avg_metric("late_chunking", "avg_cosine_sim"),
            "avg_retrieval_time":     avg_metric("late_chunking", "retrieval_time_s"),
            "correct_page_found_pct": rank_found_pct("late_chunking"),
        },
        "naive_chunking": {
            "recall_pct":             round((avg_metric("naive_chunking", "recall")    or 0) * 100, 1),
            "precision_pct":          round((avg_metric("naive_chunking", "precision") or 0) * 100, 1),
            "mrr":                    avg_metric("naive_chunking", "mrr"),
            "avg_cosine_sim":         avg_metric("naive_chunking", "avg_cosine_sim"),
            "avg_retrieval_time":     avg_metric("naive_chunking", "retrieval_time_s"),
            "correct_page_found_pct": rank_found_pct("naive_chunking"),
        },
        "wins_by_recall": win_counts("winner_recall"),
        "wins_by_mrr":    win_counts("winner_mrr"),
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

    # remove checkpoint now that the full results file is written
    if ckpt_path.exists():
        ckpt_path.unlink()
        print(f"[checkpoint] cleaned up {ckpt_path.name}")

    # -----------------------------------------------------------------------
    # pretty summary
    # -----------------------------------------------------------------------
    lc_a = aggregate["late_chunking"]
    nc_a = aggregate["naive_chunking"]

    def delta(lc_val, nc_val, higher_is_better=True):
        if lc_val is None or nc_val is None:
            return "n/a"
        d         = lc_val - nc_val
        display_d = d if higher_is_better else -d
        sign      = "▲" if display_d > 0 else ("▼" if display_d < 0 else "=")
        return f"{sign} {abs(d):.3f}"

    w = 72
    print(f"\n{'='*w}")
    print(f"  RESULTS -> {out_path}")
    print(f"{'─'*w}")
    print(f"  {'Metric':<28} {'Late':>10} {'Naive':>10} {'Delta (L-N)':>14}")
    print(f"  {'─'*28} {'─'*10} {'─'*10} {'─'*14}")

    for label, lv, nv, hib in [
        ("Recall @ k (%)",         lc_a["recall_pct"],             nc_a["recall_pct"],             True),
        ("Precision @ k (%)",      lc_a["precision_pct"],          nc_a["precision_pct"],          True),
        ("MRR",                    lc_a["mrr"],                    nc_a["mrr"],                    True),
        ("Avg cosine similarity",  lc_a["avg_cosine_sim"],         nc_a["avg_cosine_sim"],         True),
        ("Correct page found (%)", lc_a["correct_page_found_pct"], nc_a["correct_page_found_pct"], True),
        ("Avg retrieval time (s)", lc_a["avg_retrieval_time"],     nc_a["avg_retrieval_time"],     False),
    ]:
        lv_s = f"{lv}" if lv is not None else "n/a"
        nv_s = f"{nv}" if nv is not None else "n/a"
        d_s  = delta(lv, nv, hib) if (lv is not None and nv is not None) else "n/a"
        print(f"  {label:<28} {lv_s:>10} {nv_s:>10} {d_s:>14}")

    print(f"{'─'*w}")
    wr = aggregate["wins_by_recall"]
    wm = aggregate["wins_by_mrr"]
    print(f"  Win by Recall  ->  Late: {wr['late']} ({wr['late_pct']}%)  "
          f"Naive: {wr['naive']} ({wr['naive_pct']}%)  Ties: {wr['ties']} ({wr['tie_pct']}%)")
    print(f"  Win by MRR     ->  Late: {wm['late']} ({wm['late_pct']}%)  "
          f"Naive: {wm['naive']} ({wm['naive_pct']}%)  Ties: {wm['ties']} ({wm['tie_pct']}%)")
    print(f"{'='*w}\n")


if __name__ == "__main__":
    main()
