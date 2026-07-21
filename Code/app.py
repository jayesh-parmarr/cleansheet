import streamlit as st

from ingestion import load_file

SAMPLE_PATH = "datasets/retail_store_sales.csv"

st.set_page_config(page_title="Cleansheet", page_icon="📊", layout="wide")
st.title("Cleansheet")
st.caption("Upload a messy spreadsheet, see what's actually in it.")


# ---------------------------------------------------------------- loading

@st.cache_data(show_spinner="Reading file...")
def load_sample():
    return load_file(SAMPLE_PATH)


@st.cache_data(show_spinner="Reading file...")
def load_upload(file_bytes: bytes, filename: str):
    """Cached on the file's bytes, so it only re-parses when the file changes."""
    import io
    return load_file(io.BytesIO(file_bytes), filename=filename)


with st.sidebar:
    st.header("Data source")
    source = st.radio("Choose one", ["Sample data", "Upload my own"], label_visibility="collapsed")

    uploaded = None
    if source == "Upload my own":
        uploaded = st.file_uploader("Spreadsheet", type=["csv", "xlsx", "xls"])

try:
    if source == "Sample data":
        df = load_sample()
    elif uploaded is not None:
        df = load_upload(uploaded.getvalue(), uploaded.name)
    else:
        st.info("Upload a file in the sidebar to get started.")
        st.stop()
except ValueError as e:
    st.error(str(e))
    st.stop()
except Exception as e:
    st.error(f"Couldn't read that file: {e}")
    st.stop()


# ---------------------------------------------------------------- overview

rows, cols = df.shape
missing_cells = int(df.isna().sum().sum())
duplicate_rows = int(df.duplicated().sum())

a, b, c, d = st.columns(4)
a.metric("Rows", f"{rows:,}")
b.metric("Columns", cols)
c.metric("Missing cells", f"{missing_cells:,}")
d.metric("Duplicate rows", f"{duplicate_rows:,}")


# ---------------------------------------------------------------- tabs

preview_tab, missing_tab, types_tab, stats_tab = st.tabs(
    ["Preview", "Missing values", "Column types", "Summary stats"]
)

with preview_tab:
    n = st.slider("Rows to show", 5, 100, 5)
    st.dataframe(df.head(n), width="stretch")


with missing_tab:
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    if missing.empty:
        st.success("No missing values found.")
    else:
        report = missing.to_frame("missing")
        report["percent"] = (report["missing"] / rows * 100).round(1)
        st.dataframe(report, width="stretch")

        st.bar_chart(report["percent"])
        st.caption(
            f"{len(missing)} of {cols} columns have gaps. "
            "High percentages usually mean the column is optional or the export is broken."
        )


with types_tab:
    types = df.dtypes.astype(str).to_frame("dtype")
    types["unique"] = df.nunique()
    types["sample"] = [
        df[c].dropna().iloc[0] if df[c].notna().any() else "—" for c in df.columns
    ]
    st.dataframe(types, width="stretch")
    st.caption(
        "Columns showing `object` are stored as text. "
        "If a number or date column appears here, it needs converting."
    )


with stats_tab:
    numeric = df.select_dtypes("number")
    if numeric.empty:
        st.info("No numeric columns detected.")
    else:
        st.dataframe(numeric.describe().T, width="stretch")