# 📊 Dashboard Sertifikasi

Dashboard ini dibuat untuk memudahkan visualisasi dan pelaporan data sertifikasi yang berasal dari dua sumber utama, yaitu **Basys** dan **Notion**.  
Data diekspor, dibersihkan menggunakan **JupyterLab**, kemudian diimpor ke **Supabase (PostgreSQL di cloud)** agar lebih mudah dikelola dan divisualisasikan.  
Aplikasi utama dibangun menggunakan **Streamlit** sehingga user dapat melihat data secara cepat, sederhana, dan interaktif.

---

## ✨ Fitur Utama
- 🔄 **Integrasi Multi Sumber Data** → Menggabungkan data dari Basys dan Notion.  
- 🧹 **Data Cleaning** → Pembersihan data dilakukan menggunakan JupyterLab.  
- ☁️ **Database Cloud** → Penyimpanan data menggunakan Supabase (PostgreSQL).  
- 📊 **Visualisasi Interaktif** → Dashboard dengan filter berdasarkan instansi dan rentang tanggal.  
- ⚡ **Pelaporan Cepat** → Memudahkan user dalam membaca perbandingan jumlah peserta, pengajuan, progres, hingga sertifikasi yang sudah selesai.  

---

## 🏗️ Arsitektur Project
1. **Export Data** dari Basys & Notion.  
2. **Data Cleaning** menggunakan JupyterLab (cek duplikasi, nilai kosong, dll).  
3. **Import Data** hasil cleaning ke Supabase dalam format CSV.  
4. **Visualisasi Dashboard** menggunakan Streamlit (terhubung langsung ke Supabase).  

---

## ⚙️ Instalasi & Setup

### 1. Clone Repository
```bash
git clone https://github.com/username/dashboard-sertifikasi.git
cd dashboard-sertifikasi

2. Buat Virtual Environment (opsional tapi disarankan)#
