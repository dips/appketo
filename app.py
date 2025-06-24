import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🧬 Keto Nutrition Dashboard")

# Helper functions
def extract_pdf_data(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()

    return {
        "Fasting Glucose (mg/dL)": extract_value(text, r'Fasting Glucose[:\-]?\s?(\d+\.?\d*)'),
        "HbA1c (%)": extract_value(text, r'HbA1c[:\-]?\s?(\d+\.?\d*)'),
        "LDL (mg/dL)": extract_value(text, r'LDL[:\-]?\s?(\d+\.?\d*)'),
        "HDL (mg/dL)": extract_value(text, r'HDL[:\-]?\s?(\d+\.?\d*)'),
        "Triglycerides (mg/dL)": extract_value(text, r'Triglycerides[:\-]?\s?(\d+\.?\d*)')
    }

def extract_value(text, pattern):
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None

def get_date_from_filename(name):
    match = re.search(r'(\d{4}-\d{2}-\d{2})', name)
    return pd.to_datetime(match.group(1)) if match else pd.Timestamp.now()

# File uploader
files = st.file_uploader("Upload blood reports (PDF or CSV)", type=["pdf", "csv"], accept_multiple_files=True)

if files:
    all_data = []

    for f in files:
        date = get_date_from_filename(f.name)

        if f.name.endswith(".pdf"):
            data = extract_pdf_data(f)
        elif f.name.endswith(".csv"):
            df_csv = pd.read_csv(f)
            data = df_csv.iloc[0].to_dict()
        else:
            continue

        data["Date"] = date
        all_data.append(data)

    df_all = pd.DataFrame(all_data).sort_values("Date")
    st.subheader("📋 Extracted Report Data")
    st.dataframe(df_all)

    st.subheader("📈 Trends Over Time")
    for col in df_all.columns:
        if col != "Date":
            st.line_chart(df_all.set_index("Date")[col])

    # Basic Keto Recommendation
    st.subheader("🧠 Keto Recommendation")
    last = df_all.iloc[-1]
    advice = []

    if last["HbA1c (%)"] and last["HbA1c (%)"] > 5.7:
        advice.append("- Consider low-carb keto to improve insulin sensitivity.")
    if last["LDL (mg/dL)"] and last["LDL (mg/dL)"] > 130:
        advice.append("- Use olive oil, nuts, seeds. Limit saturated fat.")
    if last["HDL (mg/dL)"] and last["HDL (mg/dL)"] < 40:
        advice.append("- Include more healthy fats like avocados and fish.")

    if advice:
        st.markdown("\n".join(advice))
    else:
        st.markdown("Your markers look good. A well-balanced keto plan is suitable.")

else:
    st.info("📤 Upload at least one PDF or CSV report to start.")
