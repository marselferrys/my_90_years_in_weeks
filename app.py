import streamlit as st
import pandas as pd
from datetime import date
import math

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="My Life in Weeks",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# INISIALISASI SESSION STATE
# ==========================================
# Session state digunakan untuk menyimpan data catatan agar tidak hilang 
# saat Streamlit memuat ulang halaman (rerun).
if 'life_notes' not in st.session_state:
    # Menginisialisasi dictionary untuk umur 0 hingga 100 dengan string kosong
    st.session_state.life_notes = {i: "" for i in range(101)}

# ==========================================
# TAMPILAN SIDEBAR (PENGATURAN & PENYIMPANAN)
# ==========================================
with st.sidebar:
    st.header("⚙️ Konfigurasi Kalender")
    
    # Input tanggal lahir (Dibatasi maksimal hari ini)
    birth_date = st.date_input(
        "Tanggal Lahir:", 
        value=date(2003, 3, 22), 
        max_value=date.today()
    )
    
    # Input target umur maksimal
    target_age = st.number_input("Target Umur (Tahun):", min_value=1, max_value=100, value=90)
    
    st.divider()
    
    st.header("💾 Simpan & Muat Data (CSV)")
    
    # --- FITUR IMPORT (MUAT DATA) ---
    uploaded_file = st.file_uploader("Unggah file CSV catatan Anda", type=["csv"])
    if uploaded_file is not None:
        try:
            df_imported = pd.read_csv(uploaded_file)
            
            # Validasi apakah kolom yang dibutuhkan tersedia di file CSV
            if 'Umur' in df_imported.columns and 'Catatan' in df_imported.columns:
                for _, row in df_imported.iterrows():
                    umur = int(row['Umur'])
                    catatan = row['Catatan']
                    
                    # Memastikan umur ada dalam batasan session_state dan menangani nilai NaN (kosong)
                    if umur in st.session_state.life_notes:
                        st.session_state.life_notes[umur] = "" if pd.isna(catatan) else str(catatan)
                
                st.success("✅ Data catatan berhasil dimuat!")
            else:
                st.error("❌ Format CSV tidak valid. Pastikan ada kolom 'Umur' dan 'Catatan'.")
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat membaca file: {e}")

    # --- FITUR EXPORT (SIMPAN DATA) ---
    # Mengonversi dictionary session_state menjadi DataFrame pandas
    df_export = pd.DataFrame(list(st.session_state.life_notes.items()), columns=['Umur', 'Catatan'])
    csv_data = df_export.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Unduh Catatan (CSV)",
        data=csv_data,
        file_name='life_calendar_notes.csv',
        mime='text/csv',
        use_container_width=True
    )

# ==========================================
# LOGIKA PERHITUNGAN UMUR
# ==========================================
today = date.today()
delta_days = (today - birth_date).days
weeks_lived = max(0, delta_days // 7) # Memastikan tidak ada nilai negatif
years_lived = math.floor(delta_days / 365.25)

# ==========================================
# TAMPILAN UTAMA (HEADER & CSS)
# ==========================================
st.title("📅 MY LIFE IN WEEKS")
st.markdown("*Terinspirasi dari artikel Tim Urban 'Your Life in Weeks' di WaitButWhy.*")
st.info(f"**Statistik Saat Ini:** Anda berusia {years_lived} tahun dan telah menjalani **{weeks_lived:,} minggu** dalam hidup Anda.")

# Injeksi CSS Custom untuk merapikan grid kotak minggu dan menghilangkan margin berlebih pada input
st.markdown("""
<style>
    .week-container { 
        display: flex; 
        gap: 3px; 
        align-items: center; 
        margin-bottom: 2px;
    }
    .week-box { 
        width: 12px; 
        height: 12px; 
        border: 1px solid #d1d1d1; 
        border-radius: 2px;
        flex-shrink: 0; 
    }
    .lived { 
        background-color: #1f77b4; /* Warna kotak yang sudah dilalui */
        border-color: #1f77b4; 
    }
    .future { 
        background-color: #ffffff; /* Warna kotak masa depan */
    }
    .age-label { 
        font-size: 13px; 
        font-weight: 600;
        width: 65px; 
        color: #444; 
        font-family: monospace; 
    }
    /* Memperbaiki posisi input teks agar sejajar dengan grid */
    div[data-testid="stTextInput"] {
        margin-top: -16px;
        margin-bottom: -16px;
    }
    div[data-testid="stTextInput"] input {
        font-size: 14px;
        padding: 4px 10px;
    }
</style>
""", unsafe_allow_html=True)

st.divider()

# ==========================================
# RENDER GRID KALENDER & INPUT CATATAN
# ==========================================
# Membuat label indikator minggu di atas grid
col_label, _ = st.columns([0.45, 0.55])
with col_label:
    st.caption("Minggu 1 ➔ 52")

# Melakukan iterasi dari tahun ke-0 hingga target_age
for year in range(target_age + 1):
    # Membagi layout menjadi 2 kolom: 45% untuk Grid Kotak, 55% untuk Input Catatan
    col_grid, col_note = st.columns([0.45, 0.55])
    
    with col_grid:
        # Menyusun elemen HTML untuk baris tahun ini
        weeks_html = f'<div class="week-container"><div class="age-label">Thn {year:02d}</div>'
        
        for week in range(52):
            # Menghitung indeks minggu ke berapa secara total sejak lahir
            current_week_idx = (year * 52) + week
            
            # Menentukan apakah minggu ini sudah dilalui atau belum
            status_class = "lived" if current_week_idx < weeks_lived else "future"
            weeks_html += f'<div class="week-box {status_class}"></div>'
            
        weeks_html += '</div>'
        st.markdown(weeks_html, unsafe_allow_html=True)
    
    with col_note:
        # Membuat input teks yang langsung terikat dan mengubah session_state
        # Menggunakan key yang unik (input_year) agar Streamlit dapat melacak setiap input
        st.session_state.life_notes[year] = st.text_input(
            label=f"Catatan Umur {year}", 
            value=st.session_state.life_notes[year],
            label_visibility="collapsed", # Menyembunyikan teks label agar tampilan bersih
            key=f"input_{year}",
            placeholder=f"Tulis momen penting di usia {year}..."
        )
