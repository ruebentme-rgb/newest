"""
APRIL Bilateral Facilities Dashboard
Streamlit app — upload your APRIL_Bilateral_Facilities_dd_*.xlsx file and explore.

Requirements:
    pip install streamlit pandas openpyxl plotly
Run:
    streamlit run april_bilateral_facilities.py
"""

import io
import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="APRIL Bilateral Facilities",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #1f4e79;
        margin-bottom: 8px;
    }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #1f4e79; }
    .metric-label { font-size: 0.82rem; color: #555; margin-top: 2px; }
    .section-header {
        font-size: 1.1rem; font-weight: 600; color: #1f4e79;
        border-bottom: 2px solid #1f4e79; padding-bottom: 4px; margin-top: 20px;
    }
    div[data-testid="stDataFrame"] { border-radius: 8px; }
    .stTabs [data-baseweb="tab"] { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
EXCEL_EPOCH = date(1899, 12, 30)

def excel_serial_to_date(val):
    """Convert Excel date serial to Python date, return None otherwise."""
    try:
        n = float(str(val).strip())
        if 30000 < n < 60000:          # plausible range: ~1982–2064
            return EXCEL_EPOCH + pd.Timedelta(days=int(n))
    except (ValueError, TypeError):
        pass
    return None

def parse_date_field(val):
    """Best-effort date extraction from messy date strings."""
    if pd.isna(val) or str(val).strip().lower() in ("n/a", "negotiating", "undefined", ""):
        return None
    s = str(val).strip()
    # Try excel serial first
    d = excel_serial_to_date(s)
    if d:
        return d
    # Try to pull last dd/mm/yyyy or d/m/yyyy from the string
    matches = re.findall(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b", s)
    if matches:
        day, month, year = matches[-1]
        year = int(year)
        if year < 100:
            year += 2000
        try:
            return date(year, int(month), int(day))
        except ValueError:
            pass
    return None

def parse_quantum(val):
    """Return numeric facility size or None."""
    if pd.isna(val):
        return None
    s = str(val).replace(",", "").strip()
    # Take first number if multiple values separated by spaces
    parts = s.split()
    for p in parts:
        try:
            v = float(p)
            if v > 0:
                return v
        except ValueError:
            continue
    return None

def fmt_usd(v):
    if pd.isna(v) or v is None:
        return "—"
    if v >= 1e9:
        return f"USD {v/1e9:.2f}B"
    if v >= 1e6:
        return f"USD {v/1e6:.1f}M"
    return f"USD {v:,.0f}"

OFFICE_LABELS = {
    "HK": "Hong Kong",
    "SG": "Singapore",
    "UAE": "UAE / Middle East",
    "ID": "Indonesia",
    "MY": "Malaysia",
    "IN": "India",
}

# ─────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────
@st.cache_data(show_spinner="Reading workbook…")
def load_data(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=0,
        header=0,
        dtype=str,
    )
    # Normalise column names
    df.columns = [str(c).strip() for c in df.columns]
    # Drop fully-empty rows
    df.dropna(how="all", inplace=True)

    # The source has two header-like columns: "Bank Name" + unnamed col for office code
    # Detect the unnamed column right after Bank Name
    cols = list(df.columns)
    bn_idx = next((i for i, c in enumerate(cols) if "bank" in c.lower() and "name" in c.lower()), 0)
    # Rename unnamed/Unnamed col right after Bank Name → "Office"
    if bn_idx + 1 < len(cols) and ("unnamed" in cols[bn_idx + 1].lower() or cols[bn_idx + 1] == ""):
        cols[bn_idx + 1] = "Office"
        df.columns = cols

    # Standardise expected column names (flexible matching)
    rename_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if "bank" in cl and "name" in cl:
            rename_map[c] = "Bank Name"
        elif cl == "office":
            rename_map[c] = "Office"
        elif "borrower" in cl:
            rename_map[c] = "Borrower"
        elif "date" in cl:
            rename_map[c] = "Date of Facility"
        elif "currency" in cl:
            rename_map[c] = "Currency"
        elif "quantum" in cl:
            rename_map[c] = "Quantum"
        elif "type" in cl and "facility" in cl:
            rename_map[c] = "Type"
        elif "tenure" in cl:
            rename_map[c] = "Tenure"
        elif "status" in cl:
            rename_map[c] = "Status"
        elif "security" in cl:
            rename_map[c] = "Security Package"
    df.rename(columns=rename_map, inplace=True)

    # Ensure all expected columns exist
    for col in ["Bank Name", "Office", "Borrower", "Date of Facility",
                "Currency", "Quantum", "Type", "Tenure", "Status", "Security Package"]:
        if col not in df.columns:
            df[col] = None

    # Clean strings
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col].replace({"nan": None, "None": None, "": None}, inplace=True)

    # Derived columns
    df["Facility Date"] = df["Date of Facility"].apply(parse_date_field)
    df["Quantum (USD)"] = df["Quantum"].apply(parse_quantum)
    df["Office Label"] = df["Office"].map(OFFICE_LABELS).fillna(df["Office"])
    df["Is Negotiating"] = df["Status"].str.lower().str.contains("negotiat", na=False)
    df["Is Current"] = df["Status"].str.lower().str.contains("current", na=False)

    return df


# ─────────────────────────────────────────────
# Sidebar — file upload + filters
# ─────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/APRIL_Group_logo.svg/320px-APRIL_Group_logo.svg.png",
        width=140,
    )
    st.markdown("### 📂 Upload File")
    uploaded = st.file_uploader(
        "APRIL Bilateral Facilities (.xlsx)",
        type=["xlsx"],
        help="Upload the APRIL_Bilateral_Facilities_dd_*.xlsx file",
    )
    st.divider()

    if uploaded:
        raw = load_data(uploaded.read())

        st.markdown("### 🔍 Filters")

        offices = sorted([x for x in raw["Office"].dropna().unique()])
        sel_offices = st.multiselect("Office", options=offices, default=offices)

        statuses = sorted([x for x in raw["Status"].dropna().unique()])
        sel_statuses = st.multiselect("Status", options=statuses, default=statuses)

        facility_types = sorted([x for x in raw["Type"].dropna().unique()])
        sel_types = st.multiselect("Facility Type", options=facility_types, default=facility_types)

        currencies = sorted([x for x in raw["Currency"].dropna().unique()])
        sel_currencies = st.multiselect("Currency", options=currencies, default=currencies)

        borrowers_all = sorted(set(
            b.strip()
            for row in raw["Borrower"].dropna()
            for b in re.split(r"[,\s]+", str(row))
            if b.strip() and len(b.strip()) >= 2
        ))
        sel_borrowers = st.multiselect("Borrower Entity", options=borrowers_all)

        st.divider()
        st.caption("APRIL Group — Bilateral Facilities Tracker  \nData as at 02 Jun 2026")


# ─────────────────────────────────────────────
# Main content
# ─────────────────────────────────────────────
st.markdown("## 🏦 APRIL Bilateral Facilities Dashboard")
st.caption("Bilateral credit facilities across APRIL Group entities | Source: APRIL Treasury / Legal")

if not uploaded:
    st.info("👈 Upload your APRIL Bilateral Facilities .xlsx file in the sidebar to begin.")
    st.stop()

# Apply filters
df = raw.copy()
if sel_offices:
    df = df[df["Office"].isin(sel_offices)]
if sel_statuses:
    df = df[df["Status"].isin(sel_statuses)]
if sel_types:
    df = df[df["Type"].isin(sel_types)]
if sel_currencies:
    df = df[df["Currency"].isin(sel_currencies)]
if sel_borrowers:
    df = df[df["Borrower"].apply(
        lambda x: any(b in str(x) for b in sel_borrowers)
    )]

if df.empty:
    st.warning("No records match the current filters.")
    st.stop()

# ─────────────────────────────────────────────
# KPI row
# ─────────────────────────────────────────────
total = len(df)
current_count = df["Is Current"].sum()
neg_count = df["Is Negotiating"].sum()
total_usd = df.loc[df["Currency"] == "USD", "Quantum (USD)"].sum()
banks_count = df["Bank Name"].nunique()

c1, c2, c3, c4, c5 = st.columns(5)
for col, label, value in [
    (c1, "Total Facilities", total),
    (c2, "Current", current_count),
    (c3, "Negotiating", neg_count),
    (c4, "Unique Banks", banks_count),
    (c5, "USD Quantum (known)", fmt_usd(total_usd)),
]:
    col.markdown(
        f'<div class="metric-card"><div class="metric-value">{value}</div>'
        f'<div class="metric-label">{label}</div></div>',
        unsafe_allow_html=True,
    )

st.divider()

# ─────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 All Facilities",
    "📊 Analytics",
    "🗺️ By Office",
    "🏢 By Bank",
    "🔎 Search",
])

# ── Tab 1: Full table ──────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">All Facilities</div>', unsafe_allow_html=True)

    display_cols = [
        "Bank Name", "Office Label", "Borrower", "Date of Facility",
        "Currency", "Quantum", "Type", "Tenure", "Status", "Security Package",
    ]
    display_df = df[[c for c in display_cols if c in df.columns]].copy()
    display_df.fillna("—", inplace=True)

    # Colour-code Status
    def highlight_status(row):
        s = str(row.get("Status", ""))
        if "Current" in s:
            return ["background-color: #e6f4ea"] * len(row)
        elif "Negotiat" in s:
            return ["background-color: #fff3cd"] * len(row)
        else:
            return [""] * len(row)

    st.dataframe(
        display_df.style.apply(highlight_status, axis=1),
        use_container_width=True,
        height=520,
    )

    # Download
    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️  Export filtered table (.csv)",
        data=csv,
        file_name=f"APRIL_Bilateral_Filtered_{date.today()}.csv",
        mime="text/csv",
    )

# ── Tab 2: Analytics ──────────────────────────────────────────
with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        # Status breakdown
        st.markdown('<div class="section-header">Status Breakdown</div>', unsafe_allow_html=True)
        status_counts = df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig = px.pie(
            status_counts, values="Count", names="Status",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.45,
        )
        fig.update_layout(margin=dict(t=10, b=10), legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Facility type breakdown
        st.markdown('<div class="section-header">Facility Type Mix</div>', unsafe_allow_html=True)
        type_counts = df["Type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        fig2 = px.bar(
            type_counts, x="Count", y="Type", orientation="h",
            color="Count", color_continuous_scale="Blues",
        )
        fig2.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False, yaxis_title=None)
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        # Office distribution
        st.markdown('<div class="section-header">Facilities by Office</div>', unsafe_allow_html=True)
        off_counts = df["Office Label"].value_counts().reset_index()
        off_counts.columns = ["Office", "Count"]
        fig3 = px.bar(
            off_counts, x="Office", y="Count",
            color="Office", color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig3.update_layout(margin=dict(t=10, b=10), showlegend=False, xaxis_title=None)
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        # USD quantum by office
        st.markdown('<div class="section-header">USD Quantum by Office</div>', unsafe_allow_html=True)
        usd_df = df[df["Currency"] == "USD"].groupby("Office Label")["Quantum (USD)"].sum().reset_index()
        usd_df.columns = ["Office", "Total USD"]
        usd_df = usd_df.sort_values("Total USD", ascending=False)
        fig4 = px.bar(
            usd_df, x="Office", y="Total USD",
            color="Office", color_discrete_sequence=px.colors.qualitative.Safe,
            labels={"Total USD": "Total (USD)"},
        )
        fig4.update_layout(margin=dict(t=10, b=10), showlegend=False, xaxis_title=None)
        fig4.update_yaxes(tickformat="$.2s")
        st.plotly_chart(fig4, use_container_width=True)

    # Timeline of facility dates
    dated = df.dropna(subset=["Facility Date"]).copy()
    if not dated.empty:
        st.markdown('<div class="section-header">Facility Date Timeline</div>', unsafe_allow_html=True)
        dated["Year"] = dated["Facility Date"].apply(lambda d: d.year if d else None)
        year_counts = dated["Year"].value_counts().sort_index().reset_index()
        year_counts.columns = ["Year", "Count"]
        fig5 = px.bar(year_counts, x="Year", y="Count",
                      color="Count", color_continuous_scale="Blues")
        fig5.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)

    # Top banks by facility count
    st.markdown('<div class="section-header">Top 20 Banks by Facility Count</div>', unsafe_allow_html=True)
    top_banks = df["Bank Name"].value_counts().head(20).reset_index()
    top_banks.columns = ["Bank", "Count"]
    fig6 = px.bar(
        top_banks, x="Count", y="Bank", orientation="h",
        color="Count", color_continuous_scale="Tealgrn",
    )
    fig6.update_layout(
        margin=dict(t=10, b=10), coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"), yaxis_title=None,
    )
    st.plotly_chart(fig6, use_container_width=True)

# ── Tab 3: By Office ──────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">Facilities by Booking Office</div>', unsafe_allow_html=True)
    offices_in_data = sorted(df["Office"].dropna().unique())

    for office in offices_in_data:
        sub = df[df["Office"] == office]
        label = OFFICE_LABELS.get(office, office)
        with st.expander(f"**{label}** — {len(sub)} facilities", expanded=(office == "SG")):
            sub_display = sub[[c for c in [
                "Bank Name", "Borrower", "Date of Facility",
                "Currency", "Quantum", "Type", "Status", "Security Package",
            ] if c in sub.columns]].copy()
            sub_display.fillna("—", inplace=True)
            st.dataframe(sub_display, use_container_width=True, hide_index=True)

# ── Tab 4: By Bank ──────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">Facilities by Bank</div>', unsafe_allow_html=True)
    all_banks = sorted(df["Bank Name"].dropna().unique())
    sel_bank = st.selectbox("Select Bank", options=["— Select —"] + all_banks)

    if sel_bank != "— Select —":
        bdf = df[df["Bank Name"] == sel_bank]
        st.markdown(f"**{sel_bank}** — {len(bdf)} facilit{'y' if len(bdf)==1 else 'ies'} on record")

        bcols = [c for c in [
            "Office Label", "Borrower", "Date of Facility",
            "Currency", "Quantum", "Type", "Tenure", "Status", "Security Package",
        ] if c in bdf.columns]
        bdf_disp = bdf[bcols].copy()
        bdf_disp.fillna("—", inplace=True)
        st.dataframe(bdf_disp, use_container_width=True, hide_index=True)

        usd_total = bdf.loc[bdf["Currency"] == "USD", "Quantum (USD)"].sum()
        if usd_total > 0:
            st.markdown(f"**Total USD quantum:** {fmt_usd(usd_total)}")
    else:
        # Summary table
        summary = (
            df.groupby("Bank Name")
            .agg(
                Facilities=("Bank Name", "count"),
                Offices=("Office", lambda x: ", ".join(sorted(x.dropna().unique()))),
                Status_Mix=("Status", lambda x: " / ".join(x.value_counts().index[:3])),
                USD_Quantum=("Quantum (USD)", "sum"),
            )
            .reset_index()
            .sort_values("Facilities", ascending=False)
        )
        summary["USD_Quantum"] = summary["USD_Quantum"].apply(
            lambda v: fmt_usd(v) if v > 0 else "—"
        )
        summary.columns = ["Bank", "Facilities", "Offices", "Status Mix", "USD Quantum"]
        st.dataframe(summary, use_container_width=True, hide_index=True, height=500)

# ── Tab 5: Search ──────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-header">Full-Text Search</div>', unsafe_allow_html=True)
    query = st.text_input(
        "Search across all fields",
        placeholder="e.g.  MUFG  |  AIE  |  Trade Finance  |  APRIHL Guarantee",
    )
    if query:
        mask = df.apply(
            lambda row: row.astype(str).str.contains(query, case=False, na=False).any(),
            axis=1,
        )
        results = df[mask]
        st.markdown(f"**{len(results)} result(s)** found for `{query}`")
        if not results.empty:
            res_cols = [c for c in [
                "Bank Name", "Office Label", "Borrower", "Date of Facility",
                "Currency", "Quantum", "Type", "Status", "Security Package",
            ] if c in results.columns]
            res_disp = results[res_cols].copy()
            res_disp.fillna("—", inplace=True)
            st.dataframe(res_disp, use_container_width=True, hide_index=True)
        else:
            st.info("No matching records.")
    else:
        st.info("Enter a keyword above to search across all fields — bank name, borrower, security package, etc.")

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.divider()
st.caption(
    "APRIL Group Internal Use Only · Bilateral Facilities Tracker · "
    f"Generated {datetime.now().strftime('%d %b %Y %H:%M')}"
)
