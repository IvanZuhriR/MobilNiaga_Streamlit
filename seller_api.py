"""
╔══════════════════════════════════════════════════════════════════════╗
║           MobilNiaga - Seller API (Auto2000 / SEL001)                ║
║           Port: 8002                                                 ║
║           Database: seller_sel001_db                                 ║
╠══════════════════════════════════════════════════════════════════════╣
║  Fitur Seller:                                                       ║
║    [M1] Feature 1 - Tambah Kendaraan Baru ke Inventori               ║
║    [M1] Feature 2 - Update Stok Kendaraan                            ║
║    [M3] Feature 6 - Update Harga Kendaraan                           ║
║    [M3] Feature 5 - Lihat Rekap Penjualan                            ║
║    [M5] Feature 9 - Manajemen Data Pelanggan                         ║
╠══════════════════════════════════════════════════════════════════════╣
║  Endpoint Inter-Service (Dipanggil oleh Marketplace API):            ║
║    POST /inventory/deduct  - Kurangi stok + catat rekap              ║
║    POST /inventory/restore - Kembalikan stok + hapus rekap           ║
╚══════════════════════════════════════════════════════════════════════╝
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import logging
import os
from dotenv import load_dotenv

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("seller_api")

# ─── App Init ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Seller API - Auto2000 (SEL001)",
    description="API lokal untuk manajemen inventori dan pelanggan seller Auto2000",
    version="1.0.0"
)

# ─── Koneksi Database ─────────────────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),  # It will pull the password from .env
        database=os.getenv("DB_NAME2", "seller_sel001_db")
    )

# ─── Request Schemas ──────────────────────────────────────────────────────────

class ItemRequest(BaseModel):
    """Schema untuk menambahkan item/kendaraan baru ke inventori."""
    brand_name: str
    model_name: str
    stock: int
    selling_price: float

class StockRequest(BaseModel):
    """Schema untuk menambah stok kendaraan yang sudah ada."""
    vehicle_id: int
    added_stock: int

class PriceRequest(BaseModel):
    """Schema untuk memperbarui harga jual kendaraan."""
    vehicle_id: int
    new_price: float

class DeductRequest(BaseModel):
    """Schema inter-service: pengurangan stok saat terjadi pembelian di marketplace."""
    model_name: str
    order_global_id: str
    amount: float

class RestoreRequest(BaseModel):
    """Schema inter-service: pengembalian stok saat pesanan dibatalkan."""
    model_name: str
    order_global_id: str

class CustomerRequest(BaseModel):
    """Schema untuk menyimpan data pelanggan baru."""
    full_name: str
    phone: str
    email: str


# ─── [M1] Feature 1: Tambah Kendaraan ────────────────────────────────────────
@app.post(
    "/inventory/add",
    summary="Tambah Kendaraan Baru",
    tags=["Inventori"]
)
def add_item(req: ItemRequest):
    """
    Menambahkan kendaraan baru ke inventori seller.

    - **brand_name**: Nama merek (contoh: Toyota, Honda)
    - **model_name**: Nama model (contoh: Innova Zenix)
    - **stock**: Jumlah stok awal
    - **selling_price**: Harga jual dalam Rupiah
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO vehicle_inventory (brand_name, model_name, stock, selling_price) "
            "VALUES (%s, %s, %s, %s)",
            (req.brand_name, req.model_name, req.stock, req.selling_price)
        )
        db.commit()
        logger.info(f"Kendaraan baru ditambahkan: {req.brand_name} {req.model_name}")
        return {"message": "Kendaraan baru berhasil ditambahkan ke inventori."}
    except Exception as e:
        db.rollback()
        logger.error(f"Gagal menambahkan kendaraan: {e}")
        raise HTTPException(status_code=500, detail="Gagal menyimpan data kendaraan.")
    finally:
        cursor.close()
        db.close()


# ─── [M1] Feature 2: Update Stok ─────────────────────────────────────────────
@app.post(
    "/inventory/stock",
    summary="Tambah Stok Kendaraan",
    tags=["Inventori"]
)
def add_stock(req: StockRequest):
    """
    Menambahkan jumlah stok untuk kendaraan yang sudah ada di inventori.

    - **vehicle_id**: ID kendaraan di tabel `vehicle_inventory`
    - **added_stock**: Jumlah stok yang ingin ditambahkan
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE vehicle_inventory SET stock = stock + %s WHERE vehicle_id = %s",
            (req.added_stock, req.vehicle_id)
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Kendaraan tidak ditemukan.")
        logger.info(f"Stok vehicle_id={req.vehicle_id} bertambah {req.added_stock} unit.")
        return {"message": f"Stok berhasil ditambahkan sebanyak {req.added_stock} unit."}
    finally:
        cursor.close()
        db.close()


# ─── [M3] Feature 6: Update Harga ────────────────────────────────────────────
@app.put(
    "/inventory/price",
    summary="Update Harga Kendaraan",
    tags=["Inventori"]
)
def update_price(req: PriceRequest):
    """
    Memperbarui harga jual kendaraan di inventori seller.

    - **vehicle_id**: ID kendaraan yang harganya akan diubah
    - **new_price**: Harga baru dalam Rupiah
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE vehicle_inventory SET selling_price = %s WHERE vehicle_id = %s",
            (req.new_price, req.vehicle_id)
        )
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Kendaraan tidak ditemukan.")
        logger.info(f"Harga vehicle_id={req.vehicle_id} diupdate menjadi Rp {req.new_price:,.0f}")
        return {"message": "Harga kendaraan berhasil diperbarui."}
    finally:
        cursor.close()
        db.close()


# ─── [M3] Feature 5: Rekap Penjualan ─────────────────────────────────────────
@app.get(
    "/sales/recap",
    summary="Lihat Rekap Penjualan",
    tags=["Penjualan"]
)
def get_recap():
    """
    Mengambil seluruh data rekap penjualan milik seller,
    diurutkan dari transaksi terbaru.
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sales_recap ORDER BY sold_at DESC")
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


# ─── [M5] Feature 9: Tambah Pelanggan ────────────────────────────────────────
@app.post(
    "/customers/add",
    summary="Simpan Data Pelanggan",
    tags=["Pelanggan"]
)
def add_customer(req: CustomerRequest):
    """
    Menyimpan data pelanggan baru ke database lokal seller.

    - **full_name**: Nama lengkap pelanggan
    - **phone**: Nomor telepon
    - **email**: Alamat email
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO customers (full_name, phone, email) VALUES (%s, %s, %s)",
            (req.full_name, req.phone, req.email)
        )
        db.commit()
        logger.info(f"Pelanggan baru disimpan: {req.full_name}")
        return {"message": f"Data pelanggan '{req.full_name}' berhasil disimpan."}
    except Exception as e:
        db.rollback()
        logger.error(f"Gagal menyimpan pelanggan: {e}")
        raise HTTPException(status_code=500, detail="Gagal menyimpan data pelanggan.")
    finally:
        cursor.close()
        db.close()


# ─── [M5] Feature 9: List Pelanggan ──────────────────────────────────────────
@app.get(
    "/customers/list",
    summary="Daftar Pelanggan",
    tags=["Pelanggan"]
)
def list_customers():
    """Mengambil seluruh data pelanggan yang tersimpan di database lokal seller."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM customers ORDER BY customer_id DESC")
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT INTER-SERVICE
# Endpoint berikut dipanggil oleh Marketplace API, bukan oleh user langsung.
# ═══════════════════════════════════════════════════════════════════════════════

@app.post(
    "/inventory/deduct",
    summary="[Inter-Service] Kurangi Stok & Catat Rekap",
    tags=["Inter-Service"]
)
def deduct_stock(req: DeductRequest):
    """
    **Endpoint internal — dipanggil oleh Marketplace API saat terjadi pembelian.**

    Mengurangi stok kendaraan sebanyak 1 unit dan mencatat transaksi ke `sales_recap`.

    - **model_name**: Model yang stoknya dikurangi
    - **order_global_id**: ID order dari marketplace
    - **amount**: Nilai transaksi untuk rekap
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE vehicle_inventory SET stock = stock - 1 WHERE model_name = %s AND stock > 0",
            (req.model_name,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=400, detail=f"Stok '{req.model_name}' habis atau tidak ditemukan.")

        cursor.execute(
            "INSERT INTO sales_recap (order_global_id, model_name, amount) VALUES (%s, %s, %s)",
            (req.order_global_id, req.model_name, req.amount)
        )
        db.commit()
        logger.info(f"Stok '{req.model_name}' berkurang 1 unit. Order: {req.order_global_id}")
        return {"message": "Stok berhasil dikurangi dan rekap penjualan dicatat."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Gagal deduct stok: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan saat memproses stok.")
    finally:
        cursor.close()
        db.close()


@app.post(
    "/inventory/restore",
    summary="[Inter-Service] Kembalikan Stok & Hapus Rekap",
    tags=["Inter-Service"]
)
def restore_stock(req: RestoreRequest):
    """
    **Endpoint internal — dipanggil oleh Marketplace API saat pesanan dibatalkan.**

    Menambahkan kembali stok sebanyak 1 unit dan menghapus catatan rekap penjualan
    untuk order yang dibatalkan.

    - **model_name**: Model yang stoknya dikembalikan
    - **order_global_id**: ID order yang dibatalkan
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE vehicle_inventory SET stock = stock + 1 WHERE model_name = %s",
            (req.model_name,)
        )
        cursor.execute(
            "DELETE FROM sales_recap WHERE order_global_id = %s",
            (req.order_global_id,)
        )
        db.commit()
        logger.info(f"Stok '{req.model_name}' dikembalikan. Order {req.order_global_id} dihapus dari rekap.")
        return {"message": "Stok berhasil dikembalikan dan rekap penjualan dihapus."}
    except Exception as e:
        db.rollback()
        logger.error(f"Gagal restore stok: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan saat restore stok.")
    finally:
        cursor.close()
        db.close()