import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Homestay Management System", layout="wide")

st.title("🏠 Homestay Management Dashboard")

DATA_FILE = "bookings.csv"

# ----------------------------
# Load Data
# ----------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["Check-in", "Check-out"])
    else:
        return pd.DataFrame(columns=[
            "Nama Tamu", "No HP", "Kamar",
            "Check-in", "Check-out",
            "Harga per Malam", "Total Bayar", "Status"
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# ----------------------------
# Sidebar - Input Booking
# ----------------------------
st.sidebar.header("➕ Tambah Booking Baru")

nama = st.sidebar.text_input("Nama Tamu")
hp = st.sidebar.text_input("No HP")
kamar = st.sidebar.selectbox("Pilih Kamar", ["Kamar 1", "Kamar 2", "Kamar 3", "Family Room"])
checkin = st.sidebar.date_input("Check-in")
checkout = st.sidebar.date_input("Check-out")
harga = st.sidebar.number_input("Harga per Malam", min_value=0)

if st.sidebar.button("Simpan Booking"):
    if checkout > checkin:
        malam = (checkout - checkin).days
        total = malam * harga

        new_data = pd.DataFrame([{
            "Nama Tamu": nama,
            "No HP": hp,
            "Kamar": kamar,
            "Check-in": checkin,
            "Check-out": checkout,
            "Harga per Malam": harga,
            "Total Bayar": total,
            "Status": "Booked"
        }])

        df = pd.concat([df, new_data], ignore_index=True)
        save_data(df)
        st.success("Booking berhasil disimpan!")
    else:
        st.error("Tanggal check-out harus setelah check-in.")

# ----------------------------
# Dashboard Metrics
# ----------------------------
st.subheader("📊 Ringkasan Bisnis")

total_pendapatan = df["Total Bayar"].sum()
total_booking = len(df)
kamar_terpakai = df[df["Status"] == "Booked"]["Kamar"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
col2.metric("Total Booking", total_booking)
col3.metric("Kamar Terpakai", kamar_terpakai)

st.write("---")

# ----------------------------
# Data Table
# ----------------------------
st.subheader("📋 Data Booking")

st.dataframe(df, use_container_width=True)

# ----------------------------
# Grafik Pendapatan
# ----------------------------
st.subheader("📈 Grafik Pendapatan per Booking")

if not df.empty:
    chart_data = df.groupby("Kamar")["Total Bayar"].sum()
    st.bar_chart(chart_data)

# ----------------------------
# Download Report
# ----------------------------
st.subheader("📥 Download Laporan")

st.download_button(
    label="Download CSV",
    data=df.to_csv(index=False),
    file_name="laporan_homestay.csv",
    mime="text/csv"
)
