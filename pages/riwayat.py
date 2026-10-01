import streamlit as st

from database import get_connection


st.title("📋 Riwayat Transaksi")
st.caption("Melihat seluruh transaksi Risolcu")


# =========================================================
# FORMAT RUPIAH
# =========================================================

def rupiah(value):
    return f"Rp{value:,.0f}".replace(",", ".")


# =========================================================
# FILTER
# =========================================================

col1, col2 = st.columns(2)

with col1:

    search = st.text_input(
        "🔍 Cari transaksi / pelanggan",
        placeholder="Contoh: 12 atau Budi"
    )

with col2:

    limit = st.selectbox(
        "Jumlah transaksi",
        [20, 50, 100],
        index=0
    )


# =========================================================
# AMBIL TRANSAKSI
# =========================================================

connection = get_connection()
cursor = connection.cursor()

query = """
    SELECT
        t.id,
        t.tanggal,
        t.subtotal,
        t.diskon,
        t.total,
        t.pembayaran,
        t.kembalian,
        t.metode_pembayaran,
        c.nama AS nama_pelanggan,
        u.username AS nama_kasir
    FROM transactions t

    LEFT JOIN customers c
        ON t.customer_id = c.id

    LEFT JOIN users u
        ON t.user_id = u.id
"""

params = []

if search.strip():

    query += """
        WHERE
            CAST(t.id AS TEXT) LIKE ?
            OR c.nama LIKE ?
            OR c.no_wa LIKE ?
    """

    keyword = f"%{search.strip()}%"

    params.extend([
        keyword,
        keyword,
        keyword
    ])

query += """
    ORDER BY t.id DESC
    LIMIT ?
"""

params.append(limit)

cursor.execute(
    query,
    params
)

transactions = cursor.fetchall()

connection.close()


# =========================================================
# TAMPILKAN TRANSAKSI
# =========================================================

if not transactions:

    st.info(
        "Belum ada transaksi."
    )

else:

    st.write(
        f"Menampilkan **{len(transactions)} transaksi**."
    )

    for transaction in transactions:

        customer = (
            transaction["nama_pelanggan"]
            if transaction["nama_pelanggan"]
            else "Umum"
        )

        with st.expander(
            f"Transaksi #{transaction['id']} "
            f"— {customer} "
            f"— {rupiah(transaction['total'])}"
        ):

            col1, col2, col3 = st.columns(3)

            with col1:

                st.write(
                    f"**Tanggal**  \n"
                    f"{transaction['tanggal']}"
                )

                st.write(
                    f"**Pelanggan**  \n"
                    f"{customer}"
                )

            with col2:

                st.write(
                    f"**Kasir**  \n"
                    f"{transaction['nama_kasir']}"
                )

                st.write(
                    f"**Pembayaran**  \n"
                    f"{transaction['metode_pembayaran']}"
                )

            with col3:

                st.metric(
                    "Total",
                    rupiah(transaction["total"])
                )

            st.divider()

            # -----------------------------------------
            # DETAIL PRODUK
            # -----------------------------------------

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    p.nama_produk,
                    td.qty,
                    td.harga,
                    td.subtotal
                FROM transaction_details td

                JOIN products p
                    ON td.product_id = p.id

                WHERE td.transaction_id = ?

                ORDER BY td.id
            """, (
                transaction["id"],
            ))

            details = cursor.fetchall()

            connection.close()

            st.write("**Detail Produk**")

            for detail in details:

                st.write(
                    f"{detail['nama_produk']} — "
                    f"{detail['qty']} x "
                    f"{rupiah(detail['harga'])} = "
                    f"**{rupiah(detail['subtotal'])}**"
                )

            st.divider()

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"Subtotal: "
                    f"**{rupiah(transaction['subtotal'])}**"
                )

                st.write(
                    f"Diskon: "
                    f"**{rupiah(transaction['diskon'])}**"
                )

            with col2:

                st.write(
                    f"Pembayaran: "
                    f"**{rupiah(transaction['pembayaran'])}**"
                )

                st.write(
                    f"Kembalian: "
                    f"**{rupiah(transaction['kembalian'])}**"
                )