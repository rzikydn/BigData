# ==========================================================
# Streamlit Dashboard Sertifikasi - Supabase
# Layout: Tabs (Overview, Progress, By Institution, Status)
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
# 2. Fungsi Load Semua Data dari Supabase dengan Paging (table bigdata)
# =========================
def load_bigdata():
    all_data = []
    offset = 0
    page_size = 1000  # ambil 1000 baris per request
    while True:
        response = supabase.table("bigdata").select("*").range(offset, offset+page_size-1).execute()
        if not response.data:
            break
        all_data.extend(response.data)
        offset += page_size
    df = pd.DataFrame(all_data)
    if df.empty:
        return df
    # Pastikan kolom tanggal dalam format datetime
    df["date certification"] = pd.to_datetime(df["date certification"])
    return df



# =========================
# Fungsi Load Semua Data dari Supabase dengan Paging (table notion)
# =========================
def load_notion():
    all_data = []
    offset = 0
    page_size = 1000  # ambil 1000 baris per request
    while True:
        response = supabase.table("notion").select("*").range(offset, offset+page_size-1).execute()
        if not response.data:
            break
        all_data.extend(response.data)
        offset += page_size
    df = pd.DataFrame(all_data)
    if df.empty:
        return df
    # Pastikan kolom tanggal dalam format datetime
    df["date certification"] = pd.to_datetime(df["date certification"])
    return df


# =========================
# 3. Load Data
# =========================
st.cache_data.clear()

df_bigdata = load_bigdata()
df_notion = load_notion()

# =========================
# 4. Filter Global
# =========================
st.title("📊 DASHBOARD SERTIFIKASI")
st.markdown("---")

# Rentang tanggal
min_date = df_bigdata["date certification"].min().date()
max_date = df_bigdata["date certification"].max().date()
selected_dates = st.date_input(
    "📅 Pilih Rentang Tanggal :",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Dropdown jenis sertifikasi & instansi
col1, col2 = st.columns(2)
jenis_list = ["All"] + sorted(df_bigdata["jenis sertifikasi"].dropna().unique())
instansi_list = ["All"] + sorted(df_bigdata["instansi"].dropna().unique())

selected_jenis = col1.selectbox("Jenis Sertifikasi", jenis_list)
selected_instansi = col2.selectbox("Instansi", instansi_list)

# =========================
# 5. Filter Data
# =========================
filtered_df = df_bigdata[
    (df_bigdata["date certification"].dt.date >= selected_dates[0]) &
    (df_bigdata["date certification"].dt.date <= selected_dates[1])
]

if selected_jenis != "All":
    filtered_df = filtered_df[filtered_df["jenis sertifikasi"] == selected_jenis]

if selected_instansi != "All":
    filtered_df = filtered_df[filtered_df["instansi"] == selected_instansi]

# =========================
# 6. Buat Kolom Status
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

filtered_df['status'] = filtered_df.apply(get_status, axis=1)

# =========================
# 7. Stat Cards Function
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
# 8. Tabs Layout
# =========================
tab1, tab2, tab3, = st.tabs(["📈 Overview","🏢 By Institution", "📝By Notion"])

# ===== Tab 1: Overview =====
with tab1:
    # Stat cards
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

# ===== Tab 2: By Institution =====
with tab2:
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


# ===== Tab 3: By Notion =====
with tab3:
    st.subheader("💡VISUALISASI DATA NOTION")
    # Stat cards
    colA, colB, colC = st.columns(3)
    stat_card("Total Notion", df_notion["peserta"].sum(skipna=True), "⭐")
    stat_card("Total Pendaftar",df_bigdata["pendaftar"].sum(skipna=True), "👥")

    # Chart Overview
    df_month = (
        df_notion
        .groupby(df_notion["date certification"].dt.to_period("M"))["peserta"]
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

# Rentang tanggal
min_date = df_notion["date certification"].min().date()
max_date = df_notion["date certification"].max().date()
selected_dates = st.date_input(
    "📅 Pilih Rentang Tanggal :",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# dropdown notion
col1, = st.columns(1)
instansi_list = ["All"] + sorted(df_notion["nama sertifikasi"].dropna().unique())
selected_instansi = col1.selectbox("Nama Sertifikasi", instansi_list)

# =========================
# Filter Data By Notion
# =========================
# 1. filter tanggal
filtered_notion = df_notion[
    (df_notion["date certification"].dt.date >= selected_dates[0]) &
    (df_notion["date certification"].dt.date <= selected_dates[1])
]

# 2. filter nama sertifikasi jika tidak memilih "All"
if selected_instansi != "All":
    filtered_notion = filtered_notion[filtered_notion["nama sertifikasi"] == selected_instansi]

stat_card("Total Peserta Notion", filtered_notion["peserta"].sum(skipna=True), "⭐")

    


# =========================
# End of Dashboard
# =========================