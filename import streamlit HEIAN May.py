import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# Cấu hình giao diện
st.set_page_config(page_title="PDF Extractor", layout="wide")
st.title("📄 PDF Table Extractor")
st.markdown("Upload one or more PDF files to extract and combine table information.")

# Tải nhiều file PDF
uploaded_files = st.file_uploader("Upload PDF file(s)", type=["pdf"], accept_multiple_files=True)

# Xử lý từng file
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

        # Tìm Sheet(s) và Kit(s)
        match = re.search(r"(\d+(?:\.\d+)?)\s*Sheet\(s\)\s*=\s*(\d+(?:\.\d+)?)\s*Kit\(s\)", full_text, re.IGNORECASE)
        if match:
            sheet_count = float(match.group(1))
            kit_count = float(match.group(2))

        # Tìm Qty Nested
        match_qty = re.search(r"Qty Nested[:\s]+(\d+(?:\.\d+)?)", full_text, re.IGNORECASE)
        if match_qty:
            qty_nested_val = float(match_qty.group(1))

        # Xác định vật liệu
        if "PLYWOOD" in full_text.upper():
            material_summary = "PLY"
        elif "OSB" in full_text.upper():
            material_summary = "OSB"

        # Đếm dòng bảng (bỏ dòng chứa từ khóa)
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        if any(
                            cell and any(keyword in str(cell).upper() for keyword in ["MATERIAL", "YIELD", "PART ID"])
                            for cell in row
                        ):
                            continue
                        row_count += 1

    # Trả kết quả dưới dạng dict (1 dòng)
    return {
        "Date": current_date,
        "Program": filename,
        "Per Sheet": row_count,
        "Total Part": qty_nested_val if qty_nested_val is not None else "N/A",
        "Frame per Kit": sheet_count if sheet_count is not None else "N/A",
        "Total of Table": kit_count if kit_count is not None else "N/A",
        "Material": material_summary
    }

# Gộp kết quả tất cả file
if uploaded_files:
    all_data = [extract_info_from_pdf(f) for f in uploaded_files]
    final_df = pd.DataFrame(all_data)
    
    st.subheader("📋 Combined Table")
    st.dataframe(final_df, use_container_width=True)

    # Tải Excel (tuỳ chọn)
    excel_data = final_df.to_excel(index=False, engine='openpyxl')
    st.download_button("⬇️ Download Excel", data=excel_data, file_name="combined_result.xlsx")
