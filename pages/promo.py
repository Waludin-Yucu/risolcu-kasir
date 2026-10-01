import streamlit as st
from datetime import datetime

from database import get_connection


st.title("🏷️ Manajemen Promo")
st.caption("Kelola promo penjualan Risolcu")


def rupiah(value):
    return f"Rp{value:,.0f}".replace(",", ".")


# =========================================================
# AMBIL PRODUK
# =========================================================

connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
    SELECT
        id,
        nama_produk,
        harga_jual
    FROM products
    WHERE status = 1
    ORDER BY nama_produk
""")

products = cursor.fetchall()

connection.close()


# =========================================================
# TAMBAH PROMO
# =========================================================

with st.expander("➕ Tambah Promo", expanded=True):

    if not products:

        st.warning(
            "Belum ada produk aktif. "
            "Tambahkan produk terlebih dahulu."
        )

    else:

        product_options = {
            "Semua Produk": None
        }

        for product in products:

            product_options[
                product["nama_produk"]
            ] = product["id"]


        nama_promo = st.text_input(
            "Nama Promo",
            placeholder="Contoh: Promo Weekend"
        )


        selected_product = st.selectbox(
            "Produk",
            list(product_options.keys())
        )

        product_id = product_options[
            selected_product
        ]


        tipe_promo = st.selectbox(
            "Jenis Promo",
            [
                "Diskon Persen",
                "Diskon Nominal",
                "Harga Khusus"
            ]
        )


        if tipe_promo == "Diskon Persen":

            nilai = st.number_input(
                "Diskon (%)",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=1.0
            )

        else:

            nilai = st.number_input(
                "Nilai Promo (Rp)",
                min_value=0.0,
                value=1000.0,
                step=500.0
            )


        col1, col2 = st.columns(2)

        with col1:

            tanggal_mulai = st.date_input(
                "Tanggal Mulai"
            )

        with col2:

            tanggal_selesai = st.date_input(
                "Tanggal Selesai"
            )


        aktif = st.checkbox(
            "Aktifkan promo",
            value=True
        )


        if st.button(
            "💾 Simpan Promo",
            use_container_width=True
        ):

            if not nama_promo.strip():

                st.error(
                    "Nama promo wajib diisi."
                )

            elif tanggal_selesai < tanggal_mulai:

                st.error(
                    "Tanggal selesai tidak boleh "
                    "lebih awal dari tanggal mulai."
                )

            elif nilai <= 0:

                st.error(
                    "Nilai promo harus lebih dari 0."
                )

            else:

                mulai = (
                    f"{tanggal_mulai} 00:00:00"
                )

                selesai = (
                    f"{tanggal_selesai} 23:59:59"
                )

                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute("""
                    INSERT INTO promos (
                        product_id,
                        nama_promo,
                        tipe_promo,
                        nilai,
                        mulai,
                        selesai,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id,
                    nama_promo.strip(),
                    tipe_promo,
                    nilai,
                    mulai,
                    selesai,
                    1 if aktif else 0
                ))

                connection.commit()
                connection.close()

                st.success(
                    f"Promo '{nama_promo}' berhasil dibuat."
                )

                st.rerun()


# =========================================================
# DAFTAR PROMO
# =========================================================

st.divider()

st.subheader("📋 Daftar Promo")


connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
    SELECT
        p.id,
        p.nama_promo,
        p.tipe_promo,
        p.nilai,
        p.mulai,
        p.selesai,
        p.status,
        pr.nama_produk
    FROM promos p

    LEFT JOIN products pr
        ON p.product_id = pr.id

    ORDER BY p.id DESC
""")

promos = cursor.fetchall()

connection.close()


if not promos:

    st.info(
        "Belum ada promo."
    )

else:

    for promo in promos:

        produk = (
            promo["nama_produk"]
            if promo["nama_produk"]
            else "Semua Produk"
        )

        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [3, 3, 1]
            )

            with col1:

                st.subheader(
                    promo["nama_promo"]
                )

                st.write(
                    f"Produk: **{produk}**"
                )

            with col2:

                if promo["tipe_promo"] == "Diskon Persen":

                    nilai_promo = (
                        f"{promo['nilai']:.0f}%"
                    )

                else:

                    nilai_promo = rupiah(
                        promo["nilai"]
                    )

                st.write(
                    f"Promo: **{promo['tipe_promo']} "
                    f"{nilai_promo}**"
                )

                st.caption(
                    f"{promo['mulai']} → "
                    f"{promo['selesai']}"
                )

            with col3:

                if promo["status"] == 1:

                    st.success("AKTIF")

                else:

                    st.warning("NONAKTIF")