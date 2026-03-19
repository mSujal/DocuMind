# import fitz
# import re
#
# class Extraction:
#     @staticmethod
#     def extract_page_text(page):
#         page_width = page.rect.width
#         all_chars = []
#
#         data = page.get_text("rawdict")
#         for block in data["blocks"]:
#             if block["type"] != 0:
#                 continue
#             for line in block["lines"]:
#                 for span in line["spans"]:
#                     span_size = span.get("size", 10)
#                     for char in span["chars"]:
#                         all_chars.append({
#                             "text": char["c"],
#                             "x0": char["bbox"][0],
#                             "x1": char["bbox"][2],
#                             "top": char["bbox"][1],
#                             "size": span_size
#                         })
#
#         if not all_chars:
#             return ""
#
#         mid_left = page_width * 0.4
#         mid_right = page_width * 0.6
#         chars_in_middle = [c for c in all_chars if mid_left < c["x0"] < mid_right]
#         is_two_column = len(chars_in_middle) < len(all_chars) * 0.05
#
#         def chars_to_text(char_list):
#             if not char_list:
#                 return ""
#             lines = {}
#             for c in char_list:
#                 y = round(c["top"] / (c["size"] * 0.5)) * round(c["size"] * 0.5)
#                 lines.setdefault(y, []).append(c)
#
#             result = []
#             for y in sorted(lines):
#                 line_chars = sorted(lines[y], key=lambda c: c["x0"])
#
#                 gaps = [line_chars[i]["x0"] - line_chars[i-1]["x1"]
#                         for i in range(1, len(line_chars))
#                         if line_chars[i]["x0"] - line_chars[i-1]["x1"] >= 0]
# 
#                 if gaps:
#                     median_gap = sorted(gaps)[len(gaps) // 2]
#                     space_threshold = max(median_gap * 2.5, line_chars[0]["size"] * 0.3)
#                 else:
#                     space_threshold = line_chars[0]["size"] * 0.3
#
#                 line = ""
#                 for i, c in enumerate(line_chars):
#                     if i == 0:
#                         line += c["text"]
#                     else:
#                         prev = line_chars[i - 1]
#                         if c["x0"] - prev["x1"] > space_threshold:
#                             line += " "
#                         line += c["text"]
#                 result.append(line.strip())
#             return "\n".join(r for r in result if r)
#
#         if is_two_column:
#             midpoint = page_width / 2
#             left_chars  = [c for c in all_chars if c["x0"] <= midpoint]
#             right_chars = [c for c in all_chars if c["x0"] >  midpoint]
#             return chars_to_text(left_chars) + "\n\n" + chars_to_text(right_chars)
#         else:
#             return chars_to_text(all_chars)
#
#     @staticmethod
#     def clean_text(text):
#         # Fix hyphenated line break
#         text = re.sub(r'-\n(\w)', r'\1', text)
#         # Collapse multiple spaces
#         text = re.sub(r'  +', ' ', text)
#         # Collapse 3+ newlines
#         text = re.sub(r'\n{3,}', '\n\n', text)
#         return text.strip()   
#
#     @staticmethod
#     def extract_text(pdf_path):
#         doc = fitz.open(pdf_path)
#         pages = [Extraction.extract_page_text(page) for page in doc]
#         doc.close()
#         text = Extraction.clean_text('\n\n'.join(pages))
#         print(text)
#         return text
#
#

import pymupdf4llm

class Extraction:

    @staticmethod
    def extract_text(pdf_path):
        """
        Returns list of (page_num, clean_text) tuples, one per oage chunk
        """
        page_chunks = pymupdf4llm.to_text(pdf_path, page_chunks=True, show_progress=False)
        return [
            (chunk["metadata"]["page_number"], chunk["text"].strip()) for chunk in page_chunks if chunk["text"].strip()
        ]

