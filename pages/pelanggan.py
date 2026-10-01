import streamlit as st
from database import get_connection


st.title("👥 Data Pelanggan")
st.caption("Kelola data pelanggan Risolcu")


def rupiah(value):
    return f"Rp{value:,.0f}".replace(",", ".")


# =====================================================
# TAMBAH PELANGGAN
# =====================================================

with st.expander("➕ Tambah Pelanggan"):

    nama = st.text_input(
        "Nama Pelanggan",
        key="customer_name"
    )

    no_wa = st.text_input(
        "No. WhatsApp",
        key="customer_wa"
    )

    alamat = st.text_area(
        "Alamat",
        key="customer_address"
    )

    if st.button(
        "💾 Simpan Pelanggan",
        use_container_width=True
    ):

        if not nama.strip():

            st.error("Nama pelanggan wajib diisi.")

        else:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO customers
                (nama, alamat, no_wa)
                VALUES (?, ?, ?)
            """, (
                nama.strip(),
                alamat.strip(),
                no_wa.strip()
            ))

            connection.commit()
            connection.close()

            st.success(
                f"Pelanggan {nama} berhasil ditambahkan."
            )

            st.rerun()


# =====================================================
# PENCARIAN
# =====================================================

st.divider()

search = st.text_input(
    "🔎 Cari pelanggan",
    placeholder="Nama atau nomor WhatsApp"
)


# =====================================================
# DATA PELANGGAN
# =====================================================

connection = get_connection()
cursor = connection.cursor()

if search.strip():

    keyword = f"%{search.strip()}%"

    cursor.execute("""
        SELECT *
        FROM customers
        WHERE nama LIKE ?
           OR no_wa LIKE ?
        ORDER BY nama
    """, (
        keyword,
        keyword
    ))

else:

    cursor.execute("""
        SELECT *
        FROM customers
        ORDER BY nama
    """)


customers = cursor.fetchall()

connection.close()


# =====================================================
# TAMPILKAN DATA
# =====================================================

if not customers:

    st.info("Belum ada pelanggan.")

else:

    for customer in customers:

        # Ambil statistik pembelian
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS jumlah_transaksi,
                COALESCE(SUM(total), 0) AS total_belanja
            FROM transactions
            WHERE customer_id = ?
        """, (
            customer["id"],
        ))

        stats = cursor.fetchone()

        connection.close()

        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [3, 3, 2]
            )

            with col1:

                st.subheader(
                    customer["nama"]
                )

                if customer["no_wa"]:
                    st.write(
                        f"📱 {customer['no_wa']}"
                    )

                if customer["alamat"]:
                    st.caption(
                        customer["alamat"]
                    )

            with col2:

                st.write(
                    f"Transaksi: "
                    f"**{stats['jumlah_transaksi']}x**"
                )

                st.write(
                    f"Total belanja: "
                    f"**{rupiah(stats['total_belanja'])}**"
                )

            with col3:

                if stats["jumlah_transaksi"] > 0:

                    rata = (
                        stats["total_belanja"]
                        / stats["jumlah_transaksi"]
                    )

                    st.metric(
                        "Rata-rata transaksi",
                        rupiah(rata)
                    )

                else:

                    st.metric(
                        "Rata-rata transaksi",
                        "Rp0"
                    )