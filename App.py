# ==========================================================
# Streamlit Dashboard Sertifikasi - Supabase
# Layout: Tabs (Overview, By Institution, By Notion)
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
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFheHhzbmlsYXp5cGxqa3hva3R4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQyODAxMzcsImV4cCI6MjA2OTg1NjEzN30.l_ySjvjv0-gYpwAF5E9i6aT0W7_iakGlSEqfIXzelqE"
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
# 4. Helper
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
    if row["selesai"] > 0:         return "Selesai"
    elif row["on progress"] > 0:   return "On Progress"
    elif row["dibatalkan"] > 0:    return "Dibatalkan"
    else:                          return "Pengajuan Awal"

def dual_date_input(label_prefix, min_date, max_date, key_prefix):
    """2 input tanggal (mulai & akhir) dengan default sama2 min_date"""
    col1, col2 = st.columns(2)
    start_date = col1.date_input(
        f"{label_prefix} - awal",
        min_value=min_date, max_value=max_date,
        value=min_date, key=f"{key_prefix}_start"
    )
    end_date = col2.date_input(
        f"{label_prefix} - akhir",
        min_value=min_date, max_value=max_date,
        value=min_date,   # 🔹 revisi: default ke min_date
        key=f"{key_prefix}_end"
    )
    if start_date > end_date:
        st.warning("⚠️ Tanggal mulai tidak boleh lebih besar dari tanggal akhir.")
    return start_date, end_date

# =========================
# 5. Tabs Layout
# =========================
st.title("📊 DASHBOARD SERTIFIKASI")
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📈 Overview", "✍️ By Notion", "🏛️ By Institution"])

# ===== Tab 1: Overview =====
with tab1:
    st.subheader("VISUALISASI DATA SERTIFIKASI BY BASYS")

    #-- Filter Tanggal--#
    min_date = df_bigdata["date certification"].min().date()
    max_date = df_bigdata["date certification"].max().date()
    start_date, end_date = dual_date_input("📅 Pilih tanggal", min_date, max_date, key_prefix="overview")

    jenis_list = ["All"] + sorted(df_bigdata["jenis sertifikasi"].dropna().unique())
    instansi_list = ["All"] + sorted(df_bigdata["instansi"].dropna().unique())
    col1, col2 = st.columns(2)
    sel_jenis = col1.selectbox("Jenis Sertifikasi", jenis_list, key="jenis_overview")
    sel_instansi = col2.selectbox("Instansi", instansi_list, key="instansi_overview")

    # Filter data
    filtered_df = df_bigdata[
        (df_bigdata["date certification"].dt.date >= start_date) &
        (df_bigdata["date certification"].dt.date <= end_date)
    ]
    if sel_jenis != "All":
        filtered_df = filtered_df[filtered_df["jenis sertifikasi"] == sel_jenis]
    if sel_instansi != "All":
        filtered_df = filtered_df[filtered_df["instansi"] == sel_instansi]
    filtered_df["status"] = filtered_df.apply(get_status, axis=1)

    # Stat cards
    stat_card("Total Pendaftar", filtered_df["pendaftar"].sum(), "👥")
    stat_card("Pengajuan Awal", filtered_df["pengajuan awal"].sum(), "📌")
    stat_card("On Progress", filtered_df["on progress"].sum(), "⏳")
    stat_card("Total Dibatalkan", filtered_df["dibatalkan"].sum(), "❌")
    stat_card("Selesai", filtered_df["selesai"].sum(), "✅")

    # Chart
    df_month = (
        filtered_df
        .groupby(filtered_df["date certification"].dt.to_period("M"))["pendaftar"]
        .sum().reset_index(name="Jumlah")
    )
    df_month["date certification"] = df_month["date certification"].astype(str)
    fig_over = px.bar(df_month, x="date certification", y="Jumlah", text="Jumlah",
                      title="TOTAL PENDAFTAR SERTIFIKASI PERBULAN BERDASARKAN DATA BASYS", height=500)
    fig_over.update_traces(textposition="outside")
    st.plotly_chart(fig_over, use_container_width=True)

    with st.expander("🔽 FUNGSI BAGIAN INI", expanded=True):
        st.markdown("""...""")

# ===== Tab 2: By Notion =====
with tab2:
    st.subheader("VISUALISASI DATA PERBANDINGAN DATA NOTION & BASYS")

    sertifikasi_options = ["Semua"] + sorted(df_notion["nama sertifikasi"].dropna().unique().tolist())
    selected_sertifikasi = st.selectbox("🏢 Pilih Nama Instansi :", sertifikasi_options)

    if selected_sertifikasi != "Semua":
        df_notion_filtered = df_notion[df_notion["nama sertifikasi"] == selected_sertifikasi]
    else:
        df_notion_filtered = df_notion.copy()

    min_date_notion = df_notion_filtered["date certification"].min().date()
    max_date_notion = df_notion_filtered["date certification"].max().date()
    start_date, end_date = dual_date_input("📅 Pilih tanggal", min_date_notion, max_date_notion, key_prefix="notion")

    # === Filter BigData
    filtered_bigdata_same_date = df_bigdata[
        (df_bigdata["date certification"].dt.date >= start_date) &
        (df_bigdata["date certification"].dt.date <= end_date)
    ]
    if selected_sertifikasi != "Semua":
        filtered_bigdata_same_date = filtered_bigdata_same_date[
            filtered_bigdata_same_date["instansi"] == selected_sertifikasi
        ]

    # === Filter Notion chart
    filtered_notion_chart = df_notion_filtered[
        (df_notion_filtered["date certification"].dt.date >= start_date) &
        (df_notion_filtered["date certification"].dt.date <= end_date)
    ]

    # Hitung total peserta & selesai
    total_peserta_notion = filtered_notion_chart["peserta"].sum()
    total_selesai_filtered = filtered_bigdata_same_date["selesai"].sum()

    colB, colC = st.columns(2)
    with colB:
        stat_card(f"Total Peserta (Notion - {selected_sertifikasi})", int(total_peserta_notion), "⭐")
    with colC:
        stat_card(f"Total Selesai (Basys - {selected_sertifikasi})", int(total_selesai_filtered), "✅")

    # Chart
    df_notion_month = (
        filtered_notion_chart
        .groupby(filtered_notion_chart["date certification"].dt.to_period("M"))["peserta"]
        .sum().reset_index(name="pendaftar")
    )
    df_bigdata_month = (
        filtered_bigdata_same_date
        .groupby(filtered_bigdata_same_date["date certification"].dt.to_period("M"))["selesai"]
        .sum().reset_index(name="selesai")
    )
    df_compare = pd.merge(df_notion_month, df_bigdata_month, on="date certification", how="outer").fillna(0)
    df_compare["date certification"] = df_compare["date certification"].astype(str)

    fig_line = px.line(df_compare, x="date certification", y=["pendaftar", "selesai"],
                       markers=True, title="PERBANDINGAN DATA NOTION DAN BASYS")
    st.plotly_chart(fig_line, use_container_width=True)

# ===== Tab 3: By Institution =====
with tab3:
    st.subheader("VISUALISASI DATA TOP 5 INSTANSI")

    min_date_inst = df_bigdata["date certification"].min().date()
    max_date_inst = df_bigdata["date certification"].max().date()
    start_date, end_date = dual_date_input("📅 Pilih tanggal", min_date_inst, max_date_inst, key_prefix="institution")

    filtered_df_inst = df_bigdata[
        (df_bigdata["date certification"].dt.date >= start_date) &
        (df_bigdata["date certification"].dt.date <= end_date)
    ]

    jenis_list_inst = ["All"] + sorted(df_bigdata["jenis sertifikasi"].dropna().unique())
    sel_jenis_inst = st.selectbox("Jenis Sertifikasi", jenis_list_inst, key="jenis_institution")
    if sel_jenis_inst != "All":
        filtered_df_inst = filtered_df_inst[filtered_df_inst["jenis sertifikasi"] == sel_jenis_inst]

    colA, colB = st.columns(2)
    with colA:
        stat_card("Total Pendaftar", filtered_df_inst["pendaftar"].sum(), "👥")
    with colB:
        stat_card("Selesai", filtered_df_inst["selesai"].sum(), "✅")

    top_instansi = (
        filtered_df_inst.groupby("instansi")["pendaftar"].sum()
        .reset_index().sort_values("pendaftar", ascending=False).head(5)
        .sort_values("pendaftar", ascending=True)
    )

    fig_lolli = go.Figure()
    fig_lolli.add_trace(go.Scatter(x=top_instansi["pendaftar"], y=top_instansi["instansi"],
                                   mode='markers', marker=dict(size=12), name='Jumlah Pendaftar'))
    fig_lolli.add_trace(go.Scatter(x=top_instansi["pendaftar"], y=top_instansi["instansi"],
                                   mode='lines', line=dict(color='gray', width=2), showlegend=False))
    fig_lolli.update_layout(title="TOP 5 INSTANSI BERDASARKAN DATA BASYS",
                            xaxis_title="Jumlah Pendaftar", yaxis_title="", showlegend=False)
    st.plotly_chart(fig_lolli, use_container_width=True)
