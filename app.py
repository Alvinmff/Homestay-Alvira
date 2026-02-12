import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import matplotlib.pyplot as plt

st.set_page_config(page_title="Homestay Pro System", layout="wide")
st.title("🏠 Homestay Management System Pro")

# ============================
# DATABASE
# ============================
conn = sqlite3.connect("homestay.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT,
    hp TEXT,
    kamar TEXT,
    checkin DATE,
    checkout DATE,
    harga INTEGER,
    total INTEGER,
    status TEXT
)
""")
conn.commit()

# ============================
# FUNCTIONS
# ============================
def get_status(checkin, checkout):
    today = date.today()
    if today < checkin:
        return "Booked"
    elif checkin <= today <= checkout:
        return "Check-in"
    else:
        return "Selesai"

def is_double_booking(kamar, checkin, checkout):
    query = """
    SELECT * FROM bookings
    WHERE kamar = ?
    AND (
        (checkin <= ? AND checkout >= ?)
        OR
        (checkin <= ? AND checkout >= ?)
        OR
        (? <= checkin AND ? >= checkout)
    )
    """
    result = cursor.execute(query, (
        kamar,
        checkin, checkin,
        checkout, checkout,
        checkin, checkout
    )).fetchall()
    return len(result) > 0

def insert_booking(nama, hp, kamar, checkin, checkout, harga, total, status):
    cursor.execute("""
    INSERT INTO bookings (nama, hp, kamar, checkin, checkout, harga, total, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nama, hp, kamar, checkin, checkout, harga, total, status))
    conn.commit()

def load_data():
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    return df

# ============================
# SIDEBAR - INPUT
# ============================
st.sidebar.header("➕ Tambah Booking")

nama = st.sidebar.text_input("Nama Tamu")
hp = st.sidebar.text_input("No HP")
kamar = st.sidebar.selectbox("Kamar", ["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"])
checkin = st.sidebar.date_input("Check-in")
checkout = st.sidebar.date_input("Check-out")
harga = st.sidebar.number_input("Harga per Malam", min_value=0)

if st.sidebar.button("Simpan Booking"):
    if checkout > checkin:

        if is_double_booking(kamar, checkin, checkout):
            st.sidebar.error("❌ Kamar sudah dibooking di tanggal tersebut!")
        else:
            malam = (checkout - checkin).days
            total = malam * harga
            status = get_status(checkin, checkout)

            insert_booking(nama, hp, kamar, checkin, checkout, harga, total, status)
            st.sidebar.success("Booking berhasil!")
            st.rerun()
    else:
        st.sidebar.error("Tanggal tidak valid.")

# ============================
# LOAD DATA
# ============================
df = load_data()

if not df.empty:

    # Update status otomatis setiap reload
    for index, row in df.iterrows():
        new_status = get_status(
            datetime.strptime(row["checkin"], "%Y-%m-%d").date(),
            datetime.strptime(row["checkout"], "%Y-%m-%d").date()
        )
        cursor.execute("UPDATE bookings SET status=? WHERE id=?",
                       (new_status, row["id"]))
    conn.commit()

    df = load_data()

    # ============================
    # DATA TABLE
    # ============================
    st.subheader("📋 Data Booking")
    st.dataframe(df, use_container_width=True)

    # ============================
    # DASHBOARD
    # ============================
    st.subheader("📊 Ringkasan")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Booking", len(df))
    col2.metric("Total Pendapatan", f"Rp {df['total'].sum():,.0f}")
    col3.metric("Sedang Check-in",
                len(df[df["status"] == "Check-in"]))

    # ============================
    # GRAFIK OKUPANSI
    # ============================
    st.subheader("📈 Grafik Pendapatan per Kamar")
    chart_data = df.groupby("kamar")["total"].sum()

    fig, ax = plt.subplots()
    chart_data.plot(kind="bar", ax=ax)
    ax.set_ylabel("Total Pendapatan")
    st.pyplot(fig)

    # ============================
    # KALENDER OKUPANSI SEDERHANA
    # ============================
    st.subheader("📅 Kalender Okupansi Hari Ini")

    today = date.today()
    occupied = df[
        (df["checkin"] <= str(today)) &
        (df["checkout"] >= str(today))
    ]

    if not occupied.empty:
        st.success("Kamar Terisi Hari Ini:")
        st.write(occupied[["kamar", "nama", "status"]])
    else:
        st.info("Semua kamar kosong hari ini ✅")

else:
    st.info("Belum ada data booking.")
