import streamlit as st
from database import get_connection


# =========================================================
# KONFIGURASI & ENSURE TUSLAH (LANGKAH 4)
# =========================================================

st.title("🛒 Kasir Risolcu")
st.caption("Pencatatan transaksi penjualan")


def ensure_tuslah_column():
    """Memastikan kolom tuslah ada di tabel transactions."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        if "tuslah" not in columns:
            cursor.execute("""
                ALTER TABLE transactions
                ADD COLUMN tuslah REAL NOT NULL DEFAULT 0
            """)
            connection.commit()
    except Exception as e:
        st.warning(f"Gagal memeriksa kolom tuslah: {e}")
    finally:
        connection.close()


# Jalankan verifikasi struktur database
ensure_tuslah_column()


# =========================================================
# SESSION STATE
# =========================================================

if "last_transaction_id" not in st.session_state:
    st.session_state.last_transaction_id = None

if "last_transaction_total" not in st.session_state:
    st.session_state.last_transaction_total = 0

if "last_transaction_payment" not in st.session_state:
    st.session_state.last_transaction_payment = 0

if "last_transaction_change" not in st.session_state:
    st.session_state.last_transaction_change = 0

if "cart" not in st.session_state:
    st.session_state.cart = []

if "selected_customer" not in st.session_state:
    st.session_state.selected_customer = None

if "show_customer_form" not in st.session_state:
    st.session_state.show_customer_form = False

if "transaction_success" not in st.session_state:
    st.session_state.transaction_success = None


# =========================================================
# FUNGSI FORMAT RUPIAH
# =========================================================

def rupiah(value):
    return f"Rp{value:,.0f}".replace(",", ".")


# =========================================================
# AMBIL DATA PRODUK
# =========================================================

def get_products():
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
            stok_minimum
        FROM products
        WHERE status = 1
        ORDER BY nama_produk
    """)

    products = cursor.fetchall()
    connection.close()

    return products


# =========================================================
# AMBIL DATA PELANGGAN
# =========================================================

def get_customers():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            nama,
            alamat,
            no_wa
        FROM customers
        ORDER BY nama
    """)

    customers = cursor.fetchall()
    connection.close()

    return customers


# =========================================================
# TAMBAH PELANGGAN
# =========================================================

def add_customer(nama, alamat, no_wa):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO customers (
                nama,
                alamat,
                no_wa
            )
            VALUES (?, ?, ?)
        """, (
            nama,
            alamat,
            no_wa
        ))

        customer_id = cursor.lastrowid
        connection.commit()
        return customer_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# TAMBAH PRODUK KE KERANJANG
# =========================================================

def add_to_cart(product, qty):
    product_id = product["id"]

    # Cek apakah produk sudah ada di keranjang
    for item in st.session_state.cart:
        if item["product_id"] == product_id:
            new_qty = item["qty"] + qty

            # Jangan melebihi stok
            if new_qty > product["stok"]:
                st.error(
                    f"Stok {product['nama_produk']} hanya "
                    f"{product['stok']}."
                )
                return

            item["qty"] = new_qty
            item["subtotal"] = new_qty * item["harga"]
            return

    # Produk baru
    st.session_state.cart.append({
        "product_id": product["id"],
        "nama_produk": product["nama_produk"],
        "harga": product["harga_jual"],
        "harga_modal": product["harga_modal"],
        "qty": qty,
        "subtotal": product["harga_jual"] * qty
    })


# =========================================================
# HAPUS PRODUK DARI KERANJANG
# =========================================================

def remove_from_cart(index):
    st.session_state.cart.pop(index)


# =========================================================
# UPDATE QTY
# =========================================================

def update_qty(index, new_qty):
    item = st.session_state.cart[index]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT stok
        FROM products
        WHERE id = ?
    """, (item["product_id"],))

    product = cursor.fetchone()
    connection.close()

    if product is None:
        return

    if new_qty <= 0:
        remove_from_cart(index)
    elif new_qty > product["stok"]:
        st.error(
            f"Stok hanya tersedia {product['stok']}."
        )
    else:
        item["qty"] = new_qty
        item["subtotal"] = new_qty * item["harga"]


# =========================================================
# HASIL TRANSAKSI TERAKHIR
# =========================================================

if st.session_state.transaction_success:
    result = st.session_state.transaction_success

    st.success(
        f"Transaksi #{result['id']} berhasil disimpan. "
        f"Total {rupiah(result['total'])}."
    )

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.metric("Total", rupiah(result["total"]))

    with col_b:
        st.metric("Dibayar", rupiah(result["pembayaran"]))

    with col_c:
        st.metric("Kembalian", rupiah(result["kembalian"]))

    if st.button("🧾 Selesaikan / Transaksi Baru"):
        st.session_state.transaction_success = None
        st.session_state.selected_customer = None
        st.rerun()


# =========================================================
# HEADER PELANGGAN
# =========================================================

st.subheader("👤 Pelanggan")

customers = get_customers()

customer_options = {
    "Umum": None
}

for customer in customers:
    label = customer["nama"]
    if customer["no_wa"]:
        label += f" - {customer['no_wa']}"
    customer_options[label] = customer["id"]

col1, col2 = st.columns([4, 1])

with col1:
    selected_customer_label = st.selectbox(
        "Pilih Pelanggan",
        options=list(customer_options.keys())
    )
    st.session_state.selected_customer = customer_options[selected_customer_label]

with col2:
    st.write("")
    if st.button(
        "➕ Pelanggan Baru",
        use_container_width=True
    ):
        st.session_state.show_customer_form = True


# =========================================================
# FORM PELANGGAN BARU
# =========================================================

if st.session_state.get("show_customer_form", False):
    with st.container(border=True):
        st.subheader("Tambah Pelanggan")

        new_name = st.text_input("Nama Pelanggan")
        new_wa = st.text_input("No. WhatsApp")
        new_address = st.text_area("Alamat")

        col1, col2 = st.columns(2)

        with col1:
            save_customer = st.button(
                "💾 Simpan",
                use_container_width=True
            )

        with col2:
            cancel_customer = st.button(
                "Batal",
                use_container_width=True
            )

        if cancel_customer:
            st.session_state.show_customer_form = False
            st.rerun()

        if save_customer:
            if not new_name.strip():
                st.error("Nama pelanggan wajib diisi.")
            else:
                customer_id = add_customer(
                    new_name.strip(),
                    new_address.strip(),
                    new_wa.strip()
                )
                st.session_state.selected_customer = customer_id
                st.session_state.show_customer_form = False
                st.success(
                    f"Pelanggan {new_name.strip()} berhasil ditambahkan "
                    "dan langsung dipilih untuk transaksi."
                )
                st.rerun()

st.divider()


# =========================================================
# PILIH PRODUK
# =========================================================

st.subheader("🍴 Tambahkan Produk")

products = get_products()

if not products:
    st.warning(
        "Belum ada produk aktif. "
        "Tambahkan produk terlebih dahulu "
        "di menu Produk."
    )
else:
    product_options = {}

    for product in products:
        label = (
            f"{product['nama_produk']} "
            f"— {rupiah(product['harga_jual'])} "
            f"(stok {product['stok']})"
        )
        product_options[label] = product

    col1, col2 = st.columns([4, 1])

    with col1:
        selected_product_label = st.selectbox(
            "Produk",
            options=list(product_options.keys())
        )
        selected_product = product_options[selected_product_label]

    with col2:
        max_qty = int(selected_product["stok"])

        if max_qty > 0:
            qty = st.number_input(
                "Qty",
                min_value=1,
                max_value=max_qty,
                value=1,
                step=1
            )
        else:
            qty = 0
            st.number_input(
                "Qty",
                min_value=1,
                max_value=1,
                value=1,
                step=1,
                disabled=True
            )

    if selected_product["stok"] <= 0:
        st.error("Produk ini sedang habis.")
    else:
        if st.button(
            "➕ Tambahkan ke Keranjang",
            use_container_width=True,
            disabled=(selected_product["stok"] <= 0)
        ):
            add_to_cart(selected_product, qty)
            st.rerun()


# =========================================================
# KERANJANG
# =========================================================

st.divider()

st.subheader("🛍️ Keranjang")

if not st.session_state.cart:
    st.info("Keranjang masih kosong.")
else:
    for index, item in enumerate(st.session_state.cart):
        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])

            with col1:
                st.write(f"**{item['nama_produk']}**")

            with col2:
                new_qty = st.number_input(
                    "Qty",
                    min_value=1,
                    value=item["qty"],
                    step=1,
                    key=f"qty_{index}"
                )

            with col3:
                st.write("Harga")
                st.write(rupiah(item["harga"]))

            with col4:
                st.write("Subtotal")
                st.write(rupiah(item["subtotal"]))

            with col5:
                if st.button("🗑️", key=f"delete_{index}"):
                    remove_from_cart(index)
                    st.rerun()

            # Update qty jika berubah
            if new_qty != item["qty"]:
                update_qty(index, new_qty)
                st.rerun()


# =========================================================
# PERHITUNGAN TRANSAKSI (LANGKAH 5 & 6)
# =========================================================

if st.session_state.cart:
    subtotal = sum(item["subtotal"] for item in st.session_state.cart)

    st.divider()
    st.subheader("💰 Pembayaran")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Subtotal", rupiah(subtotal))

        diskon = st.number_input(
            "Diskon",
            min_value=0,
            max_value=int(subtotal),
            value=0,
            step=500
        )

        tuslah = st.number_input(
            "Tuslah / Biaya Tambahan",
            min_value=0,
            value=0,
            step=500
        )

        total = subtotal - diskon + tuslah

    with col2:
        st.metric("TOTAL", rupiah(total))

        # Tampilan rincian tambahan (Langkah 6)
        if diskon > 0 or tuslah > 0:
            st.caption(f"Termasuk Diskon: -{rupiah(diskon)} | Tuslah: +{rupiah(tuslah)}")

        metode = st.selectbox(
            "Metode Pembayaran",
            ["Tunai", "QRIS", "Transfer"]
        )

        if metode == "Tunai":
            pembayaran = st.number_input(
                "Jumlah Bayar",
                min_value=0,
                value=int(total),
                step=1000
            )

            kembalian = pembayaran - total

            if pembayaran < total:
                st.error(f"Uang pembayaran kurang {rupiah(total - pembayaran)}")
            else:
                st.success(f"Kembalian: {rupiah(kembalian)}")
        else:
            pembayaran = total
            kembalian = 0
            st.info(f"Pembayaran {metode}: {rupiah(total)}")

    # =========================================================
    # SIMPAN TRANSAKSI (LANGKAH 7)
    # =========================================================

    st.divider()

    if st.button(
        "💳 PROSES PEMBAYARAN",
        use_container_width=True,
        type="primary"
    ):
        # Validasi pembayaran tunai
        if metode == "Tunai" and pembayaran < total:
            st.error("Pembayaran belum mencukupi.")
            st.stop()

        connection = get_connection()
        cursor = connection.cursor()

        try:
            # ------------------------------------------
            # CEK STOK TERAKHIR
            # ------------------------------------------
            for item in st.session_state.cart:
                cursor.execute("""
                    SELECT
                        stok,
                        nama_produk
                    FROM products
                    WHERE id = ?
                """, (item["product_id"],))

                product = cursor.fetchone()

                if product is None:
                    raise Exception(f"Produk {item['nama_produk']} tidak ditemukan.")

                if product["stok"] < item["qty"]:
                    raise Exception(
                        f"Stok {product['nama_produk']} tidak mencukupi. "
                        f"Tersedia {product['stok']}."
                    )

            # ------------------------------------------
            # SIMPAN TRANSAKSI
            # ------------------------------------------
            user_id = None

            if st.session_state.get("user"):
                user_id = st.session_state.user.get("id")

            cursor.execute("""
                INSERT INTO transactions (
                    customer_id,
                    user_id,
                    subtotal,
                    diskon,
                    tuslah,
                    total,
                    pembayaran,
                    kembalian,
                    metode_pembayaran
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                st.session_state.selected_customer,
                user_id,
                subtotal,
                diskon,
                tuslah,
                total,
                pembayaran,
                kembalian,
                metode
            ))

            transaction_id = cursor.lastrowid

            # ------------------------------------------
            # SIMPAN DETAIL & KURANGI STOK
            # ------------------------------------------
            for item in st.session_state.cart:
                cursor.execute("""
                    INSERT INTO transaction_details (
                        transaction_id,
                        product_id,
                        qty,
                        harga,
                        subtotal
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    transaction_id,
                    item["product_id"],
                    item["qty"],
                    item["harga"],
                    item["subtotal"]
                ))

                # Ambil stok saat ini
                cursor.execute("""
                    SELECT stok
                    FROM products
                    WHERE id = ?
                """, (item["product_id"],))

                current_stock = cursor.fetchone()["stok"]
                new_stock = current_stock - item["qty"]

                # Update stok
                cursor.execute("""
                    UPDATE products
                    SET stok = ?
                    WHERE id = ?
                """, (new_stock, item["product_id"]))

                # Catat mutasi stok
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
                    item["product_id"],
                    "KELUAR",
                    item["qty"],
                    current_stock,
                    new_stock,
                    f"Penjualan #{transaction_id}"
                ))

            connection.commit()

            st.session_state.transaction_success = {
                "id": transaction_id,
                "total": total,
                "pembayaran": pembayaran,
                "kembalian": kembalian,
                "customer_id": st.session_state.selected_customer
            }

            # Kosongkan keranjang & simpan ID transaksi terakhir
            st.session_state.last_transaction_id = transaction_id
            st.session_state.last_transaction_total = total
            st.session_state.last_transaction_payment = pembayaran
            st.session_state.last_transaction_change = kembalian

            st.session_state.cart = []
            st.rerun()

        except Exception as e:
            connection.rollback()
            st.error(f"Transaksi gagal: {e}")

        finally:
            connection.close()