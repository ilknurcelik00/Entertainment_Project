# Power BI Güncelleme Rehberi

Bu rehber, Oracle veri ambarına eklenen uluslararası içerik ve sentetik reyting verilerini mevcut `Entertainment_Warehouse.pbix` raporuna eklemek içindir.

> **Önemli:** `FACT_USER_RATING` tablosundaki veriler gerçek kullanıcı verisi değildir. Faker ile üretilmiş, sunum ve analiz amaçlı sentetik veridir.

## 1. Oracle tablolarını yenileme

1. Power BI Desktop'ta `reports/powerbi/Entertainment_Warehouse.pbix` dosyasını açın.
2. **Giriş → Veri dönüştürme → Veri kaynağı ayarları** bölümünde Oracle bağlantısını kontrol edin.
3. **Veri al → Oracle veritabanı** ile `FACT_USER_RATING` tablosunu rapora ekleyin.
4. Mevcut tablolarda yeni gelen şu alanları işaretleyin:
   - `DIM_CONTENT[ORIGIN_COUNTRY_CODE]`
   - `DIM_CHANNEL[COUNTRY_CODE]`
5. **Yenile** düğmesine basın.

## 2. Model ilişkileri

Model görünümünde şu ilişkileri oluşturun:

| Bir tarafı | Çok tarafı | Kardinalite | Filtre yönü |
|---|---|---|---|
| `DIM_CONTENT[CONTENT_KEY]` | `FACT_USER_RATING[CONTENT_KEY]` | Birden çoğa | Tek yön |
| `DIM_DATE[DATE_KEY]` | `FACT_USER_RATING[DATE_KEY]` | Birden çoğa | Tek yön |

`FACT_USER_RATING` ile başka bir fact tablo arasında doğrudan ilişki kurmayın.

## 3. Reyting ölçüleri

```DAX
Sentetik Reyting Sayısı =
CALCULATE(
    COUNTROWS(FACT_USER_RATING),
    FACT_USER_RATING[IS_SYNTHETIC] = 1
)
```

```DAX
Ortalama Kullanıcı Reytingi =
CALCULATE(
    AVERAGE(FACT_USER_RATING[RATING]),
    FACT_USER_RATING[IS_SYNTHETIC] = 1
)
```

```DAX
Benzersiz Kullanıcı Sayısı =
CALCULATE(
    DISTINCTCOUNT(FACT_USER_RATING[USER_ID]),
    FACT_USER_RATING[IS_SYNTHETIC] = 1
)
```

```DAX
Reyting Alan İçerik Sayısı =
CALCULATE(
    DISTINCTCOUNT(FACT_USER_RATING[CONTENT_KEY]),
    FACT_USER_RATING[IS_SYNTHETIC] = 1
)
```

```DAX
Kullanıcı - TMDB Puan Farkı =
[Ortalama Kullanıcı Reytingi] - [Ortalama Puan]
```

## 4. Yeni “Reyting Analizi” sayfası

Önerilen düzen:

1. Üst sıraya dört kart ekleyin:
   - Sentetik Reyting Sayısı
   - Ortalama Kullanıcı Reytingi
   - Benzersiz Kullanıcı Sayısı
   - Reyting Alan İçerik Sayısı
2. Sol tarafa ülkeye göre içerik sayısı için kümelenmiş çubuk grafik ekleyin:
   - Eksen: `DIM_CONTENT[ORIGIN_COUNTRY_CODE]`
   - Değer: `Toplam İçerik`
3. Sağ tarafa kullanıcı ülkesine göre ortalama reyting grafiği ekleyin:
   - Eksen: `FACT_USER_RATING[COUNTRY_CODE]`
   - Değer: `Ortalama Kullanıcı Reytingi`
4. Alt bölüme tarihe göre ortalama kullanıcı reytingi çizgi grafiği ekleyin:
   - X ekseni: `DIM_DATE[FULL_DATE]`
   - Y ekseni: `Ortalama Kullanıcı Reytingi`
5. Bir tablo ekleyin:
   - `DIM_CONTENT[TITLE]`
   - `DIM_CONTENT[CONTENT_TYPE]`
   - `DIM_CONTENT[ORIGIN_COUNTRY_CODE]`
   - `Sentetik Reyting Sayısı`
   - `Ortalama Kullanıcı Reytingi`
   - `Ortalama Puan`
   - `Kullanıcı - TMDB Puan Farkı`
6. Sayfaya içerik türü, içerik ülkesi ve kullanıcı ülkesi dilimleyicileri ekleyin.

## 5. Yayın Analizi sayfasını genişletme

- `DIM_CHANNEL[COUNTRY_CODE]` alanını dilimleyici olarak ekleyin.
- Ülkelere göre yayın sayısını gösteren bir çubuk grafik oluşturun.
- Mevcut kanal ve günlük yayın görselleri bu ülke filtresine tepki vermelidir.
- TVMaze ile TMDB başlıkları her zaman birebir eşleşmediği için bazı yayınların `CONTENT_KEY` alanı boş olabilir. Kanal, ülke, tarih ve süre analizleri bundan etkilenmez.

## 6. Kontrol listesi

- Kartta sentetik reyting sayısı `10.000` görünmeli.
- Ortalama kullanıcı reytingi yaklaşık `7,23` görünmeli.
- Benzersiz kullanıcı sayısı `1.200` görünmeli.
- Ülke filtrelerinde en az `TR`, `US`, `GB`, `KR` ve `FR` bulunmalı.
- Reyting sayfasında “Sentetik veri” açıklaması görünür olmalı.
