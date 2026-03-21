"""
MCQ evaluation for DocuMind
"""

import os
import sys
import re
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
from src.doc_processing.late_chunking   import LateChunking
from src.doc_processing.ragpipeline     import RAGPipeline
from src.doc_processing.vector_store    import VectorStore
from src.doc_processing.text_extraction import Extraction

MIN_EXPLANATION_WORDS = 20
OVERLAP_THRESHOLD     = 0.75


def build_pipeline():
    print("[init] Loading model and tokenizer...")
    lc = LateChunking(model_name=config.MODEL, tokenizer_name=config.TOKENIZER)
    db_path = PROJECT_ROOT / "chroma_db"
    vs = VectorStore(persist_dir=str(db_path))
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in .env")
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



def parse_options(text):
    """
    Extract options A-D from MCQ response.
    Handles formats like:
        A) text   A. text   **A)** text   A: text
    Returns dict {A: text, B: text, C: text, D: text} or empty dict.
    """
    pattern = re.findall(
        r'\*?\*?([A-D])\*?\*?[\)\.:\s]\s*\*?\*?(.*?)(?=\n\*?\*?[A-D]\*?\*?[\)\.:\s]|\n\n|$)',
        text, re.DOTALL
    )
    options = {}
    for letter, content in pattern:
        clean = re.sub(r'\*+', '', content).strip()
        if clean:
            options[letter] = clean
    return options


def parse_answer(text):
    """
    Extract the marked correct answer letter from the response.
    Looks for patterns like:
        Answer: B   Correct Answer: C   **Answer: A**
        The correct answer is B
    """
    patterns = [
        r'\*?\*?(?:correct\s+)?answer\s*[:\-]\s*\*?\*?\s*([A-D])',
        r'the correct answer is\s+([A-D])',
        r'answer\s+is\s+([A-D])',
        r'\*\*([A-D])\*\*\s+is correct',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return None


def parse_explanation(text):
    """Extract explanation text after 'Explanation:' marker."""
    m = re.search(
        r'\*?\*?explanation\s*[:\-]\*?\*?\s*(.*?)(?=\(source page|$)',
        text, re.IGNORECASE | re.DOTALL
    )
    if m:
        return re.sub(r'\*+', '', m.group(1)).strip()
    return ""


def parse_citation(text):
    """Check if source page citation is present."""
    return bool(re.search(r'\(source page.*?\)', text, re.IGNORECASE))


def jaccard_similarity(a, b):
    """Simple word-level Jaccard similarity between two strings."""
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def check_format_valid(options, answer):
    """All four options present and answer is one of A-D."""
    return len(options) == 4 and answer in ('A', 'B', 'C', 'D')


def check_answer_extractable(answer):
    return answer is not None


def check_has_explanation(explanation):
    words = explanation.split()
    return len(words) >= MIN_EXPLANATION_WORDS


def check_citation_present(text):
    return parse_citation(text)


def check_no_option_overlap(options):
    """Return True if no two options are too similar."""
    letters = list(options.keys())
    for i in range(len(letters)):
        for j in range(i + 1, len(letters)):
            sim = jaccard_similarity(options[letters[i]], options[letters[j]])
            if sim > OVERLAP_THRESHOLD:
                return False
    return True


def evaluate_mcq_response(response_text):
    options     = parse_options(response_text)
    answer      = parse_answer(response_text)
    explanation = parse_explanation(response_text)

    fmt_valid      = check_format_valid(options, answer)
    ans_extract    = check_answer_extractable(answer)
    has_expl       = check_has_explanation(explanation)
    citation       = check_citation_present(response_text)
    no_overlap     = check_no_option_overlap(options) if len(options) == 4 else False

    return {
        "format_valid":        fmt_valid,
        "answer_extractable":  ans_extract,
        "has_explanation":     has_expl,
        "citation_present":    citation,
        "no_option_overlap":   no_overlap,
        "parsed_options":      options,
        "parsed_answer":       answer,
        "parsed_explanation":  explanation[:200] if explanation else "",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Automatic MCQ evaluation — reuses eval_set.json"
    )
    parser.add_argument("--eval_set", required=True,
                        help="Path to eval_set.json")
    parser.add_argument("--pdf_dir",  required=True,
                        help="Root directory containing PDFs (searched recursively)")
    parser.add_argument("--out", default="evaluation/mcq_results.json",
                        help="Output JSON file")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only run first N questions (smoke-test)")
    args = parser.parse_args()

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

    print(f"Running {len(eval_set)} MCQ evaluations\n{'─'*70}")

    for item in eval_set:
        found = find_pdf(pdf_dir, item["document"])
        if found is None:
            print(f"[skip] {item['document']} not found")
            continue

        pdf_path = str(found)
        if pdf_path != last_pdf:
            print(f"\n[doc] {item['document']}  ({found.parent.name})")
            load_document(pipeline, pdf_path)
            last_pdf = pdf_path

        question = item["question"]

        t0 = time.perf_counter()
        try:
            response = pipeline.query_mcq(question)
            error    = None
        except Exception as e:
            response = ""
            error    = str(e)
        elapsed = round(time.perf_counter() - t0, 3)

        metrics = evaluate_mcq_response(response)

        row = {
            "id":               item["id"],
            "document":         item["document"],
            "question":         question,
            "correct_page":     item.get("correct_page"),
            "response_time_s":  elapsed,
            "error":            error,
            "raw_response":     response,
            **metrics,
        }
        results.append(row)

        status = " ".join([
            "FMT" if metrics["format_valid"]       else "fmt",
            "ANS" if metrics["answer_extractable"] else "ans",
            "EXP" if metrics["has_explanation"]    else "exp",
            "CIT" if metrics["citation_present"]   else "cit",
            "OVL" if metrics["no_option_overlap"]  else "ovl",
        ])
        ans = metrics["parsed_answer"] or "?"
        print(f"  [Q{item['id']:03d}] {status}  ans={ans}  {elapsed}s"
              + (f"  ERR:{error[:40]}" if error else ""))

    n = len(results)

    def rate(key):
        if n == 0:
            return None
        return round(sum(1 for r in results if r.get(key) is True) / n * 100, 1)

    aggregate = {
        "n_evaluated":          n,
        "format_valid_pct":     rate("format_valid"),
        "answer_extractable_pct": rate("answer_extractable"),
        "has_explanation_pct":  rate("has_explanation"),
        "citation_present_pct": rate("citation_present"),
        "no_option_overlap_pct": rate("no_option_overlap"),
        "avg_response_time_s":  round(
            sum(r["response_time_s"] for r in results) / n, 3
        ) if n else None,
        "errors":               sum(1 for r in results if r["error"]),
    }

    output = {
        "meta": {
            "run_at":   datetime.now().isoformat(),
            "eval_set": args.eval_set,
            "pdf_dir":  str(pdf_dir),
            "n_total":  len(eval_set),
            "n_run":    n,
            "min_explanation_words": MIN_EXPLANATION_WORDS,
            "overlap_threshold":     OVERLAP_THRESHOLD,
        },
        "aggregate": aggregate,
        "results":   results,
    }

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    w = 60
    print(f"\n{'═'*w}")
    print(f"  Saved to              : {out_path}")
    print(f"{'─'*w}")
    print(f"  Questions evaluated   : {n}")
    print(f"  Errors                : {aggregate['errors']}")
    print(f"  Avg response time     : {aggregate['avg_response_time_s']}s")
    print(f"{'─'*w}")
    print(f"  Format valid          : {aggregate['format_valid_pct']}%")
    print(f"  Answer extractable    : {aggregate['answer_extractable_pct']}%")
    print(f"  Has explanation       : {aggregate['has_explanation_pct']}%")
    print(f"  Citation present      : {aggregate['citation_present_pct']}%")
    print(f"  No option overlap     : {aggregate['no_option_overlap_pct']}%")
    print(f"{'═'*w}\n")


if __name__ == "__main__":
    main()
