# app.py
import streamlit as st
from ingestion import load_file

st.title("Cleansheet")

uploaded = st.file_uploader("Upload a spreadsheet", type=["csv", "xlsx", "xls"])

if uploaded:
    try:
        df = load_file(uploaded, filename=uploaded.name)
        st.success(f"Successfully loaded your \"{uploaded.name}\" file and has {df.shape[0]:,} rows × {df.shape[1]} columns")
        st.dataframe(df.head(5))
    except ValueError as e:
        st.error(str(e))

if st.button("Try it with sample data"):
    df = load_file(f"datasets/retail_store_sales.csv")
    
    df_columns = df.columns.tolist()
    # st.write(df_columns)
    for col in df_columns:
        # st.write(col)
        # st.write(df[col].isna().sum())
        if df[col].isna().sum() > 0:
            st.warning(f"Column '{col}' has missing values.")
            