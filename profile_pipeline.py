"""
Extraction and embedding profiler for DocuMind
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
 
import config
from src.doc_processing.text_extraction import Extraction
from src.doc_processing.late_chunking   import LateChunking
from src.doc_processing.vector_store    import VectorStore
 
 
def build_components():
    print("[init] Loading model and tokenizer...")
    lc = LateChunking(
        model_name=config.MODEL,
        tokenizer_name=config.TOKENIZER,
    )
    db_path = PROJECT_ROOT / "chroma_db"
    vs = VectorStore(persist_dir=str(db_path))
    print("[init] Ready.\n")
    return lc, vs
 
 
def profile_pdf(pdf_path: str, lc: LateChunking, vs: VectorStore) -> dict:
    pdf_path = str(pdf_path)
 
    result = {
        "pdf":          Path(pdf_path).name,
        "pdf_path":     pdf_path,
        "profiled_at":  datetime.now().isoformat(),
        "mode":         None,   # "fresh" or "cached"
 
        # document stats
        "page_count":   None,
        "chunk_count":  None,
        "token_count":  None,
        "window_count": None,
 
        # fresh timings (None if loaded from cache)
        "time_extraction_s": None,
        "time_chunking_s":   None,
        "time_tokenize_s":   None,
        "time_embedding_s":  None,
        "time_store_s":      None,
 
        # cache timing (None if freshly embedded)
        "time_cache_load_s": None,
 
        "time_total_s": None,
        "error":        None,
    }
 
    total_start = time.perf_counter()
 
    try:
        # ── already in ChromaDB? load from cache ─────────────────────────────
        if vs.is_indexed(pdf_path):
            result["mode"] = "cached"
            print(f"  [cache]   already indexed — loading from ChromaDB")
 
            t0 = time.perf_counter()
            chunks, embeddings, pages = vs.load(pdf_path)
            result["time_cache_load_s"] = round(time.perf_counter() - t0, 3)
 
            lc.chunks          = chunks
            lc.chunk_embeddings = embeddings
            lc.chunk_pages     = pages
            result["chunk_count"] = len(chunks)
 
            print(f"  [cache]   {len(chunks)} chunks loaded in {result['time_cache_load_s']}s")
 
        # ── not in ChromaDB — run full pipeline ───────────────────────────────
        else:
            result["mode"] = "fresh"
            print(f"  [fresh]   not indexed — running full pipeline")
 
            # stage 1: extraction
            t0 = time.perf_counter()
            pages = Extraction.extract_text(pdf_path)
            result["time_extraction_s"] = round(time.perf_counter() - t0, 3)
            result["page_count"] = len(pages)
            print(f"  [extract] {len(pages)} pages in {result['time_extraction_s']}s")
 
            corpus = "\n\n".join(text for _, text in pages)
 
            # stage 2: chunking
            t0 = time.perf_counter()
            lc._chunk(pages)
            result["time_chunking_s"] = round(time.perf_counter() - t0, 3)
            result["chunk_count"] = len(lc.chunks)
            print(f"  [chunk]   {len(lc.chunks)} chunks in {result['time_chunking_s']}s")
 
            # stage 3: tokenization
            t0 = time.perf_counter()
            input_ids, offset_mapping = lc._tokenize_full(corpus)
            result["time_tokenize_s"] = round(time.perf_counter() - t0, 3)
            T = input_ids.shape[1]
            n_windows = max(1, (T - lc.window_overlap - 1) // lc.window_stride + 1)
            result["token_count"]  = T
            result["window_count"] = n_windows
            print(f"  [token]   {T} tokens / {n_windows} window(s) in {result['time_tokenize_s']}s")
 
            # stage 4: embedding
            t0 = time.perf_counter()
            token_boundaries    = lc._find_token_boundaries(corpus, offset_mapping)
            embeddings          = lc._embed_windowed(input_ids, token_boundaries)
            lc.chunk_embeddings = embeddings
            result["time_embedding_s"] = round(time.perf_counter() - t0, 3)
            print(f"  [embed]   {len(embeddings)} embeddings in {result['time_embedding_s']}s")
 
            # stage 5: store
            t0 = time.perf_counter()
            vs.store(pdf_path, lc.chunks, embeddings, lc.chunk_pages)
            result["time_store_s"] = round(time.perf_counter() - t0, 3)
            print(f"  [store]   saved to ChromaDB in {result['time_store_s']}s")
 
    except Exception as e:
        result["error"] = str(e)
        print(f"  [ERROR]   {e}")
 
    result["time_total_s"] = round(time.perf_counter() - total_start, 3)
    print(f"  [total]   {result['mode']} — {result['time_total_s']}s\n")
    return result
 
 
def main():
    parser = argparse.ArgumentParser(
        description="Profile DocuMind pipeline — respects ChromaDB cache like the GUI"
    )
    parser.add_argument("--pdf_dir", required=True,
                        help="Directory containing PDFs (searched recursively)")
    parser.add_argument("--out", default="profiling_results",
                        help="Output directory for JSON files (default: profiling_results)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only profile first N PDFs (smoke-test)")
    args = parser.parse_args()
 
    pdf_dir = Path(args.pdf_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
 
    pdfs = sorted(pdf_dir.rglob("*.pdf"))
    if args.limit:
        pdfs = pdfs[:args.limit]
 
    if not pdfs:
        print(f"No PDFs found in {pdf_dir}")
        return
 
    print(f"Found {len(pdfs)} PDF(s) in {pdf_dir}\n{'─'*60}")
 
    lc, vs = build_components()
 
    summary = []
 
    for pdf_path in pdfs:
        print(f"[doc] {pdf_path.name}")
        result = profile_pdf(str(pdf_path), lc, vs)
 
        out_file = out_dir / f"{pdf_path.stem}.json"
        with open(out_file, "w") as f:
            json.dump(result, f, indent=2)
 
        summary.append(result)
 
    summary_file = out_dir / "_summary.json"
    with open(summary_file, "w") as f:
        json.dump({
            "profiled_at": datetime.now().isoformat(),
            "pdf_dir":     str(pdf_dir),
            "n_pdfs":      len(summary),
            "results":     summary,
        }, f, indent=2)
 
    # ── summary table ─────────────────────────────────────────────────────────
    w = 74
    print(f"{'═'*w}")
    print(f"  Results → {out_dir}/")
    print(f"{'─'*w}")
    print(f"  {'PDF':<34} {'mode':>6} {'pg':>3} {'chk':>4} {'tok':>6} "
          f"{'win':>3} {'total(s)':>9}")
    print(f"  {'─'*34} {'─'*6} {'─'*3} {'─'*4} {'─'*6} {'─'*3} {'─'*9}")
 
    for r in summary:
        name = r["pdf"][:34]
        if r["error"]:
            print(f"  {name:<34} ERROR: {r['error'][:28]}")
            continue
        mode  = r["mode"]
        pages = str(r["page_count"])  if r["page_count"]  else "—"
        chks  = str(r["chunk_count"]) if r["chunk_count"] else "—"
        toks  = str(r["token_count"]) if r["token_count"] else "—"
        wins  = str(r["window_count"])if r["window_count"]else "—"
        print(f"  {name:<34} {mode:>6} {pages:>3} {chks:>4} {toks:>6} "
              f"{wins:>3} {r['time_total_s']:>9.2f}s")
 
    print(f"{'═'*w}")
    print(f"\n  Run again on the same --pdf_dir to see cached load times.\n")
 
 
if __name__ == "__main__":
    main()
