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

def update_booking(id, nama, hp, kamar, checkin, checkout, harga, total, status):
    cursor.execute("""
    UPDATE bookings
    SET nama=?, hp=?, kamar=?, checkin=?, checkout=?, harga=?, total=?, status=?
    WHERE id=?
    """, (nama, hp, kamar, checkin, checkout, harga, total, status, id))
    conn.commit()

def delete_booking(id):
    cursor.execute("DELETE FROM bookings WHERE id=?", (id,))
    conn.commit()

def is_double_booking_edit(kamar, checkin, checkout, booking_id):
    query = """
    SELECT * FROM bookings
    WHERE kamar = ?
    AND id != ?
    AND (
        (checkin <= ? AND checkout >= ?)
        OR
        (checkin <= ? AND checkout >= ?)
        OR
        (? <= checkin AND ? >= checkout)
    )
    """
    result = cursor.execute(query, (
        kamar, booking_id,
        checkin, checkin,
        checkout, checkout,
        checkin, checkout
    )).fetchall()
    return len(result) > 0

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

    for index, row in df.iterrows():
        with st.expander(f"{row['nama']} - {row['kamar']} (ID {row['id']})"):
    
            col1, col2 = st.columns(2)
    
            with col1:
                new_nama = st.text_input("Nama", row["nama"], key=f"nama{row['id']}")
                new_hp = st.text_input("HP", row["hp"], key=f"hp{row['id']}")
                new_kamar = st.selectbox(
                    "Kamar",
                    ["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"],
                    index=["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"].index(row["kamar"]),
                    key=f"kamar{row['id']}"
                )
    
            with col2:
                new_checkin = st.date_input(
                    "Check-in",
                    datetime.strptime(row["checkin"], "%Y-%m-%d").date(),
                    key=f"ci{row['id']}"
                )
                new_checkout = st.date_input(
                    "Check-out",
                    datetime.strptime(row["checkout"], "%Y-%m-%d").date(),
                    key=f"co{row['id']}"
                )
                new_harga = st.number_input(
                    "Harga per Malam",
                    value=row["harga"],
                    key=f"harga{row['id']}"
                )
    
            malam = (new_checkout - new_checkin).days
            new_total = malam * new_harga if malam > 0 else 0
            new_status = get_status(new_checkin, new_checkout)
    
            st.write(f"💰 Total Baru: Rp {new_total:,.0f}")
            st.write(f"📌 Status: {new_status}")
    
            col_update, col_delete = st.columns(2)
    
            if col_update.button("💾 Update", key=f"update{row['id']}"):
                if new_checkout > new_checkin:
    
                    if is_double_booking_edit(new_kamar, new_checkin, new_checkout, row["id"]):
                        st.error("❌ Jadwal bentrok dengan booking lain!")
                    else:
                        update_booking(
                            row["id"], new_nama, new_hp, new_kamar,
                            new_checkin, new_checkout,
                            new_harga, new_total, new_status
                        )
                        st.success("Booking berhasil diupdate!")
                        st.rerun()
                else:
                    st.error("Tanggal tidak valid.")
    
            if col_delete.button("🗑️ Hapus", key=f"delete{row['id']}"):
                delete_booking(row["id"])
                st.warning("Booking berhasil dihapus!")
                st.rerun()

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
