from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import io
from datetime import datetime

from io import BytesIO
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

    if today < checkin:
        return "Booked"

    if checkin <= today < checkout:
        return "Check-in"

    if today == checkout:
        return "Check-out"

    if today > checkout:
        return "Selesai"

    return "Booked"

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

        workbook = writer.book
        worksheet = writer.sheets['Laporan Booking']

        rupiah_format = workbook.add_format({'num_format': '"Rp" #,##0'})

        for col_num, column in enumerate(df.columns):
            if column in ["harga", "total", "dp", "sisa"]:
                worksheet.set_column(col_num, col_num, 18, rupiah_format)

    return output.getvalue()

def generate_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("Laporan Booking Homestay", styles["Title"]))
    elements.append(Spacer(1, 12))

    # ============================
    # FORMAT RUPIAH DI PDF
    # ============================

    def rupiah(x):
        try:
            return f"Rp {int(x):,}".replace(",", ".")
        except:
            return x

    df_pdf = df.copy()

    for col in ["harga", "total", "dp", "sisa"]:
        if col in df_pdf.columns:
            df_pdf[col] = df_pdf[col].apply(rupiah)

    data = [df_pdf.columns.tolist()] + df_pdf.values.tolist()

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

def generate_invoice(selected_data):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)
    elements = []

    styles = getSampleStyleSheet()

    # ============================
    # NOMOR INVOICE OTOMATIS
    # ============================
    tahun = datetime.now().year
    invoice_number = f"INV-{tahun}-{int(selected_data['id']):04d}"

    # ============================
    # HEADER
    # ============================
    title_style = styles["Heading1"]
    elements.append(Paragraph("Homestay Alvira", title_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>Invoice:</b> {invoice_number}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Tanggal Cetak:</b> {datetime.now().strftime('%d-%m-%Y')}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # ============================
    # FORMAT RUPIAH
    # ============================
    def rupiah(x):
        try:
            return f"Rp {int(x):,}".replace(",", ".")
        except:
            return x

    # ============================
    # DATA TABEL
    # ============================
    data = [
        ["Nama Tamu", selected_data["nama"]],
        ["No HP", selected_data["hp"]],
        ["Kamar", selected_data["kamar"]],
        ["Check-in", selected_data["checkin"]],
        ["Check-out", selected_data["checkout"]],
        ["Total", rupiah(selected_data["total"])],
        ["DP", rupiah(selected_data["dp"])],
        ["Sisa", rupiah(selected_data["sisa"])],
        ["Status", selected_data["status"]],
    ]

    table = Table(data, colWidths=[2.5*inch, 3.5*inch])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 30))

    # ============================
    # WATERMARK LUNAS
    # ============================
    if selected_data["sisa"] <= 0:
        lunas_style = ParagraphStyle(
            'LunasStyle',
            parent=styles['Heading1'],
            textColor=colors.green
        )
        elements.append(Paragraph("✔ LUNAS", lunas_style))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def generate_pdf_public(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("Jadwal Booking Homestay", styles["Title"]))
    elements.append(Spacer(1, 12))

    # 🔒 HANYA KOLOM PUBLIK (TANPA HARGA)
    df_public = df[[
        "nama",
        "kamar",
        "checkin",
        "checkout",
        "status"
    ]].copy()

    # Tambah nomor urut
    df_public = df_public.reset_index(drop=True)
    df_public.index += 1
    df_public.index.name = "No"
    df_public = df_public.reset_index()

    data = [df_public.columns.tolist()] + df_public.values.tolist()

    table = Table(data, repeatRows=1)
    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
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
kamar_list = ["Alvira 1", "Alvira 2", "Alvira 3", "Alvira 4", "Alvira 5"]
kamar = st.sidebar.selectbox("Kamar", kamar_list)
checkin = st.sidebar.date_input("Check-in")
checkout = st.sidebar.date_input("Check-out")
harga = st.sidebar.number_input(
    "Harga per Malam",
    min_value=0,
    step=50000,
    format="%d"
)

dp = st.sidebar.number_input(
    "DP (Uang Muka)",
    min_value=0,
    step=50000,
    format="%d"
)

st.sidebar.markdown(f"💰 Harga: **Rp {harga:,.0f}**".replace(",", "."))
st.sidebar.markdown(f"💳 DP: **Rp {dp:,.0f}**".replace(",", "."))

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

    def format_rupiah(x):
        try:
            return f"Rp {int(x):,}".replace(",", ".")
        except:
            return x

    # ============================
    # DATA TABLE
    # ============================
    st.subheader("📋 Data Booking (Tabel Utama)")
    
    # Copy dataframe supaya tidak mengubah data asli
    df_display = df.copy()

    # Reset index supaya mulai dari 0 lalu tambah 1
    df_display = df_display.reset_index(drop=True)
    df_display.index = df_display.index + 1
    
    # Tambahkan nama kolom index
    df_display.index.name = "No"
        
    # Format kolom uang
    for col in ["harga", "total", "dp", "sisa"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(format_rupiah)
    
    # Styling status
    def highlight_status(val):
        if val == "Check-in":
            return "background-color: #b6f2b6; color: #0f5132; font-weight: bold;"
        elif val == "Booked":
            return "background-color: #fff3b0; color: #664d03; font-weight: bold;"
        elif val == "Check-out":
            return "background-color: #a0e7ff; color: #055160; font-weight: bold;"
        elif val == "Selesai":
            return "background-color: #d3d3d3; color: #41464b; font-weight: bold;"
        elif val == "Lunas":
            return "background-color: #c8f7c5; color: #0a3622; font-weight: bold;"
        return ""
    
    styled_df = df_display.style.applymap(highlight_status, subset=["status"])
    
    st.dataframe(styled_df, use_container_width=True)
    
    # ============================
    # DOWNLOAD LAPORAN
    # ============================
    st.subheader("📥 Download Laporan")
    
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    
    # ============================
    # SIAPKAN DATA EXPORT
    # ============================
    
    df_export = df.copy()
    
    # Hide kolom id
    if "id" in df_export.columns:
        df_export = df_export.drop(columns=["id"])
    
    # Tambah nomor urut
    df_export = df_export.reset_index(drop=True)
    df_export.index += 1
    df_export.index.name = "No"
    df_export = df_export.reset_index()
    
    # Generate file
    excel_file = generate_excel(df_export)
    pdf_file = generate_pdf(df_export)
    public_pdf = generate_pdf_public(df_export)
    
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
    
    with col_dl3:
        st.download_button(
            label="📅 Download Jadwal (Tanpa Harga)",
            data=public_pdf,
            file_name="jadwal_booking_public.pdf",
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
        
    if st.button("🧾 Generate Invoice"):
        pdf_file = generate_invoice(selected_data)
    
        st.download_button(
            label="📥 Download Invoice PDF",
            data=pdf_file,
            file_name=f"invoice_{selected_data['nama']}.pdf",
            mime="application/pdf"
        )
    
    # ============================
    # RESET DATABASE
    # ============================
    st.subheader("⚙️ Reset Database")
    
    confirm = st.checkbox("Saya yakin ingin menghapus semua data")
    
    if confirm:
        if st.button("🔄 Reset Semua Data & ID"):
            cursor.execute("DELETE FROM bookings")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='bookings'")
            conn.commit()
            st.success("Database berhasil direset. ID kembali ke 1.")
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
