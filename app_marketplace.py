"""
╔══════════════════════════════════════════════════════════════════════╗
║           MobilNiaga - Marketplace Dashboard (Buyer-Facing)          ║
║           Berkomunikasi dengan: Marketplace API (:8001)              ║
╚══════════════════════════════════════════════════════════════════════╝

Jalankan dengan: streamlit run app_marketplace.py
"""

import streamlit as st
import requests
import pandas as pd

# ─── Konfigurasi ──────────────────────────────────────────────────────────────
API_MARKET = "http://localhost:8001"

# ─── Helper Functions ─────────────────────────────────────────────────────────

def api_post(url: str, payload: dict) -> dict | None:
    """Mengirim POST request dan mengembalikan JSON response, atau None jika error."""
    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        st.error("❌ Tidak dapat terhubung ke server. Pastikan API sudah berjalan.")
    except requests.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        st.error(f"❌ Error dari server: {detail}")
    return None

def api_get(url: str) -> list | dict | None:
    """Mengirim GET request dan mengembalikan JSON response, atau None jika error."""
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        st.error("❌ Tidak dapat terhubung ke server. Pastikan API sudah berjalan.")
    except requests.HTTPError as e:
        detail = e.response.json().get("detail", str(e)) if e.response else str(e)
        st.error(f"❌ Error dari server: {detail}")
    return None

def format_rupiah(value: float) -> str:
    """Format angka ke format Rupiah (Rp 1.000.000)."""
    return f"Rp {value:,.0f}".replace(",", ".")

def get_status_badge(status: str) -> str:
    """Mengembalikan HTML badge berwarna berdasarkan status pesanan."""
    color_map = {
        "CREATED":   ("🟡", "#fef3c7", "#92400e"),
        "SHIPPED":   ("🔵", "#dbeafe", "#1e40af"),
        "DELIVERED": ("🟢", "#d1fae5", "#065f46"),
        "CANCELLED": ("🔴", "#fee2e2", "#991b1b"),
    }
    emoji, bg, fg = color_map.get(status.upper(), ("⚪", "#f3f4f6", "#374151"))
    return f'<span style="background:{bg};color:{fg};padding:3px 10px;border-radius:999px;font-size:0.8rem;font-weight:600">{emoji} {status}</span>'


# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MobilNiaga — Marketplace",
    page_icon="🚙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Header gradien marketplace */
    .main-header {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .main-header p  { color: rgba(255,255,255,0.85); margin: 0.3rem 0 0; font-size: 0.95rem; }

    /* Card mobil di hasil pencarian */
    .car-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        transition: box-shadow 0.2s;
    }
    .car-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .car-brand  { font-size: 0.8rem; color: #718096; text-transform: uppercase; letter-spacing: 0.05em; }
    .car-model  { font-size: 1.1rem; font-weight: 700; color: #1a202c; margin: 0.15rem 0; }
    .car-price  { font-size: 1rem; font-weight: 600; color: #d97706; }
    .car-seller { font-size: 0.8rem; color: #a0aec0; }

    /* Info card */
    .info-card {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        font-size: 0.88rem;
        color: #78350f;
    }

    /* Order detail card */
    .order-detail {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.25rem;
    }
    .order-row { display: flex; justify-content: space-between; padding: 0.35rem 0; border-bottom: 1px solid #edf2f7; }
    .order-row:last-child { border-bottom: none; }
    .order-label { color: #718096; font-size: 0.9rem; }
    .order-value { font-weight: 600; color: #2d3748; font-size: 0.9rem; }

    /* Section title */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e2e8f0;
    }

    /* Sembunyikan footer streamlit */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🚙 MobilNiaga Marketplace</h1>
    <p>Temukan & beli kendaraan impian Anda dengan mudah dan aman</p>
</div>
""", unsafe_allow_html=True)

# ─── Tab Navigation ───────────────────────────────────────────────────────────
TAB_LABELS = [
    "🔍 Cari Mobil",
    "🛒 Beli Mobil",
    "📦 Lacak Pesanan",
    "❌ Batalkan Pesanan",
    "📑 Laporan Settlement",
]
tabs = st.tabs(TAB_LABELS)


# ═══════════════════════════════════════════════════════════════════════════════
# [M2] Feature 4 — Pencarian Mobil
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<p class="section-title">Cari Kendaraan di Katalog</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">🔍 Ketik nama model untuk mencari, atau kosongkan untuk tampilkan semua mobil yang tersedia.</div>', unsafe_allow_html=True)

    col_search, col_btn = st.columns([4, 1])
    with col_search:
        keyword = st.text_input("Nama Model Kendaraan", placeholder="Contoh: Innova, Fortuner, Jazz...", label_visibility="collapsed")
    with col_btn:
        search_clicked = st.button("🔍 Cari", type="primary", use_container_width=True)

    if search_clicked:
        with st.spinner("Mencari kendaraan..."):
            data = api_get(f"{API_MARKET}/cars/search?keyword={keyword}")

        if data is not None:
            if data:
                st.session_state["cars"] = data
                st.success(f"✅ Ditemukan **{len(data)}** kendaraan aktif.")

                # Tampilkan sebagai card
                for car in data:
                    st.markdown(f"""
                    <div class="car-card">
                        <div class="car-brand">{car['brand_name']} &nbsp;·&nbsp; ID #{car['listing_id']}</div>
                        <div class="car-model">{car['model_name']}</div>
                        <div class="car-price">{format_rupiah(float(car['price']))}</div>
                        <div class="car-seller">Seller: {car['seller_id']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Juga simpan sebagai dataframe untuk tab pembelian
                st.divider()
                with st.expander("Lihat sebagai tabel"):
                    df = pd.DataFrame(data)
                    df["price_display"] = df["price"].apply(lambda x: format_rupiah(float(x)))
                    st.dataframe(
                        df[["listing_id", "brand_name", "model_name", "price_display", "seller_id"]]
                        .rename(columns={
                            "listing_id": "ID", "brand_name": "Merek",
                            "model_name": "Model", "price_display": "Harga", "seller_id": "Seller"
                        }),
                        use_container_width=True, hide_index=True
                    )
            else:
                st.warning(f"🔎 Tidak ada kendaraan aktif yang cocok dengan kata kunci **'{keyword}'**.")
                if "cars" in st.session_state:
                    del st.session_state["cars"]


# ═══════════════════════════════════════════════════════════════════════════════
# [M2] Feature 3 — Beli Mobil
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<p class="section-title">Proses Pembelian Kendaraan</p>', unsafe_allow_html=True)

    if "cars" not in st.session_state or not st.session_state["cars"]:
        st.info("💡 Silakan lakukan pencarian kendaraan di tab **🔍 Cari Mobil** terlebih dahulu.")
    else:
        cars = st.session_state["cars"]

        st.markdown('<div class="info-card">🛒 Pilih kendaraan dari hasil pencarian terakhir, lalu masukkan nama pembeli untuk melanjutkan.</div>', unsafe_allow_html=True)

        # Pilih mobil
        car = st.selectbox(
            "Pilih Kendaraan",
            options=cars,
            format_func=lambda x: f"{x['brand_name']} {x['model_name']} — {format_rupiah(float(x['price']))}"
        )

        # Tampilkan ringkasan mobil yang dipilih
        if car:
            col1, col2, col3 = st.columns(3)
            col1.metric("Merek", car["brand_name"])
            col2.metric("Model", car["model_name"])
            col3.metric("Harga", format_rupiah(float(car["price"])))

        st.divider()

        buyer = st.text_input("Nama Lengkap Pembeli", placeholder="Contoh: Ahmad Fauzi")

        # Preview pesanan
        if buyer and car:
            st.markdown("**📋 Ringkasan Pesanan:**")
            st.markdown(f"""
            <div class="order-detail">
                <div class="order-row"><span class="order-label">Kendaraan</span><span class="order-value">{car['brand_name']} {car['model_name']}</span></div>
                <div class="order-row"><span class="order-label">Pembeli</span><span class="order-value">{buyer}</span></div>
                <div class="order-row"><span class="order-label">Total Pembayaran</span><span class="order-value" style="color:#d97706">{format_rupiah(float(car['price']))}</span></div>
                <div class="order-row"><span class="order-label">Seller</span><span class="order-value">{car['seller_id']}</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.caption("")

        if st.button("✅ Konfirmasi & Beli Sekarang", type="primary", use_container_width=True, disabled=not buyer):
            with st.spinner("Memproses pembelian..."):
                result = api_post(f"{API_MARKET}/orders/buy", {
                    "listing_id": car["listing_id"],
                    "buyer_name": buyer,
                    "model_name": car["model_name"],
                    "price": float(car["price"])
                })
            if result:
                st.success(f"🎉 Pembelian berhasil!")
                st.info(f"📋 **Order ID Anda:** `{result['order_id']}`\n\nSimpan Order ID ini untuk melacak status pesanan Anda.")
                st.balloons()


# ═══════════════════════════════════════════════════════════════════════════════
# [M4] Feature 7 — Lacak Pesanan
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<p class="section-title">Lacak Status Pesanan</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">📦 Masukkan Order ID yang Anda terima saat pembelian untuk melihat status terkini pesanan.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])
    with col1:
        track_id = st.text_input("Order ID", placeholder="Contoh: ORD-MN-1234567890", label_visibility="collapsed")
    with col2:
        track_btn = st.button("🔎 Lacak", type="primary", use_container_width=True)

    if track_btn:
        if not track_id:
            st.warning("⚠️ Masukkan Order ID terlebih dahulu.")
        else:
            with st.spinner("Mengambil data pesanan..."):
                data = api_get(f"{API_MARKET}/orders/track/{track_id}")

            if data:
                st.markdown("**Detail Pesanan:**")
                status = data.get("status", "UNKNOWN")
                st.markdown(f"Status: {get_status_badge(status)}", unsafe_allow_html=True)
                st.markdown("")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="order-detail">
                        <div class="order-row"><span class="order-label">Order ID</span><span class="order-value">{data.get('order_global_id', '-')}</span></div>
                        <div class="order-row"><span class="order-label">Pembeli</span><span class="order-value">{data.get('buyer_name', '-')}</span></div>
                        <div class="order-row"><span class="order-label">Total</span><span class="order-value">{format_rupiah(float(data.get('grand_total', 0)))}</span></div>
                        <div class="order-row"><span class="order-label">Tanggal Order</span><span class="order-value">{data.get('order_date', '-')}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error(f"❌ Order dengan ID **'{track_id}'** tidak ditemukan.")


# ═══════════════════════════════════════════════════════════════════════════════
# [M5] Feature 10 — Batalkan Pesanan
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<p class="section-title">Batalkan Pesanan</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-card">
        ⚠️ Pembatalan akan <strong>mengembalikan stok</strong> ke seller secara otomatis.
        Pastikan Anda memasukkan nama model yang benar agar stok dapat dikembalikan dengan tepat.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        cancel_id = st.text_input("Order ID yang Dibatalkan", placeholder="Contoh: ORD-MN-1234567890")
    with col2:
        model_to_restore = st.text_input("Nama Model Mobil", placeholder="Contoh: Innova Zenix")

    confirm_cancel = st.checkbox("⚠️ Saya memahami bahwa pembatalan ini tidak dapat diurungkan.")
    if st.button("❌ Batalkan Pesanan", type="primary", use_container_width=True, disabled=not confirm_cancel):
        if not cancel_id or not model_to_restore:
            st.warning("⚠️ Order ID dan nama model tidak boleh kosong.")
        else:
            with st.spinner("Memproses pembatalan..."):
                result = api_post(f"{API_MARKET}/orders/cancel", {
                    "order_global_id": cancel_id,
                    "model_name": model_to_restore
                })
            if result:
                st.success(f"✅ {result['message']}")


# ═══════════════════════════════════════════════════════════════════════════════
# [M6] Feature 12 — Laporan Settlement
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<p class="section-title">Laporan Settlement Pendapatan</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">📑 Laporan ini mencatat semua pembayaran yang telah diproses dari buyer ke seller.</div>', unsafe_allow_html=True)

    if st.button("🔃 Muat Laporan Settlement", use_container_width=True):
        with st.spinner("Mengambil data settlement..."):
            data = api_get(f"{API_MARKET}/admin/settlements")

        if data is not None:
            if data:
                df = pd.DataFrame(data)

                # Ringkasan statistik
                total_settlement = df["amount"].astype(float).sum()
                total_txn        = len(df)
                unique_sellers   = df["seller_id"].nunique()

                col1, col2, col3 = st.columns(3)
                col1.metric("Total Transaksi", f"{total_txn}")
                col2.metric("Total Settlement", format_rupiah(total_settlement))
                col3.metric("Jumlah Seller", f"{unique_sellers}")

                st.divider()

                df["amount_display"] = df["amount"].apply(lambda x: format_rupiah(float(x)))
                st.dataframe(
                    df[["settlement_id", "order_global_id", "seller_id", "amount_display", "settlement_date"]]
                    .rename(columns={
                        "settlement_id": "ID", "order_global_id": "Order ID",
                        "seller_id": "Seller", "amount_display": "Jumlah", "settlement_date": "Tanggal"
                    }),
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("📭 Belum ada data settlement.")

# ─── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption("🚗 MobilNiaga Marketplace · Platform Jual Beli Kendaraan Terpercaya")