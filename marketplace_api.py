"""
╔══════════════════════════════════════════════════════════════════════╗
║           MobilNiaga - Marketplace API                               ║
║           Port: 8001                                                 ║
║           Database: mobilniaga_master                                ║
╠══════════════════════════════════════════════════════════════════════╣
║  Fitur:                                                              ║
║    [M2] Feature 4  - Pencarian Mobil di Katalog                      ║
║    [M2] Feature 3  - Pembelian Mobil (+ Inter-service ke Seller)     ║
║    [M4] Feature 7  - Lacak Status Pesanan                            ║
║    [M4] Feature 8  - Update Status Pesanan                           ║
║    [M5] Feature 10 - Batalkan Pesanan (+ Inter-service ke Seller)    ║
║    [M6] Feature 11 - Nonaktifkan Katalog Mobil                       ║
║    [M6] Feature 12 - Laporan Settlement                              ║
╚══════════════════════════════════════════════════════════════════════╝

Inter-Service Communication:
  → POST http://localhost:8002/inventory/deduct  (saat beli mobil)
  → POST http://localhost:8002/inventory/restore (saat batalkan pesanan)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import requests
import time
import logging
import os
from dotenv import load_dotenv

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("marketplace_api")

# ─── App Init ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Marketplace API - MobilNiaga",
    description="Central API untuk marketplace jual beli kendaraan MobilNiaga",
    version="1.0.0"
)

# ─── Konstanta ────────────────────────────────────────────────────────────────
SELLER_API_URL = "http://localhost:8002"

# ─── Koneksi Database ─────────────────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),  # It will pull the password from .env
        database=os.getenv("DB_NAME1", "mobilniaga_master")
    )
# ─── Request Schemas ──────────────────────────────────────────────────────────

class OrderRequest(BaseModel):
    """Schema untuk request pembelian mobil baru."""
    listing_id: int
    buyer_name: str
    model_name: str
    price: float

class StatusRequest(BaseModel):
    """Schema untuk request update status pesanan."""
    order_global_id: str
    new_status: str

class CancelRequest(BaseModel):
    """Schema untuk request pembatalan pesanan."""
    order_global_id: str
    model_name: str

class DeactivateRequest(BaseModel):
    """Schema untuk request nonaktifkan listing katalog."""
    listing_id: int


# ─── Endpoint: Pencarian Mobil ────────────────────────────────────────────────
# [M2] Feature 4
@app.get(
    "/cars/search",
    summary="Cari Mobil di Katalog",
    tags=["Katalog"]
)
def search_cars(keyword: str = ""):
    """
    Mencari mobil aktif di katalog marketplace berdasarkan nama model.

    - **keyword**: Kata kunci nama model (opsional). Kosongkan untuk tampilkan semua.
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        query = (
            "SELECT listing_id, seller_id, brand_name, model_name, price "
            "FROM vehicle_listing_catalog "
            "WHERE model_name LIKE %s AND status = 'ACTIVE'"
        )
        cursor.execute(query, (f"%{keyword}%",))
        results = cursor.fetchall()
        logger.info(f"Pencarian '{keyword}' mengembalikan {len(results)} hasil.")
        return results
    finally:
        cursor.close()
        db.close()


# ─── Endpoint: Beli Mobil ─────────────────────────────────────────────────────
# [M2] Feature 3
@app.post(
    "/orders/buy",
    summary="Beli Mobil",
    tags=["Pesanan"]
)
def buy_car(req: OrderRequest):
    """
    Memproses pembelian mobil oleh buyer.

    Alur:
    1. Buat record order di `marketplace_orders`
    2. Kirim request inter-service ke Seller API untuk deduct stok & catat rekap
    3. Buat record settlement di `marketplace_settlements`

    - **listing_id**: ID listing mobil di katalog
    - **buyer_name**: Nama lengkap pembeli
    - **model_name**: Nama model mobil (dikirim ke seller untuk deduct stok)
    - **price**: Harga pembelian
    """
    order_id = f"ORD-MN-{int(time.time())}"
    db = get_db()
    cursor = db.cursor()

    try:
        # 1. Simpan pesanan ke marketplace
        cursor.execute(
            "INSERT INTO marketplace_orders (order_global_id, listing_id, buyer_name, grand_total) "
            "VALUES (%s, %s, %s, %s)",
            (order_id, req.listing_id, req.buyer_name, req.price)
        )
        db.commit()
        logger.info(f"Order dibuat: {order_id} oleh {req.buyer_name}")

        # 2. Inter-service: deduct stok & rekap penjualan di Seller API
        seller_resp = requests.post(
            f"{SELLER_API_URL}/inventory/deduct",
            json={"model_name": req.model_name, "order_global_id": order_id, "amount": req.price},
            timeout=5
        )
        seller_resp.raise_for_status()
        logger.info(f"Stok berhasil dideduct di Seller API untuk order {order_id}")

        # 3. Buat record settlement
        cursor.execute(
            "INSERT INTO marketplace_settlements (order_global_id, seller_id, amount) "
            "VALUES (%s, 'SEL001', %s)",
            (order_id, req.price)
        )
        db.commit()
        logger.info(f"Settlement dicatat untuk order {order_id}")

        return {"message": "Pembelian Berhasil!", "order_id": order_id}

    except requests.RequestException as e:
        logger.error(f"Gagal menghubungi Seller API: {e}")
        raise HTTPException(status_code=503, detail="Seller API tidak dapat dihubungi. Coba lagi.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saat proses pembelian: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal.")
    finally:
        cursor.close()
        db.close()


# ─── Endpoint: Lacak Pesanan ──────────────────────────────────────────────────
# [M4] Feature 7
@app.get(
    "/orders/track/{order_id}",
    summary="Lacak Status Pesanan",
    tags=["Pesanan"]
)
def track_order(order_id: str):
    """
    Mengambil detail dan status terkini sebuah pesanan berdasarkan Order ID.

    - **order_id**: ID pesanan (format: ORD-MN-xxxxxxxxxx)
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM marketplace_orders WHERE order_global_id = %s",
            (order_id,)
        )
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail=f"Order '{order_id}' tidak ditemukan.")
        return order
    finally:
        cursor.close()
        db.close()


# ─── Endpoint: Update Status Pesanan ─────────────────────────────────────────
# [M4] Feature 8
@app.put(
    "/orders/status",
    summary="Update Status Pesanan",
    tags=["Pesanan"]
)
def update_status(req: StatusRequest):
    """
    Memperbarui status sebuah pesanan (biasanya digunakan oleh seller).

    Status yang umum digunakan: CREATED, SHIPPED, DELIVERED, CANCELLED

    - **order_global_id**: ID pesanan yang akan diupdate
    - **new_status**: Status baru pesanan
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE marketplace_orders SET status = %s WHERE order_global_id = %s",
            (req.new_status, req.order_global_id)
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order tidak ditemukan.")
        logger.info(f"Status order {req.order_global_id} → {req.new_status}")
        return {"message": f"Status pesanan berhasil diupdate menjadi '{req.new_status}'"}
    finally:
        cursor.close()
        db.close()


# ─── Endpoint: Batalkan Pesanan ───────────────────────────────────────────────
# [M5] Feature 10
@app.post(
    "/orders/cancel",
    summary="Batalkan Pesanan",
    tags=["Pesanan"]
)
def cancel_order(req: CancelRequest):
    """
    Membatalkan pesanan dan mengembalikan stok ke seller.

    Alur:
    1. Set status pesanan menjadi 'CANCELLED'
    2. Kirim request inter-service ke Seller API untuk restore stok & hapus rekap

    - **order_global_id**: ID pesanan yang dibatalkan
    - **model_name**: Model mobil (untuk restore stok di seller)
    """
    db = get_db()
    cursor = db.cursor()
    try:
        # 1. Update status pesanan
        cursor.execute(
            "UPDATE marketplace_orders SET status = 'CANCELLED' WHERE order_global_id = %s",
            (req.order_global_id,)
        )
        db.commit()
        logger.info(f"Pesanan {req.order_global_id} dibatalkan.")

        # 2. Inter-service: restore stok di Seller API
        seller_resp = requests.post(
            f"{SELLER_API_URL}/inventory/restore",
            json={"model_name": req.model_name, "order_global_id": req.order_global_id},
            timeout=5
        )
        seller_resp.raise_for_status()
        logger.info(f"Stok '{req.model_name}' dikembalikan ke seller untuk order {req.order_global_id}")

        return {"message": "Pesanan berhasil dibatalkan dan stok telah dikembalikan ke Seller."}

    except requests.RequestException as e:
        logger.error(f"Gagal menghubungi Seller API saat cancel: {e}")
        raise HTTPException(status_code=503, detail="Pesanan dibatalkan, namun gagal restore stok ke Seller.")
    finally:
        cursor.close()
        db.close()


# ─── Endpoint: Nonaktifkan Katalog ────────────────────────────────────────────
# [M6] Feature 11
@app.put(
    "/cars/deactivate",
    summary="Nonaktifkan Listing Mobil",
    tags=["Katalog"]
)
def deactivate_car(req: DeactivateRequest):
    """
    Menyembunyikan (menonaktifkan) sebuah listing mobil dari marketplace.

    Mobil tidak akan muncul di hasil pencarian setelah dinonaktifkan.

    - **listing_id**: ID listing yang akan dinonaktifkan
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE vehicle_listing_catalog SET status = 'INACTIVE' WHERE listing_id = %s",
            (req.listing_id,)
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Listing tidak ditemukan.")
        logger.info(f"Listing ID {req.listing_id} dinonaktifkan dari katalog.")
        return {"message": "Mobil berhasil disembunyikan dari Marketplace."}
    finally:
        cursor.close()
        db.close()


# ─── Endpoint: Laporan Settlement ─────────────────────────────────────────────
# [M6] Feature 12
@app.get(
    "/admin/settlements",
    summary="Laporan Settlement Pendapatan",
    tags=["Admin"]
)
def get_settlements():
    """
    Mengambil seluruh data settlement (pembayaran ke seller) yang tersimpan,
    diurutkan dari yang terbaru.
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM marketplace_settlements ORDER BY settlement_date DESC"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()