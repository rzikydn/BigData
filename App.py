# ======================================================
# STREAMLIT DASHBOARD SERTIFIKASI - REVISI SESUAI REQUEST
# ======================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# -------------------------------------------
# 1. KONFIGURASI SUPABASE
# -------------------------------------------
SUPABASE_URL = "https://aaxxsnilazypljkxoktx.supabase.co"
SUPABASE_KEY = "eyJhbGc.....zelqE"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------------------
# 2. LOAD DATA
# -------------------------------------------
@st.cache_data
def load_bigdata():
    all_data = []
    offset = 0
    while True:
        res = supabase.table("bigdata").select("*").range(offset, offset+999).execute()
        if not res.data: break
        all_data.extend(res.data)
        offset += 1000
    df = pd.DataFrame(all_data)
    if not df.empty:
        df["date certification"] = pd.to_datetime(df["date certification"])
    return df

@st.cache_data
def load_notion():
    all_data = []
    offset = 0
    while True:
        res = supabase.table("notion").select("*").range(offset, offset+999).execute()
        if not res.data: break
        all_data.extend(res.data)
        offset += 1000
    df = pd.DataFrame(all_data)
    if not df.empty:
        df["date certification"] = pd.to_datetime(df["date certification"])
    return df

df_bigdata = load_bigdata()
df_notion  = load_notion()

# -------------------------------------------
# 3. FILTER GLOBAL (HANYA UNTUK TAB 1 & TAB 2)
# -------------------------------------------
st.title("📊 DASHBOARD SERTIFIKASI")
st.markdown("---")

min_date_global = df_bigdata["date certification"].min().date()
max_date_global = df_bigdata["date certification"].max().date()

selected_dates_global = st.date_input(
    "📅 Pilih Rentang Tanggal (Global):",
    value=(min_date_global, max_date_global),
    min_value=min_date_global,
    max_value=max_date_global,
    key="global_date"
)
# pastikan selected always tuple
if isinstance(selected_dates_global, tuple):
    start_global, end_global = selected_dates_global
else:
    start_global = end_global = selected_dates_global

filtered_df = df_bigdata[
    (df_bigdata["date certification"].dt.date >= start_global) &
    (df_bigdata["date certification"].dt.date <= end_global)
]

# -------------------------------------------
# 4. BUAT KOLOM STATUS
# -------------------------------------------
def get_status(row):
    if row['selesai'] > 0:
        return "Selesai"
    elif row['on progress'] > 0:
        return "On Progress"
    elif row['dibatalkan'] > 0:
        return "Dibatalkan"
    else:
        return "Pengajuan Awal"

if not filtered_df.empty:
    filtered_df['status'] = filtered_df.apply(get_status, axis=1)

# -------------------------------------------
# 5. STAT CARD
# -------------------------------------------
def stat_card(label, value, icon):
    st.markdown(f"""
        <div style="display:flex;.align-items:center;padding:10px;background:#fff;
        border-radius:12px;box-shadow:0 2px 6px rgba(0,0,0,0.15);margin-bottom:12px">
            <div style="font-size:30px;margin-right:15px;">{icon}</div>
            <div>
                <div style="font-size:14px;color:#777;">{label}</div>
                <div style="font-size:24px;font-weight:bold;">{value}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# -------------------------------------------
# 6. TABS
# -------------------------------------------
tab1, tab2, tab3 = st.tabs(["📈 Overview", "🏢 By Institution", "📝 By Notion"])

# ===== TAB 1 OVERVIEW
with tab1:
    colA, colB, colC = st.columns(3)
    stat_card("Total Pendaftar", filtered_df["pendaftar"].sum(), "👥")
    stat_card("Pengajuan Awal", filtered_df["pengajuan awal"].sum(), "📌")
    stat_card("On Progress", filtered_df["on progress"].sum(), "⏳")
    stat_card("Dibatalkan", filtered_df["dibatalkan"].sum(), "❌")
    stat_card("Selesai", filtered_df["selesai"].sum(), "✅")

    df_month = (
        filtered_df.groupby(filtered_df["date certification"].dt.to_period("M"))["pendaftar"]
        .sum().reset_index(name="Jumlah")
    )
    df_month["date certification"] = df_month["date certification"].astype(str)
    fig1 = px.bar(
        df_month, x="date certification", y="Jumlah", text="Jumlah",
        title="TOTAL PENDAFTAR SERTIFIKASI PER BULAN", height=500
    )
    fig1.update_traces(textposition="outside")
    st.plotly_chart(fig1, use_container_width=True)

# ===== TAB 2 INSTANSI
with tab2:
    st.subheader("🏆 5 INSTANSI DENGAN JUMLAH PENDAFTAR TERBANYAK")
    top5 = (
        filtered_df.groupby("instansi")["pendaftar"]
        .sum().reset_index()
        .sort_values("pendaftar", ascending=False)
        .head(5)
        .sort_values("pendaftar", ascending=True)
    )
    fig2 = px.bar(
        top5, x="pendaftar", y="instansi", orientation="h", text="pendaftar",
        title="TOP 5 INSTANSI", color_discrete_sequence=["#80c6ff"]
    )
    fig2.update_traces(textposition="inside")
    st.plotly_chart(fig2, use_container_width=True)

# ===== TAB 3 NOTION
with tab3:
    st.subheader("💡 VISUALISASI DATA NOTION")

    colA, colB, colC = st.columns(3)
    stat_card("Total Notion", df_notion["peserta"].sum(), "⭐")
    stat_card("Total Pendaftar BigData", df_bigdata["pendaftar"].sum(), "👥")

    # date khusus notion
    min_n, max_n = df_notion["date certification"].min().date(), df_notion["date certification"].max().date()
    selected_dates_n = st.date_input(
        "📅 Pilih Rentang Tanggal (Notion):",
        value=(min_n, max_n),
        min_value=min_n,
        max_value=max_n,
        key="notion_date"
    )
    if isinstance(selected_dates_n, tuple):
        st_n, en_n = selected_dates_n
    else:
        st_n = en_n = selected_dates_n

    # dropdown nama sertifikasi
    sertifikasi_list = ["All"] + sorted(df_notion["nama sertifikasi"].dropna().unique())
    selected_sertifikasi = st.selectbox("Nama Sertifikasi", sertifikasi_list)

    filtered_n = df_notion[
        (df_notion["date certification"].dt.date >= st_n) &
        (df_notion["date certification"].dt.date <= en_n)
    ]
    if selected_sertifikasi != "All":
        filtered_n = filtered_n[filtered_n["nama sertifikasi"] == selected_sertifikasi]

    dfm = (
        filtered_n.groupby(filtered_n["date certification"].dt.to_period("M"))["peserta"]
        .sum().reset_index(name="Jumlah")
    )
    dfm["date certification"] = dfm["date certification"].astype(str)
    fig3 = px.bar(
        dfm, x="date certification", y="Jumlah", text="Jumlah",
        title="TOTAL PESERTA NOTION PER BULAN", height=450
    )
    fig3.update_traces(textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)

# -------------------------------------------
# END OF DASHBOARD
# -------------------------------------------
