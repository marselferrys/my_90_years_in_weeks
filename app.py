import streamlit as st
import pandas as pd
from datetime import date, timedelta
import math
from streamlit_gsheets import GSheetsConnection
import time
import streamlit.components.v1 as components
from datetime import date, timedelta, datetime

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
    
# State untuk catatan harian
if 'daily_notes' not in st.session_state:
    st.session_state.daily_notes = {}

# Flag penanda agar tidak terus-menerus menarik data dari Google API
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# Pelacak status perubahan dan waktu
if 'unsaved_changes' not in st.session_state:
    st.session_state.unsaved_changes = False
if 'last_edit_time' not in st.session_state:
    st.session_state.last_edit_time = time.time()
    
# mengingat hari mana yang sedang Anda pilih
if 'active_day_idx' not in st.session_state:
    st.session_state.active_day_idx = 0

# ==========================================
# KONEKSI KE GOOGLE SHEETS
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_gsheets_yearly = conn.read(worksheet="Sheet1", ttl=600)
    
    try:
        df_gsheets_weekly = conn.read(worksheet="Sheet2", ttl=600)
    except:
        df_gsheets_weekly = pd.DataFrame() 
        
    # Membaca Sheet3 (Catatan Harian)
    try:
        df_gsheets_daily = conn.read(worksheet="Sheet3", ttl=600)
    except:
        df_gsheets_daily = pd.DataFrame()

    gsheets_connected = True
except Exception as e:
    st.error(f"Gagal terhubung ke Google Sheets. Pastikan secrets.toml sudah benar. Error: {e}")
    gsheets_connected = False
    df_gsheets_yearly = pd.DataFrame()
    df_gsheets_weekly = pd.DataFrame()
    df_gsheets_daily = pd.DataFrame()

if gsheets_connected and not st.session_state.data_loaded:
    # Load Data Tahunan
    if 'Umur' in df_gsheets_yearly.columns and 'Catatan' in df_gsheets_yearly.columns:
        for _, row in df_gsheets_yearly.iterrows():
            umur = int(row['Umur']) if pd.notna(row['Umur']) else None
            catatan = row['Catatan']
            if umur is not None and umur in st.session_state.life_notes:
                st.session_state.life_notes[umur] = "" if pd.isna(catatan) else str(catatan)
                
    # Load Data Mingguan
    if 'Minggu_Ke' in df_gsheets_weekly.columns and 'Catatan' in df_gsheets_weekly.columns:
        for _, row in df_gsheets_weekly.iterrows():
            minggu_idx = int(row['Minggu_Ke']) if pd.notna(row['Minggu_Ke']) else None
            catatan = row['Catatan']
            if minggu_idx is not None:
                st.session_state.weekly_notes[minggu_idx] = "" if pd.isna(catatan) else str(catatan)
                
    # Load Data Harian
    if 'Tanggal' in df_gsheets_daily.columns and 'Catatan' in df_gsheets_daily.columns:
        for _, row in df_gsheets_daily.iterrows():
            tanggal_str = str(row['Tanggal']) if pd.notna(row['Tanggal']) else None
            catatan = row['Catatan']
            if tanggal_str is not None:
                st.session_state.daily_notes[tanggal_str] = "" if pd.isna(catatan) else str(catatan)

    # Tandai bahwa data sudah berhasil ditarik dan dimasukkan ke memori lokal
    st.session_state.data_loaded = True

# ==========================================
# TAMPILAN SIDEBAR
# ==========================================
with st.sidebar:
    st.header("⚙️ Konfigurasi Kalender")
    # birth_date = st.date_input("Tanggal Lahir:", value=date(2003, 3, 22), max_value=date.today())
    birth_date = st.date_input(
        "Tanggal Lahir:", 
        value=date(2003, 3, 22),
        min_value=date(1900, 1, 1),
        max_value=date(2100, 12, 31)
    )

    # Tanggal acuan untuk menghitung umur dan progress grid
    target_date = st.date_input(
        "Tanggal Acuan (Simulasi):", 
        value=date.today(),
        min_value=date(1900, 1, 1),
        max_value=date(2100, 12, 31)
    )
    
    target_age = st.number_input("Target Umur (Tahun):", min_value=1, max_value=100, value=90)
    
    st.divider()
    
    st.header("☁️ Sinkronisasi Cloud")
    if gsheets_connected:
        st.success("Tersambung ke Google Sheets ✅")
        
        if st.button("💾 Simpan Catatan ke Cloud", type="primary", use_container_width=True):
            with st.spinner("Menyimpan & Membersihkan data lama di Sheet1, Sheet2, Sheet3..."):
                # Menyaring nilai kosong (="") agar ikut terhapus dari GSheets
                
                df_to_save_yearly = pd.DataFrame(
                    [(k, v) for k, v in st.session_state.life_notes.items() if str(v).strip() != ""], 
                    columns=['Umur', 'Catatan']
                )
                conn.update(worksheet="Sheet1", data=df_to_save_yearly)
                
                df_to_save_weekly = pd.DataFrame(
                    [(k, v) for k, v in st.session_state.weekly_notes.items() if str(v).strip() != ""], 
                    columns=['Minggu_Ke', 'Catatan']
                )
                if not df_to_save_weekly.empty or len(st.session_state.weekly_notes) > 0:
                    conn.update(worksheet="Sheet2", data=df_to_save_weekly)
                    
                # Simpan Harian ke Sheet3
                df_to_save_daily = pd.DataFrame(
                    [(k, v) for k, v in st.session_state.daily_notes.items() if str(v).strip() != ""], 
                    columns=['Tanggal', 'Catatan']
                )
                if not df_to_save_daily.empty or len(st.session_state.daily_notes) > 0:
                    conn.update(worksheet="Sheet3", data=df_to_save_daily)
                
                st.cache_data.clear()
                st.session_state.unsaved_changes = False
                st.success("Seluruh data berhasil disimpan ke Google Sheets!")

        # Tombol untuk pull data dari cloud 
        if st.button("🔄 Update Catatan dari Cloud", use_container_width=True):
            with st.spinner("Mengambil data terbaru dari Google Sheets..."):
                # 1. Bersihkan cache koneksi agar Streamlit melupakan data yang lama
                st.cache_data.clear() 
                
                # 2. Kembalikan flag menjadi False, agar blok loading di atas dieksekusi ulang
                st.session_state.data_loaded = False 
                
                # 3. Refresh (jalankan ulang) aplikasi dari baris pertama
                st.rerun()
    else:
        st.warning("Koneksi Google Sheets belum diatur.")

# ==========================================
# LOGIKA PERHITUNGAN UMUR
# ==========================================
# Menggunakan target_date dari sidebar
raw_delta_days = (target_date - birth_date).days

# Cegah angka minus jika tanggal lahir lebih besar dari tanggal acuan
delta_days = max(0, raw_delta_days)

weeks_lived = delta_days // 7
years_lived = math.floor(delta_days / 365.25)
total_weeks = target_age * 52
week_left = max(0, total_weeks - weeks_lived) 
day_left = max(0, int((target_age * 365.25) - delta_days))

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
        </span>  
        atau
        <span style="background-color:#ffc107; color:black; padding:2px 6px; border-radius:5px;">
            {day_left:,} hari 
        </span>
        menuju target usia 
        <span style="background-color:#ffc107; color:black; padding:2px 6px; border-radius:5px;">
            {target_age} tahun
        </span>.
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================
# SISTEM PERINGATAN KEAMANAN DATA (UNSAVED CHANGES)
# ==========================================
if st.session_state.unsaved_changes:
    # 1. Peringatan Berbasis Waktu di UI Streamlit
    time_lapsed = time.time() - st.session_state.last_edit_time
    
    if time_lapsed > 300: # Jika lebih dari 300 detik (5 menit) belum disimpan ke cloud
        st.error("⚠️ **Peringatan Kritis:** Anda memiliki catatan lokal yang belum diunggah ke Cloud selama lebih dari 5 menit. Segera tekan 'Simpan Catatan ke Cloud' di Sidebar agar data tidak hilang!")
    else:
        st.warning("💡 **Terdapat Perubahan:** Anda memiliki catatan yang belum diamankan ke Cloud Google Sheets.")

    # 2. Injeksi JavaScript untuk Memblokir Tab Browser Ditutup
    components.html("""
        <script>
            window.parent.onbeforeunload = function(e) {
                var dialogText = 'Anda memiliki catatan hidup yang belum disimpan ke Cloud. Yakin ingin keluar?';
                e.returnValue = dialogText;
                return dialogText;
            };
        </script>
    """, height=0, width=0)
else:
    # Hapus blokir jika data sudah aman di Cloud
    components.html("""
        <script>
            window.parent.onbeforeunload = null;
        </script>
    """, height=0, width=0)

# ==========================================
# EDITOR CATATAN MINGGUAN & HARIAN
# ==========================================
st.write("") 
with st.expander("📝 Tambah/Edit Catatan Spesifik Per Minggu & Hari", expanded=True):
    col_d, col_y, col_w = st.columns([1.5, 1, 1])
    
    with col_d:
        selected_date = st.date_input("Pilih Tanggal Acuan:", value=date.today())
        
    delta_selected = (selected_date - birth_date).days
    auto_abs_week = max(0, delta_selected // 7)
    auto_year = min(target_age, auto_abs_week // 52) 
    auto_week = (auto_abs_week % 52) + 1
    
    with col_y:
        edit_year = st.number_input("Tahun ke-", 0, target_age, int(auto_year))
    with col_w:
        edit_week = st.number_input("Minggu ke-", 1, 52, int(auto_week))
    
    abs_edit_idx = (edit_year * 52) + (edit_week - 1)
    w_start = birth_date + timedelta(weeks=abs_edit_idx)
    w_end = w_start + timedelta(days=6)
    
    # 1. INPUT CATATAN MINGGUAN
    st.markdown(f"**📌 Catatan Mingguan** *(Rentang: {w_start.strftime('%d %b')} - {w_end.strftime('%d %b %Y')})*")
    current_weekly_note = st.session_state.weekly_notes.get(abs_edit_idx, "")
    col_w_input, col_w_btn = st.columns([4, 1])
    with col_w_input:
        # Mengubah key menjadi dinamis menggunakan abs_edit_idx
        new_weekly_note = st.text_input(
            "Tulis catatan minggu ini:", 
            value=current_weekly_note, 
            label_visibility="collapsed", 
            key=f"w_note_{abs_edit_idx}" 
        )
    with col_w_btn:
        if st.button("Simpan Mingguan", use_container_width=True):
            st.session_state.weekly_notes[abs_edit_idx] = new_weekly_note
            st.session_state.unsaved_changes = True            
            st.session_state.last_edit_time = time.time()    
            st.rerun()

    st.divider()

    # 2. PICKER KOTAK HARIAN INTERAKTIF
    st.markdown("**🗓️ Pilih Hari & Edit Catatan**")
    
    # Hitung data waktu untuk progress harian
    now = datetime.now()
    real_today = now.date()
    seconds_passed = (now.hour * 3600) + (now.minute * 60) + now.second
    percent_current_day = (seconds_passed / 86400) * 100

    # Render 7 Kolom sebagai Kotak yang Bisa Diklik
    day_cols = st.columns(7)
    
    for i in range(7):
        d_date = w_start + timedelta(days=i)
        d_str = d_date.strftime('%Y-%m-%d')
        d_note = st.session_state.daily_notes.get(d_str, "")
        
        # Penentuan Nama Hari untuk Label Tombol
        day_label = d_date.strftime('%a') # Mon, Tue, dst.
        
        # Logika Warna & Progress (CSS dinamis akan diatur via st.markdown di bawah)
        is_selected = (i == st.session_state.active_day_idx)
        
        # Tombol Interaktif: Jika diklik, update active_day_idx
        if day_cols[i].button(day_label, key=f"btn_day_{i}", use_container_width=True):
            st.session_state.active_day_idx = i
            st.rerun()

    # 3. AREA INPUT OTOMATIS BERDASARKAN KOTAK YANG DIPILIH
    selected_day_idx = st.session_state.active_day_idx
    sel_day_date = w_start + timedelta(days=selected_day_idx)
    sel_day_str = sel_day_date.strftime('%Y-%m-%d')
    current_daily_note = st.session_state.daily_notes.get(sel_day_str, "")

    # Menampilkan info detail hari yang terpilih secara otomatis
    st.caption(f"📍 Mengedit: **{sel_day_date.strftime('%A, %d %B %Y')}** (Tahun {edit_year}, Minggu {edit_week})")
    
    col_d_input, col_d_btn = st.columns([4, 1])
    with col_d_input:
        # Input Note yang otomatis terhubung dengan kotak yang diklik
        new_daily_note = st.text_input(
            "Tulis catatan hari ini:", 
            value=current_daily_note, 
            label_visibility="collapsed", 
            key=f"d_note_{sel_day_str}"
        )
    with col_d_btn:
        if st.button("Simpan Harian", use_container_width=True, type="primary"):
            st.session_state.daily_notes[sel_day_str] = new_daily_note
            st.session_state.unsaved_changes = True
            st.session_state.last_edit_time = time.time()
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
    .daily-container {
        display: flex;
        gap: 10px; /* Jarak antar kotak sedikit dilebarkan agar lebih rapi */
        align-items: center;
        justify-content: center; /* Membuat kotak berada persis di tengah */
        margin-top: 20px;
        margin-bottom: 15px; /* Memberikan jarak dengan garis di bawahnya */
        padding-bottom: 5px;
    }
    .daily-box {
        width: 35px;
        height: 35px;
        border-radius: 6px;
        border: 1px solid solid;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .daily-box:hover {
        transform: scale(1.1);
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
    /* Styling Tombol Harian agar seperti Kotak Grid */
    div[data-testid="stHorizontalBlock"] > div:nth-child(n) button {
        background-color: #ffc107 !important;
        color: black !important;
        border: 1px solid #e0a800 !important;
        height: 45px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    /* Highlight untuk kotak yang sedang aktif dipilih */
    div[data-testid="stHorizontalBlock"] > div:nth-child(n) button:focus,
    div[data-testid="stHorizontalBlock"] > div:nth-child(n) button:active {
        border: 2px solid #0d6efd !important;
        box-shadow: 0px 0px 10px rgba(13, 110, 253, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

st.divider()
st.caption("Minggu 1 ➔ 52")

# ==========================================
# RENDER GRID KALENDER & TOMBOL CATATAN TAHUNAN
# ==========================================
for year in range(target_age + 1):
    col_grid, col_action = st.columns([0.95, 0.05])
    
    with col_grid:
        weeks_html = f'<div class="week-container"><div class="age-label">Thn {year:02d}</div>'
        for week in range(52):
            current_week_idx = (year * 52) + week
            
            w_start_grid = birth_date + timedelta(weeks=current_week_idx)
            w_end_grid = w_start_grid + timedelta(days=6)
            date_str = f"{w_start_grid.strftime('%d %b %Y')} - {w_end_grid.strftime('%d %b %Y')}"
            
            weekly_note_grid = st.session_state.weekly_notes.get(current_week_idx, "")
            
            tooltip_text = f"Tahun {year}, Minggu {week + 1}&#10;📅 {date_str}"
            if weekly_note_grid:
                tooltip_text += f"&#10;📝 {weekly_note_grid}"

            style = ""
            if current_week_idx < weeks_lived:
                status_class = "lived"
            elif current_week_idx == weeks_lived:
                status_class = "current"
                style = f"background: linear-gradient(to right, #1f77b4 {percent_current_week}%, #ffffff {percent_current_week}%); border-color: #1f77b4;"
                tooltip_text = f"⏳ MINGGU INI ({percent_current_week:.0f}% Berlalu)&#10;" + tooltip_text
            else:
                status_class = "future"
                
            if weekly_note_grid:
                style += " border-color: #ff9800; border-width: 2px;"

            weeks_html += f'<div class="week-box {status_class}" style="{style}" title="{tooltip_text}"></div>'
            
        weeks_html += '</div>'
        st.markdown(weeks_html, unsafe_allow_html=True)
    
    with col_action:
        current_note = st.session_state.life_notes[year]
        hover_info = current_note if current_note.strip() != "" else "Belum ada catatan."
        
        with st.popover("📝", help=hover_info):
            st.session_state.life_notes[year] = st.text_area(
                f"Catatan Umur {year}:", 
                value=st.session_state.life_notes[year],
                key=f"input_{year}",
                height=100
            )
