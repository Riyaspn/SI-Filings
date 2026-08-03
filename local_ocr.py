"""
Local OCR Engine — 100% Offline Scanned PDF Text & Table Extractor
==================================================================
Extracts text and table rows from image-based/scanned PDF pages
using RapidOCR / Tesseract locally. Zero cloud API keys required.

Features:
  - Uses pypdfium2 to render PDF pages into crisp images (2x scale)
  - Uses RapidOCR (ONNX Runtime) for fast, accurate local OCR
  - Groups OCR text boxes by vertical Y-coordinates into table rows
  - Returns extracted text lines & rows formatted for parser_engine
"""

import os
from typing import List, Dict, Any, Optional, Tuple

import pypdfium2 as pdfium
from PIL import Image


# ============================================================
# Local OCR Initializer
# ============================================================

_ocr_engine = None
_table_engine = None

def get_ocr_engine():
    """Lazy initialize the RapidOCR engine."""
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ocr_engine = RapidOCR()
        except ImportError:
            _ocr_engine = "fallback"
    return _ocr_engine


def get_table_engine():
    """Lazy initialize the RapidTable engine (PaddleOCR PP-Structure SLANet)."""
    global _table_engine
    if _table_engine is None:
        try:
            from rapid_table import RapidTable
            _table_engine = RapidTable()
        except ImportError:
            _table_engine = None
    return _table_engine


def is_local_ocr_available() -> bool:
    """Check if local OCR (RapidOCR or Tesseract) is installed."""
    try:
        from rapidocr_onnxruntime import RapidOCR
        return True
    except ImportError:
        try:
            import pytesseract
            return True
        except ImportError:
            return False


# ============================================================
# Page Image Rendering
# ============================================================

def render_pdf_page_to_image(filepath: str, page_idx: int, scale: float = 2.0) -> Image.Image:
    """
    Render a specific PDF page to a high-res PIL Image using pypdfium2.
    
    Args:
        filepath: Path to PDF file
        page_idx: 0-based page index
        scale: Resolution scale (2.0 = 144 DPI, optimal for OCR)
    """
    pdf = pdfium.PdfDocument(filepath)
    page = pdf[page_idx]
    bitmap = page.render(scale=scale)
    pil_image = bitmap.to_pil()
    pdf.close()
    return pil_image


# ============================================================
# OCR Text & Row Extraction
# ============================================================

def extract_text_from_scanned_page(
    filepath: str, 
    page_idx: int,
    line_threshold_px: int = 15
) -> Tuple[List[str], List[List[str]], List[Dict]]:
    """
    Perform local OCR on a single scanned PDF page.
    
    Returns:
        - text_lines: List of full text lines reconstructed from OCR
        - rows: List of split table rows [label, col1, col2, ...]
        - ocr_boxes: List of bounding box dictionaries mimicking pdfplumber [{'text', 'x0', 'top'}]
    """
    # Render page image
    img = render_pdf_page_to_image(filepath, page_idx, scale=2.0)

    engine = get_ocr_engine()

    ocr_boxes = []

    if engine != "fallback" and engine is not None:
        # RapidOCR
        import numpy as np
        img_np = np.array(img)
        result, _ = engine(img_np)

        if result:
            for item in result:
                bbox, text, score = item[0], item[1], item[2]
                try:
                    score_val = float(score)
                except (ValueError, TypeError):
                    score_val = 0.8

                if score_val > 0.3 and str(text).strip():
                    # bbox format: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                    y_top = float(bbox[0][1])
                    x_left = float(bbox[0][0])
                    ocr_boxes.append({
                        "text": str(text).strip(),
                        "x0": x_left,
                        "top": y_top,
                        "score": score_val
                    })
    else:
        # Pytesseract Fallback
        try:
            import pytesseract
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text = data["text"][i].strip()
                if text:
                    ocr_boxes.append({
                        "text": text,
                        "x0": data["left"][i],
                        "top": data["top"][i],
                        "score": float(data["conf"][i]) / 100.0 if "conf" in data else 0.8
                    })
        except Exception:
            pass

    if not ocr_boxes:
        return [], [], []

    # Sort boxes vertically by top coordinate
    ocr_boxes.sort(key=lambda b: (b["top"], b["x0"]))

    # Group boxes into horizontal lines based on Y coordinate proximity
    lines_grouped = []
    current_line = [ocr_boxes[0]]

    for box in ocr_boxes[1:]:
        # If Y difference is within threshold, it's on the same line
        if abs(box["top"] - current_line[-1]["top"]) <= line_threshold_px:
            current_line.append(box)
        else:
            # Sort current line horizontally by X coordinate
            current_line.sort(key=lambda b: b["x0"])
            lines_grouped.append(current_line)
            current_line = [box]

    if current_line:
        current_line.sort(key=lambda b: b["x0"])
        lines_grouped.append(current_line)

    # Reconstruct text lines and table rows
    text_lines = []
    table_rows = []

    for line_boxes in lines_grouped:
        line_str = "  ".join(b["text"] for b in line_boxes)
        text_lines.append(line_str)

        row_cells = [b["text"] for b in line_boxes]
        table_rows.append(row_cells)

    return text_lines, table_rows, ocr_boxes


def extract_scanned_pdf_pages(
    filepath: str, 
    page_indices: List[int]
) -> Tuple[List[str], List[List[str]], List[Dict]]:
    """
    Run local OCR across multiple scanned PDF pages.
    
    Args:
        filepath: Path to PDF file
        page_indices: List of 0-based page indices to OCR
    """
    all_text_lines = []
    all_table_rows = []
    all_ocr_boxes = []

    for idx in page_indices:
        try:
            lines, rows, boxes = extract_text_from_scanned_page(filepath, idx)
            all_text_lines.extend(lines)
            all_table_rows.extend(rows)
            for b in boxes:
                b["page_idx"] = idx
            all_ocr_boxes.extend(boxes)
        except Exception as e:
            print(f"Error running local OCR on page {idx+1}: {e}")

    return all_text_lines, all_table_rows, all_ocr_boxes


def extract_rapid_tables_from_scanned_pdf(filepath: str, page_indices: List[int]) -> List[List[List[str]]]:
    """
    Extract structured table rows from scanned PDF pages using RapidTable (PaddleOCR PP-Structure).
    
    Returns a list of 2D string matrices (rows x cols) for all extracted tables.
    """
    table_engine = get_table_engine()
    if not table_engine:
        return []
        
    import numpy as np
    import pandas as pd
    from io import StringIO
    
    extracted_tables = []
    
    for idx in page_indices:
        try:
            pil_img = render_pdf_page_to_image(filepath, idx, scale=2.0)
            img_np = np.array(pil_img)
            res = table_engine(img_np)
            table_html = ""
            if hasattr(res, "html"):
                table_html = getattr(res, "html")
            elif hasattr(res, "pred_html"):
                table_html = getattr(res, "pred_html")
            elif isinstance(res, (list, tuple)):
                table_html = res[0]
            elif isinstance(res, dict):
                table_html = res.get("html", "")
            else:
                table_html = str(res)
            
            if table_html and "<table" in str(table_html).lower():
                try:
                    dfs = pd.read_html(StringIO(table_html))
                    for df in dfs:
                        df = df.fillna("")
                        rows_2d = df.astype(str).values.tolist()
                        if rows_2d:
                            extracted_tables.append(rows_2d)
                except Exception as e:
                    print(f"Error parsing HTML from RapidTable page {idx+1}: {e}")
        except Exception as e:
            print(f"Error running RapidTable on page {idx+1}: {e}")
            
    return extracted_tables
