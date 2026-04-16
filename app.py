import streamlit as st
from datetime import date

# Konfigurasi halaman
st.set_page_config(page_title="My Life in Weeks", layout="wide")

# Judul berdasarkan dokumen [cite: 19]
st.title("📅 MY LIFE IN WEEKS")
st.write("Berdasarkan artikel Tim Urban di WaitButWhy: 'Your Life in Weeks' ")

# Sidebar untuk input
with st.sidebar:
    st.header("Konfigurasi")
    birth_date = st.date_input("Masukkan Tanggal Lahir Anda:", value=date(1995, 1, 1))
    target_age = st.number_input("Target Umur (Tahun):", min_value=1, max_value=100, value=90)

# Perhitungan logika
today = date.today()
delta = today - birth_date
weeks_lived = delta.days // 7
total_weeks = target_age * 52

# Informasi ringkasan
st.subheader(f"Anda telah hidup selama {weeks_lived:,} minggu.")
st.write(f"Sisa minggu hingga usia {target_age} tahun: {max(0, total_weeks - weeks_lived):,} minggu.")

# CSS untuk membuat grid kalender
st.markdown("""
<style>
    .life-grid {
        display: grid;
        grid-template-columns: repeat(52, 1fr);
        gap: 2px;
        margin-top: 20px;
    }
    .week-box {
        width: 12px;
        height: 12px;
        border: 1px solid #d1d1d1;
        border-radius: 2px;
    }
    .lived {
        background-color: #1f77b4; /* Warna biru untuk minggu yang sudah dilalui */
        border-color: #1f77b4;
    }
    .remaining {
        background-color: #ffffff; /* Putih untuk masa depan */
    }
    .year-label {
        font-size: 10px;
        color: #888;
        text-align: right;
        padding-right: 5px;
        grid-column: span 1;
    }
</style>
""", unsafe_allow_html=True)

# Render Grid
html_grid = '<div class="life-grid">'

for year in range(target_age):
    for week in range(52):
        current_week_index = (year * 52) + week
        if current_week_index < weeks_lived:
            # Minggu yang sudah berlalu
            html_grid += '<div class="week-box lived"></div>'
        else:
            # Minggu yang akan datang
            html_grid += '<div class="week-box remaining"></div>'

html_grid += '</div>'

st.markdown(html_grid, unsafe_allow_html=True)

# Catatan kaki sesuai dokumen
st.divider()
st.info("**NOTES:** Setiap kotak kecil mewakili satu minggu dalam hidup Anda hingga usia 90 tahun[cite: 23, 24].")
