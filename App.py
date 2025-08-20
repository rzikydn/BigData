# ==========================================================
# Streamlit Dashboard Sertifikasi - Supabase
# Layout: Tabs (Overview, By Notion, By Institution)
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# =========================
# 1. Konfigurasi Supabase
# =========================
SUPABASE_URL = "https://aaxxsnilazypljkxoktx.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 2. Fungsi Load Data dari Supabase
# =========================
def load_table(table_name):
    all_data = []
    offset = 0
    page_size = 1000
    while True:
        response = supabase.table(table_name).select("*").range(offset, offset+page_size-1).execute()
        if not response.data:
            break
        all_data.extend(response.data)
        offset += page_size
    df = pd.DataFrame(all_data)
    if not df.empty:
        df["date certification"] = pd.to_datetime(df["date certification"])
    return df

df_bigdata = load_table("bigdata")
df_notion = load_table("notion")

# =========================
# 3. Dashboard Header
# =========================
st.title("📊 DASHBOARD SERTIFIKASI")
st.markdown("---")

# =========================
# 4. Global Date Picker untuk Overview & By Institution
# =========================
min_date_global = df_bigdata["date certification"].min().date()
max_date_global = df_bigdata["date certification"].max().date()
selected_dates_global = st.date_input(
    "📅 Pilih Rentang Tanggal (Overview & By Institution):",
    value=(min_date_global, max_date_global),
    min_value=min_date_global,
    max_value=max_date_global
)

# Filter BigData sesuai global date
filtered_df = df_bigdata[
    (df_bigdata["date certification"].dt.date >= selected_dates_global[0]) &
    (df_bigdata["date certification"].dt.date <= selected_dates_global[1])
]

# =========================
# 5. Status Column
# =========================
def get_status(row):
    if row['selesai'] > 0:
        return 'Selesai'
    elif row['on progress'] > 0:
        return 'On Progress'
    elif row['dibatalkan'] > 0:
        return 'Dibatalkan'
    else:
        return 'Pengajuan Awal'

if not filtered_df.empty:
    filtered_df['status'] = filtered_df.apply(get_status, axis=1)

# =========================
# 6. Stat Card Function
# =========================
def stat_card(label, value, icon):
    st.markdown(f"""
        <div style="display:flex;align-items:center;padding:10px;background-color:white;
        border-radius:10px;box-shadow:0px 2px 8px rgba(0,0,0,0.1);margin-bottom:10px">
            <div style="font-size:30px;margin-right:15px;">{icon}</div>
            <div>
                <div style="font-size:14px;color:gray;">{label}</div>
                <div style="font-size:24px;font-weight:bold;color:black;">{value}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# =========================
# 7. Tabs Layout
# =========================
tab1, tab2, tab3 = st.tabs(["📈 Overview","📝 By Notion", "🏢 By Institution"])

# ===== Tab 1: Overview =====
with tab1:
    colA, colB, colC = st.columns(3)
    stat_card("Total Pendaftar", filtered_df["pendaftar"].sum(skipna=True), "👥")
    stat_card("Pengajuan Awal", filtered_df["pengajuan awal"].sum(skipna=True), "📌")
    stat_card("On Progress", filtered_df["on progress"].sum(skipna=True), "⏳")
    stat_card("Total Dibatalkan", filtered_df["dibatalkan"].sum(skipna=True), "❌")
    stat_card("Selesai", filtered_df["selesai"].sum(skipna=True), "✅")

    # Chart Overview
    df_month = (
        filtered_df
        .groupby(filtered_df["date certification"].dt.to_period("M"))["pendaftar"]
        .sum()
        .reset_index(name="Jumlah")
    )
    df_month["date certification"] = df_month["date certification"].astype(str)
    fig_overview = px.bar(
        df_month,
        x="date certification",
        y="Jumlah",
        text="Jumlah",
        title="TOTAL PENDAFTAR SERTIFIKASI PERBULAN (BY DATA BASYS)",
        color="Jumlah",
        height=500
    )
    fig_overview.update_traces(textposition="outside")
    st.plotly_chart(fig_overview, use_container_width=True)

# ===== Tab 2: By Notion =====
with tab2:
    st.subheader("💡VISUALISASI DATA NOTION")

    # Stat cards
    colA, colB, colC = st.columns(3)
    stat_card("Total Notion", df_notion["peserta"].sum(skipna=True), "⭐")
    stat_card("Total Pendaftar", df_bigdata["pendaftar"].sum(skipna=True), "👥")

    # Rentang tanggal khusus Notion
    min_date_notion = df_notion["date certification"].min().date()
    max_date_notion = df_notion["date certification"].max().date()
    selected_dates_notion = st.date_input(
        "📅 Pilih Rentang Tanggal (Notion):",
        value=(min_date_notion, max_date_notion),
        min_value=min_date_notion,
        max_value=max_date_notion
    )

    # Filter Data Notion
    filtered_notion = df_notion[
        (df_notion["date certification"].dt.date >= selected_dates_notion[0]) &
        (df_notion["date certification"].dt.date <= selected_dates_notion[1])
    ]

    # Chart Overview Notion
    df_month_notion = (
        filtered_notion
        .groupby(filtered_notion["date certification"].dt.to_period("M"))["peserta"]
        .sum()
        .reset_index(name="Jumlah")
    )
    df_month_notion["date certification"] = df_month_notion["date certification"].astype(str)
    fig_overview_notion = px.bar(
        df_month_notion,
        x="date certification",
        y="Jumlah",
        text="Jumlah",
        title="TOTAL PESERTA NOTION PER BULAN",
        color="Jumlah",
        height=500
    )
    fig_overview_notion.update_traces(textposition="outside")
    st.plotly_chart(fig_overview_notion, use_container_width=True)

# ===== Tab 3: By Institution =====
with tab3:
    st.subheader("🏆 5 INSTANSI DENGAN JUMLAH PENDAFTAR TERBANYAK")

    top_instansi = (
        filtered_df.groupby("instansi")["pendaftar"]
        .sum()
        .reset_index()
        .sort_values("pendaftar", ascending=False)
        .head(5)
        .sort_values("pendaftar", ascending=True)
    )

    fig_instansi = px.bar(
        top_instansi,
        x="pendaftar",
        y="instansi",
        orientation="h",
        text="pendaftar",
        title="Top 5 Instansi Berdasarkan Jumlah Pendaftar",
        color_discrete_sequence=["#80c6ff"]
    )
    fig_instansi.update_traces(textposition="inside")
    fig_instansi.update_layout(yaxis_title="", xaxis_title="Jumlah Pendaftar", showlegend=False)
    st.plotly_chart(fig_instansi, use_container_width=True)
