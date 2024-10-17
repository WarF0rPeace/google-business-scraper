<div id="top"></div>

![GitHub Contributors](https://img.shields.io/github/contributors/WarF0rPeace/google-business-scraper.svg?style=for-the-badge) ![GitHub Forks](https://img.shields.io/github/forks/WarF0rPeace/google-business-scraper.svg?style=for-the-badge) ![GitHub Stars](https://img.shields.io/github/stars/WarF0rPeace/google-business-scraper.svg?style=for-the-badge) ![GitHub Issues](https://img.shields.io/github/issues/WarF0rPeace/google-business-scraper.svg?style=for-the-badge) ![GitHub License](https://img.shields.io/github/license/WarF0rPeace/google-business-scraper.svg?style=for-the-badge) ![GitHub License](https://img.shields.io/github/downloads/warf0rpeace/google-business-scraper/total.svg?style=for-the-badge)

<br />
<div align="center">
  <a href="https://github.com/WarF0rPeace/google-business-scraper">
    <img src="https://i.ibb.co/j3FTTYf/logo.png" alt="Logo" width="150" height="150">
  </a>

  <h3 align="center">Google Business Scraper</h3>

  <p align="center">
    Google Earth üzerindeki işletmeleri kolayca sorgulayıp veri toplayın!
    <br />
    <a href="https://github.com/WarF0rPeace/google-business-scraper/issues">Hata Raporla</a>
    ·
    <a href="https://github.com/WarF0rPeace/google-business-scraper/issues">Öneri Yap</a>
  </p>
</div>

<details>
  <summary>İçerik Tablosu</summary>
  <ol>
    <li><a href="#🛠-Kurulum">Kurulum</a></li>
    <li><a href="#▶-Kullanım">Kullanım</a></li>
    <li><a href="#📝-Lisans">Lisans</a></li>
  </ol>
</details>

## 🛠 Kurulum

Bu projeyi güvenli bir şekilde kullanabilmek için bir sanal ortam oluşturup bağımlılıkları kurabilirsiniz. Ancak, projeyi hızlı bir şekilde kullanmak isteyenler için, `Google Business Scraper.exe` dosyasını da doğrudan indirebilirsiniz.

1. **Projeyi Klonlama:** Git kullanarak projeyi bilgisayarınıza indirin:

    ```bash
    git clone https://github.com/WarF0rPeace/google-business-scraper.git
    cd google-business-scraper
    ```

2. **Sanal Ortam Oluşturma:** Python'ın `venv` modülü ile sanal ortam oluşturun:

    ```bash
    python -m venv venv
    ```

3. **Sanal Ortamı Aktifleştirme:**

   - **Windows** için:

     ```bash
     venv\Scripts\activate
     ```

   - **MacOS/Linux** için:

     ```bash
     source venv/bin/activate
     ```

4. **Bağımlılıkları Yükleme:** Sanal ortam aktifken, gerekli bağımlılıkları yükleyin:

    ```bash
    pip install -r requirements.txt
    ```

   Alternatif olarak, aşağıdaki bağlantıdan `Google Business Scraper.exe` dosyasını indirerek hemen kullanmaya başlayabilirsiniz:
   - [Google Business Scraper.exe İndir](https://github.com/WarF0rPeace/google-business-scraper/releases/latest/download/Google.Business.Scraper.exe)


## ▶ Kullanım

Eğer `Google Business Scraper.exe` dosyasını indirdiyseniz, indirdiğiniz dosyayı çift tıklayarak çalıştırabilirsiniz. Uygulama açıldıktan sonra işletme sorgularını manuel olarak GUI üzerinden veya `.txt` dosyası yükleyerek ekleyebilirsiniz. Toplanan verileri JSON, CSV veya Excel (XLSX) formatında dışa aktarabilirsiniz.

Eğer kaynak kodu kullanmak isterseniz, sanal ortamı etkinleştirdikten sonra uygulamayı çalıştırabilirsiniz:

```bash
python main.py
```

## 📝 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için [LICENSE](https://github.com/WarF0rPeace/google-business-scraper/blob/main/LICENSE) dosyasına bakabilirsiniz.
