"""
Generate exam paper PDF with answer key at the end from stored MCQ JSONs
"""
import json
import random 
import argparse

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors


def load_questions_from_json(json_dir):
    """Load all questions from all JSON files in the specified directory"""
    questions = [] 
    for json_file in Path(json_dir).glob("mcq_*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            questions.extend(data["questions"])
    return questions 

def jumble_options(question):
    """Randomly shuffle options and update correct answer accordingly"""
    letters = ["A", "B", "C", "D"]
    options = list(question["options"].items())
    random.shuffle(options)

    new_options = {}
    new_correct = ""
    for new_letter, (old_letter, text) in zip(letters, options):
        new_options[new_letter] = text
        if old_letter == question["correct_answer"]:
            new_correct = new_letter
    
    return {**question, "options": new_options, "correct_answer": new_correct}

def generate_exam_pdf(questions, output_path, title="Exam Paper"):
    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    question_style = ParagraphStyle("Q", parent=styles["Normal"], spaceAfter=4, spaceBefore=6)
    option_style = ParagraphStyle("Opt", parent=styles["Normal"], leftIndent=20, spaceAfter=2)

    story = []

    # --- Questions section ---
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))

    for i, q in enumerate(questions, 1):
        story.append(Paragraph(f"<b>Q{i}.</b> {q['question']}", question_style))
        for letter, text in q["options"].items():
            story.append(Paragraph(f"{letter}) {text}", option_style))
        story.append(Spacer(1, 0.2 * inch))

    # --- Answer key section on new page ---
    story.append(PageBreak())
    story.append(Paragraph("Answer Key", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))

    # build grid: 5 answers per row
    answers = [f"{i}. {q['correct_answer']}" for i, q in enumerate(questions, 1)]
    cols = 5
    rows = [answers[i:i+cols] for i in range(0, len(answers), cols)]
    # pad last row
    while len(rows[-1]) < cols:
        rows[-1].append("")

    table = Table(rows, colWidths=[1.1 * inch] * cols)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.whitesmoke, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)

    doc.build(story)
    print(f"[PaperGen] Exam paper saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exam Paper Generator")
    parser.add_argument("--json-dir", default="mcq_output", help="Directory with MCQ JSON files")
    parser.add_argument("--num", type=int, default=10, help="Number of questions to sample")
    parser.add_argument("--output-dir", default="exam_output", help="Output directory")
    parser.add_argument("--title", default="Exam Paper", help="Title for the exam")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)

    all_questions = load_questions_from_json(args.json_dir)
    print(f"[PaperGen] Loaded {len(all_questions)} total questions")

    if len(all_questions) < args.num:
        print(f"[PaperGen] Warning: only {len(all_questions)} available, using all")
        sampled = all_questions
    else:
        sampled = random.sample(all_questions, args.num)

    sampled = [jumble_options(q) for q in sampled]

    Path(args.output_dir).mkdir(exist_ok=True)
    generate_exam_pdf(sampled, Path(args.output_dir) / "exam.pdf", title=args.title)