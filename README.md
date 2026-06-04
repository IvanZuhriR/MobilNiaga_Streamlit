# 🚗 MobilNiaga — Platform Marketplace Kendaraan

> Sistem marketplace jual beli kendaraan berbasis microservice dengan arsitektur multi-database.  
> Dikembangkan sebagai tugas mata kuliah — proyek kelompok 6 anggota.

---

## 📌 Daftar Isi

- [Gambaran Sistem](#-gambaran-sistem)
- [Struktur File](#-struktur-file)
- [Arsitektur & Alur Data](#-arsitektur--alur-data)
- [Daftar Fitur](#-daftar-fitur)
- [Cara Menjalankan](#-cara-menjalankan)
- [API Reference](#-api-reference)
- [Inter-Service Communication](#-inter-service-communication)
- [Troubleshooting](#-troubleshooting)

---

## 🧩 Gambaran Sistem

MobilNiaga adalah platform marketplace kendaraan yang dibangun dengan pendekatan **multi-service**:

| Komponen | Teknologi | Port | Keterangan |
|---|---|---|---|
| **Marketplace API** | FastAPI | `8001` | Backend pusat — pencarian, pembelian, pesanan |
| **Seller API** | FastAPI | `8002` | Backend lokal seller — inventori, rekap, pelanggan |
| **Marketplace Dashboard** | Streamlit | `8501` | UI untuk pembeli & admin |
| **Seller Dashboard** | Streamlit | `8502` | UI khusus seller Auto2000 (SEL001) |
| **Database Master** | MySQL | `3306` | `mobilniaga_master` — data marketplace |
| **Database Seller** | MySQL | `3306` | `seller_sel001_db` — data lokal seller |

---

## 📁 Struktur File

```
mobilniaga/
├── marketplace_api.py    # FastAPI — Marketplace (port 8001)
├── seller_api.py         # FastAPI — Seller SEL001 (port 8002)
├── app_marketplace.py    # Streamlit — Dashboard Marketplace (port 8501)
├── app_seller.py         # Streamlit — Dashboard Seller (port 8502)
├── schema.sql            # Script DDL untuk membuat semua tabel & seed data
├── requirements.txt      # Daftar dependensi Python
└── README.md             # Dokumentasi ini
```

---

## 🏗️ Arsitektur & Alur Data

```
┌─────────────────────┐        ┌─────────────────────┐
│  app_marketplace.py │        │    app_seller.py     │
│  (Streamlit :8501)  │        │  (Streamlit :8502)   │
└────────┬────────────┘        └──────────┬───────────┘
         │ HTTP                            │ HTTP
         ▼                                 ▼
┌─────────────────────┐        ┌─────────────────────┐
│  marketplace_api.py │◄──────►│    seller_api.py    │
│   (FastAPI :8001)   │  Inter │   (FastAPI :8002)   │
└────────┬────────────┘ Service└──────────┬──────────┘
         │ SQL                             │ SQL
         ▼                                 ▼
┌─────────────────────┐        ┌─────────────────────┐
│  mobilniaga_master  │        │  seller_sel001_db   │
│  (MySQL Database)   │        │  (MySQL Database)   │
└─────────────────────┘        └─────────────────────┘
```

### Alur Inter-Service

**Saat Pembelian (`/orders/buy`):**
```
app_marketplace → Marketplace API → [simpan order] 
                                  → Seller API /inventory/deduct → [kurangi stok + catat rekap]
                                  → [buat settlement record]
```

**Saat Pembatalan (`/orders/cancel`):**
```
app_marketplace → Marketplace API → [update status = CANCELLED]
                                  → Seller API /inventory/restore → [kembalikan stok + hapus rekap]
```

---

## ✅ Daftar Fitur

| No | Fitur | Endpoint | Anggota | Dashboard |
|---|---|---|---|---|
| 1 | Tambah kendaraan ke inventori | `POST /inventory/add` | M1 | Seller |
| 2 | Update stok kendaraan | `POST /inventory/stock` | M1 | Seller |
| 3 | Beli mobil di marketplace | `POST /orders/buy` | M2 | Marketplace |
| 4 | Cari mobil di katalog | `GET /cars/search` | M2 | Marketplace |
| 5 | Rekap penjualan seller | `GET /sales/recap` | M3 | Seller |
| 6 | Update harga kendaraan | `PUT /inventory/price` | M3 | Seller |
| 7 | Lacak status pesanan | `GET /orders/track/{id}` | M4 | Marketplace |
| 8 | Update status pengiriman | `PUT /orders/status` | M4 | Seller |
| 9 | Manajemen data pelanggan | `POST /customers/add` | M5 | Seller |
| 10 | Batalkan pesanan | `POST /orders/cancel` | M5 | Marketplace |
| 11 | Nonaktifkan listing katalog | `PUT /cars/deactivate` | M6 | Seller |
| 12 | Laporan settlement | `GET /admin/settlements` | M6 | Marketplace |

---

## 🚀 Cara Menjalankan

Lihat **`RUNGUIDE.md`** untuk panduan lengkap langkah demi langkah.

**Ringkasan cepat** — jalankan 4 perintah ini di 4 terminal terpisah:

```bash
# Terminal 1 — Marketplace API
uvicorn marketplace_api:app --port 8001 --reload

# Terminal 2 — Seller API
uvicorn seller_api:app --port 8002 --reload

# Terminal 3 — Marketplace Dashboard
streamlit run app_marketplace.py --server.port 8501

# Terminal 4 — Seller Dashboard
streamlit run app_seller.py --server.port 8502
```

---

## 📡 API Reference

### Marketplace API — `http://localhost:8001`

| Method | Endpoint | Body | Keterangan |
|---|---|---|---|
| `GET` | `/cars/search?keyword=` | — | Cari mobil aktif |
| `POST` | `/orders/buy` | `listing_id, buyer_name, model_name, price` | Beli mobil |
| `GET` | `/orders/track/{order_id}` | — | Lacak pesanan |
| `PUT` | `/orders/status` | `order_global_id, new_status` | Update status |
| `POST` | `/orders/cancel` | `order_global_id, model_name` | Batalkan pesanan |
| `PUT` | `/cars/deactivate` | `listing_id` | Nonaktifkan listing |
| `GET` | `/admin/settlements` | — | Laporan settlement |

> 📄 Dokumentasi interaktif: **`http://localhost:8001/docs`**

---

### Seller API — `http://localhost:8002`

| Method | Endpoint | Body | Keterangan |
|---|---|---|---|
| `POST` | `/inventory/add` | `brand_name, model_name, stock, selling_price` | Tambah kendaraan |
| `POST` | `/inventory/stock` | `vehicle_id, added_stock` | Tambah stok |
| `PUT` | `/inventory/price` | `vehicle_id, new_price` | Update harga |
| `GET` | `/sales/recap` | — | Rekap penjualan |
| `POST` | `/customers/add` | `full_name, phone, email` | Tambah pelanggan |
| `GET` | `/customers/list` | — | Daftar pelanggan |
| `POST` | `/inventory/deduct` | `model_name, order_global_id, amount` | *(Inter-service)* Kurangi stok |
| `POST` | `/inventory/restore` | `model_name, order_global_id` | *(Inter-service)* Kembalikan stok |

> 📄 Dokumentasi interaktif: **`http://localhost:8002/docs`**

---

## 🔗 Inter-Service Communication

Kedua API saling berkomunikasi secara langsung melalui HTTP:

```
Marketplace API  →  POST http://localhost:8002/inventory/deduct   (saat beli)
Marketplace API  →  POST http://localhost:8002/inventory/restore  (saat cancel)
```

Endpoint inter-service di Seller API sebaiknya **tidak dipanggil langsung** dari dashboard — hanya dipanggil oleh Marketplace API sebagai bagian dari alur transaksi.

---

## 🛠️ Troubleshooting

| Masalah | Kemungkinan Penyebab | Solusi |
|---|---|---|
| `Connection refused` di dashboard | API belum berjalan | Pastikan kedua `uvicorn` sudah aktif |
| `Access denied` ke MySQL | Password salah | Cek `DB_CONFIG` di file API |
| `ModuleNotFoundError` | Dependensi belum terinstall | Jalankan `pip install -r requirements.txt` |
| Stok tidak berkurang | Seller API tidak bisa dihubungi | Pastikan port 8002 aktif saat beli |
| `Table doesn't exist` | Schema belum dijalankan | Jalankan `schema.sql` di MySQL |

---

## 👥 Anggota Kelompok

| Anggota | Fitur yang Dikerjakan |
|---|---|
| Member 1 (M1) | Feature 1 — Tambah Kendaraan, Feature 2 — Update Stok |
| Member 2 (M2) | Feature 3 — Beli Mobil, Feature 4 — Cari Mobil |
| Member 3 (M3) | Feature 5 — Rekap Penjualan, Feature 6 — Update Harga |
| Member 4 (M4) | Feature 7 — Lacak Pesanan, Feature 8 — Update Status |
| Member 5 (M5) | Feature 9 — Manajemen Pelanggan, Feature 10 — Batalkan Pesanan |
| Member 6 (M6) | Feature 11 — Nonaktifkan Katalog, Feature 12 — Laporan Settlement |
