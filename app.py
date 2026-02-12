from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes

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
    checkin TEXT,
    checkout TEXT,
    harga INTEGER,
    total INTEGER,
    dp INTEGER DEFAULT 0,
    sisa INTEGER DEFAULT 0,
    status TEXT
)
""")
conn.commit()

# Tambah kolom jika belum ada (untuk database lama)
try:
    cursor.execute("ALTER TABLE bookings ADD COLUMN dp INTEGER DEFAULT 0")
    conn.commit()
except:
    pass

try:
    cursor.execute("ALTER TABLE bookings ADD COLUMN sisa INTEGER DEFAULT 0")
    conn.commit()
except:
    pass


# ============================
# FUNCTIONS
# ============================
def get_status(checkin, checkout, sisa):
    today = date.today()
    if sisa <= 0:
        return "Lunas"
    elif today < checkin:
        return "Booked"
    elif checkin <= today <= checkout:
        return "Check-in"
    else:
        return "Selesai"

def is_double_booking(kamar, checkin, checkout, booking_id=None):
    query = """
    SELECT * FROM bookings
    WHERE kamar = ?
    AND (? IS NULL OR id != ?)
    AND (
        (date(checkin) <= date(?) AND date(checkout) >= date(?))
        OR
        (date(checkin) <= date(?) AND date(checkout) >= date(?))
        OR
        (date(?) <= date(checkin) AND date(?) >= date(checkout))
    )
    """
    result = cursor.execute(query, (
        kamar,
        booking_id, booking_id,
        checkin, checkin,
        checkout, checkout,
        checkin, checkout
    )).fetchall()
    return len(result) > 0

def load_data():
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    return df

# ============================
# EXPORT FUNCTIONS
# ============================

def generate_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Laporan Booking')
    return output.getvalue()


def generate_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("Laporan Booking Homestay", styles["Title"]))
    elements.append(Spacer(1, 12))

    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data)

    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ])

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ============================
# TAMBAH BOOKING
# ============================
st.sidebar.header("➕ Tambah Booking")

nama = st.sidebar.text_input("Nama Tamu")
hp = st.sidebar.text_input("No HP")
kamar_list = ["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"]
kamar = st.sidebar.selectbox("Kamar", kamar_list)
checkin = st.sidebar.date_input("Check-in")
checkout = st.sidebar.date_input("Check-out")
harga = st.sidebar.number_input("Harga per Malam", min_value=0)
dp = st.sidebar.number_input("DP (Uang Muka)", min_value=0)

if st.sidebar.button("Simpan Booking"):
    if checkout > checkin:

        if is_double_booking(kamar, checkin, checkout):
            st.sidebar.error("❌ Kamar sudah dibooking di tanggal tersebut!")
        else:
            malam = (checkout - checkin).days
            total = malam * harga
            sisa = total - dp
            status = get_status(checkin, checkout, sisa)

            cursor.execute("""
            INSERT INTO bookings 
            (nama, hp, kamar, checkin, checkout, harga, total, dp, sisa, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nama, hp, kamar,
                  str(checkin), str(checkout),
                  harga, total, dp, sisa, status))
            conn.commit()
            st.sidebar.success("Booking berhasil!")
            st.rerun()
    else:
        st.sidebar.error("Tanggal tidak valid")

# ============================
# LOAD DATA
# ============================
df = load_data()

if not df.empty:

    # ============================
    # UPDATE STATUS OTOMATIS
    # ============================
    for index, row in df.iterrows():
        checkin_date = datetime.strptime(row["checkin"], "%Y-%m-%d").date()
        checkout_date = datetime.strptime(row["checkout"], "%Y-%m-%d").date()
        sisa_value = row["sisa"] if row["sisa"] is not None else 0

        new_status = get_status(checkin_date, checkout_date, sisa_value)

        cursor.execute(
            "UPDATE bookings SET status=? WHERE id=?",
            (new_status, row["id"])
        )
    conn.commit()

    df = load_data()

    # ============================
    # DATA TABLE
    # ============================
    st.subheader("📋 Data Booking (Tabel Utama)")
    st.dataframe(df, use_container_width=True)

    # ============================
    # DOWNLOAD LAPORAN
    # ============================
    st.subheader("📥 Download Laporan")

    col_dl1, col_dl2 = st.columns(2)

    excel_file = generate_excel(df)
    pdf_file = generate_pdf(df)

    with col_dl1:
        st.download_button(
            label="⬇️ Download Excel",
            data=excel_file,
            file_name="laporan_booking.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col_dl2:
        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_file,
            file_name="laporan_booking.pdf",
            mime="application/pdf"
        )

    # ============================
    # EDIT / DELETE
    # ============================
    st.subheader("✏️ Edit / Hapus Booking")

    selected_id = st.selectbox("Pilih ID Booking", df["id"])
    selected_data = df[df["id"] == selected_id].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        edit_nama = st.text_input("Nama", selected_data["nama"])
        edit_hp = st.text_input("HP", selected_data["hp"])
        edit_kamar = st.selectbox(
            "Kamar",
            kamar_list,
            index=kamar_list.index(selected_data["kamar"])
        )

    with col2:
        edit_checkin = st.date_input(
            "Check-in",
            datetime.strptime(selected_data["checkin"], "%Y-%m-%d").date()
        )
        edit_checkout = st.date_input(
            "Check-out",
            datetime.strptime(selected_data["checkout"], "%Y-%m-%d").date()
        )
        edit_harga = st.number_input(
            "Harga per Malam",
            value=int(selected_data["harga"])
        )
        edit_dp = st.number_input(
            "DP",
            value=int(selected_data["dp"])
        )

    malam = (edit_checkout - edit_checkin).days
    edit_total = malam * edit_harga if malam > 0 else 0
    edit_sisa = edit_total - edit_dp
    edit_status = get_status(edit_checkin, edit_checkout, edit_sisa)

    st.write(f"💰 Total: Rp {edit_total:,.0f}")
    st.write(f"💳 Sisa: Rp {edit_sisa:,.0f}")
    st.write(f"📌 Status: {edit_status}")

    col_update, col_delete = st.columns(2)

    if col_update.button("💾 Update Booking"):
        if edit_checkout > edit_checkin:

            if is_double_booking(edit_kamar, edit_checkin,
                                 edit_checkout, selected_id):
                st.error("❌ Jadwal bentrok dengan booking lain!")
            else:
                cursor.execute("""
                UPDATE bookings
                SET nama=?, hp=?, kamar=?, checkin=?, checkout=?,
                    harga=?, total=?, dp=?, sisa=?, status=?
                WHERE id=?
                """, (
                    edit_nama, edit_hp, edit_kamar,
                    str(edit_checkin), str(edit_checkout),
                    edit_harga, edit_total,
                    edit_dp, edit_sisa,
                    edit_status,
                    selected_id
                ))
                conn.commit()
                st.success("Booking berhasil diupdate!")
                st.rerun()

    if col_delete.button("🗑️ Hapus Booking"):
        cursor.execute("DELETE FROM bookings WHERE id=?",
                       (selected_id,))
        conn.commit()
        st.warning("Booking dihapus!")
        st.rerun()

    # ============================
    # DASHBOARD
    # ============================
    st.subheader("📊 Ringkasan")

    colA, colB, colC = st.columns(3)
    colA.metric("Total Booking", len(df))
    colB.metric("Total Pendapatan", f"Rp {df['total'].sum():,.0f}")
    colC.metric("Total DP Masuk", f"Rp {df['dp'].sum():,.0f}")

    # ============================
    # GRAFIK
    # ============================
    st.subheader("📈 Grafik Pendapatan per Kamar")
    chart_data = df.groupby("kamar")["total"].sum()

    fig, ax = plt.subplots()
    chart_data.plot(kind="bar", ax=ax)
    ax.set_ylabel("Total Pendapatan")
    st.pyplot(fig)

else:
    st.info("Belum ada data booking.")
