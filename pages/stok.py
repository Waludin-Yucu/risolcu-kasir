import streamlit as st
from database import get_connection


st.title("📦 Manajemen Stok")
st.caption("Kelola stok masuk dan stok keluar Risolcu")


def get_products():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            nama_produk,
            stok,
            stok_minimum
        FROM products
        WHERE status = 1
        ORDER BY nama_produk
    """)

    products = cursor.fetchall()

    connection.close()

    return products


def rupiah(value):

    return f"Rp{value:,.0f}".replace(",", ".")


# =====================================================
# STOK MASUK / KELUAR
# =====================================================

st.subheader("🔄 Mutasi Stok")

products = get_products()

if not products:

    st.warning(
        "Belum ada produk aktif."
    )

else:

    product_map = {}

    for product in products:

        product_map[
            product["nama_produk"]
        ] = product


    selected_name = st.selectbox(
        "Produk",
        list(product_map.keys())
    )

    selected_product = product_map[
        selected_name
    ]


    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Stok Saat Ini",
            selected_product["stok"]
        )

    with col2:

        st.metric(
            "Stok Minimum",
            selected_product["stok_minimum"]
        )


    tipe = st.radio(
        "Jenis Mutasi",
        [
            "Stok Masuk",
            "Stok Keluar"
        ],
        horizontal=True
    )


    qty = st.number_input(
        "Jumlah",
        min_value=1,
        step=1,
        value=1
    )


    keterangan = st.text_input(
        "Keterangan",
        placeholder="Contoh: Produksi hari ini"
    )


    if st.button(
        "💾 Simpan Mutasi",
        use_container_width=True
    ):

        connection = get_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                SELECT stok
                FROM products
                WHERE id = ?
            """, (
                selected_product["id"],
            ))

            current_stock = cursor.fetchone()["stok"]


            if tipe == "Stok Masuk":

                new_stock = current_stock + qty

                movement_type = "MASUK"

            else:

                if qty > current_stock:

                    st.error(
                        f"Stok tidak mencukupi. "
                        f"Stok tersedia: {current_stock}"
                    )

                    connection.close()

                    st.stop()

                new_stock = current_stock - qty

                movement_type = "KELUAR"


            # Update produk
            cursor.execute("""
                UPDATE products
                SET stok = ?
                WHERE id = ?
            """, (
                new_stock,
                selected_product["id"]
            ))


            # Catat histori
            cursor.execute("""
                INSERT INTO stock_movements (
                    product_id,
                    tipe,
                    qty,
                    stok_sebelum,
                    stok_sesudah,
                    keterangan
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                selected_product["id"],
                movement_type,
                qty,
                current_stock,
                new_stock,
                keterangan.strip()
            ))


            connection.commit()

            st.success(
                f"Stok {selected_name} berhasil diperbarui."
            )

            st.rerun()


        except Exception as e:

            connection.rollback()

            st.error(
                f"Gagal menyimpan stok: {e}"
            )

        finally:

            connection.close()


# =====================================================
# STATUS STOK
# =====================================================

st.divider()

st.subheader("⚠️ Monitoring Stok")

products = get_products()

for product in products:

    if product["stok"] <= product["stok_minimum"]:

        st.error(
            f"⚠️ {product['nama_produk']} — "
            f"stok tinggal {product['stok']}"
        )

    else:

        st.success(
            f"✓ {product['nama_produk']} — "
            f"stok {product['stok']}"
        )


# =====================================================
# RIWAYAT MUTASI
# =====================================================

st.divider()

st.subheader("📜 Riwayat Mutasi Stok")

connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
    SELECT
        sm.tanggal,
        p.nama_produk,
        sm.tipe,
        sm.qty,
        sm.stok_sebelum,
        sm.stok_sesudah,
        sm.keterangan
    FROM stock_movements sm

    JOIN products p
        ON sm.product_id = p.id

    ORDER BY sm.id DESC
    LIMIT 100
""")

movements = cursor.fetchall()

connection.close()


if not movements:

    st.info(
        "Belum ada riwayat mutasi."
    )

else:

    for movement in movements:

        if movement["tipe"] == "MASUK":

            icon = "🟢"

        else:

            icon = "🔴"

        st.write(
            f"{icon} **{movement['nama_produk']}** | "
            f"{movement['tipe']} {movement['qty']} | "
            f"{movement['stok_sebelum']} → "
            f"{movement['stok_sesudah']} | "
            f"{movement['keterangan'] or '-'} | "
            f"{movement['tanggal']}"
        )