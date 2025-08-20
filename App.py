# ==========================================================
# Streamlit Dashboard Sertifikasi - Supabase (Revisi Key Unik)
# Tabs: Overview, By Notion, By Institution
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import plotly.graph_objs as go

# =========================
# 1. Konfigurasi Supabase
# =========================
SUPABASE_URL = "https://aaxxsnilazypljkxoktx.supabase.co"
SUPABASE_KEY = "<YOUR_SUPABASE_KEY>"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 2. Fungsi Load Data
# =========================
def load_bigdata():
    all_data, offset, page_size = [], 0, 1000
    while True:
        response = supabase.table("bigdata").select("*").range(offset, offset+page_size-1).execute()
        if not response.data: break
        all_data.extend(response.data)
        offset += page_size
    df = pd.DataFrame(all_data)
    if not df.empty:
        df["date certification"] = pd.to_datetime(df["date certification"])
    return df

def load_notion():
    all_data, offset, page_size = [], 0, 1000
    while True:
        response = supabase.table("notion").select("*").range(offset, offset+page_size-1).execute()
        if not response.data: break
        all_data.extend(response.data)
        offset += page_size
    df = pd.DataFrame(all_data)
    if not df.empty:
        df["date certification"] = pd.to_datetime(df["date certification"])
    return df

# =========================
# 3. Load Source Data
# =========================
st.cache_data.clear()
df_bigdata = load_bigdata()
df_notion = load_notion()

# =========================
# 4. Helper Functions
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

def get_status(row):
    if row["selesai"] > 0: return "Selesai"
    elif row["on progress"] > 0: return "On Progress"
    elif row["dibatalkan"] > 0: return "Dibatalkan"
    else: return "Pengajuan Awal"

# =========================
# 5. Tabs Layout
# =========================
st.title("📊 DASHBOARD SERTIFIKASI")
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📈 Overview", "📝 By Notion", "🏢 By Institution"])

# ===== Tab 1: Overview =====
with tab1:
    min_date = df_bigdata["date certification"].min().date()
    max_date = df_bigdata["date certification"].max().date()
    sel_date_overview = st.date_input(
        "📅 Pilih Rentang Tanggal (Overview) :",
        (min_date, max_date),
        min_date,
        max_date,
        key="date_overview"
    )

    jenis_list = ["All"] + sorted(df_bigdata["jenis sertifikasi"].dropna().unique())
    instansi_list = ["All"] + sorted(df_bigdata["instansi"].dropna().unique())
    col1, col2 = st.columns(2)
    sel_jenis_overview = col1.selectbox("Jenis Sertifikasi", jenis_list, key="jenis_overview")
    sel_instansi_overview = col2.selectbox("Instansi", instansi_list, key="instansi_overview")

    # Filter data Overview
    filtered_df = df_bigdata[
        (df_bigdata["date certification"].dt.date >= sel_date_overview[0]) &
        (df_bigdata["date certification"].dt.date <= sel_date_overview[1])
    ]
    if sel_jenis_overview != "All":
        filtered_df = filtered_df[filtered_df["jenis sertifikasi"] == sel_jenis_overview]
    if sel_instansi_overview != "All":
        filtered_df = filtered_df[filtered_df["instansi"] == sel_instansi_overview]
    filtered_df["status"] = filtered_df.apply(get_status, axis=1)

    # Stat cards
    stat_card("Total Pendaftar", filtered_df["pendaftar"].sum(), "👥")
    stat_card("Pengajuan Awal", filtered_df["pengajuan awal"].sum(), "📌")
    stat_card("On Progress", filtered_df["on progress"].sum(), "⏳")
    stat_card("Total Dibatalkan", filtered_df["dibatalkan"].sum(), "❌")
    stat_card("Selesai", filtered_df["selesai"].sum(), "✅")

    # Chart Overview
    df_month = filtered_df.groupby(filtered_df["date certification"].dt.to_period("M"))["pendaftar"].sum().reset_index(name="Jumlah")
    df_month["date certification"] = df_month["date certification"].astype(str)
    fig_over = px.bar(df_month, x="date certification", y="Jumlah", text="Jumlah",
                      title="TOTAL PENDAFTAR SERTIFIKASI PERBULAN (BY DATA BASYS)", height=500)
    fig_over.update_traces(textposition="outside")
    st.plotly_chart(fig_over, use_container_width=True)

# ===== Tab 2: By Notion =====
with tab2:
    st.subheader("💡VISUALISASI DATA NOTION")
    min_date = df_notion["date certification"].min().date()
    max_date = df_notion["date certification"].max().date()
    sel_date_notion = st.date_input(
        "📅 Pilih Rentang Tanggal (Notion):",
        (min_date, max_date),
        min_date,
        max_date,
        key="date_notion"
    )

    sertifikasi_list = ["All"] + sorted(df_notion["nama sertifikasi"].dropna().unique())
    selected_sertifikasi_notion = st.selectbox(
        "Nama Sertifikasi",
        sertifikasi_list,
        key="selected_notion"
    )

    # Filter data Notion
    filtered_notion = df_notion[
        (df_notion["date certification"].dt.date >= sel_date_notion[0]) &
        (df_notion["date certification"].dt.date <= sel_date_notion[1])
    ]
    if selected_sertifikasi_notion != "All":
        filtered_notion = filtered_notion[filtered_notion["nama sertifikasi"] == selected_sertifikasi_notion]

    filtered_bigdata_by_notion = df_bigdata[
        (df_bigdata["date certification"].dt.date >= sel_date_notion[0]) &
        (df_bigdata["date certification"].dt.date <= sel_date_notion[1])
    ]

    # Stat cards
    colA, colB = st.columns(2)
    stat_card("Total Peserta (By Notion)", filtered_notion["peserta"].sum(), "⭐")
    stat_card("Total Selesai (By Basys)", filtered_bigdata_by_notion["selesai"].sum(), "✅")

    # Chart comparison Notion vs BigData
    df_notion_month = filtered_notion.groupby(filtered_notion["date certification"].dt.to_period("M"))["peserta"].sum().reset_index(name="peserta_notion")
    df_bigdata_month = filtered_bigdata_by_notion.groupby(filtered_bigdata_by_notion["date certification"].dt.to_period("M"))["selesai"].sum().reset_index(name="selesai")
    df_compare = pd.merge(df_notion_month, df_bigdata_month, left_on="date certification", right_on="date certification", how="outer").fillna(0)
    df_compare["date certification"] = df_compare["date certification"].astype(str)
    fig_line = px.line(df_compare, x="date certification", y=["peserta_notion", "selesai"], markers=True, title="Trend Peserta Notion vs Selesai BigData")
    st.plotly_chart(fig_line, use_container_width=True)

# ===== Tab 3: By Institution =====
with tab3:
    min_date = df_bigdata["date certification"].min().date()
    max_date = df_bigdata["date certification"].max().date()
    sel_date_institution = st.date_input(
        "📅 Pilih Rentang Tanggal (Institution) :",
        (min_date, max_date),
        min_date,
        max_date,
        key="date_institution"
    )

    jenis_list_inst = ["All"] + sorted(df_bigdata["jenis sertifikasi"].dropna().unique())
    instansi_list_inst = ["All"] + sorted(df_bigdata["instansi"].dropna().unique())
    col1, col2 = st.columns(2)
    sel_jenis_inst = col1.selectbox("Jenis Sertifikasi", jenis_list_inst, key="jenis_institution")
    sel_instansi_inst = col2.selectbox("Instansi", instansi_list_inst, key="instansi_institution")

    filtered_inst = df_bigdata[
        (df_bigdata["date certification"].dt.date >= sel_date_institution[0]) &
        (df_bigdata["date certification"].dt.date <= sel_date_institution[1])
    ]
    if sel_jenis_inst != "All":
        filtered_inst = filtered_inst[filtered_inst["jenis sertifikasi"] == sel_jenis_inst]
    if sel_instansi_inst != "All":
        filtered_inst = filtered_inst[filtered_inst["instansi"] == sel_instansi_inst]
    filtered_inst["status"] = filtered_inst.apply(get_status, axis=1)

    st.subheader("🏆 5 INSTANSI DENGAN JUMLAH PENDAFTAR TERBANYAK")
    top_instansi = filtered_inst.groupby("instansi")["pendaftar"].sum().reset_index().sort_values("pendaftar", ascending=False).head(5).sort_values("pendaftar", ascending=True)

    fig_lolli = go.Figure()
    fig_lolli.add_trace(go.Scatter(
        x=top_instansi["pendaftar"],
        y=top_instansi["instansi"],
        mode='markers',
        marker=dict(size=12),
        name='Jumlah Pendaftar'
    ))
    fig_lolli.add_trace(go.Scatter(
        x=top_instansi["pendaftar"],
        y=top_instansi["instansi"],
        mode='lines',
        line=dict(color='gray', width=2),
        showlegend=False
    ))
    fig_lolli.update_layout(
        title="Top 5 Instansi Berdasarkan Pendaftar (Lollipop Chart)",
        xaxis_title="Jumlah Pendaftar",
        yaxis_title="",
        showlegend=False
    )
    st.plotly_chart(fig_lolli, use_container_width=True)
