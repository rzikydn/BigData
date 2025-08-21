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
    with st.expander("ℹ FUNGSI BAGIAN INI", expanded=True):
        st.markdown("""
        Bagian Overview menampilkan *ringkasan keseluruhan data sertifikasi* sesuai rentang tanggal yang dipilih.

        Informasi yang ditampilkan:
        1. *Total Pendaftar* – jumlah seluruh peserta yang mendaftar sertifikasi.
        2. *Total Dibatalkan* – jumlah pendaftar yang membatalkan sertifikasi.
        3. *Selesai* – jumlah sertifikasi yang sudah diselesaikan oleh peserta.
        4. *Grafik jumlah pendaftar per bulan* – memvisualisasikan tren pendaftaran dari waktu ke waktu.

        Fungsi bagian ini adalah untuk memberikan *pandangan cepat* mengenai performa sertifikasi, sehingga pengguna dapat:
        - Menilai volume partisipasi peserta secara keseluruhan.
        - Mengidentifikasi tren pendaftaran bulanan.
        - Membuat keputusan strategis terkait perencanaan dan pengelolaan sertifikasi.
        """)


# ===== Tab 2: By Notion =====
with tab2:
    st.subheader("💡 VISUALISASI DATA NOTION")

    # -------------------------
    # 1. Filter Tanggal (hanya untuk chart)
    # -------------------------
    min_date_notion = df_notion["date certification"].min().date()
    max_date_notion = df_notion["date certification"].max().date()
    sel_date_notion = st.date_input(
        "📅 Pilih Rentang Tanggal (Notion) untuk Chart:",
        (min_date_notion, max_date_notion),
        min_value=min_date_notion,
        max_value=max_date_notion,
        key="date_notion"
    )

    # -------------------------
    # 2. Filter BigData untuk Chart (By Notion)
    # -------------------------
    filtered_bigdata_same_date = df_bigdata[
        (df_bigdata["date certification"].dt.date >= sel_date_notion[0]) &
        (df_bigdata["date certification"].dt.date <= sel_date_notion[1])
    ]


    # -------------------------
    # 3. Filter Notion untuk Chart
    # -------------------------
    filtered_notion_chart = df_notion[
        (df_notion["date certification"].dt.date >= sel_date_notion[0]) &
        (df_notion["date certification"].dt.date <= sel_date_notion[1])
    ]

    # -------------------------
    # 4. Stat Cards (Notion & BigData)
    # -------------------------
    # pastikan numeric
    df_notion["peserta"] = pd.to_numeric(df_notion["peserta"], errors="coerce")
    df_bigdata["selesai"] = pd.to_numeric(df_bigdata["selesai"], errors="coerce")

    total_peserta_notion = df_notion.loc[
        df_notion["date certification"].between(
            pd.to_datetime(sel_date_notion[0]),
            pd.to_datetime(sel_date_notion[1])
        ) if selected_sertifikasi == "All" else
        (df_notion["date certification"].between(
            pd.to_datetime(sel_date_notion[0]),
            pd.to_datetime(sel_date_notion[1])
        ) & (df_notion["nama sertifikasi"] == selected_sertifikasi)),
        "peserta"
    ].sum()

    total_selesai_all_time = df_bigdata["selesai"].fillna(0).sum()
    total_selesai_filtered = filtered_bigdata_same_date["selesai"].fillna(0).sum()

    colA, colB, colC = st.columns(3)
    with colA:
        stat_card("Total Selesai - Statis By Basys", int(total_selesai_all_time), "📌")
    with colB:
        stat_card("Total Peserta - By Notion", int(total_peserta_notion), "⭐")
    with colC:
        stat_card("Total Selesai Dinamis - By Basys", int(total_selesai_filtered), "✅")



    # -------------------------
    # 5. Chart Notion vs BigData per bulan
    # -------------------------
    df_notion_month = (
        filtered_notion_chart
        .groupby(filtered_notion_chart["date certification"].dt.to_period("M"))["peserta"]
        .sum()
        .reset_index(name="pendaftar")
    )
    df_bigdata_month = (
        filtered_bigdata_same_date
        .groupby(filtered_bigdata_same_date["date certification"].dt.to_period("M"))["selesai"]
        .sum()
        .reset_index(name="selesai")
    )
    df_compare = pd.merge(
        df_notion_month, df_bigdata_month,
        left_on="date certification", right_on="date certification",
        how="outer"
    ).fillna(0)
    df_compare["date certification"] = df_compare["date certification"].astype(str)

    fig_line = px.line(
        df_compare,
        x="date certification",
        y=["pendaftar", "selesai"],
        markers=True,
        title="Trend Peserta Notion vs Selesai BigData"
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # -------------------------
    # 6. Info Box
    # -------------------------
    with st.expander("ℹ️ FUNGSI BAGIAN INI", expanded=True):
        st.markdown("""
        Bagian By Notion menampilkan **perbandingan peserta sertifikasi dari Notion** dengan **jumlah sertifikasi selesai berdasarkan data Basys**.

        Informasi yang ditampilkan:
        1. **Total Peserta (By Notion)** – jumlah peserta yang tercatat di Notion (**seluruh data Excel**).
        2. **Total Selesai (By Basys)** – jumlah sertifikasi yang selesai sesuai data Basys (**seluruh data BigData**).
        3. **Grafik Trend** – membandingkan jumlah peserta Notion vs Selesai Basys per bulan (sesuai tanggal pilihan).

        Fungsi bagian ini:
        - Memudahkan monitoring kesesuaian data Notion dengan data resmi Basys.
        - Menunjukkan tren pendaftaran dan penyelesaian sertifikasi dari waktu ke waktu.
        """)



# ===== Tab 3: By Institution =====
with tab3:
    st.subheader("🏢 VISUALISASI DATA PER INSTANSI")

    # Filter tanggal
    min_date_inst = df_bigdata["date certification"].min().date()
    max_date_inst = df_bigdata["date certification"].max().date()
    sel_date_inst = st.date_input(
        "📅 Pilih Rentang Tanggal (Institution):",
        (min_date_inst, max_date_inst),
        min_value=min_date_inst,
        max_value=max_date_inst,
        key="date_institution"
    )

    # Filter jenis dan instansi
    jenis_list_inst = ["All"] + sorted(df_bigdata["jenis sertifikasi"].dropna().unique())
    instansi_list_inst = ["All"] + sorted(df_bigdata["instansi"].dropna().unique())
    col1, col2 = st.columns(2)
    sel_jenis_inst = col1.selectbox("Jenis Sertifikasi", jenis_list_inst, key="jenis_institution")
    sel_instansi_inst = col2.selectbox("Instansi", instansi_list_inst, key="instansi_institution")

    # Filter data
    filtered_df_inst = df_bigdata[
        (df_bigdata["date certification"].dt.date >= sel_date_inst[0]) &
        (df_bigdata["date certification"].dt.date <= sel_date_inst[1])
    ]
    if sel_jenis_inst != "All":
        filtered_df_inst = filtered_df_inst[filtered_df_inst["jenis sertifikasi"] == sel_jenis_inst]
    if sel_instansi_inst != "All":
        filtered_df_inst = filtered_df_inst[filtered_df_inst["instansi"] == sel_instansi_inst]
    filtered_df_inst["status"] = filtered_df_inst.apply(get_status, axis=1)

    # Stat cards
    colA, colB = st.columns(2)
    with colA:
        stat_card("Total Pendaftar", filtered_df_inst["pendaftar"].sum(), "👥")
    with colB:
        stat_card("Selesai", filtered_df_inst["selesai"].sum(), "✅")

    # Top 5 instansi
    top_instansi = (
        filtered_df_inst.groupby("instansi")["pendaftar"].sum()
        .reset_index().sort_values("pendaftar", ascending=False).head(5)
        .sort_values("pendaftar", ascending=True)
    )

    # Lollipop chart
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

    # Info box
    with st.expander("ℹ Fungsi Bagian Ini", expanded=True):
        st.markdown("""
        Bagian ini menampilkan *5 instansi dengan jumlah pendaftar sertifikasi terbanyak* berdasarkan rentang tanggal yang dipilih.

        Manfaat informasi ini:
        1. Mengetahui instansi mana yang paling aktif mendorong karyawannya mengikuti sertifikasi.
        2. Membantu penyelenggara memahami distribusi peserta per instansi.
        3. Mempermudah perencanaan alokasi sumber daya dan layanan untuk instansi tertentu.
        """)



# End of Dashboard