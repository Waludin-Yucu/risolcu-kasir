import streamlit as st
from database import get_connection


st.title("📦 Manajemen Produk")
st.write("Kelola produk, harga, stok, dan status produk Risolcu.")
st.divider()


# ==================================================
# FUNGSI TAMBAH PRODUK
# ==================================================

def tambah_produk(
    nama_produk,
    kategori,
    harga_modal,
    harga_jual,
    stok,
    stok_minimum
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO products (
            nama_produk,
            kategori,
            harga_modal,
            harga_jual,
            stok,
            stok_minimum
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        nama_produk,
        kategori,
        harga_modal,
        harga_jual,
        stok,
        stok_minimum
    ))

    product_id = cursor.lastrowid

    # Catat stok awal
    if stok > 0:
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
            product_id,
            "MASUK",
            stok,
            0,
            stok,
            "Stok awal produk"
        ))

    connection.commit()
    connection.close()


# ==================================================
# FUNGSI UPDATE HARGA JUAL (DITAMBAHKAN DI SINI)
# ==================================================

def update_harga_jual(product_id, harga_jual_baru):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE products
            SET harga_jual = ?
            WHERE id = ?
        """, (harga_jual_baru, product_id))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# ==================================================
# FORM TAMBAH PRODUK
# ==================================================

with st.expander("➕ Tambah Produk", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        nama_produk = st.text_input(
            "Nama Produk",
            placeholder="Contoh: Ayam Suir Pedas"
        )
        kategori = st.text_input(
            "Kategori",
            value="Risol"
        )
        harga_modal = st.number_input(
            "Harga Modal",
            min_value=0,
            step=500,
            value=0
        )

    with col2:
        harga_jual = st.number_input(
            "Harga Jual",
            min_value=0,
            step=500,
            value=10000
        )
        stok = st.number_input(
            "Stok Awal",
            min_value=0,
            step=1,
            value=0
        )
        stok_minimum = st.number_input(
            "Batas Minimum Stok",
            min_value=0,
            step=1,
            value=5
        )

    simpan = st.button(
        "💾 Simpan Produk",
        use_container_width=True
    )

    if simpan:
        if not nama_produk.strip():
            st.error("Nama produk wajib diisi.")
        elif harga_jual <= 0:
            st.error("Harga jual harus lebih dari 0.")
        else:
            tambah_produk(
                nama_produk.strip(),
                kategori.strip(),
                harga_modal,
                harga_jual,
                stok,
                stok_minimum
            )
            st.success(f"Produk '{nama_produk}' berhasil ditambahkan.")
            st.rerun()


# ==================================================
# DAFTAR PRODUK
# ==================================================

st.divider()
st.subheader("📋 Daftar Produk")

connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
    SELECT
        id,
        nama_produk,
        kategori,
        harga_modal,
        harga_jual,
        stok,
        stok_minimum,
        status
    FROM products
    ORDER BY id DESC
""")

products = cursor.fetchall()
connection.close()


if not products:
    st.info("Belum ada produk. Silakan tambahkan produk.")
else:
    for product in products:
        with st.container(border=True):
            # Diubah dari 4 kolom menjadi 5 kolom agar ada area untuk tombol Edit
            col1, col2, col3, col4, col5 = st.columns([2.5, 2, 1.5, 1, 1.5])

            with col1:
                st.write(f"### {product['nama_produk']}")
                st.caption(f"Kategori: {product['kategori']}")

            with col2:
                st.write(
                    f"Harga Jual: **Rp{product['harga_jual']:,.0f}**"
                    .replace(",", ".")
                )
                st.write(
                    f"Modal: Rp{product['harga_modal']:,.0f}"
                    .replace(",", ".")
                )

            with col3:
                stok = product["stok"]
                minimum = product["stok_minimum"]

                if stok <= minimum:
                    st.error(f"⚠️ Stok: {stok}")
                else:
                    st.success(f"Stok: {stok}")

            with col4:
                if product["status"] == 1:
                    st.success("Aktif")
                else:
                    st.warning("Nonaktif")

            # ==================================================
            # FITUR EDIT HARGA JUAL (DITAMBAHKAN DI SINI)
            # ==================================================
            with col5:
                if st.button("✏️ Edit", key=f"edit_harga_{product['id']}", use_container_width=True):
                    st.session_state[f"edit_harga_produk_{product['id']}"] = True

                if st.session_state.get(f"edit_harga_produk_{product['id']}", False):
                    harga_baru = st.number_input(
                        "Harga Jual Baru",
                        min_value=1,
                        value=int(product["harga_jual"]),
                        step=500,
                        key=f"input_harga_{product['id']}"
                    )
                    
                    col_simpan, col_batal = st.columns(2)
                    with col_simpan:
                        if st.button("💾", key=f"simpan_harga_{product['id']}", use_container_width=True, help="Simpan Perubahan"):
                            update_harga_jual(product["id"], harga_baru)
                            st.session_state[f"edit_harga_produk_{product['id']}"] = False
                            st.success(f"Harga {product['nama_produk']} diperbarui.")
                            st.rerun()

                    with col_batal:
                        if st.button("✖️", key=f"batal_harga_{product['id']}", use_container_width=True, help="Batal"):
                            st.session_state[f"edit_harga_produk_{product['id']}"] = False
                            st.rerun()