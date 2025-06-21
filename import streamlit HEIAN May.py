import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# Cấu hình giao diện
st.set_page_config(page_title="PDF Table Extractor", layout="wide")
st.title("📄 PDF Table Extractor")
st.markdown("Upload PDF files to extract table information and metadata.")

# Giao diện upload nhiều file
uploaded_files = st.file_uploader("Upload PDF file(s)", type=["pdf"], accept_multiple_files=True)

# Hàm xử lý từng file PDF
def extract_info_from_pdf(file):
    row_count = 0
    qty_nested_val = None
    sheet_count = None
    kit_count = None
    material_summary = "Unknown"

    current_date = datetime.now().strftime("%-m/%-d/%Y")
    filename = file.name

    with pdfplumber.open(file) as pdf:
        # Trích toàn bộ text để tìm thông tin
        full_text = ""
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"

        # Tìm Sheet(s) và Kit(s)
        match = re.search(r"(\d+(?:\.\d+)?)\s*Sheet\(s\)\s*=\s*(\d+(?:\.\d+)?)\s*Kit\(s\)", full_text, re.IGNORECASE)
        if match:
            sheet_count = float(match.group(1))
            kit_count = float(match.group(2))

        # Tìm Qty Nested
        match_qty = re.search(r"Qty Nested[:\s]+(\d+(?:\.\d+)?)", full_text, re.IGNORECASE)
        if match_qty:
            qty_nested_val = float(match_qty.group(1))

        # Xác định loại vật liệu
        if "PLYWOOD" in full_text.upper():
            material_summary = "PLY"
        elif "OSB" in full_text.upper():
            material_summary = "OSB"

        # Duyệt từng bảng để đếm dòng (không tính header)
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table and len(table) > 1:
                        data_rows = table[1:]  # Bỏ dòng header
                        clean_rows = [
                            row for row in data_rows
                            if not any(cell and "Yield:" in str(cell) for cell in row)
                        ]
                        row_count += len(clean_rows)

    # Tạo dataframe kết quả
    info_df = pd.DataFrame([{
        "Date": current_date,
        "Program": filename,
        "Per Sheet": row_count,
        "Total Part": qty_nested_val if qty_nested_val is not None else "N/A",
        "Frame per Kit": sheet_count if sheet_count is not None else "N/A",
        "Total of Table": kit_count if kit_count is not None else "N/A",
        "Material": material_summary
    }])

    return info_df

# Danh sách lưu kết quả nhiều file
all_info = []

# Nếu có file được upload
if uploaded_files:
    for uploaded_file in uploaded_files:
        info_df = extract_info_from_pdf(uploaded_file)
        st.subheader(f"📄 File: `{uploaded_file.name}`")
        st.dataframe(info_df, use_container_width=True)
        all_info.append(info_df)

    # Gộp kết quả lại nếu cần dùng tiếp
    if all_info:
        combined_df = pd.concat(all_info, ignore_index=True)
