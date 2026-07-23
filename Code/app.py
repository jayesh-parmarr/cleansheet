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
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stHeader"]           { background: transparent; }
[data-testid="stSidebar"]          { display: none; }

/* ── Landing cards ── */
.choice-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 2rem;
    height: 100%;
    transition: border-color 0.2s;
}
.choice-card:hover { border-color: #58a6ff; }
.choice-icon  { font-size: 2.5rem; margin-bottom: 0.75rem; }
.choice-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #e6edf3;
    margin-bottom: 0.4rem;
}
.choice-desc  { font-size: 0.85rem; color: #8b949e; line-height: 1.6; margin-bottom: 1.25rem; }
.choice-pill  {
    display: inline-block;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 0.2rem 0.75rem;
    font-size: 0.75rem;
    color: #8b949e;
    margin: 0.2rem 0.2rem 0 0;
}

/* ── Hero (landing) ── */
.landing-hero {
    text-align: center;
    padding: 3.5rem 1rem 2.5rem;
}
.landing-title {
    font-size: 3rem;
    font-weight: 800;
    color: #e6edf3;
    letter-spacing: -1px;
    margin-bottom: 0.5rem;
}
.landing-sub {
    font-size: 1.05rem;
    color: #8b949e;
    max-width: 480px;
    margin: 0 auto;
}

/* ── Dashboard top bar ── */
.dash-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #21262d;
}
.dash-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #e6edf3;
    margin: 0;
}
.dash-badge {
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 0.2rem 0.75rem;
    font-size: 0.78rem;
    color: #8b949e;
}

/* ── KPI cards ── */
.kpi-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1.1rem 1rem;
    text-align: center;
}
.kpi-value   { font-size: 1.75rem; font-weight: 700; margin: 0; line-height: 1.1; }
.kpi-label   { font-size: 0.72rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.07em; margin-top: 0.3rem; }
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
    margin: 0.75rem 0 1.25rem;
    font-size: 0.88rem;
    color: #c9d1d9;
    line-height: 1.6;
}

/* ── Section divider ── */
.section-sep { border: none; border-top: 1px solid #21262d; margin: 1.25rem 0; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 0.35rem; }
button[data-baseweb="tab"]        { border-radius: 8px 8px 0 0 !important; }

/* ── Dataframes ── */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

/* ── Divider text ── */
.or-divider {
    text-align: center;
    color: #30363d;
    font-size: 0.85rem;
    padding: 2rem 0 0;
    letter-spacing: 0.1em;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Reading file…")
def load_sample():
    return load_file(SAMPLE_PATH)


@st.cache_data(show_spinner="Reading file…")
def load_upload(file_bytes: bytes, filename: str):
    return load_file(io.BytesIO(file_bytes), filename=filename)


def kpi(value, label, tone="neutral"):
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-value kpi-{tone}">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f"</div>"
    )


def reset_to_landing():
    for k in ["chosen_source", "wdf", "_src_key", "uploaded_bytes", "uploaded_name"]:
        st.session_state.pop(k, None)
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# LANDING PAGE  (shown until user picks a source)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.get("chosen_source") is None:

    st.markdown("""
    <div class="landing-hero">
        <div class="landing-title">🧹 Cleansheet</div>
        <p class="landing-sub">
            Upload a messy spreadsheet and get instant data-quality insights — then fix it.
        </p>
    </div>
    """, unsafe_allow_html=True)

    left_card, spacer, right_card = st.columns([5, 1, 5])

    # ── Left: sample dataset ──────────────────────────────────────────────────
    with left_card:
        st.markdown("""
        <div class="choice-card">
            <div class="choice-icon">📊</div>
            <div class="choice-title">Try the sample dataset</div>
            <div class="choice-desc">
                A real-world retail sales dataset, pre-loaded and ready to explore.
                Great for a quick tour of what Cleansheet can do.
            </div>
            <span class="choice-pill">9,994 rows</span>
            <span class="choice-pill">Real-world gaps</span>
            <span class="choice-pill">No upload needed</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        if st.button("Use sample dataset", type="primary", use_container_width=True):
            st.session_state["chosen_source"] = "sample"
            st.rerun()

    # ── Right: file upload ────────────────────────────────────────────────────
    with right_card:
        st.markdown("""
        <div class="choice-card">
            <div class="choice-icon">⬆</div>
            <div class="choice-title">Upload your own file</div>
            <div class="choice-desc">
                Drop a CSV or Excel file below. Your data stays in this browser session
                and is never stored on any server.
            </div>
            <span class="choice-pill">CSV</span>
            <span class="choice-pill">XLSX</span>
            <span class="choice-pill">XLS</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Drag & drop or click to browse",
            type=["csv", "xlsx", "xls"],
            label_visibility="collapsed",
        )
        if uploaded is not None:
            st.session_state["chosen_source"] = "upload"
            st.session_state["uploaded_bytes"] = uploaded.getvalue()
            st.session_state["uploaded_name"] = uploaded.name
            st.rerun()

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD  (shown after source is chosen)
# ══════════════════════════════════════════════════════════════════════════════

# ── Load raw dataframe ────────────────────────────────────────────────────────
chosen = st.session_state["chosen_source"]
try:
    if chosen == "sample":
        _raw_df = load_sample()
        _src_key = "sample"
        _file_label = "retail_store_sales.csv"
    else:
        _raw_df = load_upload(
            st.session_state["uploaded_bytes"],
            st.session_state["uploaded_name"],
        )
        _src_key = st.session_state["uploaded_name"]
        _file_label = _src_key
except ValueError as exc:
    st.error(str(exc))
    if st.button("Go back"):
        reset_to_landing()
    st.stop()
except Exception as exc:
    st.error(f"Couldn't read that file: {exc}")
    if st.button("Go back"):
        reset_to_landing()
    st.stop()

# ── Session-state working copy ────────────────────────────────────────────────
if st.session_state.get("_src_key") != _src_key:
    st.session_state["_src_key"] = _src_key
    st.session_state["wdf"] = _raw_df.copy()

df: pd.DataFrame = st.session_state["wdf"]

# ── Top bar ───────────────────────────────────────────────────────────────────
bar_left, bar_right = st.columns([7, 1])
with bar_left:
    st.markdown(
        f'<div class="dash-bar">'
        f'<span class="dash-title">🧹 Cleansheet</span>'
        f'<span class="dash-badge">📄 {_file_label}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
with bar_right:
    if st.button("⬅ Change dataset", use_container_width=True):
        reset_to_landing()

# ── Summary stats ─────────────────────────────────────────────────────────────
rows, cols_n = df.shape
missing_cells  = int(df.isna().sum().sum())
duplicate_rows = int(df.duplicated().sum())
total_cells    = rows * cols_n
pct_missing    = missing_cells / total_cells * 100 if total_cells else 0
health         = max(0, round(100 - pct_missing - (duplicate_rows / rows * 5 if rows else 0)))

# ── KPI row ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(kpi(f"{rows:,}", "Rows"), unsafe_allow_html=True)
c2.markdown(kpi(cols_n, "Columns"), unsafe_allow_html=True)
c3.markdown(kpi(f"{missing_cells:,}", "Missing Cells",
                "bad" if missing_cells else "good"), unsafe_allow_html=True)
c4.markdown(kpi(f"{duplicate_rows:,}", "Duplicate Rows",
                "warn" if duplicate_rows else "good"), unsafe_allow_html=True)
c5.markdown(kpi(f"{health}%", "Health Score",
                "good" if health >= 90 else ("warn" if health >= 70 else "bad")),
            unsafe_allow_html=True)

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

# ── Main tabs ─────────────────────────────────────────────────────────────────
overview_tab, clean_tab, transform_tab, plot_tab = st.tabs(
    ["📋  Overview", "🧹  Clean Data", "🔧  Transform Columns", "📈  Plot Graphs"]
)

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
        types_df["Null Count"]    = df.isna().sum()
        types_df["Sample Value"]  = [
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

    if not cols_with_missing:
        st.success("Your data has no missing values — nothing to clean! 🎉")
    else:
        st.markdown("""
        <div class="info-callout">
            Select a column, pick a strategy, then hit <strong>Apply</strong>.
            Changes live in your session — download when you're done.
        </div>
        """, unsafe_allow_html=True)

        left, right = st.columns([1, 2])
        with left:
            selected_col = st.selectbox(
                "Column to fix",
                cols_with_missing,
                format_func=lambda c: f"{c}  ({df[c].isna().sum()} missing)",
            )

        col_idx   = df.columns.get_loc(selected_col)
        col_series = df[selected_col]
        n_missing  = int(col_series.isna().sum())
        pct        = round(n_missing / rows * 100, 1)
        is_numeric = pd.api.types.is_numeric_dtype(col_series)

        with right:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Missing",        f"{n_missing:,}")
            m2.metric("Missing %",      f"{pct}%")
            m3.metric("Type",           str(col_series.dtype))
            m4.metric("Unique (non-null)", int(col_series.nunique()))

        st.markdown("<hr class='section-sep'>", unsafe_allow_html=True)
        st.markdown("**Strategy**")

        strategies = (
            ["Fill with Mean", "Fill with Median", "Fill with Mode",
             "Linear Interpolation", "Fill with Custom Value", "Drop rows"]
            if is_numeric
            else ["Fill with Mode", "Fill with Custom Value", "Drop rows"]
        )
        strategy = st.radio("strategy", strategies, horizontal=True,
                            label_visibility="collapsed")

        custom_val = None
        if strategy == "Fill with Custom Value":
            custom_val = st.text_input("Custom fill value",
                                       placeholder="e.g.  0   or   Unknown")

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
                    if not custom_val or not custom_val.strip():
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

        st.markdown("<hr class='section-sep'>", unsafe_allow_html=True)
        st.markdown("**Column preview** (first 20 rows)")
        st.dataframe(
            df[[selected_col]].head(20).style.highlight_null(color="#3d1a1a"),
            use_container_width=True,
        )

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
        st.caption(f"{int(df.isna().sum().sum()):,} missing cells remain")


# ════════════════════════════════════════════════════════════════════════════════
# TRANSFORM COLUMNS TAB
# ════════════════════════════════════════════════════════════════════════════════
with transform_tab:
    st.info("Column transformations coming soon.")
    st.dataframe(df.head(10), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# PLOT GRAPHS TAB
# ════════════════════════════════════════════════════════════════════════════════
with plot_tab:
    st.info("Graph builder coming soon.")
