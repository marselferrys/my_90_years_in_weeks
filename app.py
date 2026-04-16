import streamlit as st
import pandas as pd
from datetime import date, timedelta
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
# INISIALISASI SESSION STATE DASAR
# ==========================================
if 'life_notes' not in st.session_state:
    st.session_state.life_notes = {i: "" for i in range(101)}
    
if 'weekly_notes' not in st.session_state:
    st.session_state.weekly_notes = {}

# ==========================================
# KONEKSI KE GOOGLE SHEETS
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Membaca Sheet1 (Catatan Tahunan)
    df_gsheets_yearly = conn.read(worksheet="Sheet1", ttl=0)
    
    # [FITUR BARU] Membaca Sheet2 (Catatan Mingguan)
    try:
        df_gsheets_weekly = conn.read(worksheet="Sheet2", ttl=0)
    except:
        df_gsheets_weekly = pd.DataFrame() # Jika Sheet2 belum dibuat, abaikan tanpa error
        
    gsheets_connected = True
except Exception as e:
    st.error(f"Gagal terhubung ke Google Sheets. Pastikan secrets.toml sudah benar. Error: {e}")
    gsheets_connected = False
    df_gsheets_yearly = pd.DataFrame()
    df_gsheets_weekly = pd.DataFrame()

# Memasukkan data dari GSheets ke session_state saat pertama kali dimuat
if gsheets_connected:
    # 1. Load Data Tahunan
    if 'Umur' in df_gsheets_yearly.columns and 'Catatan' in df_gsheets_yearly.columns:
        for _, row in df_gsheets_yearly.iterrows():
            umur = int(row['Umur']) if pd.notna(row['Umur']) else None
            catatan = row['Catatan']
            if umur is not None and umur in st.session_state.life_notes:
                st.session_state.life_notes[umur] = "" if pd.isna(catatan) else str(catatan)
                
    # 2. [FITUR BARU] Load Data Mingguan
    if 'Minggu_Ke' in df_gsheets_weekly.columns and 'Catatan' in df_gsheets_weekly.columns:
        for _, row in df_gsheets_weekly.iterrows():
            minggu_idx = int(row['Minggu_Ke']) if pd.notna(row['Minggu_Ke']) else None
            catatan = row['Catatan']
            if minggu_idx is not None:
                st.session_state.weekly_notes[minggu_idx] = "" if pd.isna(catatan) else str(catatan)

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
            with st.spinner("Menyimpan perubahan ke Sheet1 dan Sheet2..."):
                # Simpan Tahunan ke Sheet1
                df_to_save_yearly = pd.DataFrame(
                    list(st.session_state.life_notes.items()), 
                    columns=['Umur', 'Catatan']
                )
                conn.update(worksheet="Sheet1", data=df_to_save_yearly)
                
                # [FITUR BARU] Simpan Mingguan ke Sheet2
                df_to_save_weekly = pd.DataFrame(
                    list(st.session_state.weekly_notes.items()), 
                    columns=['Minggu_Ke', 'Catatan']
                )
                # Menyimpan hanya jika ada catatan mingguan agar tidak error jika kosong
                if not df_to_save_weekly.empty:
                    conn.update(worksheet="Sheet2", data=df_to_save_weekly)
                
                st.cache_data.clear()
                st.success("Seluruh data berhasil disimpan ke Google Sheets!")

        # Tombol untuk pull data dari cloud 
        if st.button("🔄 Update Catatan dari Cloud", use_container_width=True):
            with st.spinner("Mengambil data terbaru..."):
                st.cache_data.clear() 
                
                # Update Tahunan
                df_latest_yearly = conn.read(worksheet="Sheet1", ttl=0) 
                if 'Umur' in df_latest_yearly.columns and 'Catatan' in df_latest_yearly.columns:
                    for _, row in df_latest_yearly.iterrows():
                        umur = int(row['Umur']) if pd.notna(row['Umur']) else None
                        catatan = row['Catatan']
                        if umur is not None and umur in st.session_state.life_notes:
                            st.session_state.life_notes[umur] = "" if pd.isna(catatan) else str(catatan)
                
                # [FITUR BARU] Update Mingguan
                try:
                    df_latest_weekly = conn.read(worksheet="Sheet2", ttl=0)
                    if 'Minggu_Ke' in df_latest_weekly.columns and 'Catatan' in df_latest_weekly.columns:
                        for _, row in df_latest_weekly.iterrows():
                            minggu_idx = int(row['Minggu_Ke']) if pd.notna(row['Minggu_Ke']) else None
                            catatan = row['Catatan']
                            if minggu_idx is not None:
                                st.session_state.weekly_notes[minggu_idx] = "" if pd.isna(catatan) else str(catatan)
                except:
                    pass
                    
                st.success("Data berhasil diupdate dari Google Sheets!")
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

days_into_current_week = delta_days % 7 
percent_current_week = (days_into_current_week / 7) * 100 

# ==========================================
# TAMPILAN UTAMA & CSS
# ==========================================
st.title("📅 MY LIFE IN WEEKS")
st.markdown("*Terinspirasi dari artikel Tim Urban 'Your Life in Weeks' di WaitButWhy.*")
st.markdown(
    f"""
    <div style="
        background-color:#0f5132;
        padding:15px;
        border-radius:10px;
        color:white;
        font-size:16px;
    ">
        <b>Statistik Saat Ini:</b> Anda berusia 
        <span style="background-color:#ffc107; color:black; padding:2px 6px; border-radius:5px;">
            {years_lived} tahun
        </span>  dan telah menjalani 
        <span style="background-color:#ffc107; color:black; padding:2px 6px; border-radius:5px;">
            {weeks_lived:,} minggu
        </span>  atau 
        <span style="background-color:#ffc107; color:black; padding:2px 6px; border-radius:5px;">
            {delta_days:,} hari
        </span>  dalam hidup Anda, tersisa 
        <span style="background-color:#ffc107; color:black; padding:2px 6px; border-radius:5px;">
            {week_left:,} minggu
        </span>  menuju target usia 
        <span style="background-color:#ffc107; color:black; padding:2px 6px; border-radius:5px;">
            {target_age} tahun
        </span>.
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================
# EDITOR CATATAN MINGGUAN
# ==========================================
st.write("") 
with st.expander("📝 Tambah/Edit Catatan Spesifik Per Minggu"):
    col_y, col_w, col_input, col_btn = st.columns([1, 1, 3, 1])
    
    with col_y:
        edit_year = st.number_input("Tahun ke-", 0, target_age, years_lived)
    with col_w:
        edit_week = st.number_input("Minggu ke-", 1, 52, (weeks_lived % 52) + 1)
    
    abs_edit_idx = (edit_year * 52) + (edit_week - 1)
    current_weekly_note = st.session_state.weekly_notes.get(abs_edit_idx, "")
    
    with col_input:
        new_weekly_note = st.text_input("Tulis catatan untuk minggu ini:", value=current_weekly_note, label_visibility="collapsed")
    with col_btn:
        if st.button("Simpan Catatan Mingguan", use_container_width=True):
            st.session_state.weekly_notes[abs_edit_idx] = new_weekly_note
            st.success("Tersimpan!")

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
        cursor: pointer;
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
    col_grid, col_action = st.columns([0.95, 0.05])
    
    with col_grid:
        weeks_html = f'<div class="week-container"><div class="age-label">Thn {year:02d}</div>'
        for week in range(52):
            current_week_idx = (year * 52) + week
            
            w_start = birth_date + timedelta(weeks=current_week_idx)
            w_end = w_start + timedelta(days=6)
            date_str = f"{w_start.strftime('%d %b %Y')} - {w_end.strftime('%d %b %Y')}"
            
            weekly_note = st.session_state.weekly_notes.get(current_week_idx, "")
            
            tooltip_text = f"Tahun {year}, Minggu {week + 1}&#10;📅 {date_str}"
            if weekly_note:
                tooltip_text += f"&#10;📝 {weekly_note}"

            style = ""
            if current_week_idx < weeks_lived:
                status_class = "lived"
            elif current_week_idx == weeks_lived:
                status_class = "current"
                style = f"background: linear-gradient(to right, #1f77b4 {percent_current_week}%, #ffffff {percent_current_week}%); border-color: #1f77b4;"
                tooltip_text = f"⏳ MINGGU INI ({percent_current_week:.0f}% Berlalu)&#10;" + tooltip_text
            else:
                status_class = "future"
                
            if weekly_note:
                style += " border-color: #ff9800; border-width: 2px;"

            weeks_html += f'<div class="week-box {status_class}" style="{style}" title="{tooltip_text}"></div>'
            
        weeks_html += '</div>'
        st.markdown(weeks_html, unsafe_allow_html=True)
    
    with col_action:
        current_note = st.session_state.life_notes[year]
        hover_info = current_note if current_note.strip() != "" else "Belum ada catatan. Klik untuk menambah."
        
        with st.popover("📝", help=hover_info):
            st.session_state.life_notes[year] = st.text_area(
                f"Catatan Umur {year}:", 
                value=st.session_state.life_notes[year],
                key=f"input_{year}",
                height=100
            )
