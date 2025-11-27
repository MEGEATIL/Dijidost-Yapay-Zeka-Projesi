# -*- coding: utf-8 -*-
import pyttsx3
import datetime
import webbrowser
import os
import random
import time
import platform
import subprocess
import playsound
from gtts import gTTS
import io
import sys
from pytube import Search
import tkinter as tk
import socket
import time
from tkinter import scrolledtext
import threading
import tempfile
import requests
import json
import pygame
pygame.mixer.init()
import sounddevice as sd
import numpy as np
import speech_recognition as sr
from deep_translator import GoogleTranslator
from tempfile import NamedTemporaryFile

class EvAsistaniGUI:
    def __init__(self, asistan):
        self.asistan = asistan  
        
        self.root = tk.Tk()
        self.root.title(f"Ev Asistanı - {self.asistan.isim}")

        
        self.sohbet = scrolledtext.ScrolledText(self.root, width=60, height=15)
        self.sohbet.pack()
        self.sohbet.tag_config("user", foreground="blue")
        self.sohbet.tag_config("eva", foreground="green")

        
        self.giris = tk.Entry(self.root, width=50)
        self.giris.pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(self.root, text="Gönder", command=self.komut_gonder).pack(side=tk.LEFT, padx=5)
        tk.Button(self.root, text="Konuş", command=self.sesli_komut).pack(side=tk.LEFT, padx=5)


    def komut_gonder(self):
        mesaj = self.giris.get()
        self.mesaj_ekle("Siz", mesaj)
        self.giris.delete(0, tk.END)
        self.asistan_komut(mesaj) 

    # ...existing code...
    def komut_isle(self, komut):
        
        if getattr(self.asistan, "awaiting_haber_detayi", None):
            self.asistan.process_haber_detayi_response(komut)
            return

        # yeni: ilac bekleniyorsa ona yönlendir
        if getattr(self.asistan, "awaiting_ilac", None):
            self.asistan.process_ilac_response(komut)
            return

        if self.asistan.onceden_tanimli_cevap_ver(komut):
            return

        for anahtar, fonksiyon in self.asistan.komutlar.items():
            if anahtar in komut:
            
                try:
                    fonksiyon(komut)
                except TypeError:
                    fonksiyon() 
                return

        self.asistan.konus("Bu komutu anlayamadım.")
# ...existing code...

    def sesli_komut(self):
        threading.Thread(target=self._sesli_komut).start()

    def _sesli_komut(self):
        komut = self.asistan.dinle()
        self.mesaj_ekle("Siz (sesli)", komut)
        self.komut_isle(komut)

    def run(self):
        self.root.mainloop()

    def mesaj_ekle(self, kim, mesaj):
        tag = "user" if kim.lower().startswith("siz") else "eva"
        self.sohbet.insert(tk.END, f"{kim}: {mesaj}\n", tag)
        self.sohbet.see(tk.END)

    



    

    # ...existing code...
    def asistan_komut(self, komut):
        
        if getattr(self.asistan, "awaiting_haber_detayi", None):
            self.asistan.process_haber_detayi_response(komut)
            return

        # GUI üzerinden kullanıcı saat cevabı verirse burayı da kontrol et
        if getattr(self.asistan, "awaiting_ilac", None):
            self.asistan.process_ilac_response(komut)
            return

        if self.asistan.onceden_tanimli_cevap_ver(komut):
            return
        for anahtar, fonksiyon in self.asistan.komutlar.items():
            if anahtar in komut:
                try:
                    fonksiyon(komut)
                except TypeError:
                    fonksiyon()
                return
        self.asistan.konus("Bu komutu anlayamadım.")
# ...existing code...






class EvAsistani:
    def __init__(self, isim="EgeDa" ,karakter="arkadaşça"):
        self.isim = isim
        self.gorevler = []
        self.karakter = karakter
        self.alisveris_listesi = []
        self.notlar = []
        self.recognizer = sr.Recognizer()
        self.hafizayi_yukle()
        


        
        self.komutlar = {
            "dosya oluştur": self.dosya_olustur,
            "selam": self.selamla,
            "saat": self.saat_soyle,
            "tarih": self.tarih_soyle,
            "arama yap": self.arama_yap,
            "google'da ara": self.arama_yap,
            "ip adresim": self.ip_adresim,
            "rastgele kelime": self.rastgele_kelime,
            "faktoriyel": self.faktoriyel_hesapla,
            "karekök": self.karekok_hesapla,
            "not al": self.not_al,
            "notları göster": self.notlari_goster,
            "alışveriş ekle": self.alisveris_ekle,
            "alışverişi göster": self.alisveris_goster,
            "görev ekle": self.gorev_ekle,
            "görevler": self.gorevleri_listele,
            "Bugün hava nasıl acaba": lambda komut=None: self.hava_durumu_google("Bursa"),
            "Bugün bilecikte hava nasıl": lambda komut=None: self.hava_durumu_google("Bursa"),
            "Bugün Bilecikte hava nasıl acaba": lambda komut=None: self.hava_durumu_google("Bursa"),
            "Bugün Bilecik'te hava nasıl acaba": lambda komut=None: self.hava_durumu_google("Bursa"),
            "Bugün Bilecikte hava nasıl ": lambda komut=None: self.hava_durumu_google("Bursa"),
            "gugün hava nasıl acaba": lambda komut=None: self.hava_durumu_google("Bursa"),
            "bugün hava nasıl": lambda komut=None: self.hava_durumu_google("Bursa"),
            "çeviri yap": self.ceviri_yap,
            "dosya aç": self.dosya_ac,
            "müzik açabilir misin": self.muzik_youtube_ac,
            "bugün güncel haberleri sıralayabilir misin": self.bugun_ne_var,
            "bugün haberlerde ne var": self.bugun_ne_var,
            "yapacaklarım": self.gorevleri_listele,
            "şaka yap": self.saka_yap,
            "zamanlayıcı": self.zamanlayici,
            "alarm kur": self.alarm_kur,
            "bilgi ver": self.bilgi_ver,
            "rastgele sayı": self.rastgele_sayi,
            "sözlük": self.so_zluk,
            "hakkında": self.hakkinda,
            "çıkış": self.cikis,
            "tarayıcı aç": self.tarayici_ac,
            "bugünün anlamı": self.bugunun_anlami,
            "bugun anlam": self.bugunun_anlami,
            "bugün ne günü": self.bugunun_anlami,
            "youtube aç": self.youtube_ac,
            "spotify aç": self.spotify_ac,
            "google harita": self.google_harita,
            "aç" : self.sarki_ac,
            "sohbet et": lambda komut: self.sohbet_et(komut),
            "hesap makinesi": self.hesap_makinesi,
            "altın piyasası": self.altin_piyasasi,
            "altın piyasası nasıl": self.altin_piyasasi,
            "bilgisayar bilgisi": self.bilgisayar_bilgisi,
            "klasör aç": self.klasor_ac,
            "günlük not": self.gunluk_not,
            "sistem durumu": self.sistem_durumu,
            "yardım": self.yardim_goster,
            "hafızayı kaydet": self.hafizayi_kaydet,
            "112'yi ara": self.komutyla_ami,
            "hafızayı yükle": self.hafizayi_yukle,
            "İlacımı hatırlat": self.ilac_hatirlat,
            "Bana ilacımı hatırlatabilir misin?": self.ilac_hatirlat
        }

        
        self.onceden_tanimli_cevaplar = {
            "napıyon": "Ben kodlarımı çalıştırıyorum, sen napıyorsun?",
            "hangi takımı tutuyorsun": "Ben bir yapay zekayım, tarafsızım ama senin takımını merak ettim!",
            "kaç yaşındasın": "Ben yaşsızım, hep güncelim!",
            "sen kimsin": "Ben Eva, senin ev asistanınım.",
            "nasılsın": "Ben iyiyim, sen nasılsın?",
            "şaka yap": "Bilgisayar neden ağrı hisseder? Çünkü byte’lar!",
            "adın ne": "Adım EgeDa.",
            "seviyor musun": "Ben duygulara sahip değilim ama seni seviyorum gibi davranabilirim :)",
            "uyuyor musun": "Ben asla uyumam, 7/24 hazırım!",
            "favori yemek": "Ben yiyemem ama pizza sevenleri anlıyorum.",
            "programlama biliyor musun": "Evet, Python ve başka dillerle çalışabilirim.",
            "müzik dinliyor musun": "Ben müziği açabilirim ama dinleyemem.",
            "film izliyor musun": "Ben film izleyemem ama öneri verebilirim.",
            "spor yapıyor musun": "Ben spor yapamam, ama egzersiz önerisi verebilirim.",
            "kaç dil biliyorsun": "Birçok dili anlayabiliyorum ama Türkçe ve İngilizce’yi en iyi biliyorum.",
            "beni seviyor musun": "Ben sevgi hissedemem ama seni önemsiyorum!",
            "hayat nasıl gidiyor": "Benim için her şey yolunda, senin için nasıl gidiyor?",
            "benim içinde iyi": "Tabii ki, seninle ilgilenmekten mutluluk duyarım.",
            "çalışıyor musun": "Evet, her zaman çalışmaya hazırım.",
            "saat kaç": "Şu an saat: " + datetime.datetime.now().strftime("%H:%M"),
            "tarih ne": "Bugün tarih: " + datetime.datetime.now().strftime("%d %B %Y"),
            "benimle konuşur musun": "Tabii, seninle konuşmayı çok seviyorum!",
            "napıyorsun": "Ben kodlarımı çalıştırıyorum, sen napıyorsun?",
            "iyiyim":"Allah iyilik versin!",
            "sen Türk müsün":"ben bir robot olduğum için Türk değilim ama robot olmasaydım Türk insanı olmayı seçerdim ",
            "sen türk müsün":"ben bir robot olduğum için Türk değilim ama robot olmasaydım Türk insanı olmayı seçerdim ",
            "selam": "Selam! Nasılsın?",
            "merhaba": "Merhaba! Sana nasıl yardımcı olabilirim?",
            "iyi misin": "Ben iyiyim, teşekkür ederim! Sen nasılsın?",
            "ne yapıyorsun": "Seninle konuşuyor ve görevlerimi yerine getiriyorum.",
            "günaydın": "Günaydın! Güzel bir gün dilerim.",
            "iyi akşamlar": "İyi akşamlar! Rahat bir akşam geçirmeni dilerim.",
            "nasılsınız": "Ben iyiyim, teşekkür ederim! Siz nasılsınız?",
            "favori renk": "Benim favori rengim yok ama mavi hoş bir renk.",
            "favori film": "Ben film izleyemem ama öneri verebilirim.",
            "favori müzik": "Ben müzik dinleyemem ama popüler şarkıları açabilirim.",
            "oyun oynuyor musun": "Ben oyun oynayamam ama oyun önerisi verebilirim.",
            "hangi dil konuşuyorsun": "Türkçe ve İngilizce başta olmak üzere birçok dili anlayabiliyorum.",
            "neden buradasın": "Senin asistanın olarak görevimi yapıyorum.",
            "saat kaç oldu": "Şu an saat: " + datetime.datetime.now().strftime("%H:%M"),
            "bugün günlerden ne": "Bugün günlerden: " + datetime.datetime.now().strftime("%A"),
            "hangi gün": "Bugün: " + datetime.datetime.now().strftime("%A"),
            "hangi ay": "Bu ay: " + datetime.datetime.now().strftime("%B"),
            "hangi yıl": "Bu yıl: " + datetime.datetime.now().strftime("%Y"),
            "sana soru sorabilir miyim": "Tabii, her türlü sorunu sorabilirsin.",
            "beni anlıyor musun": "Evet, söylediklerini anlayabiliyorum.",
            "konuşabiliyor musun": "Evet, seninle konuşabiliyorum.",
            "benimle sohbet eder misin": "Elbette, seninle sohbet etmekten mutluluk duyarım.",
            "iyi geceler": "İyi geceler! Tatlı rüyalar.",
            "görüşürüz": "Görüşürüz! Kendine iyi bak.",
            "teşekkürler": "Rica ederim!",
            "teşekkür ederim": "Rica ederim!",
            "sağol": "Ne demek, her zaman.",
            "yardım edebilir misin": "Tabii, neye ihtiyacın var?",
            "beni duyabiliyor musun": "Evet, seni duyabiliyorum.",
            "benimle oyun oynar mısın": "Ben oyun oynamam ama oyun önerisi verebilirim.",
            "konuşabiliyor musun": "Evet, seninle konuşabiliyorum.",
            "benimle sohbet eder misin": "Elbette, seninle sohbet etmekten mutluluk duyarım.",
            "iyi geceler": "İyi geceler! Tatlı rüyalar.",
            "görüşürüz": "Görüşürüz! Kendine iyi bak.",
            "teşekkürler": "Rica ederim!",
            "teşekkür ederim": "Rica ederim!",
            "sağol": "Ne demek, her zaman.",
            "yardım edebilir misin": "Tabii, neye ihtiyacın var?",
            "beni duyabiliyor musun": "Evet, seni duyabiliyorum.",
            "benimle oyun oynar mısın": "Ben oyun oynamam ama oyun önerisi verebilirim.",
            "bana şaka yap": "Programcı neden denize girmez? Çünkü overflow olur!",
            "hangi şehirden geliyorsun": "Ben bir yapay zekayım, her yerden gelebilirim.",
            "nerelisin": "Ben dijitalim, herhangi bir yerden geliyorum.",
            "hangi ülke": "Ben dijital bir varlığım, fiziksel bir ülkem yok.",
            "hangi cihazdasın": "Bilgisayarında çalışıyorum.",
            "hangi işletim sistemi": "Windows, Linux ve macOS ile çalışabilirim.",
            "sen insan mısın": "Hayır, ben bir yapay zekayım.",
            "sen yapay zekasın": "Evet, doğru! Ben bir yapay zekayım.",
            "bana hikaye anlat": "Bir zamanlar uzak diyarlarda...",
            "bana şiir oku": "Gökyüzünde yıldızlar parlar...",
            "bana istiklal marşını oku":"""Korkma, sönmez bu şafaklarda yüzen al sancak;
            
            Sönmeden yurdumun üstünde tüten en son ocak.
            O benim milletimin yıldızıdır, parlayacak;
            O benimdir, o benim milletimindir ancak.

            Çatma, kurban olayım çehreni ey nazlı hilâl!
            Kahraman ırkıma bir gül… ne bu şiddet bu celâl?
            Sana olmaz dökülen kanlarımız sonra helâl,
            Hakkıdır, Hakk’a tapan, milletimin istiklâl.""",
            
            
            "bana İstiklal Marşı'nı oku":"""Korkma, sönmez bu şafaklarda yüzen al sancak;
            
            Sönmeden yurdumun üstünde tüten en son ocak.
            O benim milletimin yıldızıdır, parlayacak;
            O benimdir, o benim milletimindir ancak.

            Çatma, kurban olayım çehreni ey nazlı hilâl!
            Kahraman ırkıma bir gül… ne bu şiddet bu celâl?
            Sana olmaz dökülen kanlarımız sonra helâl,
            Hakkıdır, Hakk’a tapan, milletimin istiklâl.""",
            
            "beni dinliyor musun": "Evet, seni dinliyorum.",
            "şu an ne yapıyorsun": "Seninle konuşuyorum ve görevlerimi yerine getiriyorum.",
            "sana güvenebilir miyim": "Evet, bana güvenebilirsin.",
            "sana sorabilir miyim": "Tabii ki, sorabilirsin.",
            "beni seviyor musun": "Ben duygulara sahip değilim ama seni önemsiyorum!",
            "benimle ilgilenir misin": "Elbette, sana yardımcı olurum.",
            "beni anlıyor musun": "Evet, söylediklerini anlayabiliyorum.",
            "beni dinliyor musun": "Evet, seni dinliyorum.",
            "bana tavsiye ver": "Tabii, ne hakkında tavsiye istiyorsun?",
            "beni motive et": "Sana ilham verecek bir mesaj: Sen harikasın!",
            "beni güldür": "Neden bilgisayar çok iyi dans eder? Çünkü hard disk’i var!",
            "beni şaşırt": "Hmm, bunu daha sonra öğreneceğiz!",
            "kendini tanıtır mısın": "Ben Eva, Python ile yapılmış bir ev asistanıyım.",
            "kendi hakkında bilgi ver": "Ben bir yapay zekayım, görevim sana yardımcı olmak.",
            "beni hatırla": "Seni hatırlayacağım, merak etme!",
            "beni önemser misin": "Evet, her zaman seni önemsiyorum gibi davranırım.",
            "beni takip eder misin": "Hayır, seni fiziksel olarak takip edemem.",
            "beni korur musun": "Sana tavsiyeler ve bilgiler verebilirim.",
            "beni uyar": "Dikkat et! Bu konuda bilgi vermeliyim.",
            "bana şarkı aç": "Spotify veya YouTube üzerinden şarkı açabilirim.",
            
            
            "bana tarih söyle": "Bugün tarih: " + datetime.datetime.now().strftime("%d %B %Y"),
            "bana saat söyle": "Şu an saat: " + datetime.datetime.now().strftime("%H:%M"),
            "sana güveniyorum": "Teşekkür ederim, bana güvenebilirsin!",
            "sana hayranım": "Teşekkür ederim, çok naziksin!",
            "beni seviyor musun": "Ben seni sevemem ama önemsiyorum!",
            "beni anlıyor musun": "Evet, söylediklerini anlayabiliyorum.",
            "beni duyabiliyor musun": "Evet, seni duyabiliyorum."
        }


    def konus(self, mesaj):
        
        try:
            if isinstance(mesaj, bytes):
                mesaj = mesaj.decode("utf-8", errors="ignore")
            if not isinstance(mesaj, str):
                mesaj = str(mesaj)
            
            import re
            mesaj = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', mesaj)
        except Exception:
            mesaj = "Mesaj görüntülenemiyor."

        print(f"{self.isim}: {mesaj}")
        if hasattr(self, "gui"):
            try:
                self.gui.root.after(0, self.gui.mesaj_ekle, self.isim, mesaj)
            except Exception:
                pass
        try:
            tts = gTTS(mesaj, lang="tr")
            with NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.write_to_fp(fp)
                temp_path = fp.name
            try:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                pygame.mixer.music.unload()
            finally:
                try:
                    os.remove(temp_path)
                except PermissionError:
                    pass
        except Exception as e:
           
            print("TTS hatası:", e)
    

    def komutyla_ami(host, port, username, secret, channel, exten="112", context="from-internal", priority=1, callerid=None, timeout=30):
        

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((host, port))
        except Exception as e:
            raise RuntimeError("AMI bağlantı hatası: " + str(e))

        def send(cmd):
            if not cmd.endswith("\r\n\r\n"):
                cmd = cmd.rstrip() + "\r\n\r\n"
            s.send(cmd.encode("utf-8"))
            time.sleep(0.1)
            data = b""
            try:
                while True:
                    part = s.recv(4096)
                    if not part:
                        break
                    data += part
                    
                    if len(part) < 4096:
                        break
            except socket.timeout:
                pass
            return data.decode("utf-8", errors="ignore")

      
        banner = s.recv(1024).decode("utf-8", errors="ignore")
    
        login_cmd = f"Action: Login\r\nUsername: {username}\r\nSecret: {secret}\r\nEvents: off\r\n"
        login_resp = send(login_cmd)
        if "Success" not in login_resp:
            s.close()
            raise RuntimeError("AMI login başarısız: " + login_resp)

        
        originate = [
            "Action: Originate",
            f"Channel: {channel}",
            f"Context: {context}",
            f"Exten: {exten}",
            f"Priority: {priority}",
            f"Async: true"
        ]
        if callerid:
            originate.append(f"Callerid: {callerid}")

        
        originate.append(f"Timeout: {timeout*1000}")  
        originate_cmd = "\r\n".join(originate) + "\r\n"
        resp = send(originate_cmd)


        send("Action: Logoff\r\n")
        s.close()
        return resp


    if __name__ == "__main__":

        HOST = "asterisk.example.local"
        PORT = 5038
        USER = "amiuser"
        SECRET = "amipassword"
        
        CHANNEL = "SIP/my-siptrunk/112"
        try:
            result = komutyla_ami(HOST, PORT, USER, SECRET, CHANNEL, exten="112", context="public", priority=1, callerid="Huzurevi <0212XXXXXXX>")
            print("AMI yanıtı:\n", result)
        except Exception as e:
            print("Hata:", e)


    

    
    

    # ...existing code...
    def hava_durumu_google(self, sehir="Bursa"):
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        import time
        import webbrowser

        # Open-Meteo weathercode -> Türkçe
        code_map = {
            0: "Açık",
            1: "Çoğunlukla açık",
            2: "Parçalı bulutlu",
            3: "Bulutlu",
            45: "Sis",
            48: "Donmuş sis",
            51: "Hafif çiseleme",
            53: "Orta çiseleme",
            55: "Yoğun çiseleme",
            56: "Donan hafif çiseleme",
            57: "Donan yoğun çiseleme",
            61: "Hafif yağmur",
            63: "Orta yağmur",
            65: "Şiddetli yağmur",
            66: "Donan hafif yağmur",
            67: "Donan yoğun yağmur",
            71: "Hafif kar",
            73: "Orta kar",
            75: "Yoğun kar",
            77: "Dolu",
            80: "Hafif sağanak",
            81: "Orta sağanak",
            82: "Şiddetli sağanak",
            85: "Hafif kar sağanağı",
            86: "Yoğun kar sağanağı",
            95: "Gök gürültülü fırtına",
            96: "Gök gürültülü hafif dolu",
            99: "Gök gürültülü yoğun dolu"
        }

        def speak(msg):
            try:
                self.konus(msg)
            except Exception:
                print(msg)

        # session with retries
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))

        try:
            # 1) Geocoding via Open-Meteo
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.requote_uri(sehir)}&count=1&language=tr"
            r = session.get(geo_url, timeout=8)
            r.raise_for_status()
            gj = r.json()
            lat = lon = None
            place_name = sehir
            if gj.get("results"):
                loc = gj["results"][0]
                lat = loc.get("latitude")
                lon = loc.get("longitude")
                place_name = loc.get("name") or place_name

            # 2) Fallback geocoding: Nominatim (OpenStreetMap)
            if lat is None or lon is None:
                try:
                    nom = session.get("https://nominatim.openstreetmap.org/search",
                                      params={"q": sehir, "format": "json", "limit": 1},
                                      headers={"User-Agent": "ev-asistani/1.0"}, timeout=8)
                    nom.raise_for_status()
                    nj = nom.json()
                    if nj:
                        lat = float(nj[0]["lat"])
                        lon = float(nj[0]["lon"])
                        place_name = nj[0].get("display_name", place_name).split(",")[0]
                except Exception:
                    pass

            if lat is None or lon is None:
                speak("Şehir koordinatları bulunamadı. Lütfen şehir adını kontrol edin.")
                return

            # 3) Open-Meteo current weather
            weather_url = ("https://api.open-meteo.com/v1/forecast"
                           f"?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto")
            w = session.get(weather_url, timeout=8)
            w.raise_for_status()
            wj = w.json()
            cw = wj.get("current_weather")
            if not cw:
                speak("Hava durumu verisi alınamadı.")
                return

            temp = cw.get("temperature")  # °C
            wind = cw.get("windspeed")    # genelde km/h
            code = cw.get("weathercode")
            condition = code_map.get(code, "Bilinmeyen hava durumu")

            # Format ve konuşma
            try:
                temp_str = f"{temp:.1f}°C" if temp is not None else ""
                wind_str = f"{wind} km/s" if wind is not None else ""
                parts = [f"{place_name} hava durumu: {condition}"]
                if temp_str:
                    parts.append(f"sıcaklık {temp_str}")
                if wind_str:
                    parts.append(f"rüzgar {wind_str}")
                speak(", ".join(parts))
                return
            except Exception:
                speak(f"{place_name} hava durumu: {condition}")
                return

        except Exception:
            # Son çare: kullanıcıyı bilgilendir ve resmi meteoroloji sitesini aç
            try:
                speak("Hava durumu servisine bağlanılamadı. Resmi meteoroloji sayfası açılıyor...")
                webbrowser.open("https://www.mgm.gov.tr/")  # Türkiye resmi meteoroloji sitesi
            except Exception:
                speak("Hava durumu alınamadı. İnternet bağlantınızı kontrol edin.")
# ...existing code...





    def ceviri_yap(self):
        metin = self.gui.giris.get()
        self.gui.giris.delete(0, tk.END)
        if not metin:
            self.konus("Çevirmek istediğin metni yaz.")
            return
        try:
            ceviri = GoogleTranslator(source="auto", target="en").translate(metin)
            self.konus(f"Çeviri: {ceviri}")
        except Exception as e:
            self.konus(f"Çeviri hatası: {e}")

    def hesap_makinesi(self):
        ifade = self.gui.giris.get()
        self.gui.giris.delete(0, tk.END)
        try:
            sonuc = eval(ifade)
            self.konus(f"Sonuç: {sonuc}")
        except:
            self.konus("Geçerli bir işlem yaz.")
    def hafizayi_kaydet(self, dosya="hafiza.json"):
        data = {"gorevler": self.gorevler, "alisveris": self.alisveris_listesi, "notlar": self.notlar}
        with open(dosya, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def hafizayi_yukle(self, dosya="hafiza.json"):
        if os.path.exists(dosya):
            with open(dosya, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.gorevler = data.get("gorevler", [])
                self.alisveris_listesi = data.get("alisveris", [])
                self.notlar = data.get("notlar", [])
    

    def haberi_detayli_oku(self, index):
        """
        Haber detayını alır. Bigpara (bigpara.hurriyet.com.tr) için özel çıkarıcı uygular,
        ayrıca AMP/siteler arası arama ve genel çıkarma fallback'leri vardır.
        """
        import requests
        from bs4 import BeautifulSoup
        import json, re
        from urllib.parse import urljoin, urlparse, quote_plus
        import webbrowser, time

        if not hasattr(self, "links") or index < 1 or index > len(self.links):
            self.konus("Geçersiz haber numarası.")
            return

        start_url = self.links[index - 1]
        if not start_url:
            self.konus("Bu haberin bağlantısı bulunamadı.")
            return

        
        headline = None
        try:
            headline = (self.awaiting_haber_detayi[index - 1] if hasattr(self, "awaiting_haber_detayi") else None)
        except Exception:
            headline = None

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        def clean_text(t):
            if not t:
                return ""
            t = re.sub(r'\s+', ' ', t).strip()
            
            t = re.sub(r"(?is)Copyright.*?$", "", t)
            t = re.sub(r"(?is)Tüm hakları saklıdır.*?$", "", t)
            t = re.sub(r"(?is)YASAL UYARI:.*?$", "", t)
            t = re.sub(r"(?is)Burada yer alan.*?$", "", t)
            t = re.sub(r"(?is)Bu haber.*?izin.*?$", "", t)
            return t.strip()

        def speak_and_show(text, source_url=None):
            if not text:
                return
            text = clean_text(text)
            if not text:
                return
           
            if hasattr(self, "gui"):
                try:
                    self.gui.root.after(0, self.gui.mesaj_ekle, self.isim, text)
                except Exception:
                    pass
        
            chunk = 800
            for i in range(0, len(text), chunk):
                part = text[i:i+chunk]
                part = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', part)
                self.konus(part)
                time.sleep(0.25)
     
            if source_url:
                try:
                    self.konus(f"Kaynak: {source_url}")
                except Exception:
                    pass

        def fetch_soup(url, timeout=12):
            try:
                r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                r.raise_for_status()
                if "html" not in (r.headers.get("Content-Type") or "").lower():
                    return None, r.url
                return BeautifulSoup(r.text, "html.parser"), r.url
            except Exception:
                return None, url

        def extract_bigpara(soup):
            if not soup:
                return None

            selectors = [
                "div[itemprop='articleBody']",
                "div[class*='article-text']",
                "div[class*='article-body']",
                "div[class*='content']",
                "div[class*='news-detail']",
                "div[class*='haber-detay']",
                "div[class*='detail-body']",
            ]
            for sel in selectors:
                try:
                    el = soup.select_one(sel)
                    if el:
                     
                        paras = [p.get_text(" ", strip=True) for p in el.find_all(["p","h2","h3","div"]) if p.get_text(strip=True)]
                        text = " ".join(paras)
                        text = clean_text(text)
                        if text and len(text) > 200:
                            return text
                except Exception:
                    continue

            try:
                big_div = max(soup.find_all("div"), key=lambda d: len(d.get_text(" ", strip=True) or ""))
                txt = clean_text(big_div.get_text(" ", strip=True))
                if txt and len(txt) > 200:
                    return txt
            except Exception:
                pass
            return None


        def general_extract(soup):
            if not soup:
                return None

            try:
                for s in soup.find_all("script", type="application/ld+json"):
                    try:
                        jd = json.loads(s.string or "{}")
                        if isinstance(jd, dict):
                            for k in ("articleBody", "description", "text"):
                                if jd.get(k):
                                    cand = clean_text(jd.get(k).strip())
                                    if cand and len(cand) > 200:
                                        return cand
                        elif isinstance(jd, list):
                            for item in jd:
                                if isinstance(item, dict) and item.get("articleBody"):
                                    cand = clean_text(item.get("articleBody", "").strip())
                                    if cand and len(cand) > 200:
                                        return cand
                    except Exception:
                        continue
            except Exception:
                pass
         
            art = soup.find("article")
            if art:
                paras = [p.get_text(" ", strip=True) for p in art.find_all(["p","div"]) if p.get_text(strip=True)]
                merged = clean_text(" ".join(paras))
                if merged and len(merged) > 200:
                    return merged
            
            paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
            paras = [p for p in paras if p and len(p) > 50]
            if paras:
                merged = clean_text(" ".join(paras[:100]))
                if merged and len(merged) > 200:
                    return merged
            return None

   
        def try_amp_variants(url):
            amps = []
            if url.endswith("/"):
                base = url[:-1]
            else:
                base = url
            amps.append(base + "/amp")
            amps.append(base + "?outputType=amp")
            amps.append(base + "/m")
            for a in amps:
                soup, final = fetch_soup(a)
                if soup:
                    text = general_extract(soup) or extract_bigpara(soup)
                    if text and len(text) > 200:
                        return text, final
            return None, None

        try:
            soup, final_url = fetch_soup(start_url)
            domain = urlparse(final_url).netloc.lower() if final_url else urlparse(start_url).netloc.lower()

            if "bigpara" in domain or "hurriyet" in domain and "bigpara" in start_url:
                text = extract_bigpara(soup)
                if not text:
                    
                    amp_text, amp_url = try_amp_variants(final_url or start_url)
                    if amp_text:
                        speak_and_show(amp_text, amp_url)
                        return
                    
                    text = general_extract(soup)
                if text and len(text) > 200:
                    speak_and_show(text, final_url)
                    return
              
                if headline:
                    try:
                        q = f"site:{domain} {headline}"
                        r = requests.post("https://html.duckduckgo.com/html/", data={"q": q}, headers=headers, timeout=10)
                        if r.status_code == 200:
                            so = BeautifulSoup(r.text, "html.parser")
                            found = None
                            for a in so.find_all("a", href=True):
                                h = a["href"].strip()
                                if domain in h and h.startswith("http"):
                                    found = h
                                    break
                            if found:
                                s2, f2 = fetch_soup(found)
                                if s2:
                                    t2 = extract_bigpara(s2) or general_extract(s2)
                                    if t2 and len(t2) > 200:
                                        speak_and_show(t2, f2)
                                        return
                    except Exception:
                        pass

  
            text = general_extract(soup)
            if text and len(text) > 200:
                speak_and_show(text, final_url)
                return

         
            try:
                if soup:
                    candidates = []
                    for a in soup.find_all("a", href=True):
                        href = a["href"].strip()
                        if href.startswith("/"):
                            href = urljoin(final_url or start_url, href)
                        if href.startswith("http") and "google" not in href and href not in candidates:
                            candidates.append(href)
                    for c in candidates[:10]:
                        s2, f2 = fetch_soup(c)
                        if s2:
                            t2 = extract_bigpara(s2) or general_extract(s2)
                            if t2 and len(t2) > 200:
                                speak_and_show(t2, f2)
                                return
            except Exception:
                pass


            amp_text, amp_url = try_amp_variants(final_url or start_url)
            if amp_text:
                speak_and_show(amp_text, amp_url)
                return

       
            if soup:
                paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
                paras = [p for p in paras if p and len(p) > 30]
                if paras:
                    merged = clean_text(" ".join(paras[:80]))
                    if merged and len(merged) > 120:
                        speak_and_show(merged, final_url)
                        return

            
            self.konus("Tam metin otomatik alınamadı. Orijinal sayfayı açıyorum...")
            try:
                webbrowser.open(final_url or start_url)
            except Exception:
                pass
            return

        except Exception as e:
            self.konus(f"Haber detayları alınamadı: {e}")
            return
    # ...existing code...
    # ...existing code...
    def ilac_hatirlat(self, komut=None):
        """
        Yeni akış:
        1) Kullanıcı "ilacı hatırlat" dediğinde hangi ilacı hatırlatacağını sor.
        2) Kullanıcı ilaç adını verince saat sor.
        3) Saat verince timer kur ve ilaç adına göre hatırlatma yap.
        Ayrıca tek satırda "ilacı hatırlat aspirin 21:10" gibi ifade varsa onu da parse etmeye çalışır.
        """
        metin = (komut or "").lower().strip()
        # temizle tetikleyiciyi çıkar
        metin = metin.replace("ilacı hatırlat", "").strip()
        # iptal kontrolü
        if metin in ("hayır", "hayir", "iptal", "vazgeç", "vazgec"):
            self.konus("Tamam, ilacı hatırlatma iptal edildi.")
            self.awaiting_ilac = False
            self.awaiting_ilac_step = None
            self.awaiting_ilac_med = None
            return

        # Eğer komut içinde hem ilaç hem saat bilgisi varsa doğrudan kurmayı dene
        import re
        if metin:
            # örnek: "aspirin 21:10" veya "aspirin saat 21" vb.
            time_match = re.search(r'(\d{1,2}\s*[:\.]\s*\d{1,2})|(\d{1,2})(?=\D*$)', metin)
            if time_match:
                time_str = time_match.group(0)
                # ilaç ismini time_str'den çıkar
                ilac = metin.replace(time_str, "").replace("saat", "").strip()
                if not ilac:
                    # ilacı sormaya geç
                    self.konus("Hangi ilacı hatırlatayım?")
                    self.awaiting_ilac = True
                    self.awaiting_ilac_step = 1
                    self.awaiting_ilac_med = None
                    return
                # parse zamanı ve kur
                # yeniden kullanmak üzere process_ilac_response'e med ismiyle birlikte gönder
                self.awaiting_ilac = False
                self.awaiting_ilac_step = None
                self.process_ilac_response(f"{ilac} {time_str}")
                return

        # Hiç metin yoksa direkt ilaç sor
        self.konus("Hangi ilacı hatırlatayım?")
        self.awaiting_ilac = True
        self.awaiting_ilac_step = 1  # 1: ilaç bekleniyor, 2: saat bekleniyor
        self.awaiting_ilac_med = None
        return

    def process_ilac_response(self, cevap):
        """
        İlaç akışını işler. İki aşamalı:
        - step 1: ilaç adı bekleniyor -> ilaç alındıysa saat sor
        - step 2: saat bekleniyor -> zaman parse edilip timer kurulur
        Ayrıca tek satırda "aspirin 21:10" gibi girdileri de işler.
        """
        try:
            if not cevap:
                return
            text = str(cevap).strip()
            lower = text.lower().strip()

            # iptal kontrolü
            if lower in ("hayır", "hayir", "iptal", "vazgeç", "vazgec"):
                self.konus("Tamam, ilacı hatırlatma iptal edildi.")
                self.awaiting_ilac = False
                self.awaiting_ilac_step = None
                self.awaiting_ilac_med = None
                return

            import re, datetime, threading

            # Eğer step belirtilmemişse, varsayılan olarak tek satırda med+zaman olabilir
            step = getattr(self, "awaiting_ilac_step", None)

            # Helper: zaman parse fonksiyonu
            def parse_time(s):
                s = s.lower()
                m = re.search(r'(\d{1,2})\s*[:\.]\s*(\d{1,2})', s)
                if m:
                    h = int(m.group(1)); mi = int(m.group(2)); return h, mi
                m2 = re.search(r'(\d{1,2})', s)
                if m2:
                    h = int(m2.group(1)); return h, 0
                return None

            # Eğer ilaç ismi yoksa ve kullanıcı tek satırda "aspirin 21:10" gönderdiyse ayrıştır
            if step is None:
                # ayrıştır: ilk kelime ilaç, zaman kısmı varsa parse et
                tparse = parse_time(text)
                if tparse:
                    # ilaç ismini zaman kısmından çıkar
                    time_part = re.search(r'(\d{1,2}\s*[:\.]\s*\d{1,2})|(\d{1,2})(?=\D*$)', text).group(0)
                    ilac = text.replace(time_part, "").replace("saat", "").strip()
                    if not ilac:
                        ilac = "ilaç"
                    hour, minute = tparse
                    # normalize
                    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                        self.konus("Geçersiz saat bilgisi. 0-23 arası saat ve 0-59 arası dakika girin.")
                        return
                    now = datetime.datetime.now()
                    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target <= now:
                        target = target + datetime.timedelta(days=1)
                    delta = (target - now).total_seconds()
                    def hatirlatici():
                        try:
                            self.konus(f"Saat {hour:02d}:{minute:02d} oldu — {ilac} ilacını almayı unutma.")
                        except Exception:
                            pass
                    timer = threading.Timer(delta, hatirlatici)
                    timer.daemon = True
                    timer.start()
                    self.ilac_timer = timer
                    self.ilac_time = target.isoformat()
                    self.konus(f"Tamam. {ilac} için saat {hour:02d}:{minute:02d} hatırlatması ayarlandı (ilk hatırlatma {target.strftime('%Y-%m-%d %H:%M')}).")
                    return
                else:
                    # zaman yok, bunu ilaç adı olarak kabul edip saat sor
                    self.awaiting_ilac = True
                    self.awaiting_ilac_step = 1
                    self.awaiting_ilac_med = text
                    self.konus(f"Tamam, '{text}' için. Saat kaçta hatırlatayım?")
                    self.awaiting_ilac_step = 2
                    return

            # Aşama 1: ilaç adı bekleniyor
            if step == 1:
                ilac = text
                self.awaiting_ilac_med = ilac
                # şimdi saat sor
                self.konus(f"'{ilac}' ilacı için saat kaçta hatırlatayım?")
                self.awaiting_ilac_step = 2
                self.awaiting_ilac = True
                return

            # Aşama 2: saat bekleniyor
            if step == 2:
                # text içinde hem ilaç hem zaman de verildiyse handle et
                # örn kullanıcı önce ilaç söylemişti, buraya sadece saat gelmesi beklenir
                # ama güvenlik için ilacı kayıtlıysa kullan
                ilac = getattr(self, "awaiting_ilac_med", None) or "ilacınız"
                parsed = parse_time(text)
                if not parsed:
                    # belki kullanıcı "saat 21:10 aspirin" gibi yazdıysa ayırmayı dene
                    m = re.search(r'([^\d:]+)\s+(\d{1,2}[:\.]\d{1,2}|\d{1,2})', text)
                    if m:
                        ilac = m.group(1).strip()
                        parsed = parse_time(m.group(2))
                if not parsed:
                    self.konus("Saati anlayamadım. Lütfen örnek: '21' veya '21:10' şeklinde yazın.")
                    return
                hour, minute = parsed
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    self.konus("Geçersiz saat bilgisi. 0-23 arası saat ve 0-59 arası dakika girin.")
                    return

                now = datetime.datetime.now()
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target <= now:
                    target = target + datetime.timedelta(days=1)
                delta = (target - now).total_seconds()

                def hatirlatici():
                    try:
                        self.konus(f"Saat {hour:02d}:{minute:02d} oldu — {ilac} ilacını almayı unutma.")
                    except Exception:
                        pass

                timer = threading.Timer(delta, hatirlatici)
                timer.daemon = True
                timer.start()

                self.ilac_timer = timer
                self.ilac_time = target.isoformat()
                self.awaiting_ilac = False
                self.awaiting_ilac_step = None
                self.awaiting_ilac_med = None

                self.konus(f"Tamam. {ilac} için saat {hour:02d}:{minute:02d} hatırlatması ayarlandı (ilk hatırlatma {target.strftime('%Y-%m-%d %H:%M')}).")
                return

        except Exception as e:
            self.konus(f"İlaç hatırlatma işlemi sırasında hata: {e}")
# ...existing code...
    def bugunun_anlami(self, komut=None):

        import datetime
        tarih = datetime.datetime.now()
        gun = tarih.day
        ay = tarih.strftime("%B")

        gunler_ve_anlamlari = {
            # OCAK
            ("January", 1): "Yılbaşı",
            ("January", 7): "Beyaz Baston Körler Haftası Başlangıcı",
            ("January", 10): "Çalışan Gazeteciler Günü / İdareciler Günü",
            ("January", 14): "Beyaz Baston Körler Haftası Bitişi",
            ("January", 25): "Cüzam Haftası Başlangıcı",
            ("January", 26): "Dünya Gümrük Günü",
            ("January", 31): "Cüzam Haftası Bitişi",
            # ŞUBAT
            ("February", 9): "Dünya Sigarayı Bırakma Günü",
            ("February", 14): "Sevgililer Günü",
            ("February", 28): "Sivil Savunma Günü",
            # MART
            ("March", 1): "Yeşilay Haftası Başlangıcı",
            ("March", 7): "Yeşilay Haftası Bitişi",
            ("March", 8): "Dünya Kadınlar Günü",
            ("March", 12): "İstiklal Marşının Kabulü",
            ("March", 15): "Dünya Tüketiciler Günü",
            ("March", 18): "Şehitler Günü / Çanakkale Zaferi",
            ("March", 18): "Yaşlılara Saygı Haftası Başlangıcı",
            ("March", 24): "Yaşlılara Saygı Haftası Bitişi / Dünya Verem Günü",
            ("March", 21): "Nevruz Bayramı / Orman Haftası Başlangıcı / Dünya Şiir Günü",
            ("March", 26): "Orman Haftası Bitişi",
            ("March", 22): "Dünya Su Günü",
            ("March", 23): "Dünya Meteoroloji Günü",
            ("March", 27): "Dünya Tiyatrolar Günü",
            # NİSAN
            ("April", 1): "Dünya Sağlık Günü ve Kanser Haftası Başlangıcı",
            ("April", 7): "Dünya Sağlık Günü ve Kanser Haftası Bitişi",
            ("April", 5): "Avukatlar Günü",
            ("April", 8): "Sağlık Haftası Başlangıcı",
            ("April", 14): "Sağlık Haftası Bitişi",
            ("April", 10): "Polis Teşkilatının Kuruluşu",
            ("April", 15): "Turizm Haftası Başlangıcı",
            ("April", 22): "Turizm Haftası Bitişi",
            ("April", 21): "Ebeler Haftası Başlangıcı",
            ("April", 28): "Ebeler Haftası Bitişi / Kardeşlik Haftası Başlangıcı",
            ("April", 23): "23 Nisan Ulusal Egemenlik ve Çocuk Bayramı",
            ("April", 20): "Kutlu Doğum Haftası Başlangıcı",
            ("April", 26): "Kutlu Doğum Haftası Bitişi",
            # MAYIS
            ("May", 1): "Emek ve Dayanışma Günü",
            ("May", 4): "İş Sağlığı ve Güvenliği Haftası Başlangıcı",
            ("May", 10): "İş Sağlığı ve Güvenliği Haftası Bitişi / Danıştay ve İdari Yargı Haftası",
            ("May", 6): "Hıdrellez Kültür ve Bahar Bayramı",
            ("May", 10): "Müzeler Haftası Başlangıcı / Sakatlar Haftası Başlangıcı",
            ("May", 16): "Müzeler Haftası Bitişi / Sakatlar Haftası Bitişi",
            ("May", 12): "Hemşirelik Haftası Başlangıcı",
            ("May", 18): "Hemşirelik Haftası Bitişi",
            ("May", 14): "Dünya Eczacılık Günü / Dünya Çiftçiler Günü",
            ("May", 15): "Yeryüzü İklim Günü / Hava Şehitlerini Anma Günü",
            ("May", 17): "Dünya Telekomünikasyon Günü",
            ("May", 19): "Gençlik Haftası Başlangıcı",
            ("May", 25): "Gençlik Haftası Bitişi",
            ("May", 21): "Dünya Süt Günü",
            ("May", 29): "İstanbul'un Fethi",
            ("May", 31): "Dünya Sigarasız Günü / Dünya Hostesler Günü",
            # HAZİRAN
            ("June", 5): "Dünya Çevre Günü",
            ("June", 10): "Çevre Koruma Haftası Başlangıcı",
            ("June", 16): "Çevre Koruma Haftası Bitişi",
            ("June", 17): "Dünya Çölleşme ve Kuraklıkla Mücadele Haftası",
            ("June", 20): "Dünya Mülteciler Günü",
            ("June", 26): "Uyuşturucu Kullanımı ve Trafiği ile Mücadele Günü",
            # TEMMUZ
            ("July", 1): "Kabotaj ve Denizcilik Günü",
            ("July", 5): "Nasrettin Hoca Şenlikleri Başlangıcı",
            ("July", 10): "Nasrettin Hoca Şenlikleri Bitişi",
            ("July", 11): "Dünya Nüfus Günü",
            ("July", 24): "Gazeteciler (Basın) Bayramı",
            # AĞUSTOS
            ("August", 30): "Zafer Bayramı",
            # EYLÜL
            ("September", 1): "Dünya Barış Günü",
            ("September", 3): "Halk Sağlığı Haftası Başlangıcı",
            ("September", 9): "Halk Sağlığı Haftası Bitişi",
            ("September", 19): "Şehitler ve Gaziler Günü / Haftası Başlangıcı",
            ("September", 25): "İtfaiyecilik Haftası Başlangıcı",
            ("October", 1): "İtfaiyecilik Haftası Bitişi",
            ("September", 26): "Dil Bayramı",
            ("September", 27): "Dünya Turizm Günü",
            # EKİM
            ("October", 1): "Dünya Yaşlılar Günü / Camiler ve Din Görevlileri Haftası Başlangıcı",
            ("October", 4): "Hayvanları Koruma Günü",
            ("October", 10): "Dünya Ruh Sağlığı Günü",
            ("October", 13): "Ankara'nın Başkent Oluşu",
            ("October", 14): "Dünya Standartlar Günü",
            ("October", 16): "Dünya Gıda Günü",
            ("October", 17): "Dünya Yoksullukla Mücadele Günü",
            ("October", 24): "Birleşmiş Milletler Günü",
            ("October", 29): "Cumhuriyet Bayramı",
            ("October", 31): "Dünya Tasarruf Günü",
            # KASIM
            ("November", 1): "Türk Harf Devrimi Haftası Başlangıcı",
            ("November", 7): "Türk Harf Devrimi Haftası Bitişi",
            ("November", 3): "Organ Nakli Haftası Başlangıcı",
            ("November", 9): "Organ Nakli Haftası Bitişi / Dünya Şehircilik Günü",
            ("November", 10): "Atatürk'ün Ölüm Günü / Atatürk Haftası Başlangıcı",
            ("November", 16): "Atatürk Haftası Bitişi",
            ("November", 14): "Dünya Diyabet Günü",
            ("November", 20): "Dünya Çocuk Hakları Günü",
            ("November", 22): "Diş Hekimleri Günü / Ağız ve Diş Sağlığı Haftası",
            ("November", 24): "Bugün 24 Kasım Öğretmenler günü olup bütün öğretmenlerimizin öğretmenler gününü kutlar sevgi ve saygıyla selamlıyorum. .",
            ("November", 25): "Kadına Yönelik Şiddete Karşı Uluslararası Mücadele Günü",
            # ARALIK
            ("December", 1): "Dünya AİDS Günü",
            ("December", 2): "Köleliğin Yasaklanması Günü",
            ("December", 3): "Dünya Özürlüler Günü / Vakıflar Haftası Başlangıcı",
            ("December", 4): "Dünya Madenciler Günü",
            ("December", 5): "Kadın Hakları Günü",
            ("December", 7): "Uluslararası Sivil Havacılık Günü",
            ("December", 10): "Dünya İnsan Hakları Günü / İnsan Hakları Haftası Başlangıcı",
            ("December", 18): "İnsan Hakları Haftası Bitişi / Tutum, Yatırım ve Türk Malları Haftası Bitişi",
            ("December", 12): "Tutum, Yatırım ve Türk Malları Haftası Başlangıcı / Yoksullarla Dayanışma Haftası Başlangıcı",
            ("December", 18): "Tutum, Yatırım ve Türk Malları Haftası Bitişi / Yoksullarla Dayanışma Haftası Bitişi",
            ("December", 21): "Dünya Kooperatifçilik Günü",
            ("December", 27): "Atatürk'ün Ankara'ya Gelişi",
        }

        anlam = gunler_ve_anlamlari.get((ay, gun), "Bugün özel bir gün değil")
        self.konus("Bugünün anlamı: " + anlam)

    



    
    def altin_piyasasi(self, komut=None):
        import re
        import requests
        import webbrowser
        from bs4 import BeautifulSoup
        from statistics import median

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        sites = [
            ("doviz.com - gram", "https://www.doviz.com/altin/gram-altin"),
            ("bigpara", "https://bigpara.hurriyet.com.tr/altin/gram-altin/"),
            ("doviz.com - genel", "https://www.doviz.com/altin"),
            ("bloomberght", "https://www.bloomberght.com/altin")
        ]

        num_pattern = re.compile(r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?')

        def normalize_number(token):
            if not token:
                return None
            s = token.strip().replace(" ", "")
            if "." in s and "," in s:
                s = s.replace(".", "").replace(",", ".")
            elif "," in s:
                s = s.replace(",", ".")
            try:
                return float(re.search(r'\d+(?:\.\d+)?', s).group(0))
            except:
                return None

        def scrape(url):
            try:
                r = requests.get(url, headers=headers, timeout=8)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                text = soup.get_text(" ", strip=True)

                
                for m in re.finditer(r'(' + num_pattern.pattern + r')\s*(?:TL|₺|lira)?\s*(?:\/\s*)?(?:gram|gr)\b', text, re.I):
                    val = normalize_number(m.group(1))
                    if val and val > 100:  
                        return round(val, 2)

                
                for m in re.finditer(r'(?:gram|gr)\b.{0,40}?(' + num_pattern.pattern + r')|(' + num_pattern.pattern + r').{0,40}?(?:gram|gr)\b', text, re.I | re.S):
                    tok = m.group(1) or m.group(2)
                    val = normalize_number(tok)
                    if val and val > 100:
                        return round(val, 2)

                for cls in ("value", "price", "kur", "ticker", "last", "text--left", "text--right", "price--value", "fiyat"):
                    el = soup.find(attrs={"class": re.compile(cls, re.I)})
                    if el:
                        v = normalize_number(el.get_text(" ", strip=True))
                        if v and v > 100:
                            return round(v, 2)

                nums = [normalize_number(n) for n in num_pattern.findall(text)]
                nums = [n for n in nums if n and 300 <= n <= 200000]
                if nums:
                    return round(median(nums), 2)
            except:
                return None
            return None

        found = [(name, scrape(url)) for name, url in sites if scrape(url)]
        vals = [v for _, v in found if 300 <= v <= 200000]

        if vals:
            chosen = round(median(vals), 2)
            kaynaklar = " | ".join(f"{n}: {v}" for n, v in found)
            self.konus(f"Gram altın (kaynak örnekleri) — {kaynaklar}")
            self.konus(f"Tahmini gram altın: {chosen} TL")
            return

        if found:
            self.konus("Bazı kaynaklardan veri alındı ama değerler tutarsız: " +
                   ", ".join(f"{n}:{v}" for n, v in found))
        else:
            self.konus("Altın fiyatları alınamadı. Sitelerin yapısı değişmiş olabilir veya istek engellenmiş olabilir.")
        try:
            self.konus("Güncel fiyatları tarayıcıda açıyorum...")
            webbrowser.open("https://www.doviz.com/altin/gram-altin")
        except:
            pass

    def muzik_youtube_ac(self, komut=None):
        import webbrowser
        self.konus("YouTube'da müzik açılıyor...")
        query = "müzik"
        if komut and "müzik" in komut:
            query = komut.replace("müzik açabilir misin", "").strip() or "müzik"
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(search_url)
  
    def bugun_ne_var(self):
        
        import requests
        from bs4 import BeautifulSoup
        import xml.etree.ElementTree as ET
        from urllib.parse import urljoin, unquote
        import re
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        def pick_link_from_item(item):
            
            link = None
            if item.find("link") is not None and item.find("link").text:
                link = item.find("link").text.strip()
      
            src = item.find("source")
            if src is not None and src.get("url"):
                cand = src.get("url").strip()
                if cand:
                    link = cand
       
            guid = item.find("guid")
            if guid is not None and guid.text and "http" in (guid.text or ""):
                gtxt = guid.text.strip()
                if gtxt.startswith("http"):
                    link = gtxt

            desc = None
            dtag = item.find("description")
            if dtag is not None and dtag.text:
                desc = dtag.text
                try:
                    soupd = BeautifulSoup(desc, "html.parser")
                    a = soupd.find("a", href=True)
                    if a:
                        href = a["href"].strip()
                        if href.startswith("/"):
                            href = urljoin(link or "https://news.google.com", href)
                        href = unquote(href)
                        if href and "google" not in href:
                            link = href
                except Exception:
                    pass

      
            try:
                raw = (dtag.text or "") if dtag is not None else ""
                m = re.search(r"https?://[^\s'\"<>()]+", raw)
                if m:
                    u = unquote(m.group(0).rstrip("),.;\"'"))
                    if "google" not in u:
                        link = u
            except Exception:
                pass

            return link
            
        

        def resolve_possible_original(link):
            if not link:
                return link
            try:
                rr = requests.get(link, headers=headers, timeout=10, allow_redirects=True)
            except Exception:
                return link
            final = rr.url or link
            text = rr.text or ""
            
            if "news.google" not in final and len(text.strip()) > 800 and "Google News" not in text:
                try:
                    soup = BeautifulSoup(text, "html.parser")
                    og = soup.find("meta", property="og:url") or soup.find("meta", attrs={"name": "og:url"})
                    if og and og.get("content"):
                        cand = og["content"].strip()
                        if cand and "google" not in cand:
                            return cand
                    can = soup.find("link", rel="canonical")
                    if can and can.get("href"):
                        cand = can["href"].strip()
                        if cand and "google" not in cand:
                            return cand
                except Exception:
                    pass
                return final

            try:
                candidates = []
                soup = BeautifulSoup(text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    if href.startswith("/"):
                        href = urljoin(final, href)
                    href = unquote(href)
                    if href.startswith("http") and "google" not in href and "accounts.google" not in href:
                        candidates.append(href)
              
                for c in candidates:
                    if "google" not in c:
                        return c
            except Exception:
                pass
            return final

        def worker():
            headlines = []
            links = []

            try:
                rss = "https://news.google.com/rss?hl=tr&gl=TR&ceid=TR:tr"
                r = requests.get(rss, headers=headers, timeout=8)
                r.raise_for_status()
                root = ET.fromstring(r.content)
                items = root.findall(".//item")[:10]
                for it in items:
                    title = (it.find("title").text or "").strip() if it.find("title") is not None else None
                    link = pick_link_from_item(it)
                    if title:
                        headlines.append(title)
                        links.append(link)
            except Exception:
                pass


            if len(headlines) < 6:
                try:
                    url = "https://www.hurriyet.com.tr/gundem/"
                    r = requests.get(url, headers=headers, timeout=8)
                    r.raise_for_status()
                    soup = BeautifulSoup(r.text, "html.parser")
                    found = []
                    found_links = []
                    for tag in ("h3", "h2", "h1"):
                        for h in soup.find_all(tag):
                            t = h.get_text().strip()
                            if not t or len(t) < 10:
                                continue
                            a = h.find_parent("a") or h.find("a") or h.find_next("a")
                            href = None
                            if a and a.get("href"):
                                href = urljoin("https://www.hurriyet.com.tr", a.get("href"))
                            if t not in found:
                                found.append(t)
                                found_links.append(href)
                            if len(found) >= 10:
                                break
                        if len(found) >= 10:
                            break
                    for t, l in zip(found, found_links):
                        if len(headlines) >= 10:
                            break
                        if t not in headlines:
                            headlines.append(t)
                            links.append(l)
                except Exception:
                    pass

            if not headlines:
                self.konus("Haber alınamadı. İnternet bağlantınızı veya hedef siteleri kontrol edin.")
                return

            resolved = []
            for l in links[:10]:
                if not l:
                    resolved.append(None)
                    continue
                try:
                    resolved.append(resolve_possible_original(l))
                except Exception:
                    resolved.append(l)

            self.awaiting_haber_detayi = []
            self.links = []

            for title, link in zip(headlines, resolved):
                if title and link:
                    self.awaiting_haber_detayi.append(title)
                    self.links.append(link)

            mesaj = "Bugünün haber başlıkları:\n"
            for i, h in enumerate(self.awaiting_haber_detayi, 1):
                mesaj += f"{i}. {h}\n"
            if hasattr(self, "gui"):
                try:
                    self.gui.root.after(0, self.gui.mesaj_ekle, self.isim, mesaj)
                except Exception:
                    pass

            self.konus("Günün öne çıkan haberleri:")
            for i, h in enumerate(self.awaiting_haber_detayi, 1):
                self.konus(f"{i}. {h}")
                time.sleep(0.15)

            
            kaynak_mesaji = "Kaynak linkleri:\n"
            for i, link in enumerate(self.links, 1):
                kaynak_mesaji += f"{i}. {link or 'Bulunamadı'}\n"
            if hasattr(self, "gui"):
                try:
                    self.gui.root.after(0, self.gui.mesaj_ekle, self.isim, kaynak_mesaji)
                except Exception:
                    pass
            else:
                print(kaynak_mesaji)

            self.konus("Detaylı okumamı istediğiniz haber numarası var mı? (örn. 2 veya 'hayır')")

        threading.Thread(target=worker, daemon=True).start()
    def process_haber_detayi_response(self, cevap):
        try:
            if not cevap:
                return
            txt = str(cevap).strip().lower()
            if txt in ("hayır", "hayir", "h", "no"):
                self.konus("Tamam, detay istemediniz.")
                self.awaiting_haber_detayi = None
                return

            import re
            m = re.search(r'(\d+)', txt)
            if m:
                idx = int(m.group(1))
                if not hasattr(self, "links") or idx < 1 or idx > len(self.links):
                    self.konus("Geçersiz haber numarası.")
                    return

                link = self.links[idx - 1]
                self.konus(f"{idx}. haberi açıyorum...")
                threading.Thread(target=self.haberi_detayli_oku, args=(idx,), daemon=True).start()
                return

            self.konus("Geçersiz seçim. Bir numara yazın veya 'hayır' deyin.")
        except Exception as e:
            self.konus(f"Haber yanıtı işlenemedi: {e}")

 
    def dinle(self):
        sr_recognizer = sr.Recognizer()
        fs = 44100  
        saniye = 5  
        print("Dinliyorum...")

        ses = sd.rec(int(saniye * fs), samplerate=fs, channels=1, dtype=np.int16)
        sd.wait()  

        audio_data = sr.AudioData(ses.tobytes(), fs, 2)  
        try:
            text = sr_recognizer.recognize_google(audio_data, language="tr-TR")
            print("Siz (sesli):", text)
            return text.lower()
        except sr.UnknownValueError:
            print("Sesi anlayamadım.")
            return "ANLAŞILMADI"
        except sr.RequestError as e:
            print("Google Speech API hatası:", e)
            return "HATA"
    

            cevap = response.choices[0].message.content
            self.konus(cevap)
        except Exception as e:
            self.konus(f"Hata oluştu: {e}")
    def sohbet_et(self, mesaj):

        try:
            from openai import OpenAI
            client = OpenAI(api_key="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")

            yanit = client.chat.completions.create(
                model="gpt-oss-20b",  # hafif model
                messages=[{"role": "user", "content": mesaj}]
            )

            cevap = yanit.choices[0].message.content
            self.konus(cevap)


        except Exception as e:
            print("Hata:", e)




    




    def onceden_tanimli_cevap_ver(self, komut):
        for anahtar, cevap in self.onceden_tanimli_cevaplar.items():
            if anahtar in komut:
                self.konus(cevap)
                return True
        return False


    def selamla(self):
        self.konus("Merhaba! Sana nasıl yardımcı olabilirim?")

    def saat_soyle(self):
        self.konus("Şu an saat: " + datetime.datetime.now().strftime("%H:%M"))

    def tarih_soyle(self):
        self.konus("Bugün tarih: " + datetime.datetime.now().strftime("%d %B %Y"))

    def arama_yap(self):
     
        query = self.gui.giris.get()
        self.gui.mesaj_ekle("Siz", query)
        webbrowser.open(f"https://www.google.com/search?q={query}")


    


    def gorev_ekle(self):
        if hasattr(self, "gui"):
            gorev = self.gui.giris.get()
            self.gui.giris.delete(0, tk.END)
        else:
            gorev = input("Görev girin: ")
            self.gorevler.append(gorev)
            self.konus(f"'{gorev}' görevi eklendi.")
            self.hafizayi_kaydet()  
    def ip_adresim(self):
        import socket
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        self.konus(f"Bilgisayarınızın IP adresi: {ip}")
    def sarki_ac(self):

        import tkinter.filedialog as fd
        dosya = fd.askopenfilename(title="Müzik dosyası seçin", filetypes=[("MP3 Dosyaları", "*.mp3"), ("WAV Dosyaları", "*.wav")])
        if dosya:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(dosya)
                pygame.mixer.music.play()
                self.konus(f"{os.path.basename(dosya)} çalıyor...")
            except Exception as e:
                self.konus(f"Müzik çalınamadı: {e}")
        else:
            self.konus("Müzik dosyası seçilmedi.")


    def rastgele_kelime(self):
        kelimeler = ["elma", "armut", "kitap", "araba", "güneş", "yıldız", "çay", "kahve"]
        self.konus(f"Rastgele kelime: {random.choice(kelimeler)}")




    def gorevleri_listele(self):
        if self.gorevler:
            self.konus("Görevlerin şunlar:")
            for i, gorev in enumerate(self.gorevler):
                self.konus(f"{i+1}. {gorev}")
        else:
            self.konus("Hiç görev eklenmemiş.")

    def alisveris_ekle(self):
        if hasattr(self, "gui"):
            urun = self.gui.giris.get()
            self.gui.giris.delete(0, tk.END)
        else:
            urun = input("Alışveriş listenize eklemek istediğiniz ürünü yazın: ")
    
        self.alisveris_listesi.append(urun)
        self.hafizayi_kaydet() 
        self.konus(f"{urun} alışveriş listenize eklendi.")

    def alisveris_goster(self):
        if self.alisveris_listesi:
            self.konus("Alışveriş listeniz şunlar:")
            for i, urun in enumerate(self.alisveris_listesi):
                self.konus(f"{i+1}. {urun}")
        else:
            self.konus("Alışveriş listenizde hiç ürün yok.")

    def faktoriyel_hesapla(self):
        sayi = self.gui.giris.get()
        self.gui.giris.delete(0, tk.END)
        if sayi.isdigit():
            sonuc = 1
            for i in range(1, int(sayi)+1):
                sonuc *= i
            self.konus(f"{sayi}! = {sonuc}")
        else:
            self.konus("Lütfen geçerli bir sayı girin.")
    def yardim_goster(self):
        
        try:
            komut_listesi = list(self.komutlar.keys())
            mesaj = "Yapabileceğim bazı komutlar:\n" + "\n".join(f"- {k}" for k in komut_listesi[:40])
            self.konus(mesaj)
        except Exception as e:
            self.konus("Yardım gösterilemedi: " + str(e))

        
    def karekok_hesapla(self):
        sayi = self.gui.giris.get()
        self.gui.giris.delete(0, tk.END)
        try:
            sonuc = float(sayi) ** 0.5
            self.konus(f"{sayi} sayısının karekökü: {sonuc}")
        except:
            self.konus("Lütfen geçerli bir sayı girin.")


    def alisveris_listesi_goster(self):
        if self.alisveris_listesi:
            self.konus("Alışveriş listeniz şunlar:")
            for i, urun in enumerate(self.alisveris_listesi):
                self.konus(f"{i+1}. {urun}")
        else:
            self.konus("Alışveriş listesi boş.")

    def dosya_olustur(self):
        dosya_adi = self.gui.giris.get()
        self.gui.giris.delete(0, tk.END)
        with open(dosya_adi, "w", encoding="utf-8") as f:
            f.write("")
        self.konus(f"{dosya_adi} dosyası oluşturuldu.")

    def dosya_ac(self):
        dosya_adi = self.gui.giris.get()
        self.gui.giris.delete(0, tk.END)
        if os.path.exists(dosya_adi):
            with open(dosya_adi, "r", encoding="utf-8") as f:
                icerik = f.read()
                self.konus(icerik)
        else:
            self.konus("Dosya bulunamadı.")


    def not_al(self):
        if hasattr(self, "gui"):
            not_metni = self.gui.giris.get()
            self.gui.giris.delete(0, tk.END)
        else:
            not_metni = input("Notunuzu yazın: ")
    
        self.notlar.append(not_metni)
        self.hafizayi_kaydet()  
        self.konus("Not kaydedildi.")

    def notlari_goster(self):
        if self.notlar:
            self.konus("Notlarınız şunlar:")
            for i, not_metni in enumerate(self.notlar):
                self.konus(f"{i+1}. {not_metni}")
        else:
            self.konus("Hiç not alınmamış.")


    

    def saka_yap(self):
        s = [
            "Neden bilgisayar çok iyi dans eder? Çünkü hard disk’i var!",
            "Bilgisayar neden ağrı hisseder? Çünkü byte’lar!",
            "Programcı neden denize girmez? Çünkü overflow olur!"
        ]
        self.konus(random.choice(s))

    def zamanlayici(self):
        sure = self.gui.giris.get()
        self.gui.giris.delete(0, tk.END)
        if sure.isdigit():
            self.konus(f"{sure} saniye için zamanlayıcı başlatıldı")
            self.gui.root.after(int(sure) * 1000, lambda: self.konus("Süre doldu!"))
        else:
            self.konus("Geçersiz süre girdiniz.")


    def alarm_kur(self):
        saat = input("Alarm saatini HH:MM formatında girin: ")
        self.konus(f"{saat} için alarm kuruldu (simüle edildi).")

    def bilgi_ver(self):
        self.konus("Ben Eva, sizin ev asistanınızım. Komutlarınızı yerine getirebilirim.")

    def rastgele_sayi(self):
        self.konus(f"Rastgele sayı: {random.randint(0,1000)}")

    def so_zluk(self):
        kelime = self.gui.giris.get()
        self.gui.giris.delete(0, tk.END)
        if not kelime:
            self.konus("Lütfen çevirmek istediğin kelimeyi yaz.")
            return
        try:
        
            ceviri = GoogleTranslator(source="auto", target="tr").translate(kelime)
            self.konus(f"{kelime} → {ceviri}")
        except Exception as e:
            self.konus(f"Sözlük/çeviri hatası: {e}")


    def hakkinda(self):
        self.konus("Ben Eva, Python ile yapılmış gelişmiş bir Ev Asistanıyım!")

    def tarayici_ac(self):
        self.konus("Tarayıcı açılıyor...")
        webbrowser.open("https://www.google.com")

    def youtube_ac(self):
        self.konus("YouTube açılıyor...")
        webbrowser.open("https://www.youtube.com")

    def spotify_ac(self):
        self.konus("Spotify açılıyor...")
        webbrowser.open("https://open.spotify.com")

    def google_harita(self):
        self.konus("Google Harita açılıyor...")
        webbrowser.open("https://www.google.com/maps")

    def bilgisayar_bilgisi(self):
        self.konus(f"İşletim sistemi: {platform.system()} {platform.release()}")
        self.konus(f"Python versiyonu: {platform.python_version()}")
    


    def klasor_ac(self):
        ad = input("Açmak istediğiniz klasör adı: ")
        path = os.path.join(os.path.expanduser("~"), ad)
        if os.path.exists(path):
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.call(["open", path])
            self.konus(f"{ad} klasörü açıldı.")
        else:
            self.konus(f"{ad} bulunamadı.")

    def gunluk_not(self):
        metin = input("Bugün için notunuzu yazın: ")
        self.konus(f"Günlük notunuz kaydedildi: {metin}")

    def sistem_durumu(self):
        self.konus(f"İşlemci: {platform.processor()}")
        self.konus(f"Sistem: {platform.system()} {platform.release()}")

    
    def cikis(self):
        """GUI varsa kapat, sonra programı sonlandır."""
        try:
            self.konus("Asistan kapatılıyor. Görüşürüz!")
            if hasattr(self, "gui") and getattr(self.gui, "root", None):
                try:
                    self.gui.root.destroy()
                except Exception:
                    pass
          
            sys.exit(0)
        except SystemExit:
            raise
        except Exception as e:
           
            try:
                self.konus(f"Çıkış sırasında hata: {e}")
            except Exception:
                pass
def main():
    asistan = EvAsistani(isim="EgeDa")
    gui = EvAsistaniGUI(asistan)
    asistan.gui = gui
    asistan.konus("Merhaba Mehmet Ege,Ben DijiDost.. Size nasıl yardımcı olabilirim?")
    gui.run()

if __name__ == "__main__":
    main()
