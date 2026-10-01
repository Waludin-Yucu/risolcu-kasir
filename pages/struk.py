import streamlit as st
from database import get_connection

st.title("🧾 Struk Pembayaran")
st.caption("Cetak atau simpan bukti transaksi")

# =========================================================
# FORMAT RUPIAH
# =========================================================
def rupiah(value):
    return f"Rp{value:,.0f}".replace(",", ".")

# =========================================================
# AMBIL ID TRANSAKSI
# =========================================================
# Ambil dari query parameter jika ada, atau dari session state transaksi terakhir
query_params = st.query_params
transaction_id = query_params.get("id", st.session_state.get("last_transaction_id"))

if not transaction_id:
    st.warning("Belum ada transaksi yang dipilih atau diproses.")
    st.info("Silakan lakukan transaksi di menu Kasir atau pilih transaksi dari menu Riwayat.")
    st.stop()

# Convert ID ke integer jika berupa string
try:
    transaction_id = int(transaction_id)
except ValueError:
    st.error("ID Transaksi tidak valid.")
    st.stop()

# =========================================================
# AMBIL DATA TRANSAKSI DARI DATABASE
# =========================================================
connection = get_connection()
cursor = connection.cursor()

# Detail Header Transaksi
cursor.execute("""
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
        c.no_wa,
        u.username AS nama_kasir
    FROM transactions t
    LEFT JOIN customers c ON t.customer_id = c.id
    LEFT JOIN users u ON t.user_id = u.id
    WHERE t.id = ?
""", (transaction_id,))

tx = cursor.fetchone()

if not tx:
    st.error(f"Transaksi #{transaction_id} tidak ditemukan.")
    connection.close()
    st.stop()

# Detail Item Transaksi
cursor.execute("""
    SELECT 
        p.nama_produk,
        td.qty,
        td.harga,
        td.subtotal
    FROM transaction_details td
    JOIN products p ON td.product_id = p.id
    WHERE td.transaction_id = ?
""", (transaction_id,))

items = cursor.fetchall()
connection.close()

# =========================================================
# TAMPILAN STRUK
# =========================================================
col1, col2 = st.columns([1, 1])

with col1:
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center;'>🍴 RISOLCU</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 12px;'>Jl. Contoh No. 123 | WA: 0812-3456-7890</p>", unsafe_allow_html=True)
        st.divider()

        # Info Transaksi
        st.write(f"**No. Transaksi:** #{tx['id']}")
        st.write(f"**Tanggal:** {tx['tanggal']}")
        st.write(f"**Kasir:** {tx['nama_kasir'] if tx['nama_kasir'] else '-'}")
        st.write(f"**Pelanggan:** {tx['nama_pelanggan'] if tx['nama_pelanggan'] else 'Umum'}")
        st.divider()

        # Daftar Item
        for item in items:
            st.write(f"**{item['nama_produk']}**")
            c_qty, c_sub = st.columns([2, 2])
            with c_qty:
                st.caption(f"{item['qty']} x {rupiah(item['harga'])}")
            with c_sub:
                st.write(f"**{rupiah(item['subtotal'])}**")

        st.divider()

        # Total Perhitungan
        st.write(f"Subtotal: **{rupiah(tx['subtotal'])}**")
        if tx['diskon'] > 0:
            st.write(f"Diskon: **-{rupiah(tx['diskon'])}**")
        st.markdown(f"### Total: {rupiah(tx['total'])}")
        st.write(f"Metode: **{tx['metode_pembayaran']}**")
        st.write(f"Bayar: **{rupiah(tx['pembayaran'])}**")
        st.write(f"Kembali: **{rupiah(tx['kembalian'])}**")

        st.divider()
        st.markdown("<p style='text-align: center; font-size: 13px;'>-- Terima Kasih & Selamat Menikmati! --</p>", unsafe_allow_html=True)

with col2:
    st.subheader("⚙️ Aksi")
    
    # Tombol Transaksi Baru
    if st.button("➕ Transaksi Baru", use_container_width=True, type="primary"):
        st.session_state.last_transaction_id = None
        st.switch_page("pages/kasir.py")

    # Format Teks untuk Cetak / Salin
    struk_text = f"""
================================
            RISOLCU
================================
No. Tx : #{tx['id']}
Tgl    : {tx['tanggal']}
Kasir  : {tx['nama_kasir'] if tx['nama_kasir'] else '-'}
Plg    : {tx['nama_pelanggan'] if tx['nama_pelanggan'] else 'Umum'}
--------------------------------
"""
    for item in items:
        struk_text += f"{item['nama_produk']}\n  {item['qty']} x {rupiah(item['harga'])} = {rupiah(item['subtotal'])}\n"

    struk_text += f"""--------------------------------
Subtotal : {rupiah(tx['subtotal'])}
Diskon   : {rupiah(tx['diskon'])}
Total    : {rupiah(tx['total'])}
Metode   : {tx['metode_pembayaran']}
Bayar    : {rupiah(tx['pembayaran'])}
Kembali  : {rupiah(tx['kembalian'])}
================================
  Terima Kasih Atas Kunjungannya!
"""

    st.download_button(
        label="📥 Download Struk (.txt)",
        data=struk_text,
        file_name=f"Struk_Risolcu_{tx['id']}.txt",
        mime="text/plain",
        use_container_width=True
    )