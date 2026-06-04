"""
╔══════════════════════════════════════════════════════════════════════╗
║           MobilNiaga - Seller Dashboard                              ║
║           Target: Auto2000 (SEL001)                                  ║
║           Berkomunikasi dengan: Seller API (:8002) & Market API (:8001)║
╚══════════════════════════════════════════════════════════════════════╝

Jalankan dengan: streamlit run app_seller.py
"""

import streamlit as st
import requests
import pandas as pd

# ─── Konfigurasi ──────────────────────────────────────────────────────────────
API_SELLER = "http://localhost:8002"
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
        st.error(f"❌ Error dari server: {e.response.json().get('detail', str(e))}")
    return None

def api_put(url: str, payload: dict) -> dict | None:
    """Mengirim PUT request dan mengembalikan JSON response, atau None jika error."""
    try:
        resp = requests.put(url, json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        st.error("❌ Tidak dapat terhubung ke server. Pastikan API sudah berjalan.")
    except requests.HTTPError as e:
        st.error(f"❌ Error dari server: {e.response.json().get('detail', str(e))}")
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
        st.error(f"❌ Error dari server: {e.response.json().get('detail', str(e))}")
    return None

def format_rupiah(value: float) -> str:
    """Format angka ke format Rupiah (Rp 1.000.000)."""
    return f"Rp {value:,.0f}".replace(",", ".")


# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MobilNiaga — Seller Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Warna utama dashboard */
    :root {
        --primary: #1a56db;
        --success: #057a55;
        --danger: #e02424;
    }

    /* Header utama */
    .main-header {
        background: linear-gradient(135deg, #1a56db 0%, #0e3a8c 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .main-header p  { color: rgba(255,255,255,0.8); margin: 0.3rem 0 0; font-size: 0.95rem; }

    /* Card info kecil */
    .info-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #1a56db;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        font-size: 0.88rem;
        color: #4a5568;
    }

    /* Form section */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e2e8f0;
    }

    /* Status badge */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }
    .badge-blue   { background: #dbeafe; color: #1e40af; }
    .badge-green  { background: #d1fae5; color: #065f46; }
    .badge-red    { background: #fee2e2; color: #991b1b; }
    .badge-yellow { background: #fef3c7; color: #92400e; }

    /* Tabel lebih rapi */
    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

    /* Sembunyikan footer streamlit */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏢 Seller Dashboard — Auto2000</h1>
    <p>Seller ID: SEL001 &nbsp;|&nbsp; Kelola inventori, penjualan, dan pelanggan Anda</p>
</div>
""", unsafe_allow_html=True)

# ─── Tab Navigation ───────────────────────────────────────────────────────────
TAB_LABELS = [
    "📦 Tambah Mobil",
    "🔢 Update Stok",
    "💰 Update Harga",
    "📊 Rekap Penjualan",
    "🚚 Update Pengiriman",
    "👥 Pelanggan",
    "🚫 Hapus Katalog",
]
tabs = st.tabs(TAB_LABELS)


# ═══════════════════════════════════════════════════════════════════════════════
# [M1] Feature 1 — Tambah Kendaraan Baru
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<p class="section-title">Tambah Kendaraan Baru ke Inventori</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">📌 Kendaraan yang ditambahkan akan masuk ke inventori lokal seller. Daftarkan ke katalog marketplace secara terpisah jika diperlukan.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        brand  = st.text_input("Merek Kendaraan", placeholder="Contoh: Toyota")
        model  = st.text_input("Nama Model", placeholder="Contoh: Innova Zenix")
    with col2:
        stock = st.number_input("Jumlah Stok Awal", min_value=1, value=1, step=1)
        price = st.number_input("Harga Jual (Rp)", min_value=10_000_000, value=300_000_000, step=1_000_000)
        st.caption(f"Preview harga: **{format_rupiah(price)}**")

    if st.button("💾 Simpan Kendaraan", type="primary", use_container_width=True):
        if not brand or not model:
            st.warning("⚠️ Merek dan nama model tidak boleh kosong.")
        else:
            result = api_post(f"{API_SELLER}/inventory/add", {
                "brand_name": brand, "model_name": model,
                "stock": stock, "selling_price": price
            })
            if result:
                st.success(f"✅ {result['message']}")
                st.balloons()


# ═══════════════════════════════════════════════════════════════════════════════
# [M1] Feature 2 — Update Stok
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<p class="section-title">Tambah Stok Kendaraan</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">📌 Masukkan ID kendaraan sesuai tabel <code>vehicle_inventory</code> di database lokal seller.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        vid      = st.number_input("ID Kendaraan", min_value=1, value=1, step=1)
    with col2:
        add_qty  = st.number_input("Jumlah Stok yang Ditambahkan", min_value=1, value=1, step=1)

    if st.button("🔄 Update Stok", type="primary", use_container_width=True):
        result = api_post(f"{API_SELLER}/inventory/stock", {
            "vehicle_id": vid, "added_stock": add_qty
        })
        if result:
            st.success(f"✅ {result['message']}")


# ═══════════════════════════════════════════════════════════════════════════════
# [M3] Feature 6 — Update Harga
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<p class="section-title">Perbarui Harga Jual Kendaraan</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">📌 Perubahan harga hanya berlaku di inventori lokal. Update juga harga di katalog marketplace jika diperlukan.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        vid2      = st.number_input("ID Kendaraan (Ubah Harga)", min_value=1, value=1, step=1)
    with col2:
        new_price = st.number_input("Harga Baru (Rp)", min_value=10_000_000, value=300_000_000, step=1_000_000)
        st.caption(f"Preview harga baru: **{format_rupiah(new_price)}**")

    if st.button("💰 Update Harga", type="primary", use_container_width=True):
        result = api_put(f"{API_SELLER}/inventory/price", {
            "vehicle_id": vid2, "new_price": new_price
        })
        if result:
            st.success(f"✅ {result['message']}")


# ═══════════════════════════════════════════════════════════════════════════════
# [M3] Feature 5 — Rekap Penjualan
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<p class="section-title">Rekap Penjualan</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">📊 Menampilkan semua transaksi penjualan yang telah diproses dari Marketplace.</div>', unsafe_allow_html=True)

    if st.button("🔃 Muat Data Rekap", use_container_width=True):
        data = api_get(f"{API_SELLER}/sales/recap")
        if data is not None:
            if data:
                df = pd.DataFrame(data)
                # Format kolom harga
                if "amount" in df.columns:
                    df["amount_display"] = df["amount"].apply(lambda x: format_rupiah(float(x)))

                # Tampilkan metrik ringkasan
                total_trx  = len(df)
                total_rev  = df["amount"].astype(float).sum()
                col1, col2 = st.columns(2)
                col1.metric("Total Transaksi", f"{total_trx} pesanan")
                col2.metric("Total Pendapatan", format_rupiah(total_rev))
                st.divider()

                st.dataframe(
                    df[["recap_id", "order_global_id", "model_name", "amount_display", "sold_at"]]
                    .rename(columns={
                        "recap_id": "ID", "order_global_id": "Order ID",
                        "model_name": "Model", "amount_display": "Pendapatan", "sold_at": "Waktu"
                    }),
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("📭 Belum ada data penjualan.")


# ═══════════════════════════════════════════════════════════════════════════════
# [M4] Feature 8 — Update Status Pengiriman
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<p class="section-title">Update Status Pengiriman Pesanan</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">🚚 Update status ini akan tercatat di sistem Marketplace. Hubungi pembeli setelah status diperbarui.</div>', unsafe_allow_html=True)

    STATUS_OPTIONS = {
        "SHIPPED":   "📦 SHIPPED — Pesanan sedang dikirim",
        "DELIVERED": "✅ DELIVERED — Pesanan telah diterima pembeli",
    }

    col1, col2 = st.columns(2)
    with col1:
        oid      = st.text_input("Order ID", placeholder="Contoh: ORD-MN-1234567890")
    with col2:
        new_stat = st.selectbox("Status Baru", options=list(STATUS_OPTIONS.keys()),
                                format_func=lambda x: STATUS_OPTIONS[x])

    if st.button("🚀 Update Status", type="primary", use_container_width=True):
        if not oid:
            st.warning("⚠️ Order ID tidak boleh kosong.")
        else:
            result = api_put(f"{API_MARKET}/orders/status", {
                "order_global_id": oid, "new_status": new_stat
            })
            if result:
                st.success(f"✅ {result['message']}")


# ═══════════════════════════════════════════════════════════════════════════════
# [M5] Feature 9 — Manajemen Pelanggan
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown('<p class="section-title">Manajemen Data Pelanggan</p>', unsafe_allow_html=True)

    sub1, sub2 = st.tabs(["➕ Tambah Pelanggan", "📋 Daftar Pelanggan"])

    with sub1:
        st.markdown('<div class="info-card">👥 Data pelanggan disimpan di database lokal seller dan tidak terhubung ke Marketplace.</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            c_name  = st.text_input("Nama Lengkap", placeholder="Contoh: Budi Santoso")
            c_phone = st.text_input("Nomor Telepon", placeholder="Contoh: 08123456789")
        with col2:
            c_email = st.text_input("Email", placeholder="Contoh: budi@email.com")

        if st.button("💾 Simpan Pelanggan", type="primary", use_container_width=True):
            if not c_name or not c_phone or not c_email:
                st.warning("⚠️ Semua kolom harus diisi.")
            else:
                result = api_post(f"{API_SELLER}/customers/add", {
                    "full_name": c_name, "phone": c_phone, "email": c_email
                })
                if result:
                    st.success(f"✅ {result['message']}")

    with sub2:
        if st.button("🔃 Tampilkan Daftar Pelanggan", use_container_width=True):
            data = api_get(f"{API_SELLER}/customers/list")
            if data is not None:
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(
                        df.rename(columns={
                            "customer_id": "ID", "full_name": "Nama",
                            "phone": "Telepon", "email": "Email"
                        }),
                        use_container_width=True, hide_index=True
                    )
                    st.caption(f"Total {len(df)} pelanggan terdaftar.")
                else:
                    st.info("📭 Belum ada data pelanggan.")


# ═══════════════════════════════════════════════════════════════════════════════
# [M6] Feature 11 — Nonaktifkan Katalog
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown('<p class="section-title">Nonaktifkan Listing dari Katalog Marketplace</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">⚠️ Mobil yang dinonaktifkan tidak akan muncul di hasil pencarian marketplace. Tindakan ini tidak menghapus data dari database.</div>', unsafe_allow_html=True)

    lid = st.number_input("Listing ID di Marketplace", min_value=1, value=1, step=1)

    confirm = st.checkbox("Saya konfirmasi ingin menonaktifkan listing ini dari katalog.")
    if st.button("🚫 Nonaktifkan Listing", type="primary", use_container_width=True, disabled=not confirm):
        result = api_put(f"{API_MARKET}/cars/deactivate", {"listing_id": lid})
        if result:
            st.success(f"✅ {result['message']}")

# ─── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption("🚗 MobilNiaga Seller Dashboard · SEL001 — Auto2000 · Sistem Manajemen Inventori & Penjualan")