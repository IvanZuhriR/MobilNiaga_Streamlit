-- ╔══════════════════════════════════════════════════════════════════════╗
-- ║           MobilNiaga - Database Schema                               ║
-- ║                                                                      ║
-- ║  Database 1 (Master/Marketplace): mobilniaga_master                 ║
-- ║  Database 2 (Seller Lokal)      : seller_sel001_db                  ║
-- ╚══════════════════════════════════════════════════════════════════════╝
--
-- Cara pakai:
--   Jalankan script ini di MySQL/MariaDB untuk membuat semua tabel sekaligus.
--   mysql -u root -p < schema.sql
--
-- Catatan arsitektur:
--   - mobilniaga_master  : diakses oleh Marketplace API (port 8001)
--   - seller_sel001_db   : diakses oleh Seller API (port 8002)
--   - Kedua database berjalan di server yang sama (localhost)
-- ─────────────────────────────────────────────────────────────────────────────


-- ═════════════════════════════════════════════════════════════════════════════
-- DATABASE 1 : mobilniaga_master (Database Pusat / Marketplace)
-- ═════════════════════════════════════════════════════════════════════════════
CREATE DATABASE IF NOT EXISTS mobilniaga_master
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE mobilniaga_master;

-- ─────────────────────────────────────────────────────────────────────────────
-- Tabel: vehicle_listing_catalog
-- Deskripsi : Katalog publik kendaraan yang ditampilkan di marketplace.
--             Seller mendaftarkan kendaraannya di sini agar bisa dibeli.
-- Digunakan : Marketplace API — Feature 4 (Cari), Feature 3 (Beli), Feature 11 (Nonaktifkan)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vehicle_listing_catalog (
    listing_id   INT            AUTO_INCREMENT PRIMARY KEY COMMENT 'ID unik listing di marketplace',
    seller_id    VARCHAR(50)    NOT NULL                   COMMENT 'ID seller pemilik listing (e.g. SEL001)',
    brand_name   VARCHAR(100)   NOT NULL                   COMMENT 'Nama merek kendaraan (e.g. Toyota)',
    model_name   VARCHAR(100)   NOT NULL                   COMMENT 'Nama model kendaraan (e.g. Innova Zenix)',
    price        DECIMAL(15,2)  NOT NULL                   COMMENT 'Harga jual dalam Rupiah',
    status       VARCHAR(20)    NOT NULL DEFAULT 'ACTIVE'  COMMENT 'Status listing: ACTIVE | INACTIVE'
) COMMENT = 'Katalog kendaraan yang tampil di marketplace publik';


-- ─────────────────────────────────────────────────────────────────────────────
-- Tabel: marketplace_orders
-- Deskripsi : Menyimpan semua record pesanan yang dibuat di marketplace.
-- Digunakan : Marketplace API — Feature 3 (Beli), Feature 7 (Lacak), Feature 8 (Update Status),
--                               Feature 10 (Batalkan)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS marketplace_orders (
    order_global_id VARCHAR(100)     NOT NULL PRIMARY KEY          COMMENT 'ID order unik global (format: ORD-MN-<timestamp>)',
    listing_id      INT              NOT NULL                      COMMENT 'Referensi ke vehicle_listing_catalog.listing_id',
    buyer_name      VARCHAR(100)     NOT NULL                      COMMENT 'Nama lengkap pembeli',
    grand_total     DECIMAL(15,2)    NOT NULL                      COMMENT 'Total pembayaran dalam Rupiah',
    status          VARCHAR(50)      NOT NULL DEFAULT 'CREATED'    COMMENT 'Status pesanan: CREATED | SHIPPED | DELIVERED | CANCELLED',
    order_date      DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Waktu pembuatan pesanan'
) COMMENT = 'Record pesanan dari seluruh transaksi di marketplace';


-- ─────────────────────────────────────────────────────────────────────────────
-- Tabel: marketplace_settlements
-- Deskripsi : Catatan pembayaran/settlement dari marketplace ke seller
--             setelah transaksi berhasil.
-- Digunakan : Marketplace API — Feature 3 (dibuat otomatis saat beli), Feature 12 (Laporan)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS marketplace_settlements (
    settlement_id   INT            AUTO_INCREMENT PRIMARY KEY   COMMENT 'ID unik record settlement',
    order_global_id VARCHAR(100)   NOT NULL                     COMMENT 'Referensi ke marketplace_orders.order_global_id',
    seller_id       VARCHAR(50)    NOT NULL                     COMMENT 'ID seller yang menerima pembayaran',
    amount          DECIMAL(15,2)  NOT NULL                     COMMENT 'Jumlah yang diselesaikan dalam Rupiah',
    settlement_date DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Waktu pencatatan settlement'
) COMMENT = 'Catatan pembayaran dari marketplace ke seller';


-- ─────────────────────────────────────────────────────────────────────────────
-- Data Awal (Seed Data) — mobilniaga_master
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO vehicle_listing_catalog (seller_id, brand_name, model_name, price, status)
VALUES ('SEL001', 'Toyota', 'Innova Zenix', 450000000.00, 'ACTIVE');


-- ═════════════════════════════════════════════════════════════════════════════
-- DATABASE 2 : seller_sel001_db (Database Lokal Seller Auto2000)
-- ═════════════════════════════════════════════════════════════════════════════
CREATE DATABASE IF NOT EXISTS seller_sel001_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE seller_sel001_db;


-- ─────────────────────────────────────────────────────────────────────────────
-- Tabel: vehicle_inventory
-- Deskripsi : Inventori fisik kendaraan milik seller. Stok di sini yang
--             dikurangi saat terjadi transaksi di marketplace.
-- Digunakan : Seller API — Feature 1 (Tambah), Feature 2 (Stok), Feature 6 (Harga),
--                          Inter-service deduct & restore
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vehicle_inventory (
    vehicle_id    INT            AUTO_INCREMENT PRIMARY KEY COMMENT 'ID kendaraan di inventori lokal seller',
    brand_name    VARCHAR(100)   NOT NULL                   COMMENT 'Nama merek kendaraan',
    model_name    VARCHAR(100)   NOT NULL                   COMMENT 'Nama model kendaraan',
    stock         INT            NOT NULL DEFAULT 0         COMMENT 'Jumlah stok yang tersedia',
    selling_price DECIMAL(15,2)  NOT NULL                   COMMENT 'Harga jual dalam Rupiah'
) COMMENT = 'Inventori fisik kendaraan milik seller SEL001';


-- ─────────────────────────────────────────────────────────────────────────────
-- Tabel: sales_recap
-- Deskripsi : Rekap penjualan seller. Diisi secara otomatis saat inter-service
--             deduct dipanggil, dan dihapus saat inter-service restore dipanggil.
-- Digunakan : Seller API — Feature 5 (Rekap), Inter-service deduct & restore
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales_recap (
    recap_id        INT            AUTO_INCREMENT PRIMARY KEY COMMENT 'ID unik record rekap',
    order_global_id VARCHAR(100)   NOT NULL                   COMMENT 'Referensi ke order dari marketplace',
    model_name      VARCHAR(100)   NOT NULL                   COMMENT 'Model kendaraan yang terjual',
    amount          DECIMAL(15,2)  NOT NULL                   COMMENT 'Nilai transaksi dalam Rupiah',
    sold_at         DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Waktu transaksi dicatat'
) COMMENT = 'Rekap penjualan seller — otomatis diisi/dihapus oleh marketplace';


-- ─────────────────────────────────────────────────────────────────────────────
-- Tabel: customers
-- Deskripsi : Data pelanggan yang disimpan secara lokal oleh seller.
--             Tidak terhubung ke database marketplace.
-- Digunakan : Seller API — Feature 9 (Manajemen Pelanggan)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT            AUTO_INCREMENT PRIMARY KEY COMMENT 'ID unik pelanggan',
    full_name   VARCHAR(100)   NOT NULL                   COMMENT 'Nama lengkap pelanggan',
    phone       VARCHAR(20)    NOT NULL                   COMMENT 'Nomor telepon pelanggan',
    email       VARCHAR(100)   NOT NULL                   COMMENT 'Alamat email pelanggan'
) COMMENT = 'Data pelanggan lokal milik seller SEL001';


-- ─────────────────────────────────────────────────────────────────────────────
-- Data Awal (Seed Data) — seller_sel001_db
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO vehicle_inventory (brand_name, model_name, stock, selling_price)
VALUES ('Toyota', 'Innova Zenix', 5, 450000000.00);