from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from datetime import datetime
from reportlab.lib.units import cm
import io

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes

import streamlit as st
import pandas as pd
from datetime import datetime, date
import matplotlib.pyplot as plt
import streamlit as st

from PIL import Image
from reportlab.platypus import Image as RLImage
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

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

col1, col2 = st.columns([1,4])

with col1:
    st.image(logo, width=120)

with col2:
    st.title("HOMESTAY ALVIRA")
    st.caption("Sistem Manajemen Booking Profesional")

if "keep_alive" not in st.session_state:
    st.session_state.keep_alive = True

st.set_page_config(page_title="Homestay Pro System", layout="wide")
st.title("🏠 Homestay Alvira Management")

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

except Exception as e:
    st.error(f"Database error: {e}")

finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()

    # ============================
    # FUNCTIONS
    # ============================
        
    # Fungsi ini bisa dipanggil di luar blok database, tapi jika menggunakan cursor, pastikan di dalam try
    # (Untuk sekarang, functions didefinisikan di sini; panggil di tempat lain jika perlu)
        
    # Catatan: harga_kamar tidak didefinisikan di sini; pastikan didefinisikan di tempat lain atau tambahkan
        
except psycopg2.OperationalError as e:
    st.error(f"Kesalahan operasional koneksi: {e}")
except psycopg2.DatabaseError as e:
    st.error(f"Kesalahan database: {e}")
except Exception as e:
    st.error(f"Kesalahan umum: {e}")
finally:
    # Tutup cursor dan koneksi jika ada
    if cursor:
        cursor.close()
    if conn:
        conn.close()
        st.info("Koneksi database ditutup.")

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
    # Fungsi ini perlu akses database, jadi panggil di dalam blok try jika digunakan
    # Untuk sekarang, ini contoh; integrasikan ke blok database jika diperlukan
    # Misalnya, di dalam try:
    # query = """
    # SELECT * FROM bookings
    # WHERE kamar = %s
    # AND (%s IS NULL OR id != %s)
    # AND (
    #     checkin::date < %s::date
    #     AND
    #     checkout::date > %s::date
    # )
    # """
    # cursor.execute(query, (kamar, booking_id, booking_id, checkout, checkin))
    # result = cursor.fetchall()
    # return len(result) > 0
    pass  # Ganti dengan implementasi jika diperlukan

# ============================
# LOAD DATA FUNCTION
# ============================

@st.cache_data(ttl=60)
def load_data():
    query = "SELECT * FROM bookings ORDER BY checkin ASC"
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
            status
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

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesizes.A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    elements = []
    styles = getSampleStyleSheet()

    # =========================
    # FORMAT RUPIAH
    # =========================
    def rupiah(x):
        return f"Rp {int(x):,}".replace(",", ".")

    # =========================
    # HEADER (KIRI LOGO | KANAN INFO)
    # =========================
    logo = RLImage("assets/logo.png", width=1.2*inch, height=1.2*inch)

    info_style = ParagraphStyle(
        "InfoStyle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey
    )
    
    header_left = [
        Paragraph("<b>HOMESTAY ALVIRA SIDOARJO</b>", styles["Heading1"]),
        Spacer(1, 4),
        Paragraph("Jl. Raya Lingkar Barat Gading Fajar 2 Blok C5 No 28", info_style),
        Paragraph("Sidoarjo - Jawa Timur", info_style),
        Paragraph("Telp: 081231646523", info_style),
    ]

    header_right = [
        Paragraph("<b>INVOICE</b>", styles["Title"]),
        Spacer(1, 6),
        Paragraph(f"Invoice #: INV-{datetime.now().year}-{int(selected_data['id']):04d}", styles["Normal"]),
        Paragraph(f"Date: {datetime.now().strftime('%d %b %Y')}", styles["Normal"]),
    ]

    header_table = Table(
        [[logo, header_left, header_right]],
        colWidths=[1.5*inch, 3*inch, 2.5*inch]  # logo lebih kecil, text lebih lebar
    )
    
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    
        # Logo padding kecil
        ("LEFTPADDING", (0,0), (0,0), 0),
        ("RIGHTPADDING", (0,0), (0,0), 10),
    
        # Text kiri mepet ke logo
        ("LEFTPADDING", (1,0), (1,0), 0),
    
        # Invoice block geser kanan
        ("LEFTPADDING", (2,0), (2,0), 40),
    
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 20))

    # =========================
    # BILL TO
    # =========================
    bill_to = Table([
        ["Bill To:"],
        [selected_data["nama"]],
        [selected_data["hp"]],
    ], colWidths=[3*inch])

    bill_to.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ("LEFTPADDING", (1,0), (1,0), 0),
    ]))

    elements.append(bill_to)
    elements.append(Spacer(1, 20))

    # =========================
    # TABEL ITEM
    # =========================
    nights = (
        datetime.strptime(selected_data["checkout"], "%Y-%m-%d") -
        datetime.strptime(selected_data["checkin"], "%Y-%m-%d")
    ).days

    item_data = [
        ["Description", "Qty", "Price", "Amount"],
        [
            f"Kamar {selected_data['kamar']} ({selected_data['checkin']} - {selected_data['checkout']})",
            str(nights),
            rupiah(selected_data["total"] // nights if nights else selected_data["total"]),
            rupiah(selected_data["total"])
        ]
    ]

    item_table = Table(item_data, colWidths=[3*inch, 0.8*inch, 1*inch, 1.2*inch])

    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAECEE")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    elements.append(item_table)
    elements.append(Spacer(1, 20))

    # =========================
    # TOTAL SECTION
    # =========================
    total_table = Table([
        ["Total", rupiah(selected_data["total"])]
    ], colWidths=[4.8*inch, 1.2*inch])

    total_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))

    elements.append(total_table)
    elements.append(Spacer(1, 50))

    # =========================
    # SIGNATURE AREA
    # =========================
    sign_table = Table([
        ["Authorized Signature"],
        ["\n\n\n__________________________"],
        [datetime.now().strftime('%d %b %Y')]
    ], colWidths=[2.5*inch])

    sign_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))

    elements.append(sign_table)

    if selected_data["total"] <= 0 or selected_data.get("sisa", 0) <= 0:
        doc.build(elements, onFirstPage=add_lunas_watermark)
    else:
        doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def add_header(elements, logo_path):

    # Logo kiri
    logo = Image(logo_path, width=2.5*cm, height=2.5*cm)

    # Teks tengah
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    title_style.textColor = colors.HexColor("#1B5E20")  # Brand hijau Alvira
    title_style.alignment = 1  # Center

    subtitle_style = styles["Normal"]
    subtitle_style.alignment = 1

    header_text = [
        Paragraph("<b>Homestay Alvira</b>", title_style),
        Paragraph("Laporan Booking 2026", subtitle_style),
    ]

    # Layout tabel 2 kolom (logo kiri, teks tengah)
    header_table = Table(
        [[logo, header_text]],
        colWidths=[3*cm, 12*cm]
    )

    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 8))

    # 🔥 Garis emas tipis
    line = Table(
        [[""]],
        colWidths=[17*cm],
        rowHeights=[2]
    )

    line.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#C9A227"))  # Gold elegan
    ]))

    elements.append(line)
    elements.append(Spacer(1, 20))


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

    doc.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)
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

# ============================
# TAMBAH BOOKING
# ============================
st.sidebar.header("➕ Tambah Booking")

nama = st.sidebar.text_input("Nama Tamu")
hp = st.sidebar.text_input("No HP")
kamar_list = ["Alvira 1", "Alvira 2", "Alvira 3", "Alvira 4", "Alvira 5"]
kamar = st.sidebar.multiselect("Pilih Kamar", kamar_list)
checkin = st.sidebar.date_input("Check-in")
checkout = st.sidebar.date_input("Check-out")

dp = st.sidebar.number_input(
    "DP (Uang Muka)",
    min_value=0,
    step=50000,
    format="%d"
)

jumlah_kamar = len(kamar)

st.sidebar.markdown(f"🛏 Jumlah Kamar: **{jumlah_kamar}**")
if kamar and checkout > checkin:

    st.sidebar.markdown("### 💰 Rincian Harga")

    total_semua = 0

    for k in kamar:
        total_kamar = hitung_total_kamar(k, checkin, checkout)
        total_semua += total_kamar

        st.sidebar.markdown(
            f"{k} : Rp {total_kamar:,.0f}".replace(",", ".")
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"💵 Total Booking: **Rp {total_semua:,.0f}**".replace(",", ".")
    )

st.sidebar.markdown(f"💳 DP: **Rp {dp:,.0f}**".replace(",", "."))

if st.sidebar.button("Simpan Booking"):

    if not kamar:
        st.sidebar.error("Pilih minimal 1 kamar!")
    
    elif checkout <= checkin:
        st.sidebar.error("Tanggal tidak valid")

    else:
        
        total_semua = 0

        for k in kamar:

            if is_double_booking(k, checkin, checkout):
                st.sidebar.error(f"❌ {k} sudah dibooking di tanggal tersebut!")
                st.stop()

        total_kamar = hitung_total_kamar(k, checkin, checkout)
        total_semua += total_kamar

        sisa = total_semua - dp
        status = get_status(checkin, checkout, sisa)

        for k in kamar:

            total_kamar = hitung_total_kamar(k, checkin, checkout)
        
            cursor.execute("""
                INSERT INTO bookings
                (nama, hp, kamar, checkin, checkout, harga, total, dp, sisa, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nama, hp, k,
                str(checkin), str(checkout),
                0,  # harga per malam tidak tetap lagi
                total_kamar,
                dp,
                sisa,
                status
            ))

        conn.commit()
        st.sidebar.success("Booking berhasil!")
        st.rerun()

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
                SET nama=%s, hp=%s, kamar=%s, checkin=%s, checkout=%s,
                    harga=%s, total=%s, dp=%s, sisa=%s, status=%s
                WHERE id=%s
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
            cursor.execute("TRUNCATE TABLE bookings RESTART IDENTITY;")
            conn.commit()
            st.success("Database berhasil direset.")
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
