import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Homestay Management", layout="wide")

st.title("🏠 Homestay Management System")

# ==============================
# DATABASE CONNECTION
# ==============================
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

# ==============================
# FUNCTIONS
# ==============================
def insert_booking(nama, hp, kamar, checkin, checkout, harga, total):
    cursor.execute("""
    INSERT INTO bookings (nama, hp, kamar, checkin, checkout, harga, total, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (nama, hp, kamar, checkin, checkout, harga, total, "Booked"))
    conn.commit()

def load_data():
    return pd.read_sql_query("SELECT * FROM bookings", conn)

def delete_booking(id):
    cursor.execute("DELETE FROM bookings WHERE id = ?", (id,))
    conn.commit()

def update_booking(id, nama, hp, kamar, checkin, checkout, harga, total):
    cursor.execute("""
    UPDATE bookings
    SET nama=?, hp=?, kamar=?, checkin=?, checkout=?, harga=?, total=?
    WHERE id=?
    """, (nama, hp, kamar, checkin, checkout, harga, total, id))
    conn.commit()

# ==============================
# SIDEBAR - ADD BOOKING
# ==============================
st.sidebar.header("➕ Tambah Booking")

nama = st.sidebar.text_input("Nama Tamu")
hp = st.sidebar.text_input("No HP")
kamar = st.sidebar.selectbox("Kamar", ["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"])
checkin = st.sidebar.date_input("Check-in")
checkout = st.sidebar.date_input("Check-out")
harga = st.sidebar.number_input("Harga per Malam", min_value=0)

if st.sidebar.button("Simpan Booking"):
    if checkout > checkin:
        malam = (checkout - checkin).days
        total = malam * harga
        insert_booking(nama, hp, kamar, checkin, checkout, harga, total)
        st.success("Booking berhasil ditambahkan!")
    else:
        st.error("Tanggal tidak valid.")

# ==============================
# DISPLAY DATA
# ==============================
st.subheader("📋 Data Booking")

df = load_data()

if not df.empty:
    for index, row in df.iterrows():
        with st.expander(f"{row['nama']} - {row['kamar']} (ID: {row['id']})"):

            col1, col2 = st.columns(2)

            with col1:
                new_nama = st.text_input("Nama", row["nama"], key=f"nama{row['id']}")
                new_hp = st.text_input("No HP", row["hp"], key=f"hp{row['id']}")
                new_kamar = st.selectbox(
                    "Kamar",
                    ["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"],
                    index=["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"].index(row["kamar"]),
                    key=f"kamar{row['id']}"
                )

            with col2:
                new_checkin = st.date_input("Check-in", pd.to_datetime(row["checkin"]), key=f"checkin{row['id']}")
                new_checkout = st.date_input("Check-out", pd.to_datetime(row["checkout"]), key=f"checkout{row['id']}")
                new_harga = st.number_input("Harga per Malam", value=row["harga"], key=f"harga{row['id']}")

            malam = (new_checkout - new_checkin).days
            new_total = malam * new_harga if malam > 0 else 0

            st.write(f"💰 Total Baru: Rp {new_total:,.0f}")

            col_update, col_delete = st.columns(2)

            if col_update.button("💾 Update", key=f"update{row['id']}"):
                if new_checkout > new_checkin:
                    update_booking(row["id"], new_nama, new_hp, new_kamar, new_checkin, new_checkout, new_harga, new_total)
                    st.success("Booking berhasil diupdate!")
                    st.rerun()
                else:
                    st.error("Tanggal tidak valid.")

            if col_delete.button("🗑 Hapus", key=f"delete{row['id']}"):
                delete_booking(row["id"])
                st.warning("Booking dihapus!")
                st.rerun()

else:
    st.info("Belum ada data booking.")
