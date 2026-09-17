# Entertainment Warehouse

TMDB ve TVMaze verilerini Apache Hop ile yöneten, Oracle veri ambarına yükleyen ve Power BI ile analiz eden eğlence sektörü veri projesi.

Proje; Türkiye, ABD, Birleşik Krallık, Güney Kore ve Fransa için içerik ve yayın verisi toplar. Ayrıca Faker ile tekrar üretilebilir sentetik kullanıcı reytingleri oluşturur.

> Sentetik kullanıcı reytingleri gerçek kişilere ait değildir ve yalnızca eğitim, demo ve analiz amacıyla kullanılmalıdır.

## Güncel rapor durumu

17.09.2026 tarihinde Power BI raporunda doğrulanan değerler:

- 818 içerik: 419 film ve 399 dizi
- 10.000 sentetik kullanıcı reytingi, 1.200 sentetik kullanıcı ve reyting alan 580 içerik
- Sentetik kullanıcı puanı ortalaması: 7,23
- TMDB kaynaklı içerik puanı ortalaması: 5,73
- Türkiye ile sınırlı Yayın Analizi görünümünde 5 kanala dağılmış 6 TVMaze yayın kaydı
- Tamamlanan Power BI sayfaları: Genel Bakış, Yayın Analizi ve Reyting Analizi

14.09.2026 tarihli ayrı Oracle doğrulamasında 740 içerik, 111 kanal, 883 yayın kaydı ve 395 günlük tarih boyutu vardı. Bunlar eski tarihli veri ambarı sayılarıdır; Power BI'daki Türkiye yayın görünümünün 6 kayıtlık kapsamıyla karıştırılmamalıdır. API sonuçları ve yenileme tarihiyle sayılar değişebilir.

## Mimari

```text
TMDB ─────┐
          ├─> Python extractors ─> JSON staging ─> Apache Hop ─> Oracle
TVMaze ───┘                                              │
Faker ─────> Sentetik reyting JSON'u ────────────────────┘
                                                         │
                                                         └─> Power BI
```

## Veri modeli

Temel boyut tabloları:

- `DIM_CONTENT`
- `DIM_GENRE`
- `DIM_CHANNEL`
- `DIM_DATE`

Köprü ve fact tabloları:

- `BRIDGE_CONTENT_GENRE`
- `FACT_CONTENT_METRICS`
- `FACT_BROADCAST`
- `FACT_USER_RATING`

`FACT_USER_RATING.IS_SYNTHETIC = 1`, reytingin Faker ile üretildiğini belirtir. Bu puanlar gerçek izleyici reytingleri olarak yorumlanmamalıdır.

## Kurulum

1. Python sanal ortamını oluşturun ve bağımlılıkları kurun:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. `.env.example` dosyasını `.env` olarak kopyalayın ve kendi bağlantı bilgilerinizi girin.
3. Apache Hop içinde `DIGITURK_ORACLE` bağlantısının mevcut Oracle şemasını gösterdiğini kontrol edin.

Gizli anahtarların bulunduğu `.env` dosyası Git'e eklenmez.

## Çalıştırma

Yalnızca API verilerini ve sentetik reytingleri üretmek için:

```powershell
.\scripts\run_daily_extract.cmd
```

Oracle şema migration'larını uygulamak için:

```powershell
.\scripts\apply_migrations.cmd
```

Tüm günlük ETL akışını Apache Hop üzerinden çalıştırmak için:

```powershell
.\scripts\run_scheduled_etl.cmd
```

İş akışının sırası:

1. Çok ülkeli TMDB ve TVMaze verilerini çekme
2. Faker reytinglerini üretme
3. Oracle migration'larını uygulama
4. TMDB ve TVMaze staging tablolarını Hop ile yükleme
5. Faker staging tablosunu toplu yükleme
6. Boyut, köprü ve fact tablolarını set tabanlı Oracle `MERGE` işlemleriyle yükleme

## Ayarlanabilir değişkenler

| Değişken | Varsayılan |
|---|---|
| `TMDB_COUNTRIES` | `TR,US,GB,KR,FR` |
| `TMDB_PAGES_PER_COUNTRY` | `3` |
| `TVMAZE_COUNTRIES` | `TR,US,GB,KR,FR` |
| `TVMAZE_DAYS_BACK` | `6` |
| `FAKER_RATING_COUNT` | `10000` |
| `FAKER_USER_COUNT` | `1200` |
| `FAKER_SEED` | `20260911` |

## Testler

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Testler; ülke normalizasyonu, TMDB tekilleştirme, TVMaze eksik alan yönetimi, Faker tekrar üretilebilirliği ve Oracle migration ayrıştırmasını kapsar.

## Analiz ve Power BI

- Hazır Oracle analizleri: [`sql/analysis_queries.sql`](sql/analysis_queries.sql)
- Power BI ilk kurulum adımları ve DAX örnekleri: [`docs/POWER_BI_GUIDE.md`](docs/POWER_BI_GUIDE.md)
- Power BI dosyası: `reports/powerbi/Entertainment_Warehouse.pbix`

Genel Bakış sayfasındaki TMDB puanı ile Reyting Analizi sayfasındaki sentetik kullanıcı puanı farklı veri kaynaklarından gelir. Genel Bakış'taki popülerlik grafiğinin tarihi, içeriklerin çıkış tarihini değil TMDB verisinin alım tarihini gösterir. Reyting Analizi sayfasında en yüksek puanlı içerikler grafiği, en az 10 sentetik reyting alan içerikleri listeler.

TVMaze ve TMDB farklı kimlik sistemleri kullandığı için yayın başlıklarının tamamı içerik kataloğuyla otomatik eşleşmeyebilir. Yayınların kanal, ülke, tarih ve süre analizleri bu sınırlamadan etkilenmez.
