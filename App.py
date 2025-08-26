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
# 0. Fungsi Helper Tambahan
# =========================
def normalize_date_input(sel_date):
    """
    Pastikan sel_date selalu tuple (start_date, end_date)
    """
    if isinstance(sel_date, (tuple, list)):
        if len(sel_date) == 2:
            return sel_date
        elif len(sel_date) == 1:
            return (sel_date[0], sel_date[0])
    else:  # misal hanya 1 tanggal dipilih
        return (sel_date, sel_date)
    return (sel_date[0], sel_date[0])

# =========================
# 1. Konfigurasi Supabase
# =========================
SUPABASE_URL = "https://aaxxsnilazypljkxoktx.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 2. Fungsi Load Data
# =========================
def load_bigdata():
    all_data, offset, page_size = [], 0, 1000
    while True:
        response = supabase.table("bigdata").select("*").range(offset, offset+page_size-1).execute()
        if not response.data: 
            break
        all_data.extend(response.data)
        offset += page_size
    df = pd.DataFrame(all_data)
    if df.empty:
        df = pd.DataFrame(columns=["nama sertifikasi", "jenis sertifikasi", "instansi",
                                   "pendaftar", "pengajuan awal", "on progress", "dibatalkan", "selesai", "date certification"])
    else:
        df["date certification"] = pd.to_datetime(df["date certification"])
    return df

def load_notion():
    all_data, offset, page_size = [], 0, 1000
    while True:
        response = supabase.table("notion").select("*").range(offset, offset+page_size-1).execute()
        if not response.data: 
            break
        all_data.extend(response.data)
        offset += page_size
    df = pd.DataFrame(all_data)
    if df.empty:
        df = pd.DataFrame(columns=["id", "no", "nama sertifikasi", "peserta", "date certification"])
    else:
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
    if row.get("selesai", 0) > 0:         return "Selesai"
    elif row.get("on progress", 0) > 0:   return "On Progress"
    elif row.get("dibatalkan", 0) > 0:    return "Dibatalkan"
    else:                                 return "Pengajuan Awal"

# =========================
# 5. Tabs Layout
# =========================
st.title("📊 DASHBOARD SERTIFIKASI")
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📈 Overview", "📝 By Notion", "🏢 By Institution"])

# ===== Tab 1: Overview =====
with tab1:
    min_date = df_bigdata["date certification"].min().date() if not df_bigdata.empty else pd.Timestamp.today().date()
    max_date = df_bigdata["date certification"].max().date() if not df_bigdata.empty else pd.Timestamp.today().date()
    sel_date = st.date_input(
        "📅 Pilih rentang tanggal :",
        (min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_overview"
    )
    sel_date = normalize_date_input(sel_date)

    jenis_list = ["All"] + sorted(df_bigdata["jenis sertifikasi"].dropna().unique()) if not df_bigdata.empty else ["All"]
    instansi_list = ["All"] + sorted(df_bigdata["instansi"].dropna().unique()) if not df_bigdata.empty else ["All"]
    col1, col2 = st.columns(2)
    sel_jenis = col1.selectbox("Jenis Sertifikasi", jenis_list, key="jenis overview")
    sel_instansi = col2.selectbox("Instansi", instansi_list, key="instansi overview")

    filtered_df = df_bigdata.copy()
    if not filtered_df.empty:
        filtered_df = filtered_df[
            (filtered_df["date certification"].dt.date >= sel_date[0]) &
            (filtered_df["date certification"].dt.date <= sel_date[1])
        ]
        if sel_jenis != "All":
            filtered_df = filtered_df[filtered_df["jenis sertifikasi"] == sel_jenis]
        if sel_instansi != "All":
            filtered_df = filtered_df[filtered_df["instansi"] == sel_instansi]
        filtered_df["status"] = filtered_df.apply(get_status, axis=1)
    else:
        filtered_df = pd.DataFrame(columns=df_bigdata.columns)

    # Stat cards
    stat_card("Total Pendaftar", filtered_df["pendaftar"].sum() if not filtered_df.empty else 0, "👥")
    stat_card("Pengajuan Awal", filtered_df["pengajuan awal"].sum() if not filtered_df.empty else 0, "📌")
    stat_card("On Progress", filtered_df["on progress"].sum() if not filtered_df.empty else 0, "⏳")
    stat_card("Total Dibatalkan", filtered_df["dibatalkan"].sum() if not filtered_df.empty else 0, "❌")
    stat_card("Selesai", filtered_df["selesai"].sum() if not filtered_df.empty else 0, "✅")

    # Chart
    if not filtered_df.empty:
        df_month = (
            filtered_df
            .groupby(filtered_df["date certification"].dt.to_period("M"))["pendaftar"]
            .sum().reset_index(name="Jumlah")
        )
        df_month["date certification"] = df_month["date certification"].astype(str)
        fig_over = px.bar(df_month, x="date certification", y="Jumlah", text="Jumlah",
                          title="TOTAL PENDAFTAR SERTIFIKASI PERBULAN (BY DATA BASYS)", height=500)
        fig_over.update_traces(textposition="outside")
        st.plotly_chart(fig_over, use_container_width=True)

# ===== Tab 2: By Notion =====
with tab2:
    st.subheader("💡 VISUALISASI DATA NOTION")
    min_date_notion = df_notion["date certification"].min().date() if not df_notion.empty else pd.Timestamp.today().date()
    max_date_notion = df_notion["date certification"].max().date() if not df_notion.empty else pd.Timestamp.today().date()
    sel_date_notion = st.date_input(
        "📅 Pilih rentang tanggal :",
        (min_date_notion, max_date_notion),
        min_value=min_date_notion,
        max_value=max_date_notion,
        key="date_notion"
    )
    sel_date_notion = normalize_date_input(sel_date_notion)

    instansi_list_notion = ["All"] + sorted(df_bigdata["instansi"].dropna().unique()) if not df_bigdata.empty else ["All"]
    sel_instansi_notion = st.selectbox("🏢 Pilih Instansi :", instansi_list_notion, key="instansi_notion")

    df_merge = pd.merge(
        df_notion, df_bigdata[['nama sertifikasi', 'instansi']],
        on='nama sertifikasi', how='left'
    ) if not df_notion.empty else pd.DataFrame(columns=["nama sertifikasi", "peserta", "date certification", "instansi"])

    df_merge = df_merge[
        (df_merge['date certification'] >= pd.to_datetime(sel_date_notion[0])) &
        (df_merge['date certification'] <= pd.to_datetime(sel_date_notion[1]))
    ] if not df_merge.empty else df_merge

    if sel_instansi_notion != "All" and not df_merge.empty:
        df_merge = df_merge[df_merge['instansi'] == sel_instansi_notion]

    df_merge['peserta'] = pd.to_numeric(df_merge.get('peserta', pd.Series(dtype='float')), errors='coerce')
    df_bigdata['selesai'] = pd.to_numeric(df_bigdata.get('selesai', pd.Series(dtype='float')), errors='coerce')

    total_peserta = df_merge['peserta'].sum() if not df_merge.empty else 0
    total_selesai_all_time = df_bigdata['selesai'].sum() if not df_bigdata.empty else 0

    filtered_bigdata_for_selesai = df_bigdata[
        (df_bigdata['date certification'] >= pd.to_datetime(sel_date_notion[0])) &
        (df_bigdata['date certification'] <= pd.to_datetime(sel_date_notion[1]))
    ] if not df_bigdata.empty else pd.DataFrame(columns=df_bigdata.columns)

    if sel_instansi_notion != "All" and not filtered_bigdata_for_selesai.empty:
        filtered_bigdata_for_selesai = filtered_bigdata_for_selesai[
            filtered_bigdata_for_selesai['instansi'] == sel_instansi_notion
        ]

    total_selesai_filtered = filtered_bigdata_for_selesai['selesai'].sum() if not filtered_bigdata_for_selesai.empty else 0

    colA, colB, colC = st.columns(3)
    stat_card("Total Selesai - Statis By Basys", int(total_selesai_all_time), "📌")
    stat_card("Total Peserta - By Notion", int(total_peserta), "⭐")
    stat_card("Total Selesai Dinamis - By Basys", int(total_selesai_filtered), "✅")

# ===== Tab 3: By Institution =====
with tab3:
    st.subheader("🏆 5 TOP INSTANSI ")
    min_date_inst = df_bigdata["date certification"].min().date() if not df_bigdata.empty else pd.Timestamp.today().date()
    max_date_inst = df_bigdata["date certification"].max().date() if not df_bigdata.empty else pd.Timestamp.today().date()
    sel_date_inst = st.date_input(
        "📅 Pilih rentang tanggal :",
        (min_date_inst, max_date_inst),
        min_value=min_date_inst,
        max_value=max_date_inst,
        key="date_inst"
    )
    sel_date_inst = normalize_date_input(sel_date_inst)

    jenis_list_inst = ["All"] + sorted(df_bigdata["jenis sertifikasi"].dropna().unique()) if not df_bigdata.empty else ["All"]
    sel_jenis_inst = st.selectbox("Jenis Sertifikasi", jenis_list_inst, key="jenis_institution")

    filtered_df_inst = df_bigdata.copy()
    if not filtered_df_inst.empty:
        filtered_df_inst = filtered_df_inst[
            (filtered_df_inst["date certification"].dt.date >= sel_date_inst[0]) &
            (filtered_df_inst["date certification"].dt.date <= sel_date_inst[1])
        ]
        if sel_jenis_inst != "All":
            filtered_df_inst = filtered_df_inst[filtered_df_inst["jenis sertifikasi"] == sel_jenis_inst]
    else:
        filtered_df_inst = pd.DataFrame(columns=df_bigdata.columns)

    colA, colB = st.columns(2)
    stat_card("Total Pendaftar", filtered_df_inst["pendaftar"].sum() if not filtered_df_inst.empty else 0, "👥")
    stat_card("Selesai", filtered_df_inst["selesai"].sum() if not filtered_df_inst.empty else 0, "✅")
