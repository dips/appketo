import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
import random

st.set_page_config(layout="wide")
st.title("🥑 Smart Personalized Keto Diet Plan")

# ---------------------------
# Safe Comparison Helper
# ---------------------------

def is_higher(value, threshold):
    return value is not None and value > threshold

# ---------------------------
# PDF Extraction
# ---------------------------

def extract_pdf_data(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    text = re.sub(r'\s+', ' ', text)

    return {
        "HbA1c (%)": extract_value(text, r'HbA1c.*?(\d{1,2}\.?\d{0,2})\s?%'),
        "Fasting Glucose (mg/dL)": extract_value(text, r'Blood Sugar Fasting.*?(\d{2,3}\.?\d*)\s?mg'),
        "Vitamin D (ng/mL)": extract_value(text, r'Vitamin D.*?(\d{1,3}\.?\d*)\s?ng'),
        "Vitamin B12 (pg/mL)": extract_value(text, r'Vitamin B12.*?(\d{2,4}\.?\d*)\s?pg'),
        "HDL (mg/dL)": extract_value(text, r'HDL.*?(\d{2,3}\.?\d*)\s?mg'),
        "LDL (mg/dL)": extract_value(text, r'LDL CHOLESTEROL.*?(\d{2,3}\.?\d*)\s?mg'),
        "Triglycerides (mg/dL)": extract_value(text, r'Triglycerides.*?(\d{2,4}\.?\d*)\s?mg')
    }

def extract_value(text, pattern):
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None

# ---------------------------
# Health Summary
# ---------------------------

def summarize_health_markers(data):
    summary = []
    supplements = []

    if is_higher(data.get("Fasting Glucose (mg/dL)"), 110):
        summary.append("⚠️ High fasting glucose: pre-diabetes risk")
    if is_higher(data.get("HbA1c (%)"), 5.7):
        summary.append("⚠️ HbA1c indicates pre-diabetes or diabetes")
    if data.get("Vitamin D (ng/mL)") is not None and data["Vitamin D (ng/mL)"] < 30:
        summary.append("⚠️ Vitamin D deficiency")
        supplements.append("- Vitamin D3 (2000–5000 IU/day)")
    if data.get("Vitamin B12 (pg/mL)") is not None and data["Vitamin B12 (pg/mL)"] < 300:
        summary.append("⚠️ Vitamin B12 borderline low")
        supplements.append("- Methylcobalamin (1500 mcg, 3x/week)")
    if data.get("HDL (mg/dL)") is not None and data["HDL (mg/dL)"] < 40:
        summary.append("⚠️ Low HDL – increase omega-3 & exercise")
    if is_higher(data.get("LDL (mg/dL)"), 130):
        summary.append("⚠️ High LDL cholesterol")
    if is_higher(data.get("Triglycerides (mg/dL)"), 150):
        summary.append("⚠️ High triglycerides")

    if not summary:
        summary.append("✅ All markers appear normal.")
    return summary, supplements

def recommend_macros(data):
    macros = {"Protein": 20, "Fat": 70, "Carbs": 5, "Fiber": 5}

    if is_higher(data.get("HbA1c (%)"), 5.7) or is_higher(data.get("Fasting Glucose (mg/dL)"), 110):
        macros.update({"Fat": 70, "Protein": 20})
    if is_higher(data.get("Triglycerides (mg/dL)"), 150):
        macros.update({"Fat": 65, "Protein": 25})
    if is_higher(data.get("LDL (mg/dL)"), 130):
        macros.update({"Fat": 60, "Protein": 25, "Fiber": 10})

    return macros

# ---------------------------
# Descriptive Meal Generator
# ---------------------------

def generate_custom_plan(is_veg, likes, dislikes):
    meals = {
        "protein": ["paneer", "tofu", "eggs", "chicken", "fish", "lentils"],
        "veggies": ["spinach", "broccoli", "cauliflower", "zucchini", "mushroom"],
        "fats": ["ghee", "olive oil", "butter", "coconut oil", "chia seeds", "avocado"],
        "others": ["flaxseed", "almond flour", "cucumber", "greek yogurt", "moong soup"]
    }

    if is_veg:
        meals["protein"] = [i for i in meals["protein"] if i not in ["chicken", "fish", "eggs"]]

    def filter_and_prioritize(category):
        return [item for item in category if item not in dislikes]

    def build_meal():
        protein = random.choice(filter_and_prioritize(meals["protein"])) if meals["protein"] else "protein"
        veg = random.choice(filter_and_prioritize(meals["veggies"])) if meals["veggies"] else "veggies"
        fat = random.choice(filter_and_prioritize(meals["fats"])) if meals["fats"] else "fat"
        extra = random.choice(filter_and_prioritize(meals["others"])) if meals["others"] else "side"

        meal = f"{protein.capitalize()} cooked in {fat}, with sautéed {veg} and a side of {extra}"
        favorites = [i for i in [protein, veg, fat, extra] if any(l in i for l in likes)]
        if favorites:
            meal += f" (contains your favorite: {', '.join(set(favorites))})"
        return meal

    plan = []
    for i in range(7):
        plan.append({
            "Day": f"Day {i+1}",
            "Breakfast": build_meal(),
            "Lunch": build_meal(),
            "Dinner": build_meal()
        })
    return pd.DataFrame(plan)

# ---------------------------
# Streamlit UI
# ---------------------------

uploaded_file = st.file_uploader("📤 Upload your blood report (PDF or CSV)", type=["pdf", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        values = extract_pdf_data(uploaded_file)
    elif uploaded_file.name.endswith(".csv"):
        df_csv = pd.read_csv(uploaded_file)
        values = df_csv.iloc[0].to_dict()
    else:
        st.error("Unsupported file type.")
        st.stop()

    st.subheader("📋 Extracted Health Markers")
    st.write(values)

    st.subheader("🔍 Health Summary")
    summary, supplements = summarize_health_markers(values)
    for s in summary:
        st.markdown(f"- {s}")
    if supplements:
        st.subheader("💊 Supplement Suggestions")
        for s in supplements:
            st.markdown(s)

    st.subheader("⚖️ Macronutrient Targets")
    macro = recommend_macros(values)
    st.write(pd.DataFrame.from_dict(macro, orient='index', columns=["% of total calories"]))

    st.subheader("🍽️ Customize Your Meal Plan")
    meal_type = st.radio("Meal Preference:", ["Vegetarian", "Non-Vegetarian"])
    is_veg = meal_type == "Vegetarian"

    ingredients = ["paneer", "eggs", "spinach", "tofu", "avocado", "chicken", "fish", "mushroom", "chia seeds", "yogurt", "ghee", "coconut oil", "zucchini"]
    likes = st.multiselect("✅ Favorite Ingredients", ingredients)
    dislikes = st.multiselect("❌ Ingredients to Avoid", ingredients)

    st.subheader("📅 7-Day Personalized Keto Plan")
    plan_df = generate_custom_plan(is_veg, [i.lower() for i in likes], [i.lower() for i in dislikes])
    st.dataframe(plan_df)

    csv = plan_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Meal Plan", csv, "keto_custom_plan.csv", "text/csv")
else:
    st.info("Upload your blood report (PDF or CSV) to generate your personalized plan.")
