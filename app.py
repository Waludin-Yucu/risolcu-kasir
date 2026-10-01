import streamlit as st

from database import create_tables
from auth import login


# ==========================================
# DATABASE
# ==========================================

create_tables()


# ==========================================
# KONFIGURASI HALAMAN
# ==========================================

st.set_page_config(
    page_title="Risolcu",
    page_icon="🍴",
    layout="wide"
)


# ==========================================
# FUNGSI LOGIN
# ==========================================

def show_login():

    st.title("🍴 Risolcu")

    st.subheader("Sistem Manajemen Penjualan")

    st.divider()

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    login_button = st.button(
        "🔐 Masuk",
        use_container_width=True
    )

    if login_button:

        user = login(
            username,
            password
        )

        if user:

            st.session_state.logged_in = True
            st.session_state.user = user

            st.success(
                "Login berhasil!"
            )

            st.rerun()

        else:

            st.error(
                "Username atau password salah."
            )


# ==========================================
# DASHBOARD
# ==========================================

def show_dashboard():

    user = st.session_state.user

    st.title("📊 Dashboard Risolcu")

    st.write(
        f"Selamat datang, **{user['username']}**"
    )

    st.write(
        f"Role: **{user['role']}**"
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Omzet Hari Ini",
            "Rp0"
        )

    with col2:
        st.metric(
            "Transaksi Hari Ini",
            "0"
        )

    with col3:
        st.metric(
            "Produk Terjual",
            "0"
        )

    with col4:
        st.metric(
            "Pelanggan",
            "0"
        )

    st.divider()

    st.subheader(
        "📈 Grafik Penjualan"
    )

    st.info(
        "Grafik akan kita hubungkan dengan data transaksi pada tahap berikutnya."
    )

    st.divider()

    if st.button("🚪 Keluar"):

        st.session_state.logged_in = False
        st.session_state.user = None

        st.rerun()


# ==========================================
# SESSION STATE
# ==========================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if "user" not in st.session_state:

    st.session_state.user = None


# ==========================================
# ROUTING
# ==========================================

if st.session_state.logged_in:

    show_dashboard()

else:

    show_login()