import streamlit as st
import pandas as pd
from datetime import date
import math
from streamlit_gsheets import GSheetsConnection

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
# KONEKSI KE GOOGLE SHEETS
# ==========================================
# Pastikan sudah mengatur secrets.toml di folder .streamlit
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_gsheets = conn.read(worksheet="Sheet1", ttl=0) # ttl=0 agar selalu ambil data fresh
    gsheets_connected = True
except Exception as e:
    st.error(f"Gagal terhubung ke Google Sheets. Pastikan secrets.toml sudah benar. Error: {e}")
    gsheets_connected = False
    df_gsheets = pd.DataFrame()

# ==========================================
# INISIALISASI SESSION STATE
# ==========================================
if 'life_notes' not in st.session_state:
    st.session_state.life_notes = {i: "" for i in range(101)}
    
    # Masukkan data dari GSheets ke session_state saat pertama kali dimuat
    if gsheets_connected and 'Umur' in df_gsheets.columns and 'Catatan' in df_gsheets.columns:
        for _, row in df_gsheets.iterrows():
            umur = int(row['Umur']) if pd.notna(row['Umur']) else None
            catatan = row['Catatan']
            if umur is not None and umur in st.session_state.life_notes:
                st.session_state.life_notes[umur] = "" if pd.isna(catatan) else str(catatan)

# ==========================================
# TAMPILAN SIDEBAR
# ==========================================
with st.sidebar:
    st.header("⚙️ Konfigurasi Kalender")
    birth_date = st.date_input("Tanggal Lahir:", value=date(2003, 3, 22), max_value=date.today())
    target_age = st.number_input("Target Umur (Tahun):", min_value=1, max_value=100, value=90)
    
    st.divider()
    
    st.header("☁️ Sinkronisasi Cloud")
    if gsheets_connected:
        st.success("Tersambung ke Google Sheets ✅")
        
        # Tombol untuk push data ke cloud
        if st.button("💾 Simpan Catatan ke Cloud", type="primary", use_container_width=True):
            with st.spinner("Menyimpan perubahan..."):
                df_to_save = pd.DataFrame(
                    list(st.session_state.life_notes.items()), 
                    columns=['Umur', 'Catatan']
                )
                conn.update(worksheet="Sheet1", data=df_to_save)
                st.cache_data.clear()
                st.success("Data berhasil disimpan ke Google Sheets!")
    else:
        st.warning("Koneksi Google Sheets belum diatur.")

# ==========================================
# LOGIKA PERHITUNGAN UMUR
# ==========================================
today = date.today()
delta_days = (today - birth_date).days
weeks_lived = max(0, delta_days // 7)
years_lived = math.floor(delta_days / 365.25)
total_weeks = target_age * 52
week_left = max(0, total_weeks - weeks_lived) 

# ==========================================
# TAMPILAN UTAMA & CSS
# ==========================================
st.title("📅 MY LIFE IN WEEKS")
st.markdown("*Terinspirasi dari artikel Tim Urban 'Your Life in Weeks' di WaitButWhy.*")
st.info(f"**Statistik Saat Ini:** Anda berusia {years_lived} tahun dan telah menjalani **{weeks_lived:,} minggu** atau **{delta_days:,} hari** dalam hidup Anda, tersisa **{week_left}** minggu menuju target **{target_age}** usia anda")

# Injeksi CSS Custom
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
    .lived { background-color: #1f77b4; border-color: #1f77b4; }
    .future { background-color: #ffffff; }
    .age-label { 
        font-size: 13px; 
        font-weight: 600;
        width: 65px; 
        color: #444; 
        font-family: monospace; 
    }
    /* Mengatur ukuran tombol popover agar sejajar dengan grid */
    div[data-testid="stPopover"] button {
        padding: 0px 8px;
        min-height: 24px;
        height: 24px;
        margin-top: -2px;
    }
</style>
""", unsafe_allow_html=True)

st.divider()

st.caption("Minggu 1 ➔ 52")

# ==========================================
# RENDER GRID KALENDER & TOMBOL CATATAN
# ==========================================
for year in range(target_age + 1):
    # Proporsi diubah: Grid mengambil 95% ruang, Tombol mengambil 5% ruang di ujung kanan
    col_grid, col_action = st.columns([0.95, 0.05])
    
    with col_grid:
        weeks_html = f'<div class="week-container"><div class="age-label">Thn {year:02d}</div>'
        for week in range(52):
            current_week_idx = (year * 52) + week
            status_class = "lived" if current_week_idx < weeks_lived else "future"
            weeks_html += f'<div class="week-box {status_class}"></div>'
        weeks_html += '</div>'
        st.markdown(weeks_html, unsafe_allow_html=True)
    
    with col_action:
        # Teks yang akan muncul saat tombol di-hover
        current_note = st.session_state.life_notes[year]
        hover_info = current_note if current_note.strip() != "" else "Belum ada catatan. Klik untuk menambah."
        
        # st.popover bertindak seperti tombol yang jika diklik akan membuka menu dropdown
        with st.popover("📝", help=hover_info):
            st.session_state.life_notes[year] = st.text_area(
                f"Catatan Umur {year}:", 
                value=st.session_state.life_notes[year],
                key=f"input_{year}",
                height=100
            )
