# video_to_ppt — Video'dan Otomatik Slayt Üretici

> **Geliştirme aşamasında** — proje aktif olarak geliştirilmektedir, bazı özellikler eksik veya değişkenlik gösterebilir.

YouTube videolarını analiz ederek sahne geçişlerini tespit eden ve her sahne için bir slayt oluşturan masaüstü uygulaması. Çıktı `.pptx` formatındadır.

## Özellikler

- **Akış modu** — video indirmeden doğrudan YouTube'dan frame okur
- **İndirme modu** — videoyu kalıcı olarak kaydedip işler
- **Toplu işlem** — birden fazla URL aynı anda verilebilir
- **Sahne tespiti** — piksel farkı algoritmasıyla otomatik kesme noktası bulur
- **Zaman damgası** — her slayta `SS:DD:ms` formatında konum bilgisi eklenir
- **PPT editörü** — dönüştürme tamamlandıktan sonra otomatik açılan düzenleme sekmesi:
  - Slaytları önizleme ve seçme
  - Seçili slaytları silme
  - Birden fazla slayt görselini tek bir grid görüntüsüne birleştirme
  - Slayt görselini yüksek çözünürlüklü versiyonuyla değiştirme (orijinal video akışından yeniden çeker)
  - Seçili slaytları GIF animasyonuna dönüştürme
  - Slayta karşılık gelen video segmentindeki frame'ler arasında gezinip istenen kareyi seçme
- **Ayarlar** — video kayıt klasörü ve diğer tercihler kalıcı olarak saklanır

## Gereksinimler

- **Python 3.9+**
- **Windows 10/11** (Linux/macOS desteklenmez)
- **ffmpeg** — proje kök dizinine `ffmpeg.exe` koy veya sistem PATH'ine ekle
  - İndir: [ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## Kurulum

```bash
# 1. Sanal ortam oluştur
python -m venv venv
venv\Scripts\activate

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. ffmpeg.exe dosyasını proje kök dizinine koy
# (veya sistem PATH'inde olduğundan emin ol)
```

## Çalıştırma

```bash
py -3.13 main.py
```

## Kullanım

1. **"Video ➔ Slayt"** sekmesine geç
2. URL alanına bir veya birden fazla YouTube linki gir (her satıra bir tane)
3. Videoyu diske kaydetmek istiyorsan **"Videoyu kalıcı olarak kaydet"** kutusunu işaretle ve klasör seç
4. **"Dönüştürmeyi Başlat"** butonuna tıkla
5. İşlem tamamlandığında `.pptx` dosyası proje dizininde oluşur

## Proje Yapısı

```
video_to_ppt/
├── main.py                        # Giriş noktası
├── config/settings.py             # Sabitler ve varsayılan değerler
├── domain/                        # Arayüzler (soyut katman)
├── core/                          # İş mantığı (generator, engine, thread yönetimi)
├── infrastructure/                # Somut implementasyonlar (yt-dlp, pptx, ffmpeg)
│   └── frame_adapters/            # FFmpeg pipe ve dosya tabanlı frame okuyucular
├── strategies/                    # Değiştirilebilir algoritmalar
│   ├── scene_detection/           # RobustDiff, AbsDiff
│   └── frame_sampling/            # TimeBasedSampler, EveryFrameSampler
├── factories/                     # Bağımlılıkları bir araya getiren factory
├── gui/                           # Tkinter arayüzü
├── services/                      # Yardımcı servisler (GIF, grid, segment)
└── utils/                         # Görüntü, zaman, ffmpeg yardımcıları
```

## Teknik Detaylar

**Sahne tespiti algoritması:**
İki ardışık frame arasındaki piksel farkı ortalaması hesaplanır ve 255'e bölünerek normalize edilir. Bu oran `0.02`'yi (`%2`) aştığında yeni sahne başladığı kabul edilir.

**Frame örnekleme:**
Performans için varsayılan olarak saniyede 1 frame işlenir (`TimeBasedSampler`). Bu değer `config/settings.py` içinde `DEFAULT_FPS` sabiti ile değiştirilebilir.

**Thread mimarisi:**
GUI ile dönüştürme işlemi farklı thread'lerde çalışır. İletişim `queue.Queue` üzerinden sağlanır; GUI 100ms'de bir kuyruğu kontrol ederek ilerleme bilgisini günceller.

## Bağımlılıklar

| Paket | Kullanım |
|---|---|
| `yt-dlp` | YouTube video bilgisi ve akış URL'si |
| `opencv-python` | Frame okuma ve piksel farkı hesaplama |
| `python-pptx` | PowerPoint dosyası oluşturma |
| `Pillow` | Görüntü yeniden boyutlandırma ve sıkıştırma |
| `numpy` | Frame verisi üzerinde dizi işlemleri |
| `ffmpeg` (harici) | Video codec işleme ve ham frame akışı |
