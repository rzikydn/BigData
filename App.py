# ==========================================================
# Streamlit Dashboard Sertifikasi - Supabase
# Layout: Tabs (Overview, By Institution, By Notion)
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

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
    sel_date = st.date_input("📅 Pilih Rentang Tanggal (Overview) :", (min_date, max_date), min_date, max_date, key="date overview")

    jenis_list = ["All"] + sorted(df_bigdata["jenis sertifikasi"].dropna().unique())
    instansi_list = ["All"] + sorted(df_bigdata["instansi"].dropna().unique())
    col1, col2 = st.columns(2)
    sel_jenis = col1.selectbox("Jenis Sertifikasi", jenis_list, key="jenis overview")
    sel_instansi = col2.selectbox("Instansi", instansi_list, key="instansi overview")

    # Filter data
    filtered_df = df_bigdata[
        (df_bigdata["date certification"].dt.date >= sel_date[0]) &
        (df_bigdata["date certification"].dt.date <= sel_date[1])
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
                      title="TOTAL PENDAFTAR SERTIFIKASI PERBULAN (BY DATA BASYS)", height=500)
    fig_over.update_traces(textposition="outside")
    st.plotly_chart(fig_over, use_container_width=True)

    # Info box / expander untuk penjelasan
    with st.expander("ℹ️ FUNGSI BAGIAN INI", expanded=True):
        st.markdown("""
        Bagian Overview menampilkan **ringkasan keseluruhan data sertifikasi** sesuai rentang tanggal yang dipilih.

        Informasi yang ditampilkan:
        1. **Total Pendaftar** – jumlah seluruh peserta yang mendaftar sertifikasi.
        2. **Total Dibatalkan** – jumlah pendaftar yang membatalkan sertifikasi.
        3. **Selesai** – jumlah sertifikasi yang sudah diselesaikan oleh peserta.
        4. **Grafik jumlah pendaftar per bulan** – memvisualisasikan tren pendaftaran dari waktu ke waktu.

        Fungsi bagian ini adalah untuk memberikan **pandangan cepat** mengenai performa sertifikasi, sehingga pengguna dapat:
        - Menilai volume partisipasi peserta secara keseluruhan.
        - Mengidentifikasi tren pendaftaran bulanan.
        - Membuat keputusan strategis terkait perencanaan dan pengelolaan sertifikasi.
        """)


# ===== Tab 2: By Notion =====
with tab2:
    st.subheader("💡VISUALISASI DATA NOTION")

    min_date = df_notion["date certification"].min().date()
    max_date = df_notion["date certification"].max().date()
    sel_date = st.date_input("📅 Pilih Rentang Tanggal (Notion):", (min_date, max_date), min_date, max_date, key="date notion")

    sertifikasi_list = ["All"] + sorted(df_notion["nama sertifikasi"].dropna().unique())
    selected_sertifikasi = st.selectbox("Nama Sertifikasi", sertifikasi_list, key="selected notion")

    # FILTER SESUAI TANGGAL & SERTIFIKASI
    filtered_notion = df_notion[
        (df_notion["date certification"].dt.date >= sel_date[0]) &
        (df_notion["date certification"].dt.date <= sel_date[1])
    ]
    if selected_sertifikasi != "All":
        filtered_notion = filtered_notion[filtered_notion["nama sertifikasi"] == selected_sertifikasi]

    filtered_bigdata_by_notion = df_bigdata[
    (df_bigdata["date certification"].dt.date >= sel_date[0]) &
    (df_bigdata["date certification"].dt.date <= sel_date[1])
]

    # ==== STAT CARD BERDASARKAN FILTER ====
    colA, colB = st.columns(2)
    stat_card("Total Peserta", filtered_notion["peserta"].sum(), "⭐")
    stat_card("Total Selesai (BigData)", filtered_df["selesai"].sum(), "✅")
    
    # ==== CHART ====
    # ==== CHART PERBANDINGAN NOTION vs BIGDATA (per bulan) ====

# 1) Hitung peserta notion per bulan
df_notion_month = (
    filtered_notion
    .groupby(filtered_notion["date certification"].dt.to_period("M"))["peserta"]
    .sum()
    .reset_index(name="peserta_notion")
)

# 2) Hitung jumlah selesai BigData per bulan,
#    menggunakan filtered_df (dari tab Overview),
#    jika tidak ingin pakai filter Overview gunakan df_bigdata lalu filter tanggal yg sama.
df_bigdata_month = (
    filtered_df
    .groupby(filtered_df["date certification"].dt.to_period("M"))["selesai"]
    .sum()
    .reset_index(name="selesai_bigdata")
)

# 3) Gabungkan Notion vs BigData
df_compare = pd.merge(df_notion_month, df_bigdata_month, on="date certification", how="outer").fillna(0)
df_compare["date certification"] = df_compare["date certification"].astype(str)

# 4) Tampilkan chart grouped bar
fig_compare = px.bar(
    df_compare,
    x="date certification",
    y=["peserta_notion", "selesai_bigdata"],
    barmode="group",
    text_auto=True,
    title="Perbandingan Peserta Notion vs Selesai BigData (Bulanan)"
)
st.plotly_chart(fig_compare, use_container_width=True)




# ===== Tab 3: By Institution =====
with tab3:
    min_date = df_bigdata["date certification"].min().date()
    max_date = df_bigdata["date certification"].max().date()
    sel_date = st.date_input("📅 Pilih Rentang Tanggal (institution) :", (min_date, max_date), min_date, max_date, key="date institution")

    jenis_list = ["All"] + sorted(df_bigdata["jenis sertifikasi"].dropna().unique())
    instansi_list = ["All"] + sorted(df_bigdata["instansi"].dropna().unique())
    col1, col2 = st.columns(2)
    sel_jenis = col1.selectbox("Jenis Sertifikasi", jenis_list, key="jenis institution")
    sel_instansi = col2.selectbox("Instansi", instansi_list, key="instansi institution")

    filtered_df = df_bigdata[
        (df_bigdata["date certification"].dt.date >= sel_date[0]) &
        (df_bigdata["date certification"].dt.date <= sel_date[1])
    ]
    if sel_jenis != "All":
        filtered_df = filtered_df[filtered_df["jenis sertifikasi"] == sel_jenis]
    if sel_instansi != "All":
        filtered_df = filtered_df[filtered_df["instansi"] == sel_instansi]
    filtered_df["status"] = filtered_df.apply(get_status, axis=1)

    st.subheader("🏆 5 INSTANSI DENGAN JUMLAH PENDAFTAR TERBANYAK")
    top_instansi = (
        filtered_df.groupby("instansi")["pendaftar"].sum()
        .reset_index().sort_values("pendaftar", ascending=False).head(5)
        .sort_values("pendaftar", ascending=True)
    )
    fig_inst = px.bar(top_instansi, x="pendaftar", y="instansi", orientation="h", text="pendaftar")
    fig_inst.update_layout(yaxis_title="", xaxis_title="Jumlah Pendaftar", showlegend=False)
    st.plotly_chart(fig_inst, use_container_width=True)

    # Info box / expander untuk penjelasan
    with st.expander("ℹ️ Fungsi Bagian Ini", expanded=True):
        st.markdown("""
        Bagian ini menampilkan **5 instansi dengan jumlah pendaftar sertifikasi terbanyak** berdasarkan rentang tanggal yang dipilih.

        Manfaat informasi ini:
        1. Mengetahui instansi mana yang paling aktif mendorong karyawannya mengikuti sertifikasi.
        2. Membantu penyelenggara memahami distribusi peserta per instansi.
        3. Mempermudah perencanaan alokasi sumber daya dan layanan untuk instansi tertentu.

        Dengan visualisasi ini, pengguna dapat langsung melihat instansi dengan partisipasi tertinggi dan memantau tren perubahan jumlah pendaftar dari waktu ke waktu.
        """)

# End of Dashboard
