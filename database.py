import sqlite3
from pathlib import Path


# Lokasi database
BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / "risolcu.db"


def get_connection():
    """Membuat koneksi ke database SQLite."""
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def migrate_tuslah():
    """Menambahkan kolom tuslah ke tabel transactions jika belum ada."""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Cek kolom yang ada di tabel transactions
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in cursor.fetchall()]

        # Jika kolom tuslah belum ada, tambahkan ke tabel
        if "tuslah" not in columns:
            cursor.execute("""
                ALTER TABLE transactions
                ADD COLUMN tuslah REAL NOT NULL DEFAULT 0
            """)
            connection.commit()
            print("Berhasil menambahkan kolom 'tuslah' ke tabel transactions.")
    except Exception as e:
        print(f"Gagal melakukan migrasi tuslah: {e}")
    finally:
        connection.close()


def create_tables():
    """Membuat seluruh tabel database Risolcu."""

    connection = get_connection()
    cursor = connection.cursor()

    # ==========================================
    # TABEL USERS
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'kasir',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ==========================================
    # TABEL PRODUCTS
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_produk TEXT NOT NULL,
            kategori TEXT,
            harga_modal REAL NOT NULL DEFAULT 0,
            harga_jual REAL NOT NULL DEFAULT 0,
            stok INTEGER NOT NULL DEFAULT 0,
            stok_minimum INTEGER NOT NULL DEFAULT 5,
            status INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ==========================================
    # TABEL CUSTOMERS
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            alamat TEXT,
            no_wa TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ==========================================
    # TABEL TRANSACTIONS (DITAMBAHKAN KOLOM TUSLAH)
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal DATETIME DEFAULT CURRENT_TIMESTAMP,
            customer_id INTEGER,
            user_id INTEGER,
            subtotal REAL NOT NULL DEFAULT 0,
            diskon REAL NOT NULL DEFAULT 0,
            tuslah REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            pembayaran REAL NOT NULL DEFAULT 0,
            kembalian REAL NOT NULL DEFAULT 0,
            metode_pembayaran TEXT DEFAULT 'Tunai',

            FOREIGN KEY (customer_id)
                REFERENCES customers(id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    # ==========================================
    # TABEL TRANSACTION DETAILS
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            qty INTEGER NOT NULL,
            harga REAL NOT NULL,
            subtotal REAL NOT NULL,

            FOREIGN KEY (transaction_id)
                REFERENCES transactions(id),

            FOREIGN KEY (product_id)
                REFERENCES products(id)
        )
    """)

    # ==========================================
    # TABEL STOCK MOVEMENTS
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            tanggal DATETIME DEFAULT CURRENT_TIMESTAMP,
            tipe TEXT NOT NULL,
            qty INTEGER NOT NULL,
            stok_sebelum INTEGER NOT NULL,
            stok_sesudah INTEGER NOT NULL,
            keterangan TEXT,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
        )
    """)

    # ==========================================
    # TABEL PROMOS
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            nama_promo TEXT NOT NULL,
            tipe_promo TEXT NOT NULL,
            nilai REAL NOT NULL DEFAULT 0,
            mulai DATETIME,
            selesai DATETIME,
            status INTEGER NOT NULL DEFAULT 1,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
        )
    """)

    # ==========================================
    # USER ADMIN AWAL
    # ==========================================
    cursor.execute("""
        INSERT OR IGNORE INTO users
        (username, password, role)
        VALUES (?, ?, ?)
    """, ("admin", "admin123", "admin"))

    connection.commit()
    connection.close()

    # Jalankan migrasi tuslah secara otomatis
    migrate_tuslah()


if __name__ == "__main__":
    create_tables()
    print("Database Risolcu berhasil dibuat dan diperbarui!")