import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO

# Untuk Export Excel
from openpyxl import Workbook

# Untuk Export PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes

st.set_page_config(page_title="Homestay Management Pro", layout="wide")
st.title("🏠 Homestay Management System")

# =============================
# DATABASE
# =============================
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
    total INTEGER
)
""")
conn.commit()

# =============================
# FUNCTIONS
# =============================
def insert_booking(nama, hp, kamar, checkin, checkout, harga, total):
    cursor.execute("""
    INSERT INTO bookings (nama, hp, kamar, checkin, checkout, harga, total)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nama, hp, kamar, checkin, checkout, harga, total))
    conn.commit()

def load_data():
    return pd.read_sql_query("SELECT * FROM bookings", conn)

def delete_booking(id):
    cursor.execute("DELETE FROM bookings WHERE id=?", (id,))
    conn.commit()

def update_booking(id, nama, hp, kamar, checkin, checkout, harga, total):
    cursor.execute("""
    UPDATE bookings
    SET nama=?, hp=?, kamar=?, checkin=?, checkout=?, harga=?, total=?
    WHERE id=?
    """, (nama, hp, kamar, checkin, checkout, harga, total, id))
    conn.commit()

# =============================
# SIDEBAR INPUT
# =============================
st.sidebar.header("➕ Tambah Booking")

nama = st.sidebar.text_input("Nama Tamu")
hp = st.sidebar.text_input("No HP")
kamar = st.sidebar.selectbox("Kamar", ["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"])
checkin = st.sidebar.date_input("Check-in")
checkout = st.sidebar.date_input("Check-out")
harga = st.sidebar.number_input("Harga per Malam", min_value=0)

if st.sidebar.button("Simpan"):
    if checkout > checkin:
        malam = (checkout - checkin).days
        total = malam * harga
        insert_booking(nama, hp, kamar, checkin, checkout, harga, total)
        st.success("Booking berhasil ditambahkan!")
        st.rerun()
    else:
        st.error("Tanggal tidak valid.")

# =============================
# DASHBOARD
# =============================
df = load_data()

st.subheader("📊 Ringkasan Bisnis")

if not df.empty:
    total_pendapatan = df["total"].sum()
    total_booking = len(df)

    col1, col2 = st.columns(2)
    col1.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
    col2.metric("Total Booking", total_booking)

    # =============================
    # GRAFIK PENDAPATAN PER KAMAR
    # =============================
    st.subheader("📈 Grafik Pendapatan per Kamar")

    chart_data = df.groupby("kamar")["total"].sum()

    fig, ax = plt.subplots()
    chart_data.plot(kind="bar", ax=ax)
    ax.set_ylabel("Total Pendapatan")
    st.pyplot(fig)

    # =============================
    # DATA TABLE + CRUD
    # =============================
    st.subheader("📋 Data Booking")

    for index, row in df.iterrows():
        with st.expander(f"{row['nama']} - {row['kamar']} (ID {row['id']})"):

            new_nama = st.text_input("Nama", row["nama"], key=f"nama{row['id']}")
            new_hp = st.text_input("HP", row["hp"], key=f"hp{row['id']}")
            new_kamar = st.selectbox(
                "Kamar",
                ["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"],
                index=["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"].index(row["kamar"]),
                key=f"kamar{row['id']}"
            )
            new_checkin = st.date_input("Check-in", pd.to_datetime(row["checkin"]), key=f"ci{row['id']}")
            new_checkout = st.date_input("Check-out", pd.to_datetime(row["checkout"]), key=f"co{row['id']}")
            new_harga = st.number_input("Harga", value=row["harga"], key=f"h{row['id']}")

            malam = (new_checkout - new_checkin).days
            new_total = malam * new_harga if malam > 0 else 0

            col_upd, col_del = st.columns(2)

            if col_upd.button("Update", key=f"upd{row['id']}"):
                update_booking(row["id"], new_nama, new_hp, new_kamar,
                               new_checkin, new_checkout, new_harga, new_total)
                st.success("Updated!")
                st.rerun()

            if col_del.button("Hapus", key=f"del{row['id']}"):
                delete_booking(row["id"])
                st.warning("Dihapus!")
                st.rerun()

    # =============================
    # DOWNLOAD EXCEL
    # =============================
    st.subheader("📥 Download Laporan")

    def convert_to_excel(data):
        output = BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.append(list(data.columns))
        for row in data.itertuples(index=False):
            ws.append(row)
        wb.save(output)
        return output.getvalue()

    excel_data = convert_to_excel(df)

    st.download_button(
        label="Download Excel",
        data=excel_data,
        file_name="laporan_homestay.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # =============================
    # DOWNLOAD PDF
    # =============================
    def generate_pdf(data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("Laporan Booking Homestay", styles["Title"]))
        elements.append(Spacer(1, 12))

        table_data = [list(data.columns)] + data.values.tolist()
        table = Table(table_data)
        table.setStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ])

        elements.append(table)
        doc.build(elements)
        return buffer.getvalue()

    pdf_data = generate_pdf(df)

    st.download_button(
        label="Download PDF",
        data=pdf_data,
        file_name="laporan_homestay.pdf",
        mime="application/pdf"
    )

else:
    st.info("Belum ada data booking.")
