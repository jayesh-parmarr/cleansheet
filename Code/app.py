import io
from pathlib import Path

import pandas as pd
import streamlit as st

from clean import (
    fill_missing_values_interpolation,
    fill_missing_values_mean,
    fill_missing_values_median,
    fill_missing_values_mode,
    fill_missing_values_specific_value,
    remove_missing_values,
)
from ingestion import load_file

SAMPLE_PATH = Path(__file__).parent.parent / "datasets" / "retail_store_sales.csv"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Cleansheet", page_icon="🧹", layout="wide")

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] {
    background: #0d1117;
}
[data-testid="stHeader"] { background: transparent; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #161b22;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] .stRadio label { color: #c9d1d9 !important; }

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f3460 100%);
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 1.75rem 2rem;
    margin-bottom: 1.75rem;
}
.hero-title {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.5px;
}
.hero-sub {
    color: #8b949e;
    font-size: 0.95rem;
    margin: 0;
}

/* ── Metric cards ── */
.kpi-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1.1rem 1rem;
    text-align: center;
    height: 100%;
}
.kpi-value {
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0;
    line-height: 1.1;
}
.kpi-label {
    font-size: 0.72rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-top: 0.3rem;
}
.kpi-neutral { color: #58a6ff; }
.kpi-good    { color: #3fb950; }
.kpi-warn    { color: #e3b341; }
.kpi-bad     { color: #f85149; }

/* ── Info callout ── */
.info-callout {
    background: #0d1117;
    border-left: 3px solid #58a6ff;
    border-radius: 0 8px 8px 0;
    padding: 0.85rem 1.1rem;
    margin: 0.75rem 0 1.25rem 0;
    font-size: 0.88rem;
    color: #c9d1d9;
    line-height: 1.6;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 4rem 1rem;
    color: #8b949e;
}
.empty-icon { font-size: 3.5rem; margin-bottom: 1rem; }
.empty-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: #c9d1d9;
    margin-bottom: 0.4rem;
}

/* ── Section divider ── */
.section-sep {
    border: none;
    border-top: 1px solid #21262d;
    margin: 1.25rem 0;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 0.35rem; }
button[data-baseweb="tab"] {
    border-radius: 8px 8px 0 0 !important;
}

/* ── Dataframes ── */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-title">🧹 Cleansheet</div>
    <p class="hero-sub">Upload a messy spreadsheet and get instant data-quality insights — then fix it.</p>
</div>
""", unsafe_allow_html=True)


# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Reading file…")
def load_sample():
    return load_file(SAMPLE_PATH)


@st.cache_data(show_spinner="Reading file…")
def load_upload(file_bytes: bytes, filename: str):
    return load_file(io.BytesIO(file_bytes), filename=filename)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Data Source")
    source = st.radio(
        "source",
        ["📊 Sample dataset", "⬆ Upload my own file"],
        label_visibility="collapsed",
    )

    uploaded = None
    if "Upload" in source:
        st.markdown("---")
        uploaded = st.file_uploader(
            "Drag & drop or browse",
            type=["csv", "xlsx", "xls"],
            label_visibility="visible",
        )
        if uploaded:
            st.success(f"✅ {uploaded.name}")

    st.markdown("---")
    st.caption("Supported formats: CSV · XLSX · XLS")


# ── Load raw dataframe ────────────────────────────────────────────────────────
try:
    if "Sample" in source:
        _raw_df = load_sample()
        _src_key = "sample"
    elif uploaded is not None:
        _raw_df = load_upload(uploaded.getvalue(), uploaded.name)
        _src_key = uploaded.name
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📂</div>
            <div class="empty-title">No file loaded yet</div>
            <div>Pick <strong>Sample dataset</strong> in the sidebar or upload your own CSV / Excel file.</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Couldn't read that file: {exc}")
    st.stop()


# ── Session-state working copy ────────────────────────────────────────────────
# Reset whenever the source changes so cleaning history doesn't bleed across files.
if st.session_state.get("_src_key") != _src_key:
    st.session_state["_src_key"] = _src_key
    st.session_state["wdf"] = _raw_df.copy()

df: pd.DataFrame = st.session_state["wdf"]


# ── Summary stats ─────────────────────────────────────────────────────────────
rows, cols_n = df.shape
missing_cells = int(df.isna().sum().sum())
duplicate_rows = int(df.duplicated().sum())
total_cells = rows * cols_n
pct_missing = missing_cells / total_cells * 100 if total_cells else 0
health = max(0, round(100 - pct_missing - (duplicate_rows / rows * 5 if rows else 0)))

# ── KPI row ───────────────────────────────────────────────────────────────────
def kpi(value, label, tone="neutral"):
    return f"""
    <div class="kpi-card">
        <div class="kpi-value kpi-{tone}">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>"""


c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(kpi(f"{rows:,}", "Rows"), unsafe_allow_html=True)
c2.markdown(kpi(cols_n, "Columns"), unsafe_allow_html=True)
c3.markdown(
    kpi(f"{missing_cells:,}", "Missing Cells", "bad" if missing_cells else "good"),
    unsafe_allow_html=True,
)
c4.markdown(
    kpi(f"{duplicate_rows:,}", "Duplicate Rows", "warn" if duplicate_rows else "good"),
    unsafe_allow_html=True,
)
c5.markdown(
    kpi(
        f"{health}%",
        "Health Score",
        "good" if health >= 90 else ("warn" if health >= 70 else "bad"),
    ),
    unsafe_allow_html=True,
)

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

# ── Main tabs ─────────────────────────────────────────────────────────────────
overview_tab, clean_tab = st.tabs(["📋  Overview", "🧹  Clean Data"])


# ════════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ════════════════════════════════════════════════════════════════════════════════
with overview_tab:
    preview_sub, missing_sub, dupes_sub, types_sub, stats_sub = st.tabs(
        ["Preview", "Missing Values", "Duplicates", "Column Types", "Summary Stats"]
    )

    with preview_sub:
        n = st.slider("Rows to show", 5, min(200, rows), 10)
        st.dataframe(df.head(n), use_container_width=True)

    with missing_sub:
        missing_s = df.isna().sum()
        missing_s = missing_s[missing_s > 0].sort_values(ascending=False)

        if missing_s.empty:
            st.success("No missing values — data looks clean! ✨")
        else:
            report = missing_s.to_frame("Missing")
            report["% of Rows"] = (report["Missing"] / rows * 100).round(1)
            report["Severity"] = report["% of Rows"].apply(
                lambda x: "🔴 High" if x > 20 else ("🟡 Medium" if x > 5 else "🟢 Low")
            )

            col_a, col_b = st.columns([3, 2])
            with col_a:
                st.dataframe(
                    report.style.background_gradient(subset=["% of Rows"], cmap="YlOrRd"),
                    use_container_width=True,
                )
            with col_b:
                st.markdown("**Missing % by column**")
                st.bar_chart(report["% of Rows"])

            st.caption(
                f"{len(missing_s)} of {cols_n} columns have gaps. "
                "Columns above 20% are flagged High — consider dropping them."
            )

    with dupes_sub:
        if duplicate_rows == 0:
            st.success("No duplicate rows found. ✨")
        else:
            st.warning(f"{duplicate_rows:,} duplicate rows detected.")
            st.dataframe(df[df.duplicated()], use_container_width=True)

    with types_sub:
        types_df = df.dtypes.astype(str).to_frame("Type")
        types_df["Unique Values"] = df.nunique()
        types_df["Null Count"] = df.isna().sum()
        types_df["Sample Value"] = [
            str(df[c].dropna().iloc[0]) if df[c].notna().any() else "—"
            for c in df.columns
        ]
        st.dataframe(types_df, use_container_width=True)
        st.caption(
            "Columns typed `object` are stored as text. "
            "Numbers or dates appearing here need type conversion."
        )

    with stats_sub:
        numeric = df.select_dtypes("number")
        if numeric.empty:
            st.info("No numeric columns detected.")
        else:
            st.dataframe(
                numeric.describe().T.style.background_gradient(subset=["mean"], cmap="Blues"),
                use_container_width=True,
            )


# ════════════════════════════════════════════════════════════════════════════════
# CLEAN DATA TAB
# ════════════════════════════════════════════════════════════════════════════════
with clean_tab:
    cols_with_missing = df.columns[df.isna().any()].tolist()

    # ── No issues ─────────────────────────────────────────────────────────────
    if not cols_with_missing:
        st.success("Your data has no missing values — nothing to clean! 🎉")
    else:
        st.markdown("""
        <div class="info-callout">
            Select a column, pick a strategy, then hit <strong>Apply</strong>.
            All changes are applied to your in-session copy — download when you're done.
        </div>
        """, unsafe_allow_html=True)

        # ── Column picker ──────────────────────────────────────────────────────
        left, right = st.columns([1, 2])

        with left:
            selected_col = st.selectbox(
                "Column to fix",
                cols_with_missing,
                format_func=lambda c: f"{c}  ({df[c].isna().sum()} missing)",
            )

        col_idx = df.columns.get_loc(selected_col)
        col_series = df[selected_col]
        n_missing = int(col_series.isna().sum())
        pct = round(n_missing / rows * 100, 1)
        is_numeric = pd.api.types.is_numeric_dtype(col_series)

        with right:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Missing", f"{n_missing:,}")
            m2.metric("Missing %", f"{pct}%")
            m3.metric("Type", str(col_series.dtype))
            m4.metric("Unique (non-null)", int(col_series.nunique()))

        st.markdown("<hr class='section-sep'>", unsafe_allow_html=True)

        # ── Strategy picker ────────────────────────────────────────────────────
        if is_numeric:
            strategies = [
                "Fill with Mean",
                "Fill with Median",
                "Fill with Mode",
                "Linear Interpolation",
                "Fill with Custom Value",
                "Drop rows",
            ]
        else:
            strategies = [
                "Fill with Mode",
                "Fill with Custom Value",
                "Drop rows",
            ]

        st.markdown("**Strategy**")
        strategy = st.radio("strategy", strategies, horizontal=True, label_visibility="collapsed")

        custom_val = None
        if strategy == "Fill with Custom Value":
            custom_val = st.text_input(
                "Custom fill value",
                placeholder="e.g.  0   or   Unknown",
            )

        apply_col, reset_col, _ = st.columns([1, 1, 6])

        with apply_col:
            apply = st.button("✅ Apply", type="primary")
        with reset_col:
            reset = st.button("↩ Reset column")

        if apply:
            try:
                wdf = st.session_state["wdf"]
                if strategy == "Fill with Mean":
                    wdf = fill_missing_values_mean(wdf, col_idx)
                elif strategy == "Fill with Median":
                    wdf = fill_missing_values_median(wdf, col_idx)
                elif strategy == "Fill with Mode":
                    wdf = fill_missing_values_mode(wdf, col_idx)
                elif strategy == "Linear Interpolation":
                    wdf = fill_missing_values_interpolation(wdf, col_idx)
                elif strategy == "Fill with Custom Value":
                    if custom_val is None or custom_val.strip() == "":
                        st.warning("Enter a custom value first.")
                        st.stop()
                    typed_val: object = custom_val
                    if is_numeric:
                        try:
                            typed_val = float(custom_val)
                        except ValueError:
                            pass
                    wdf = fill_missing_values_specific_value(wdf, col_idx, typed_val)
                elif strategy == "Drop rows":
                    wdf = remove_missing_values(wdf, col_idx)

                st.session_state["wdf"] = wdf
                st.success(f"Applied **{strategy}** to `{selected_col}`.")
                st.rerun()
            except Exception as exc:
                st.error(f"Error: {exc}")

        if reset:
            st.session_state["wdf"][selected_col] = _raw_df[selected_col]
            st.success(f"Reset `{selected_col}` to original values.")
            st.rerun()

        # ── Column preview ─────────────────────────────────────────────────────
        st.markdown("<hr class='section-sep'>", unsafe_allow_html=True)
        st.markdown("**Column preview** (first 20 rows)")
        st.dataframe(
            df[[selected_col]].head(20).style.highlight_null(color="#3d1a1a"),
            use_container_width=True,
        )

    # ── Download ───────────────────────────────────────────────────────────────
    st.markdown("<hr class='section-sep'>", unsafe_allow_html=True)
    st.markdown("**Export cleaned data**")

    dl1, dl2, _ = st.columns([1, 1, 6])
    with dl1:
        st.download_button(
            "⬇ Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="cleansheet_export.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
    with dl2:
        remaining = int(df.isna().sum().sum())
        st.caption(f"{remaining:,} missing cells remain")
