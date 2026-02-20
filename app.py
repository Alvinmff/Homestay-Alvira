from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import cm
import io

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes

from reportlab.pdfbase.pdfmetrics import stringWidth
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import streamlit as st
import uuid

from PIL import Image
from reportlab.platypus import Image as RLImage
from reportlab.pdfgen import canvas

bulan_indonesia = {
    1: "JANUARI",
    2: "FEBRUARI",
    3: "MARET",
    4: "APRIL",
    5: "MEI",
    6: "JUNI",
    7: "JULI",
    8: "AGUSTUS",
    9: "SEPTEMBER",
    10: "OKTOBER",
    11: "NOVEMBER",
    12: "DESEMBER"
}

pdfmetrics.registerFont(
    TTFont('Playfair-Bold', 'assets/pairflay/PlayfairDisplay-Bold.ttf')
)

pdfmetrics.registerFont(
    TTFont('Poppins-Regular', 'assets/poppins/Poppins-Regular.ttf')
)

pdfmetrics.registerFont(
    TTFont('Poppins-Light', 'assets/poppins/Poppins-Light.ttf')
)

def add_lunas_watermark(canvas, doc):
    canvas.saveState()
    
    canvas.setFont("Helvetica-Bold", 80)
    
    # warna hijau transparan
    canvas.setFillColor(Color(0, 0.5, 0, alpha=0.15))
    
    canvas.translate(300, 400)
    canvas.rotate(45)
    
    canvas.drawCentredString(0, 0, "LUNAS")
    
    canvas.restoreState()

def add_watermark(canvas, doc):
    canvas.saveState()

    # Transparansi sangat tipis
    canvas.setFillAlpha(0.015)

    # Abu-abu sangat soft
    canvas.setFillColor(colors.HexColor("#BDBDBD"))

    # Font lebih ringan & sedikit lebih kecil
    canvas.setFont("Helvetica-Bold", 55)

    width, height = doc.pagesize
    canvas.translate(width / 2, height / 2)
    canvas.rotate(45)

    canvas.drawCentredString(0, 0, "HOMESTAY ALVIRA")

    canvas.restoreState()

logo = Image.open("assets/logo.png")

col1, col2 = st.columns([0.8, 6], gap="small")

with col1:
    st.image(logo, width=100)

with col2:
    st.markdown(
        """
        <div style="display:flex; flex-direction:column; justify-content:center; height:100px;">
            <h1 style='margin:0; padding:0;'>HOMESTAY ALVIRA</h1>
            <p style='margin:0; padding:0; color:gray;'>
            Sistem Manajemen Booking Profesional
            </p>
        </div>
        <style>
        .block-container {
            padding-left: 4rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


if "keep_alive" not in st.session_state:
    st.session_state.keep_alive = True

st.set_page_config(page_title="Homestay Pro System", layout="wide")
st.title("")

# ============================
# DATABASE
# ============================

import psycopg2
import streamlit as st

conn = psycopg2.connect(
    st.secrets["DATABASE_URL"],
    sslmode="require"
)
    
cursor = conn.cursor()
    
# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    nama TEXT,
    hp TEXT,
    kamar TEXT,
    checkin DATE,
    checkout DATE,
    harga INTEGER,
    total INTEGER,
    dp INTEGER DEFAULT 0,
    sisa INTEGER DEFAULT 0,
    status TEXT
);
""")
conn.commit()
st.success("Tabel 'bookings' berhasil dibuat atau sudah ada!")
        
        # Jika ada query lain di baris 214 atau sekitarnya, tambahkan di sini
        # Misalnya, jika ini INSERT atau SELECT, ganti dengan kode Anda
        # Contoh INSERT ke tabel bookings:
        # cursor.execute("""
        #     INSERT INTO bookings (nama, hp, kamar, checkin, checkout, harga, total, dp, sisa, status)
        #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        # """, ("Nama Contoh", "08123456789", "Room 1", "2023-01-01", "2023-01-02", 100000, 100000, 50000, 50000, "Confirmed"))
        # conn.commit()
        # st.write("Data berhasil dimasukkan!")
        
        # Contoh SELECT:
        # cursor.execute("SELECT * FROM rooms;")
        # results = cursor.fetchall()
        # st.write(results)

        
    # ============================
    # CREATE TABLE ROOMS
    # ============================
cursor.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id SERIAL PRIMARY KEY,
        nama_kamar TEXT UNIQUE,
        harga INTEGER,
        aktif INTEGER DEFAULT 1
    );
    """)

conn.commit()
st.success("Database ready ✅")

    # ============================
    # FUNCTIONS
    # ============================
        
    # Fungsi ini bisa dipanggil di luar blok database, tapi jika menggunakan cursor, pastikan di dalam try
    # (Untuk sekarang, functions didefinisikan di sini; panggil di tempat lain jika perlu)
        
    # Catatan: harga_kamar tidak didefinisikan di sini; pastikan didefinisikan di tempat lain atau tambahkan
    

# ============================
# FUNCTIONS
# ============================

from datetime import timedelta

def hitung_total_kamar(kamar, checkin, checkout):
    # Asumsikan harga_kamar didefinisikan di tempat lain, misalnya:
    # harga_kamar = {"Room1": {"weekday": 100000, "weekend": 150000}, ...}
    # Jika tidak, tambahkan atau pass
    total = 0
    current = checkin
    
    while current < checkout:
        weekday_number = current.weekday()  # 0=Senin, 6=Minggu
        
        if weekday_number <= 3:  # Senin-Kamis
            harga = harga_kamar[kamar]["weekday"]
        else:  # Jumat-Minggu
            harga = harga_kamar[kamar]["weekend"]
        
        total += harga
        current += timedelta(days=1)
    
    return total

def get_status(checkin, checkout, sisa):
    today = date.today()

    # 1️⃣ PRIORITAS UTAMA → Kalau sudah lewat tanggal
    if today > checkout:
        return "Selesai"

    # 2️⃣ Kalau hari ini checkout
    if today == checkout:
        return "Check-out"

    # 3️⃣ Kalau sedang menginap
    if checkin <= today < checkout:
        return "Check-in"

    # 4️⃣ Kalau belum masuk tanggal
    if today < checkin:
        if sisa <= 0:
            return "Lunas"
        return "Booked"

    return "Booked"

def is_double_booking(kamar, checkin, checkout, booking_id=None):

    query = """
        SELECT 1
        FROM bookings
        WHERE kamar = %s
        AND (%s IS NULL OR id != %s)
        AND (
            checkin::date < %s::date
            AND checkout::date > %s::date
        )
        LIMIT 1
    """

    cursor.execute(
        query,
        (
            kamar,
            booking_id, booking_id,
            checkout, checkin
        )
    )

    result = cursor.fetchone()

    return result is not None

# ============================
# LOAD DATA FUNCTION
# ============================

@st.cache_data(ttl=60)
def load_data():
    query = "SELECT * FROM bookings ORDER BY checkin ASC LIMIT 200"
    df = pd.read_sql_query(query, conn)
    return df

def load_data():
    try:
        query = """
        SELECT 
            id,
            nama,
            hp,
            kamar,
            checkin,
            checkout,
            harga,
            total,
            dp,
            sisa,
            status,
            group_id
        FROM bookings
        """
        df = pd.read_sql_query(query, conn)
        return df

    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# ============================
# EXPORT FUNCTIONS
# ============================

def generate_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_excel = df.copy()

        # Format rupiah
        def rupiah(x):
            try:
                return f"Rp {int(x):,}".replace(",", ".")
            except:
                return x

        for col in ["harga", "total", "dp", "sisa"]:
            if col in df_excel.columns:
                df_excel[col] = df_excel[col].apply(rupiah)

        df_excel.to_excel(writer, index=False, sheet_name='Laporan Booking')

        workbook = writer.book
        worksheet = writer.sheets['Laporan Booking']

        # Format warna status
        format_booked = workbook.add_format({'bg_color': '#FFF3B0'})
        format_checkin = workbook.add_format({'bg_color': '#B6F2B6'})
        format_checkout = workbook.add_format({'bg_color': '#A0E7FF'})
        format_selesai = workbook.add_format({'bg_color': '#D3D3D3'})
        format_lunas = workbook.add_format({'bg_color': '#C8F7C5'})

        status_col = df_excel.columns.get_loc("status")

        for row_num, value in enumerate(df_excel["status"], start=1):
            if value == "Booked":
                worksheet.write(row_num, status_col, value, format_booked)
            elif value == "Check-in":
                worksheet.write(row_num, status_col, value, format_checkin)
            elif value == "Check-out":
                worksheet.write(row_num, status_col, value, format_checkout)
            elif value == "Selesai":
                worksheet.write(row_num, status_col, value, format_selesai)
            elif value == "Lunas":
                worksheet.write(row_num, status_col, value, format_lunas)

    return output.getvalue()

def generate_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)
    elements = []

    styles = getSampleStyleSheet()

    # ======================
    # HEADER PREMIUM
    # ======================
    
    logo = RLImage("assets/logo.png", width=1.3*inch, height=1.3*inch)
    
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontName="Playfair-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1B5E20"),
        alignment=1,
        spaceAfter=5
    )
    
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        textColor=colors.black,
        alignment=1,
        spaceAfter=6
    )
    
    info_style = ParagraphStyle(
        "InfoStyle",
        parent=styles["Normal"],
        fontName="Poppins-Regular",
        fontSize=8,
        leading=10,
        textColor=colors.grey,
        alignment=1,
        spaceAfter=3
    )
     
    header_text = [
        Paragraph("<b>HOMESTAY ALVIRA SIDOARJO</b>", title_style),
        Spacer(1, 2),  # 🔥 tambahan jarak manual
        Paragraph("<b>LAPORAN BOOKING</b>", subtitle_style),
        Spacer(1, 4),  # 🔥 tambahan jarak manual
        Paragraph("Jl. Raya Lingkar Barat Gading Fajar 2 Blok C5 No 28 Kota Sidoarjo - Jawa Timur", info_style),
        Paragraph("Telp: 081231646523 (Bu Yanie) | Website: www.alvirahomestay.com", info_style),
    ]

    header_table = Table(
        [[logo, header_text]],
        colWidths=[3*cm, 12*cm]
    )
    
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    
        # Logo kolom 0
        ("LEFTPADDING", (0,0), (0,0), 0),
    
        # Text kolom 1 → geser ke kanan
        ("LEFTPADDING", (1,0), (1,0), 20),
    
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 6))
    
    gold_line = Table([[""]], colWidths=[17*cm])
    gold_line.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#C6A700"))
    ]))
    
    elements.append(gold_line)
    elements.append(Spacer(1, 15))

    def rupiah(x):
        try:
            return f"Rp {int(x):,}".replace(",", ".")
        except:
            return x

    df_pdf = df.copy()

    # 🔥 WAJIB: convert datetime dulu
    df_pdf["checkin"] = pd.to_datetime(df_pdf["checkin"], errors="coerce")
    df_pdf["checkout"] = pd.to_datetime(df_pdf["checkout"], errors="coerce")

    # Urutkan berdasarkan checkin
    df_pdf = df_pdf.sort_values("checkin")

    # Buat kolom bulan SEBELUM format string
    df_pdf["bulan"] = df_pdf["checkin"].dt.to_period("M")

    # Loop per bulan
    for periode, group in df_pdf.groupby("bulan"):

        nama_bulan = periode.strftime("%B %Y").upper()
        elements.append(Paragraph(f"📅 {nama_bulan}", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        # Reset nomor urut khusus bulan ini
        group = group.sort_values("checkin").reset_index(drop=True)
        group.index = group.index + 1
        group.index.name = "No"
        group = group.reset_index()

        # Format tanggal ke string SETELAH grouping
        group["checkin"] = group["checkin"].dt.strftime("%d-%m-%Y")
        group["checkout"] = group["checkout"].dt.strftime("%d-%m-%Y")

        # Format rupiah
        for col in ["harga", "total", "dp", "sisa"]:
            if col in group.columns:
                group[col] = group[col].apply(rupiah)

        # Hapus kolom bulan
        group_export = group.drop(columns=["bulan"])

        data = [group_export.columns.tolist()] + group_export.values.tolist()

        table = Table(data, repeatRows=1)

        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E8449")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#C8A951")),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]

        # Warna status
        if "status" in group_export.columns:
            status_index = group_export.columns.get_loc("status")

            for i, status in enumerate(group_export["status"], start=1):
                if status == "Booked":
                    style.append(('BACKGROUND', (status_index, i), (status_index, i), colors.HexColor("#FFF3B0")))
                elif status == "Check-in":
                    style.append(('BACKGROUND', (status_index, i), (status_index, i), colors.HexColor("#B6F2B6")))
                elif status == "Check-out":
                    style.append(('BACKGROUND', (status_index, i), (status_index, i), colors.HexColor("#A0E7FF")))
                elif status == "Selesai":
                    style.append(('BACKGROUND', (status_index, i), (status_index, i), colors.HexColor("#D3D3D3")))
                elif status == "Lunas":
                    style.append(('BACKGROUND', (status_index, i), (status_index, i), colors.HexColor("#C8F7C5")))

        table.setStyle(style)

        elements.append(table)
        elements.append(Spacer(1, 20))

        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor("#C0392B")
        )
        
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            "*harga dapat berubah sewaktu-waktu",
            disclaimer_style
        ))

    doc.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def generate_invoice(selected_data):

    with psycopg2.connect(
        st.secrets["DATABASE_URL"],
        sslmode="require"
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM bookings
                WHERE group_id = %s
                ORDER BY id
            """, (selected_data["group_id"],))

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

    bookings = [dict(zip(columns, row)) for row in rows]

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesizes.A4,
        rightMargin=30,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    elements = []
    styles = getSampleStyleSheet()

    # =========================
    # FORMAT RUPIAH
    # =========================
    def rupiah(x):
        return f"Rp {int(x):,}".replace(",", ".")

    # =========================
    # HEADER
    # =========================
    logo = RLImage("assets/logo.png", width=1.1*inch, height=1.1*inch)

    title_style = ParagraphStyle(
        "BrandTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1B5E20"),
        spaceAfter=4
    )

    info_style = ParagraphStyle(
        "InfoStyle",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        leading=10
    )

    header_left = [
        Paragraph("<b>HOMESTAY ALVIRA SIDOARJO</b>", title_style),
        Paragraph("Jl. Raya Lingkar Barat Gading Fajar 2 Blok C5 No 28", info_style),
        Paragraph("Sidoarjo - Jawa Timur", info_style),
        Paragraph("Telp: 081231646523", info_style),
    ]

    group_id = bookings[0]["group_id"]
    nama = bookings[0]["nama"]
    hp = bookings[0]["hp"]

    header_right = [
        Paragraph("<b>INVOICE</b>", styles["Title"]),
        Spacer(1, 6),
        Paragraph(f"Invoice #: INV-{datetime.now().year}-{int(selected_data['id']):04d}", styles["Normal"]),
        Paragraph(f"Date: {datetime.now().strftime('%d %b %Y')}", styles["Normal"]),
    ]

    header_table = Table(
        [[logo, header_left, header_right]],
        colWidths=[1.3*inch, 3.2*inch, 2.3*inch]
    )

    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (1,0), (1,0), 0),
        ("LEFTPADDING", (2,0), (2,0), 30),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 25))

    # =========================
    # BILL TO
    # =========================
    bill_to = Table([
        ["Bill To"],
        [nama],
        [hp],
    ], colWidths=[3*inch])

    bill_to.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))

    bill_to.hAlign = 'LEFT'

    elements.append(bill_to)
    elements.append(Spacer(1, 20))

    # =========================
    # ITEM TABLE
    # =========================
    group_id = selected_data.get("group_id")

    if not group_id:
        bookings = [selected_data]
        
    item_data = [["Kamar", "Check-in", "Check-out", "Nights", "Amount"]]

    grand_total = 0

    for b in bookings:
    
        checkin = b["checkin"]
        checkout = b["checkout"]
    
        if hasattr(checkin, "date"):
            checkin = checkin.date()
        if hasattr(checkout, "date"):
            checkout = checkout.date()
    
        nights = (checkout - checkin).days
    
        item_data.append([
            f"Kamar {b['kamar']} ({checkin} - {checkout})",
            str(nights),
            rupiah(b["total"])
        ])
    
        grand_total += b["total"]
    
        item_data.append([
            row["kamar"],
            str(checkin),
            str(checkout),
            str(nights),
            rupiah(row["total"])
        ])

    item_table = Table(item_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 0.8*inch, 1.2*inch])

    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F2F3F4")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D5D8DC")),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    elements.append(item_table)
    elements.append(Spacer(1, 30))

    # =========================
    # TOTAL SECTION
    # =========================
    total_table = Table([
        ["total", rupiah(total_all)],
        ["dp", rupiah(dp_all)],
        ["sisa", rupiah(sisa_all)],
    ], colWidths=[4.6*inch, 1.2*inch])

    total_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 1.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))

    elements.append(total_table)
    elements.append(Spacer(1, 60))

    # =========================
    # WATERMARK LUNAS PREMIUM (ENHANCED VERSION WITH PREMIUM DESIGN - FIXED POLYGON AND STROKE ISSUES)
    # =========================
    from math import cos, sin, radians
    
    def draw_bottom_text(canvas, text, center_x, center_y, radius):
        angle_step = 10  # Diubah ke 10 derajat untuk jarak antar huruf yang lebih dekat
        angle = -50  # Diubah ke -75 untuk geser ke kanan menyamping agar tidak bertabrakan dengan "ALVIRA HOMESTAY"
        
        for char in text:
            canvas.saveState()
            canvas.translate(center_x, center_y)
            canvas.rotate(angle)
            canvas.drawCentredString(0, -radius, char)
            canvas.restoreState()
            angle += angle_step
    
    def draw_top_text(canvas, text, center_x, center_y, radius):
        angle_step = 180 / len(text)
        angle = 90
        
        for char in text:
            canvas.saveState()
            canvas.translate(center_x, center_y)
            canvas.rotate(angle)
            canvas.drawCentredString(0, radius, char)
            canvas.restoreState()
            angle -= angle_step
    
    def add_lunas_watermark(canvas, doc):
        canvas.saveState()
        
        width, height = doc.pagesize
        x = width / 2
        y = height / 2 - 100  # Posisi diturunkan agar tidak mengganggu tabel
        
        # Warna merah transparan yang lebih halus
        red_transparent = Color(0.9, 0.1, 0.1, alpha=0.25)
        light_red = Color(1, 0.5, 0.5, alpha=0.15)
        
        # Lingkaran luar dengan gradien simulasi (lapisan)
        canvas.setStrokeColor(red_transparent)
        canvas.setFillColor(red_transparent)
        canvas.setLineWidth(6)
        canvas.circle(x, y, 130)
        
        canvas.setStrokeColor(light_red)
        canvas.setFillColor(light_red)
        canvas.setLineWidth(4)
        canvas.circle(x, y, 125)
        
        # Lingkaran dalam
        canvas.setStrokeColor(red_transparent)
        canvas.setFillColor(red_transparent)
        canvas.setLineWidth(3)
        canvas.circle(x, y, 95)
        
        # Garis putus-putus tengah yang lebih halus
        canvas.setLineWidth(1)
        canvas.setDash(3, 3)
        canvas.setStrokeColor(Color(0.8, 0.2, 0.2, alpha=0.4))
        canvas.circle(x, y, 108)
        canvas.setDash()
        
        # Elemen dekoratif: bintang kecil di sekitar - DIHAPUS sesuai permintaan
        
        # Tulisan melengkung atas: ALVIRA HOMESTAY
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(Color(0.6, 0, 0, alpha=0.7))
        draw_top_text(canvas, "ALVIRA HOMESTAY", x, y, 115)
        
        # Tulisan tengah LUNAS dengan font yang lebih elegan dan efek
        canvas.setFont("Times-Bold", 60)
        canvas.translate(x, y)
        canvas.rotate(15)  # Rotasi lebih kecil untuk kesan lebih stabil
        canvas.setFillColor(Color(0.7, 0, 0, alpha=0.8))  # Warna lebih gelap untuk kontras
        canvas.drawCentredString(0, -20, "LUNAS")
        canvas.rotate(-15)
        canvas.translate(-x, -y)
        
        # Tanggal pelunasan kecil di tengah bawah dengan posisi yang lebih baik
        tanggal_lunas = datetime.now().strftime("%d %b %Y")
        canvas.setFont("Helvetica", 12)
        canvas.setFillColor(Color(0.5, 0, 0, alpha=0.6))
        canvas.drawCentredString(x, y - 60, f"Paid on {tanggal_lunas}")
        
        # Kalimat terima kasih melengkung di bawah, agak turun (radius 110), jarak huruf dekat (10 derajat), geser ke kanan (angle -75)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(Color(0.6, 0, 0, alpha=0.7))
        draw_bottom_text(canvas, "Terima Kasih", x, y, 110)
        
        canvas.restoreState()
    
        # Kondisi pembangunan dokumen tetap sama
        if selected_data.get("sisa", 0) <= 0:
            doc.title = str(selected_data["id"])
            doc.build(elements, onFirstPage=add_lunas_watermark)
        else:
            doc.build(elements)
            
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def generate_pdf_public(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)
    elements = []

    styles = getSampleStyleSheet()

    # ======================
    # HEADER PREMIUM
    # ======================
    
    logo = RLImage("assets/logo.png", width=1.3*inch, height=1.3*inch)
    
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontName="Playfair-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1B5E20"),
        alignment=1,
        spaceAfter=5
    )
    
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        textColor=colors.black,
        alignment=1,
        spaceAfter=6
    )
    
    info_style = ParagraphStyle(
        "InfoStyle",
        parent=styles["Normal"],
        fontName="Poppins-Regular",
        fontSize=8,
        leading=10,
        textColor=colors.grey,
        alignment=1,
        spaceAfter=3
    )
     
    header_text = [
        Paragraph("<b>HOMESTAY ALVIRA SIDOARJO</b>", title_style),
        Spacer(1, 2),  # 🔥 tambahan jarak manual
        Paragraph("<b>LAPORAN BOOKING</b>", subtitle_style),
        Spacer(1, 4),  # 🔥 tambahan jarak manual
        Paragraph("Jl. Raya Lingkar Barat Gading Fajar 2 Blok C5 No 28 Sidoarjo Kota - Jawa Timur", info_style),
        Paragraph("Telp: 081231646523 (Bu Yanie) | Website: www.alvirahomestay.com", info_style),
    ]

    header_table = Table(
        [[logo, header_text]],
        colWidths=[3*cm, 12*cm]
    )
    
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    
        # Logo kolom 0
        ("LEFTPADDING", (0,0), (0,0), 0),
    
        # Text kolom 1 → geser ke kanan
        ("LEFTPADDING", (1,0), (1,0), 20),
    
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 6))
    
    gold_line = Table([[""]], colWidths=[17*cm])
    gold_line.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#C6A700"))
    ]))
    
    elements.append(gold_line)
    elements.append(Spacer(1, 15))

    df_pdf = df.copy()

    # Convert ke datetime dulu
    df_pdf["checkin"] = pd.to_datetime(df_pdf["checkin"], errors="coerce")
    df_pdf["checkout"] = pd.to_datetime(df_pdf["checkout"], errors="coerce")

    # Urutkan berdasarkan checkin
    df_pdf = df_pdf.sort_values("checkin")

    # Buat kolom bulan
    df_pdf["bulan"] = df_pdf["checkin"].dt.to_period("M")

    # Loop per bulan
    for periode, group in df_pdf.groupby("bulan"):

        nama_bulan = periode.strftime("%B %Y").upper()
        elements.append(Paragraph(f"📅 {nama_bulan}", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        group = group.sort_values("checkin").reset_index(drop=True)

        # Nomor urut per bulan
        group.index = group.index + 1
        group.index.name = "No"
        group = group.reset_index()

        # Format tanggal
        group["checkin"] = group["checkin"].dt.strftime("%d-%m-%Y")
        group["checkout"] = group["checkout"].dt.strftime("%d-%m-%Y")

        # ❌ HIDE KOLOM HARGA UNTUK PUBLIC
        for col in ["harga", "total", "dp", "sisa", "id","hp"]:
            if col in group.columns:
                group = group.drop(columns=[col])

        group_export = group.drop(columns=["bulan"])

        data = [group_export.columns.tolist()] + group_export.values.tolist()

        table = Table(data, repeatRows=1)

        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E8449")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#C8A951")),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]

        # 🎨 Warna Status
        if "status" in group_export.columns:
            status_index = group_export.columns.get_loc("status")

            for i, status in enumerate(group_export["status"], start=1):
                if status == "Booked":
                    style.append(('BACKGROUND', (status_index, i), (status_index, i), colors.HexColor("#FFF3B0")))
                elif status == "Check-in":
                    style.append(('BACKGROUND', (status_index, i), (status_index, i), colors.HexColor("#B6F2B6")))
                elif status == "Check-out":
                    style.append(('BACKGROUND', (status_index, i), (status_index, i), colors.HexColor("#A0E7FF")))
                elif status == "Selesai":
                    style.append(('BACKGROUND', (status_index, i), (status_index, i), colors.HexColor("#D3D3D3")))
                elif status == "Lunas":
                    style.append(('BACKGROUND', (status_index, i), (status_index, i), colors.HexColor("#C8F7C5")))

        table.setStyle(style)

        elements.append(table)
        elements.append(Spacer(1, 20))

    doc.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# ============================
# MASTER HARGA KAMAR
# ============================
harga_kamar = {
    "Alvira 1": {
        "weekday": 350000,
        "weekend": 400000
    },
    "Alvira 2": {
        "weekday": 300000,
        "weekend": 350000
    },
    "Alvira 3": {
        "weekday": 190000,
        "weekend": 225000
    },
    "Alvira 4": {
        "weekday": 300000,
        "weekend": 350000
    },
    "Alvira 5": {
        "weekday": 450000,
        "weekend": 500000
    },
}

def hitung_total_kamar(kamar, checkin, checkout):
    total = 0
    current_date = checkin

    while current_date < checkout:
        # Weekend = Jumat (4), Sabtu (5), Minggu (6)
        if current_date.weekday() >= 4:
            total += harga_kamar[kamar]["weekend"]
        else:
            total += harga_kamar[kamar]["weekday"]

        current_date += timedelta(days=1)

    return total

# ============================
# TAMBAH BOOKING (UPGRADE)
# ============================

st.sidebar.header("➕ Tambah Booking")

with st.sidebar.form("form_tambah_booking"):

    nama = st.text_input("Nama Tamu")
    hp = st.text_input("No HP")

    kamar_list = ["Alvira 1", "Alvira 2", "Alvira 3", "Alvira 4", "Alvira 5"]
    kamar = st.multiselect("Pilih Kamar", kamar_list)

    checkin = st.date_input("Check-in")
    checkout = st.date_input("Check-out")

    dp = st.number_input(
        "DP (Uang Muka)",
        min_value=0,
        step=50000,
        format="%d"
    )

    submit = st.form_submit_button("💾 Cek Harga")
    
jumlah_kamar = len(kamar)

st.sidebar.markdown(f"🛏 Jumlah Kamar: **{jumlah_kamar}**")

if kamar and checkout > checkin:

    st.sidebar.markdown("### 💰 Rincian Harga")

    total_semua = 0
    
    for k in kamar:
        st.sidebar.markdown(f"#### 🛏 {k}")
        
        current_date = checkin
        total_kamar = 0
    
        while current_date < checkout:
            if current_date.weekday() >= 5:
                harga = harga_kamar[k]["weekend"]
                tipe = "Weekend"
            else:
                harga = harga_kamar[k]["weekday"]
                tipe = "Weekday"
    
            st.sidebar.write(
                f"{current_date} ({tipe}) : Rp {harga:,.0f}".replace(",", ".")
            )
    
            total_kamar += harga
            current_date += timedelta(days=1)
    
        st.sidebar.markdown(
            f"**Subtotal {k}: Rp {total_kamar:,.0f}**".replace(",", ".")
        )
        st.sidebar.markdown("---")
    
        total_semua += total_kamar
    
    st.sidebar.markdown(
        f"### 💵 Total Booking: Rp {total_semua:,.0f}".replace(",", ".")
    )

    st.sidebar.markdown(
        f"💳 **DP: Rp {dp:,.0f}**".replace(",", ".")
    )
    
if st.sidebar.button("Simpan Booking"):

    if not kamar:
        st.sidebar.error("Pilih minimal 1 kamar!")
    
    elif checkout <= checkin:
        st.sidebar.error("Tanggal tidak valid")

    else:
        try:
            # 🔥 Buat 1 GROUP ID untuk semua kamar
            group_id = str(uuid.uuid4())[:8]

            total_semua = 0

            # Cek double booking dulu
            for k in kamar:
                if is_double_booking(k, checkin, checkout):
                    st.sidebar.error(f"❌ {k} sudah dibooking di tanggal tersebut!")
                    st.stop()

                total_kamar = hitung_total_kamar(k, checkin, checkout)
                total_semua += total_kamar

            # 💎 Split DP rata per kamar
            dp_per_kamar = dp / len(kamar)
            sisa_group = total_semua - dp
            status_group = get_status(checkin, checkout, sisa_group)

            # 🔥 Insert per kamar tapi group_id sama
            for k in kamar:
                total_kamar = hitung_total_kamar(k, checkin, checkout)
                sisa_kamar = total_kamar - dp_per_kamar

                cursor.execute("""
                    INSERT INTO bookings
                    (nama, hp, kamar, checkin, checkout, harga,
                     total, dp, sisa, status, group_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    nama,
                    hp,
                    k,
                    str(checkin),
                    str(checkout),
                    0,
                    total_kamar,
                    dp_per_kamar,
                    sisa_kamar,
                    status_group,
                    group_id
                ))

            conn.commit()
            st.sidebar.success(f"✅ Booking berhasil! Invoice Group: {group_id}")
            st.cache_data.clear()
            st.rerun()

        except Exception as e:
            st.sidebar.error(f"Terjadi error: {e}")
        
# ============================
# LOAD DATA
# ============================
df = load_data()

if not df.empty:

    # Pastikan datetime
    df["checkin"] = pd.to_datetime(df["checkin"], errors="coerce")
    df["checkout"] = pd.to_datetime(df["checkout"], errors="coerce")

    # Urutkan berdasarkan checkin
    df = df.sort_values("checkin").reset_index(drop=True)

    # ============================
    # DATA TABLE (UTAMA DI ATAS)
    # ============================
    st.subheader("📋 Data Booking (Tabel Utama)")

    df_display = df.copy()

    # Format tanggal tanpa jam
    df_display["checkin"] = df_display["checkin"].dt.strftime("%d-%m-%Y")
    df_display["checkout"] = df_display["checkout"].dt.strftime("%d-%m-%Y")

    # Tambahkan nomor urut mulai dari 1
    df_display.insert(0, "No", range(1, len(df_display) + 1))

    # Format rupiah
    def format_rupiah(x):
        try:
            return f"Rp {int(x):,}".replace(",", ".")
        except:
            return x

    for col in ["harga", "total", "dp", "sisa"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(format_rupiah)

    # Styling status
    def highlight_status(val):
        if val == "Check-in":
            return "background-color: #b6f2b6; font-weight: bold;"
        elif val == "Booked":
            return "background-color: #fff3b0; font-weight: bold;"
        elif val == "Check-out":
            return "background-color: #a0e7ff; font-weight: bold;"
        elif val == "Selesai":
            return "background-color: #d3d3d3; font-weight: bold;"
        elif val == "Lunas":
            return "background-color: #c8f7c5; font-weight: bold;"
        return ""

    styled_df = df_display.style.applymap(highlight_status, subset=["status"])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ============================
    # TAMPIL PER BULAN
    # ============================

    df["bulan"] = df["checkin"].dt.to_period("M")

    for periode, group in df.groupby("bulan"):

        nama_bulan = periode.strftime("%B %Y").upper()
        st.markdown(f"## 📅 {nama_bulan}")
        st.markdown("---")

        group = group.sort_values("checkin").reset_index(drop=True)

        # Nomor urut mulai 1
        group.insert(0, "No", range(1, len(group) + 1))

        # Format tanggal
        group["checkin"] = group["checkin"].dt.strftime("%d-%m-%Y")
        group["checkout"] = group["checkout"].dt.strftime("%d-%m-%Y")

        group_display = group.drop(columns=["bulan"])

        st.dataframe(group_display, use_container_width=True, hide_index=True)

    # ============================
    # UPDATE STATUS OTOMATIS
    # ============================

    for index, row in df.iterrows():
        checkin_date = pd.to_datetime(row["checkin"]).date()
        checkout_date = pd.to_datetime(row["checkout"]).date()
        sisa_value = row["sisa"] if row["sisa"] is not None else 0

        new_status = get_status(checkin_date, checkout_date, sisa_value)

        cursor.execute(
            "UPDATE bookings SET status=%s WHERE id=%s",
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

    # =========================
    # SESSION STATE INIT
    # =========================
    if "selected_booking_id" not in st.session_state:
        st.session_state.selected_booking_id = df["id"].iloc[0]
    
    booking_ids = df["id"].tolist()
    
    # =========================
    # SELECT BOOKING
    # =========================

    booking_ids = df["id"].tolist()

    # Kalau data kosong
    if not booking_ids:
        st.warning("Belum ada booking.")
        st.stop()
    
    # Kalau selected ID sudah tidak ada (habis dihapus)
    if st.session_state.selected_booking_id not in booking_ids:
        st.session_state.selected_booking_id = booking_ids[0]
        
    selected_id = st.selectbox(
        "Pilih Booking ID",
        booking_ids,
        index=booking_ids.index(st.session_state.selected_booking_id),
        key="booking_selector"
    )
    
    st.session_state.selected_booking_id = selected_id

    # Ambil data terbaru berdasarkan ID
    selected_data = df[df["id"] == selected_id].iloc[0]
    
    # =========================
    # FORM EDIT
    # =========================
    with st.form("form_edit_booking"):

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
            edit_checkin = st.date_input("Check-in", selected_data["checkin"])
            edit_checkout = st.date_input("Check-out", selected_data["checkout"])
            edit_harga = st.number_input(
                "Harga per Malam",
                value=int(selected_data["harga"]),
                min_value=0
            )
            edit_dp = st.number_input(
                "DP",
                value=int(selected_data["dp"]),
                min_value=0
            )
    
        malam = (edit_checkout - edit_checkin).days
        edit_total = malam * edit_harga if malam > 0 else 0
        edit_sisa = edit_total - edit_dp
        edit_status = get_status(edit_checkin, edit_checkout, edit_sisa)
    
        st.write(f"💰 Total: Rp {edit_total:,.0f}")
        st.write(f"💳 Sisa: Rp {edit_sisa:,.0f}")
        st.write(f"📌 Status: {edit_status}")
    
        col_update, col_delete = st.columns(2)
        update_clicked = col_update.form_submit_button("💾 Update Booking")
        delete_clicked = col_delete.form_submit_button("🗑️ Hapus Booking")
    
        # =========================
        # UPDATE LOGIC
        # =========================
        if update_clicked:
        
            if edit_checkout <= edit_checkin:
                st.error("❌ Checkout harus setelah checkin!")
        
            elif is_double_booking(edit_kamar, edit_checkin,
                                   edit_checkout, selected_id):
                st.error("❌ Jadwal bentrok dengan booking lain!")
        
            else:
                try:
                    with psycopg2.connect(
                        st.secrets["DATABASE_URL"],
                        sslmode="require"
                    ) as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                UPDATE bookings
                                SET nama=%s, hp=%s, kamar=%s,
                                    checkin=%s, checkout=%s,
                                    harga=%s, total=%s,
                                    dp=%s, sisa=%s, status=%s
                                WHERE id=%s
                            """, (
                                edit_nama, edit_hp, edit_kamar,
                                edit_checkin, edit_checkout,
                                edit_harga, edit_total,
                                edit_dp, edit_sisa,
                                edit_status,
                                selected_id
                            ))
                            conn.commit()
        
                    st.success("✅ Booking berhasil diupdate!")
                    st.cache_data.clear()
                    st.rerun()
        
                except Exception as e:
                    st.error(f"Terjadi error: {e}")
            
        # =========================
        # DELETE LOGIC
        # =========================
        if delete_clicked:
            try:
                with psycopg2.connect(
                    st.secrets["DATABASE_URL"],
                    sslmode="require"
                ) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "DELETE FROM bookings WHERE id=%s",
                            (selected_id,)
                        )
                        conn.commit()
        
                st.success("🗑️ Booking berhasil dihapus!")
                st.cache_data.clear()
                st.session_state.selected_booking_id = None
                st.rerun()
        
            except Exception as e:
                st.error(f"Gagal menghapus booking: {e}")
                
    # =========================
    # GENERATE INVOICE
    # =========================
    st.divider()

    if st.button("🧾 Generate Invoice"):
    
        # 🔐 Ambil group_id dengan fallback
        group_id = selected_data.get("group_id")
    
        # Kalau tidak ada group_id (booking lama)
        if not group_id:
            group_bookings = [selected_data.to_dict()]
        else:
            group_bookings = df[df["group_id"] == group_id].to_dict("records")
    
        pdf_file = generate_invoice(group_bookings)

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
    
            try:
                with st.spinner("Mereset database..."):
    
                    with psycopg2.connect(
                        st.secrets["DATABASE_URL"],
                        sslmode="require"
                    ) as conn:
    
                        with conn.cursor() as cursor:
                            cursor.execute("DELETE FROM bookings;")
                            cursor.execute("ALTER SEQUENCE bookings_id_seq RESTART WITH 1;")
                            conn.commit()
    
                    st.cache_data.clear()
    
                st.success("✅ Database berhasil direset!")
                st.rerun()
    
            except Exception as e:
                st.error(f"Terjadi error: {e}")

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
