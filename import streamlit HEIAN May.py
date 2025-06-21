import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# Cấu hình giao diện
st.set_page_config(page_title="PDF Table Extractor", layout="wide")
st.title("📄 PDF Table Extractor")
st.markdown("Upload one or more PDF files to extract information into a single table.")

# Upload nhiều file PDF
uploaded_files = st.file_uploader("Upload PDF file(s)", type=["pdf"], accept_multiple_files=True)

def extract_info_from_pdf(file):
    row_count = 0
    qty_nested_val = None
    sheet_count = None
    kit_count = None
    material_summary = "Unknown"
    current_date = datetime.now().strftime("%-m/%-d/%Y")
    filename = file.name

    with pdfplumber.open(file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"

        # Trích thông tin tổng quan
        match = re.search(r"(\d+(?:\.\d+)?)\s*Sheet\(s\)\s*=\s*(\d+(?:\.\d+)?)\s*Kit\(s\)", full_text, re.IGNORECASE)
        if match:
            sheet_count = float(match.group(1))
            kit_count = float(match.group(2))

        match_qty = re.search(r"Qty Nested[:\s]+(\d+(?:\.\d+)?)", full_text, re.IGNORECASE)
        if match_qty:
            qty_nested_val = float(match_qty.group(1))

        if "PLYWOOD" in full_text.upper():
            material_summary = "PLY"
        elif "OSB" in full_text.upper():
            material_summary = "OSB"

        # Đếm dòng trong bảng – bỏ dòng chứa "Part ID"
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        if row and not any("Part ID" in str(cell) for cell in row):
                            if not any(cell and "Yield:" in str(cell) for cell in row):
                                row_count += 1

    return {
        "Date": current_date,
        "Program": filename,
        "Per Sheet": row_count,
        "Total Part": qty_nested_val if qty_nested_val is not None else "N/A",
        "Frame per Kit": sheet_count if sheet_count is not None else "N/A",
        "Total of Table": kit_count if kit_count is not None else "N/A",
        "Material": material_summary
    }

# Gộp dữ liệu nhiều file vào 1 bảng
if uploaded_files:
    results = [extract_info_from_pdf(f) for f in uploaded_files]
    final_df = pd.DataFrame(results)
    st.subheader("📋 Combined Result Table")
    st.dataframe(final_df, use_container_width=True)
