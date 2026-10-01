import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database import get_connection


# =========================================================
# KONFIGURASI
# =========================================================

st.title("📊 Laporan Penjualan")
st.caption("Analisis penjualan Risolcu")


# =========================================================
# FORMAT RUPIAH
# =========================================================

def rupiah(value):
    return f"Rp{value:,.0f}".replace(",", ".")


# =========================================================
# FILTER PERIODE
# =========================================================

st.subheader("📅 Periode Laporan")

col1, col2 = st.columns(2)

with col1:
    tanggal_mulai = st.date_input(
        "Tanggal Mulai",
        value=date.today().replace(day=1)
    )

with col2:
    tanggal_selesai = st.date_input(
        "Tanggal Selesai",
        value=date.today()
    )


if tanggal_selesai < tanggal_mulai:

    st.error(
        "Tanggal selesai tidak boleh lebih kecil "
        "dari tanggal mulai."
    )

    st.stop()


# =========================================================
# DATA TRANSAKSI
# =========================================================

connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
    SELECT
        id,
        tanggal,
        subtotal,
        diskon,
        total,
        pembayaran,
        kembalian,
        metode_pembayaran,
        customer_id
    FROM transactions
    WHERE DATE(tanggal) BETWEEN ? AND ?
    ORDER BY tanggal
""", (
    str(tanggal_mulai),
    str(tanggal_selesai)
))

transactions = cursor.fetchall()

connection.close()


# =========================================================
# TIDAK ADA DATA
# =========================================================

if not transactions:

    st.info(
        "Tidak ada transaksi pada periode yang dipilih."
    )

    st.stop()


# =========================================================
# DATAFRAME TRANSAKSI
# =========================================================

transaction_data = []

for transaction in transactions:

    transaction_data.append({

        "ID": transaction["id"],

        "Tanggal": transaction["tanggal"],

        "Subtotal": transaction["subtotal"],

        "Diskon": transaction["diskon"],

        "Total": transaction["total"],

        "Pembayaran": transaction["pembayaran"],

        "Kembalian": transaction["kembalian"],

        "Metode": transaction["metode_pembayaran"],

        "Customer ID": transaction["customer_id"]
    })


df_transactions = pd.DataFrame(
    transaction_data
)


# =========================================================
# KPI UTAMA
# =========================================================

total_omzet = df_transactions["Total"].sum()

jumlah_transaksi = len(
    df_transactions
)

total_diskon = df_transactions["Diskon"].sum()

rata_transaksi = (
    total_omzet / jumlah_transaksi
    if jumlah_transaksi > 0
    else 0
)


# =========================================================
# PRODUK TERJUAL
# =========================================================

connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
    SELECT
        td.product_id,
        p.nama_produk,
        SUM(td.qty) AS qty_terjual,
        SUM(td.subtotal) AS omzet_produk,
        SUM(
            (td.harga - p.harga_modal) * td.qty
        ) AS laba_kotor
    FROM transaction_details td

    JOIN products p
        ON td.product_id = p.id

    JOIN transactions t
        ON td.transaction_id = t.id

    WHERE DATE(t.tanggal)
        BETWEEN ? AND ?

    GROUP BY
        td.product_id,
        p.nama_produk

    ORDER BY
        qty_terjual DESC
""", (
    str(tanggal_mulai),
    str(tanggal_selesai)
))

product_sales = cursor.fetchall()

connection.close()


# =========================================================
# HITUNG PRODUK
# =========================================================

total_produk_terjual = sum(
    row["qty_terjual"]
    for row in product_sales
)

total_laba_kotor = sum(
    row["laba_kotor"]
    for row in product_sales
)


# =========================================================
# KPI
# =========================================================

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "💰 Omzet",
        rupiah(total_omzet)
    )

with col2:

    st.metric(
        "🧾 Transaksi",
        f"{jumlah_transaksi:,}".replace(
            ",", "."
        )
    )

with col3:

    st.metric(
        "🛒 Rata-rata Transaksi",
        rupiah(rata_transaksi)
    )

with col4:

    st.metric(
        "📦 Produk Terjual",
        f"{total_produk_terjual:,}".replace(
            ",", "."
        )
    )


# =========================================================
# LABA
# =========================================================

st.divider()

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "🏦 Laba Kotor",
        rupiah(total_laba_kotor)
    )

with col2:

    st.metric(
        "🏷️ Total Diskon",
        rupiah(total_diskon)
    )


# =========================================================
# GRAFIK OMZET HARIAN
# =========================================================

st.divider()

st.subheader("📈 Omzet Harian")


df_daily = df_transactions.copy()

df_daily["Tanggal"] = pd.to_datetime(
    df_daily["Tanggal"]
).dt.date

daily_sales = (
    df_daily
    .groupby("Tanggal")["Total"]
    .sum()
    .reset_index()
)


st.bar_chart(
    daily_sales.set_index("Tanggal")
)


# =========================================================
# PRODUK TERLARIS
# =========================================================

st.divider()

st.subheader("🏆 Produk Terlaris")


if product_sales:

    top_products = []

    for row in product_sales[:10]:

        top_products.append({

            "Produk":
                row["nama_produk"],

            "Qty Terjual":
                row["qty_terjual"],

            "Omzet":
                rupiah(row["omzet_produk"]),

            "Laba Kotor":
                rupiah(row["laba_kotor"])
        })


    st.dataframe(
        pd.DataFrame(top_products),
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "Belum ada data produk."
    )


# =========================================================
# PRODUK PALING SEDIKIT
# =========================================================

st.subheader("📉 Produk Paling Sedikit Terjual")


if product_sales:

    bottom_products = sorted(
        product_sales,
        key=lambda x: x["qty_terjual"]
    )[:10]


    bottom_data = []

    for row in bottom_products:

        bottom_data.append({

            "Produk":
                row["nama_produk"],

            "Qty Terjual":
                row["qty_terjual"],

            "Omzet":
                rupiah(row["omzet_produk"])
        })


    st.dataframe(
        pd.DataFrame(bottom_data),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# KONTRIBUSI OMZET
# =========================================================

st.divider()

st.subheader("💰 Kontribusi Omzet Produk")


contribution_data = []

for row in product_sales:

    if total_omzet > 0:

        kontribusi = (
            row["omzet_produk"]
            / total_omzet
            * 100
        )

    else:

        kontribusi = 0


    contribution_data.append({

        "Produk":
            row["nama_produk"],

        "Omzet":
            rupiah(row["omzet_produk"]),

        "Kontribusi":
            f"{kontribusi:.2f}%",

        "Qty":
            row["qty_terjual"],

        "Laba Kotor":
            rupiah(row["laba_kotor"])
    })


st.dataframe(
    pd.DataFrame(contribution_data),
    use_container_width=True,
    hide_index=True
)


# =========================================================
# METODE PEMBAYARAN
# =========================================================

st.divider()

st.subheader("💳 Metode Pembayaran")


payment_summary = (
    df_transactions
    .groupby("Metode")["Total"]
    .agg(
        ["count", "sum"]
    )
    .reset_index()
)


payment_summary.columns = [
    "Metode",
    "Jumlah Transaksi",
    "Omzet"
]


payment_summary["Omzet"] = (
    payment_summary["Omzet"]
    .apply(rupiah)
)


st.dataframe(
    payment_summary,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# TRANSAKSI TERBESAR
# =========================================================

st.divider()

st.subheader("💎 Transaksi Terbesar")


largest_transactions = (
    df_transactions
    .sort_values(
        "Total",
        ascending=False
    )
    .head(10)
    .copy()
)


largest_transactions["Total"] = (
    largest_transactions["Total"]
    .apply(rupiah)
)


largest_transactions["Diskon"] = (
    largest_transactions["Diskon"]
    .apply(rupiah)
)


st.dataframe(
    largest_transactions[
        [
            "ID",
            "Tanggal",
            "Total",
            "Diskon",
            "Metode"
        ]
    ],
    use_container_width=True,
    hide_index=True
)
