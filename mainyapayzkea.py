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
import os
from openai import OpenAI
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
try:
    import pygame
    pygame.mixer.init()
except Exception as e:
    print("Ses başlatılamadı (boot modunda sorun olabilir):", e)

import sounddevice as sd
import numpy as np
import speech_recognition as sr
from deep_translator import GoogleTranslator
from tempfile import NamedTemporaryFile
import requests

# Hugging Face API bilgileri

class EvAsistaniGUI:
    def __init__(self, asistan):
        self.asistan = asistan  
        self.root = tk.Tk()
        self.root.title(f"Ev Asistanı - {self.asistan.isim}")
        self.sohbet = scrolledtext.ScrolledText(self.root, width=60, height=15)
        self.sohbet.pack()
        self.sohbet.tag_config("user", foreground="blue")
        self.sohbet.tag_config("eva", foreground="green")
        class DummyEntry:
            def __init__(self, owner):
                self.owner = owner
            def get(self):
                return getattr(self.owner, "last_spoken", "")
            def delete(self, a=None, b=None):
                return
        self.giris = DummyEntry(self.asistan)
        threading.Thread(target=self.asistan.listen_loop, daemon=True).start()
    def komut_isle(self, komut):
        if getattr(self.asistan, "awaiting_haber_detayi", None):
            self.asistan.process_haber_detayi_response(komut)
            return
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
        self.asistan.konus("Bu komutu anlayamadım.Tekrar söyleyebilir misin?")
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
    def asistan_komut(self, komut):
        if getattr(self.asistan, "waiting_haber_detayi", None):
            self.asistan.process_haber_detayi_response(komut)
            return
        if getattr(self.asistan, "waiting_ilac", None):
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
class EvAsistani:
    def __init__(self, isim="EgeDa" ,karakter="arkadaşça"):
        self.isim = isim
        self.gui = gui = None
        self.gorevler = []
        self.messages = []
        self.karakter = karakter
        self.alisveris_listesi = []
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key="*****************",
        )
        self.notlar = []
        self.recognizer = sr.Recognizer()
        self.hafizayi_yukle()   
        self.speaking = False
        self.awaiting_not = False  
        self.awaiting_alisveris = False
        self.awaiting_youtube = False
        self.reading_haber = False
        self.awaiting_hatirlatici = False
        self.hatirlatici_step = None
        self.hatirlatici_konu = None
        self.komutlar = {
            "dosya oluştur": self.dosya_olustur,
            "selam": self.selamla,
            "saat": self.saat_soyle,
            "saat kaç": self.saat_soyle,
            "tarih ne": self.tarih_soyle,
            "tarih": self.tarih_soyle,
            "Bugünün tarihi nedir": self.tarih_soyle,
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
            "Bugün hava nasıl acaba": lambda komut=None: self.hava_durumu_google("Bilecik"),
            "Bugün bilecikte hava nasıl": lambda komut=None: self.hava_durumu_google("Bilecik"),
            "Bugün Bilecikte hava nasıl acaba": lambda komut=None: self.hava_durumu_google("Bilecik"),
            "Bugün Bilecik'te hava nasıl acaba": lambda komut=None: self.hava_durumu_google("Bilecik"),
            "Bugün Bilecikte hava nasıl ": lambda komut=None: self.hava_durumu_google("Bilecik"),
            "gugün hava nasıl acaba": lambda komut=None: self.hava_durumu_google("Bilecik"),
            "bugün hava nasıl": lambda komut=None: self.hava_durumu_google("Bilecik"),
            "çeviri yap": self.ceviri_yap,
            "dosya aç": self.dosya_ac,
            "bugün güncel haberleri sıralayabilir misin": self.bugun_ne_var,
            "bugün haberlerde ne var": self.bugun_ne_var,
            "yapacaklarım": self.gorevleri_listele,
            "şaka yap": self.saka_yap,
            "alarm kur": self.alarm_kur,
            "bilgi ver": self.bilgi_ver,
            "rastgele sayı": self.rastgele_sayi,
            "hatırlatıcı": self.hatirlatici_kur,
            "hatirlatici": self.hatirlatici_kur,
            "sözlük": self.so_zluk,
            "hakkında": self.hakkinda,
            "çıkış": self.cikis,
            "tarayıcı aç": self.tarayici_ac,
            "bugünün anlamı": self.bugunun_anlami,
            "bugun anlam": self.bugunun_anlami,
            "bugün ne günü": self.bugunun_anlami,

            "spotify aç": self.spotify_ac,
            "google harita": self.google_harita,
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
            "hafızayı yükle": self.hafizayi_yukle,
            " İlacımı hatırlat": self.ilac_hatirlat,
            "i̇lacımı hatırlat": self.ilac_hatirlat,
            " i̇lacımı hatırlatabilir misin": self.ilac_hatirlat,
            "yeter": self.stop_reading,
            "dur": self.stop_reading,
            "okumayı durdur": self.stop_reading,
            "okumayi durdur": self.stop_reading,
            " bana İlacımı hatırlatabilir misin": self.ilac_hatirlat,
            "kes": self.stop_reading,
            "sus": self.stop_reading,
            "teşekkür ederim": self.stop_reading,
            "müzik aç": self.muzik_ac,
            "müzik oynat": self.muzik_ac,
            "müziği aç": self.muzik_ac,
            "müzik kapat": self.muzik_kapat,
            "müziği kapat": self.muzik_kapat,
            "kapat": self.muzik_kapat

        }

        self.keyword_triggers = {
            "dosya": self.dosya_olustur,
            "selam": self.selamla,
            "saat": self.saat_soyle,
            "tarih": self.tarih_soyle,
            "arama": self.arama_yap,
            "ip": self.ip_adresim,
            "aypi": self.ip_adresim,
            "rastgele_kelime": self.rastgele_kelime,
            "faktoriyel": self.faktoriyel_hesapla,
            "karekök": self.karekok_hesapla,
            "not al": self.not_al,
            "notları göster": self.notlari_goster,
            "alışveriş ekle ": self.alisveris_ekle,
            "alışveriş listesi göster": self.alisveris_goster,
            "görev": self.gorev_ekle,
            "görevleri listele": self.gorevleri_listele,
            "hava": lambda komut=None: self.hava_durumu_google("Bilecik"),
            "çeviri": self.ceviri_yap,
            "dosya_ac": self.dosya_ac,
            "haber": self.bugun_ne_var,
            "şaka": self.saka_yap,
            "alarm": self.alarm_kur,
            "bilgi": self.bilgi_ver,
            "rastgele_sayı": self.rastgele_sayi,
            "sözlük": self.so_zluk,
            "hakkında": self.hakkinda,
            "çıkış": self.cikis,
            "tarayıcı": self.tarayici_ac,
            "anlam": self.bugunun_anlami,
            "spotify": self.spotify_ac,
            "harita": self.google_harita,
            "sohbet": lambda komut: self.sohbet_et(komut),
            "hesap": self.hesap_makinesi,
            "altın": self.altin_piyasasi,
            "bilgisayar": self.bilgisayar_bilgisi,
            "klasör": self.klasor_ac,
            "günlük_not": self.gunluk_not,
            "sistem": self.sistem_durumu,
            "yardım": self.yardim_goster,
            "hafıza_kaydet": self.hafizayi_kaydet,
            "hafıza_yükle": self.hafizayi_yukle,
            "hatırlatıcı": self.hatirlatici_kur,
            "hatirlatici": self.hatirlatici_kur,
            "ilaç": self.ilac_hatirlat
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
            "helal olsun be":"Teşekkür ederim",
            "sıkıldım": "Merak etme, sana yardımcı olabileceğim şeyler var. Müzik dinleteyim, haber okuyayım, bir şaka yapayım veya sohbet edelim. Ne yapmak istersin?",
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
            "bana i̇stiklal marşı'nı oku":"""Korkma, sönmez bu şafaklarda yüzen al sancak;
            
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
            "sana güveniyorum": "Teşekkür ederim, bana güvenebilirsin!",
            "sana hayranım": "Teşekkür ederim, çok naziksin!",
            "beni seviyor musun": "Ben seni sevemem ama önemsiyorum!",
            "beni anlıyor musun": "Evet, söylediklerini anlayabiliyorum.",
            "beni duyabiliyor musun": "Evet, seni duyabiliyorum."
        }
    def konus(self, mesaj):
        if getattr(self, "stop_speaking", False):
            self.stop_speaking = False
            return

        print(f"{self.isim}: {mesaj}")
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
            self.speaking = True
            tts = gTTS(mesaj, lang="tr")
            with NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.write_to_fp(fp)
                temp_path = fp.name
            try:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    if getattr(self, "stop_speaking", False):
                        try:
                            pygame.mixer.music.stop()
                        except Exception:
                            pass
                        break
                    time.sleep(0.1)
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass
            finally:
                try:
                    os.remove(temp_path)
                except PermissionError:
                    pass
        except Exception as e:
            print("TTS hatası:", e)
        finally:
            self.speaking = False
    def listen_loop(self):

        while True:
            try:
                if getattr(self, "reading_haber", False) or getattr(self, "speaking", False):
                    try:
                        hot = self.dinle_hotword()
                        if hot and any(k in hot.lower() for k in ("yeter", "dur", "kes","teşekkür ederim","teşekkürler","sağol")):
                            self.stop_reading(hot)
                            time.sleep(0.5)
                            continue
                    except Exception as e:
                        print(f"Hotword hatası: {e}")
                        pass

                komut = self.dinle()
            except Exception as e:
                print(f"Dinleme hatası: {e}")
                komut = None

            if not komut:
                time.sleep(0.5)
                continue
            
            if isinstance(komut, str) and komut.upper() in ("ANLAŞILMADI", "ANLASILMADI", "HATA"):
                print("Ses tanıma başarısız veya hata, tekrar dinleniyor...")
                time.sleep(0.5)
                continue
            
            if hasattr(self, "gui"):
                try:
                    self.gui.root.after(0, self.gui.mesaj_ekle, "Siz (sesli)", komut)
                except Exception:
                    pass
            
            try:
                self.handle_command(komut)
            except Exception as e:
                print(f"Komut işleme hatası: {e}")
            
            time.sleep(0.2)
    def handle_command(self, komut):
        if getattr(self, "awaiting_youtube", None):
            try:
                self.process_youtube_response(komut)
            except Exception:
                pass
            return
        if getattr(self, "awaiting_alisveris", None):
            try:
                self.process_alisveris_response(komut)
            except Exception:
                pass
            return
        if getattr(self, "awaiting_not", None):
            try:
                self.process_not_response(komut)
            except Exception:
                pass
            return
        if getattr(self, "awaiting_haber_detayi", None):
            try:
                self.process_haber_detayi_response(komut)
            except Exception:
                pass
            return
        if getattr(self, "awaiting_ilac", None):
            try:
                self.process_ilac_response(komut)
            except Exception:
                pass
            return
        # Hatırlatıcı beklemesi
        if getattr(self, "awaiting_hatirlatici", None):
            try:
                self.process_hatirlatici_response(komut)
            except Exception:
                pass
            return
        
        # Önceden tanımlı cevaplar
        if self.onceden_tanimli_cevap_ver(komut):
            return

        # Keyword triggers (haber, ara, müzik vb.)
        try:
            komut_lower = (komut or "").lower()
            for kw, func in getattr(self, "keyword_triggers", {}).items():
                if kw in komut_lower:
                    try:
                        func(komut)
                    except TypeError:
                        func()
                    return
        except Exception:
            pass

        # Komutlar sözlüğü
        for anahtar, fonksiyon in self.komutlar.items():
            if anahtar in komut.lower():
                try:
                    fonksiyon(komut)
                except TypeError:
                    try:
                        fonksiyon()
                    except Exception:
                        pass
                return

        self.konus("Bu komutu anlayamadım. Tekrar söyleyebilir misin?")
    def stop_reading(self, komut=None):
        print("Okuma durduruldu, beni dinlemeye hazır...")
        
        self.stop_speaking = True
        self.reading_haber = False
        self.awaiting_haber_detayi = False  
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        

        if hasattr(self, "gui"):
            try:
                self.gui.root.after(0, self.gui.mesaj_ekle, self.isim, "Seni dinliyorum, ne diyeceksin?")
            except Exception:
                pass
        else:
            print(f"{self.isim}: Seni dinliyorum, ne diyeceksin?")

        time.sleep(0.3)
    def process_haber_detayi_response(self, komut):
        try:
            if not komut:
                return
            text = str(komut).strip().lower()
            

            if text in ("hayır", "hayir", "iptal", "vazgeç", "vazgec", "olmaz", "yok"):
                self.konus("Tamam. Başka ne yapabilirim?")
                self.awaiting_haber_detayi = False  
                return

            try:
                num = int(text.split()[0])
                if 1 <= num <= len(self.links):
                    self.haberi_detayli_oku(num)
                    self.awaiting_haber_detayi = False 
                    return
            except (ValueError, IndexError):
                pass
            

            self.konus("Haber numarası veya 'hayır' söyleyin.")
            
        except Exception as e:
            self.konus(f"Haber detayı işleme hatası: {e}")
            self.awaiting_haber_detayi = False
    def dinle_hotword(self):
     
        sr_recognizer = sr.Recognizer()
        sr_recognizer.energy_threshold = 3000
        fs = 44100
        saniye = 0.5  
        try:
            ses = sd.rec(int(saniye * fs), samplerate=fs, channels=1, dtype=np.int16)
            sd.wait(timeout=1)
            ses = np.asarray(ses, dtype=np.float32)
            ses = ses / 32768.0
            audio_data = sr.AudioData((ses * 32768).astype(np.int16).tobytes(), fs, 2)
            try:
                text = sr_recognizer.recognize_google(audio_data, language="tr-TR")
                return text.lower()
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                return None
        except Exception:
            return None

    def hava_durumu_google(self, sehir="Bilecik"):
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        import time
        import webbrowser
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
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))
        try:
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
            weather_url = ("https://api.open-meteo.com/v1/forecast"
                           f"?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto")
            w = session.get(weather_url, timeout=8)
            w.raise_for_status()
            wj = w.json()
            cw = wj.get("current_weather")
            if not cw:
                speak("Hava durumu verisi alınamadı.")
                return
            temp = cw.get("temperature")  
            wind = cw.get("windspeed")    
            code = cw.get("weathercode")
            condition = code_map.get(code, "Bilinmeyen hava durumu")
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
            try:
                speak("Hava durumu servisine bağlanılamadı. Resmi meteoroloji sayfası açılıyor...")
                webbrowser.open("https://www.mgm.gov.tr/")  
            except Exception:
                speak("Hava durumu alınamadı. İnternet bağlantınızı kontrol edin.")
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

    def stop_reading(self, komut=None):
        

        self.stop_speaking = True

        self.reading_haber = False
        self.awaiting_haber_detayi = None

        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        if hasattr(self, "gui"):
            try:
                self.gui.root.after(0, self.gui.mesaj_ekle, "Sistem", "Haber okuma durduruldu.")
            except Exception:
                pass
        else:
            print("Haber okuma durduruldu.")

    def haberi_detayli_oku(self, index):
        import requests
        from bs4 import BeautifulSoup
        import json, re
        from urllib.parse import urljoin, urlparse, quote_plus, unquote
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
        headline = None
        try:
            headline = (self.haber_basliklari[index - 1] if hasattr(self, "haber_basliklari") else None)
        except Exception:
            headline = None
        headline = None
        try:
            if hasattr(self, "haber_basliklari"):
                headline = self.haber_basliklari[index - 1]
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
            soup, final_url = fetch_soup(start_url)
            domain = urlparse(final_url).netloc.lower() if final_url else urlparse(start_url).netloc.lower()
            parsed = urlparse(final_url or start_url)
            path = (parsed.path or "").strip("/")
            if (not path or path == "") and headline:
                try:
                    q = f"site:{domain} {headline}"
                    r = requests.post("https://html.duckduckgo.com/html/", data={"q": q}, headers=headers, timeout=10)
                    if r.status_code == 200:
                        so = BeautifulSoup(r.text, "html.parser")
                        found = None
                        for a in so.find_all("a", href=True):
                            h = a["href"].strip()
                            if h.startswith("/"):
                                h = urljoin(f"https://{domain}", h)
                            if h.startswith("http") and domain in urlparse(h).netloc:
                                found = h
                                break
                        if found:
                            soup, final_url = fetch_soup(found)
                            domain = urlparse(final_url).netloc.lower() if final_url else domain
                except Exception:
                    pass
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

    def ilac_hatirlat(self, komut=None):
        metin = (komut or "").lower().strip()
        metin = metin.replace("ilacı hatırlat", "").strip()
        if metin in ("hayır", "hayir", "iptal", "vazgeç", "vazgec"):
            self.konus("Tamam, ilacı hatırlatma iptal edildi.")
            self.awaiting_ilac = False
            self.awaiting_ilac_step = None
            self.awaiting_ilac_med = None
            return
        import re
        if metin:
            time_match = re.search(r'(\d{1,2}\s*[:\.]\s*\d{1,2})|(\d{1,2})(?=\D*$)', metin)
            if time_match:
                time_str = time_match.group(0)
                ilac = metin.replace(time_str, "").replace("saat", "").strip()
                if not ilac:
                    self.konus("Hangi ilacı hatırlatayım?")
                    self.awaiting_ilac = True
                    self.awaiting_ilac_step = 1
                    self.awaiting_ilac_med = None
                    return
                self.awaiting_ilac = False
                self.awaiting_ilac_step = None
                self.process_ilac_response(f"{ilac} {time_str}")
                return
        self.konus("Hangi ilacı hatırlatayım?")
        self.awaiting_ilac = True
        self.awaiting_ilac_step = 1  
        self.awaiting_ilac_med = None
        return
    def process_ilac_response(self, cevap):
        try:
            if not cevap:
                return
            text = str(cevap).strip()
            lower = text.lower().strip()
            if lower in ("hayır", "hayir", "iptal", "vazgeç", "vazgec"):
                self.konus("Tamam, ilacı hatırlatma iptal edildi.")
                self.awaiting_ilac = False
                self.awaiting_ilac_step = None
                self.awaiting_ilac_med = None
                return
            import re, datetime, threading
            step = getattr(self, "awaiting_ilac_step", None)
            def parse_time(s):
                s = s.lower()
                m = re.search(r'(\d{1,2})\s*[:\.]\s*(\d{1,2})', s)
                if m:
                    h = int(m.group(1)); mi = int(m.group(2)); return h, mi
                m2 = re.search(r'(\d{1,2})', s)
                if m2:
                    h = int(m2.group(1)); return h, 0
                return None
            if step is None:
                tparse = parse_time(text)
                if tparse:
                    time_part = re.search(r'(\d{1,2}\s*[:\.]\s*\d{1,2})|(\d{1,2})(?=\D*$)', text).group(0)
                    ilac = text.replace(time_part, "").replace("saat", "").strip()
                    if not ilac:
                        ilac = "ilaç"
                    hour, minute = tparse

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
                    self.awaiting_ilac = True
                    self.awaiting_ilac_step = 1
                    self.awaiting_ilac_med = text
                    self.konus(f"Tamam, '{text}' için. Saat kaçta hatırlatayım?")
                    self.awaiting_ilac_step = 2
                    return
            if step == 1:
                ilac = text
                self.awaiting_ilac_med = ilac
                self.konus(f"'{ilac}' ilacı için saat kaçta hatırlatayım?")
                self.awaiting_ilac_step = 2
                self.awaiting_ilac = True
                return
            if step == 2:
                ilac = getattr(self, "awaiting_ilac_med", None) or "ilacınız"
                parsed = parse_time(text)
                if not parsed:
                    m = re.search(r'([^\d:]+)\s+(\d{1,2}[:\.]\d{1,2}|\d{1,2})', text)
                    if m:
                        ilac = m.group(1).strip()
                        parsed = parse_time(m.group(2))
                if not parsed:
                    self.konus("Saati anlayamadım. Lütfen örnek: '10' veya '10:10' şeklinde yazın.")
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
    
    def bugun_ne_var(self): 
        import requests
        from bs4 import BeautifulSoup
        import xml.etree.ElementTree as ET
        from urllib.parse import urljoin, unquote
        import re
        import threading
        import time
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
            blacklist = ["diken", "sozcu", "rudaw"]
            try:
                rss = "https://news.google.com/rss?hl=tr&gl=TR&ceid=TR:tr"
                r = requests.get(rss, headers=headers, timeout=8)
                r.raise_for_status()
                root = ET.fromstring(r.content)
                items = root.findall(".//item")[:10]
                for it in items:
                    title = (it.find("title").text or "").strip() if it.find("title") is not None else None
                    link = pick_link_from_item(it)
                    if title and link:
                        if not any(b in link.lower() for b in blacklist):
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
                            if t not in found and href:
                                if not any(b in href.lower() for b in blacklist):
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
                self.konus("Haber alınamadı. İnternet bağlantınızı veya siteleri kontrol edin.")
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
            self.haber_basliklari = []
            self.links = []
            for title, link in zip(headlines, resolved):
                if title and link:
                    if not any(b in link.lower() for b in blacklist):
                        self.haber_basliklari.append(title)
                        self.links.append(link)
            mesaj = "Bugünün haber başlıkları:\n"
            for i, h in enumerate(self.haber_basliklari, 1):
                mesaj += f"{i}. {h}\n"
            if hasattr(self, "gui"):
                try:
                    self.gui.root.after(0, self.gui.mesaj_ekle, self.isim, mesaj)
                except Exception:
                    pass
            self.reading_haber = True
            try:
                self.konus("Günün öne çıkan haberleri:")
                for i, h in enumerate(self.haber_basliklari, 1):
                    if getattr(self, "stop_speaking", False):
                        self.stop_speaking = False
                        break
                    self.konus(f"{i}. {h}")
                    time.sleep(0.15)
                

                if not getattr(self, "stop_speaking", False):
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
                    self.awaiting_haber_detayi = True
                else:
                    self.stop_speaking = False
            finally:
                self.reading_haber = False
                if getattr(self, "stop_speaking", False):
                    self.stop_speaking = False

        threading.Thread(target=worker, daemon=True).start()
    def dinle(self):
        sr_recognizer = sr.Recognizer()
        sr_recognizer.energy_threshold = 4000
        fs = 44100  
        saniye = 5  
        print("Dinliyorum...")    
        try:
            ses = sd.rec(int(saniye * fs), samplerate=fs, channels=1, dtype=np.int16)
            sd.wait()  
            ses = np.asarray(ses, dtype=np.float32)
            ses = ses / 32768.0  
            audio_data = sr.AudioData(
                (ses * 32768).astype(np.int16).tobytes(),
                fs,
                2
            ) 
            try:
                text = sr_recognizer.recognize_google(audio_data, language="tr-TR")
                print("Siz (sesli):", text)
                return text.lower()
            except sr.UnknownValueError:
                print("Sesi anlayamadım.")
                return "ANLAŞILMADI"
            except sr.RequestError as e:
                print(f"Google Speech API hatası: {e}")
                return "HATA"
        except Exception as e:
            print(f"Dinleme hatası: {e}")
            return "HATA"
    
    def sohbet_et(self, komut=None):
        user_text = komut or self.gui.giris.get()
        self.gui.giris.delete(0, "end")

    # Mesajı kaydet
        self.messages.append({"role": "user", "content": user_text})

        try:
            completion = self.client.chat.completions.create(
                model="meta-llama/Llama-3.2-3B-Instruct:novita",
                messages=self.messages,
            )

            # Nokta ile content al
            reply = completion.choices[0].message.content

            # Cevabı kaydet (multi-turn için)
            self.messages.append({"role": "assistant", "content": reply})
            self.konus(reply)

        except Exception as e:
            self.konus("Üzgünüm, yanıt alınamadı: " + str(e))

    def onceden_tanimli_cevap_ver(self, komut):
        for anahtar, cevap in self.onceden_tanimli_cevaplar.items():
            if anahtar in komut:
                self.konus(cevap)
                return True
        return False
    def selamla(self):
        self.konus("Merhaba! Sana nasıl yardımcı olabilirim?")
    # ...existing code...
    def muzik_ac(self, komut=None):
        # Sadece masaüstünün kökündeki mp3 dosyalarını listele (alt klasörleri dahil etme)
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        mp3s = []
        try:
            for f in os.listdir(desktop):
                p = os.path.join(desktop, f)
                if os.path.isfile(p) and f.lower().endswith(".mp3"):
                    mp3s.append(p)
        except Exception:
            pass
        if not mp3s:
            self.konus("Masaüstünde mp3 dosyası bulunamadı.")
            return
        self.muzik_list = mp3s
        isimler = [os.path.splitext(os.path.basename(p))[0] for p in mp3s]
        mesaj = "Masaüstündeki şarkılar:\n" + "\n".join(f"{i+1}. {n}" for i, n in enumerate(isimler))
        self.konus(mesaj)
        self.konus("Hangi müziği açmamı istiyorsun? İsim ya da numara söyle.")
        self.awaiting_muzik = True
    def process_muzik_response(self, cevap):
        if not getattr(self, "awaiting_muzik", False):
            return
        if not cevap:
            return
        import re
        text = str(cevap).strip().lower()
        if text in ("hayır", "hayir", "iptal", "vazgeç", "vazgec", "olmaz"):
            self.konus("Tamam, müzik seçimi iptal edildi.")
            self.awaiting_muzik = False
            return

        def text_to_number(s):
            # Basit Türkçe sayı/ordinal -> int dönüştürücü
            s = s.lower()
            tokens = re.findall(r"[\wçğıöşü]+", s, flags=re.UNICODE)
            mapping = {
                "bir": 1, "iki": 2, "üç": 3, "uc": 3, "dört": 4, "dort": 4,
                "beş": 5, "bes": 5, "altı": 6, "alti": 6, "yedi": 7,
                "sekiz": 8, "dokuz": 9, "on": 10, "onbir": 11, "on iki": 12
            }
            for t in tokens:
                if t.isdigit():
                    try:
                        return int(t)
                    except:
                        pass
                if t in mapping:
                    return mapping[t]
                for k, v in mapping.items():
                    if t.startswith(k):
                        return v
            return None

        sel = None
        num = None
        try:
            num = int(text.split()[0])
        except Exception:
            num = text_to_number(text)

        if isinstance(num, int) and 1 <= num <= len(getattr(self, "muzik_list", [])):
            sel = self.muzik_list[num - 1]

        if sel is None:
            for p in getattr(self, "muzik_list", []):
                name = os.path.splitext(os.path.basename(p))[0].lower()
                if text in name or any(tok in name for tok in text.split()):
                    sel = p
                    break

        if sel is None:
            self.konus("Seçiminizi anlayamadım. Lütfen numara veya tam/parsiyel isim söyleyin.")
            return

        # Önce sesli olarak söylüyoruz, TTS bitince dosyayı yükleyip çalacağız
        try:
            mesaj = f"Çalıyor: {os.path.basename(sel)}. Müzik kapatmak için 'kapat' veya 'müziği kapat' söyleyin."
            self.konus(mesaj)
        except Exception:
            pass

        try:
            pygame.mixer.music.load(sel)
            pygame.mixer.music.play()
            self.current_music = sel
        except Exception as e:
            self.konus(f"Müzik çalınamadı: {e}")
        finally:
            self.awaiting_muzik = False

    def muzik_kapat(self, komut=None):
        try:
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
            if hasattr(self, "current_music"):
                ad = os.path.basename(self.current_music)
                self.konus(f"{ad} durduruldu.")
                del self.current_music
            else:
                self.konus("Müzik durduruldu.")
        except Exception as e:
            self.konus(f"Müzik kapatılamadı: {e}")
    def saat_soyle(self):
        self.konus("Şu an saat: " + datetime.datetime.now().strftime("%H:%M"))
        try:
            from zoneinfo import ZoneInfo
            now = datetime.datetime.now(ZoneInfo("Europe/Istanbul"))
        except Exception:
            try:
                import pytz
                now = datetime.datetime.now(pytz.timezone("Europe/Istanbul"))
            except Exception:
                now = datetime.datetime.now()
        self.konus("Şu an saat (İstanbul): " + now.strftime("%H:%M"))
    def tarih_soyle(self):
        tarih_str = self._format_tarih_turkce()
        self.konus("Bugün tarih: " + tarih_str)
        import datetime
        dt = datetime.datetime.now()
        months = {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
            7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
        }
        tarih_str = f"{dt.day} {months.get(dt.month, '')} {dt.year}"
        self.konus("Bugün tarih: " + tarih_str)
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
        # Kullanıcıdan ürün ismini alabilmek için beklemeye geç
        self.konus("Ne almak istiyorsunuz? Ürün adını söyleyin.")
        self.awaiting_alisveris = True
        return
        try:
            if not cevap:
                return
            text = str(cevap).strip()
            lower = text.lower()
            if lower in ("hayır", "hayir", "iptal", "vazgeç", "vazgec", "olmaz","istemiyorum"):
                self.konus("Tamam, alışveriş eklemeyi iptal ettim.")
                self.awaiting_alisveris = False
                return
            self.alisveris_listesi.append(text)
            self.hafizayi_kaydet()
            self.konus(f"'{text}' alışveriş listenize eklendi.")
            self.awaiting_alisveris = False    
        except Exception as e:
            self.konus(f"Alışveriş işleme hatası: {e}")
            self.awaiting_alisveris = False  
        # Kullanıcıdan ürün ismini alabilmek için beklemeye geç
        self.konus("Ne almak istiyorsunuz? Ürün adını söyleyin.")
        self.awaiting_alisveris = True
        return

    def process_alisveris_response(self, komut):
        try:
            if not komut:
                return
            text = str(komut).strip()
            lower = text.lower()
            if lower in ("hayır", "hayir", "iptal", "vazgeç", "vazgec", "olmaz"):
                self.konus("Tamam, alışveriş eklemeyi iptal ettim.")
                self.awaiting_alisveris = False
                return
            self.alisveris_listesi.append(text)
            self.hafizayi_kaydet()
            self.konus(f"'{text}' alışveriş listenize eklendi.")
            self.awaiting_alisveris = False
        except Exception as e:
            self.konus(f"Alışveriş işleme hatası: {e}")
            self.awaiting_alisveris = False
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
        self.konus(f"{dosya_adi} dosyası oluşturuldum.")
    def dosya_ac(self):
        dosya_adi = self.gui.giris.get()
        self.gui.giris.delete(0, tk.END)
        if os.path.exists(dosya_adi):
            with open(dosya_adi, "r", encoding="utf-8") as f:
                icerik = f.read()
                self.konus(icerik)
        else:
            self.konus("Dosya bulunamadı.")
    def hatirlatici_kur(self, komut=None):
        """Hatırlatıcı kurulum başlangıcı"""
        self.konus("Neyi hatırlatayım? Söyleyin. (Örn: Kardeşimin doğum günü, Toplantı, Spor antrenmanı vb.)")
        self.awaiting_hatirlatici = True
        self.hatirlatici_step = 1  # 1. adım: konu al
        self.hatirlatici_konu = None
        return

    def process_hatirlatici_response(self, komut):
        """Hatırlatıcı yanıt işleme"""
        import re
        import datetime
        import threading
        
        try:
            if not komut:
                return
            
            text = str(komut).strip()
            lower = text.lower()
            
            # İptal seçenekleri
            if lower in ("hayır", "hayir", "iptal", "vazgeç", "vazgec", "olmaz"):
                self.konus("Tamam, hatırlatıcı kurulumu iptal edildi.")
                self.awaiting_hatirlatici = False
                self.hatirlatici_step = None
                self.hatirlatici_konu = None
                return
            
            step = getattr(self, "hatirlatici_step", None)
            
            # 1. Adım: Konuyu al
            if step == 1:
                self.hatirlatici_konu = text
                self.konus(f"'{text}' için — Saat kaçta hatırlatayım? (Örn: '8', '14:30', 'yarın 8', 'pazartesi 9' vb.)")
                self.hatirlatici_step = 2
                self.awaiting_hatirlatici = True
                return
            
            # 2. Adım: Saati parse et ve hatırlatıcıyı kur
            if step == 2:
                konu = self.hatirlatici_konu or "Hatırlatıcı"
                
                # Saat parsing
                def parse_time_advanced(s):
                    """Saat, 'yarın X', 'pazartesi X' vb. formatları parse eder"""
                    s_lower = s.lower()
                    
                    # "yarın 8", "yarın 14:30" vb.
                    if "yarın" in s_lower or "yarin" in s_lower:
                        m = re.search(r'(\d{1,2})\s*[:\.]\s*(\d{1,2})|(\d{1,2})(?=\D*$)', s)
                        if m:
                            h = int(m.group(1) or m.group(3))
                            mi = int(m.group(2)) if m.group(2) else 0
                            delta_days = 1
                            return (h, mi, delta_days, "yarın")
                    
                    # "pazartesi 9", "salı 10:30" vb.
                    gun_map = {
                        "pazartesi": 0, "salı": 1, "çarşamba": 2, "perşembe": 3,
                        "cuma": 4, "cumartesi": 5, "pazar": 6,
                        "sali": 1, "carsamba": 2, "persembe": 3, "cumartesi": 5
                    }
                    for gun_tr, gun_idx in gun_map.items():
                        if gun_tr in s_lower:
                            m = re.search(r'(\d{1,2})\s*[:\.]\s*(\d{1,2})|(\d{1,2})(?=\D*$)', s)
                            if m:
                                h = int(m.group(1) or m.group(3))
                                mi = int(m.group(2)) if m.group(2) else 0
                                today_idx = datetime.datetime.now().weekday()
                                delta = (gun_idx - today_idx) % 7
                                if delta == 0:
                                    delta = 7  # Eğer bugün o gün ise, gelecek hafta o gün
                                return (h, mi, delta, gun_tr)
                    
                    # Sadece saat: "8", "14:30"
                    m = re.search(r'(\d{1,2})\s*[:\.]\s*(\d{1,2})|(\d{1,2})(?=\D*$)', s)
                    if m:
                        h = int(m.group(1) or m.group(3))
                        mi = int(m.group(2)) if m.group(2) else 0
                        return (h, mi, 0, None)  # Bugün, delta=0
                    
                    return None
                
                parsed = parse_time_advanced(text)
                if not parsed:
                    self.konus("Saati anlayamadım. Lütfen örnek: '8', '14:30', 'yarın 9', 'pazartesi 10' gibi söyleyin.")
                    return
                
                hour, minute, delta_days, day_info = parsed
                
                # Saat geçerliliği
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    self.konus("Geçersiz saat bilgisi. 0-23 arası saat ve 0-59 arası dakika girin.")
                    return
                
                # Target zamanı hesapla
                now = datetime.datetime.now()
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if delta_days > 0:
                    target = target + datetime.timedelta(days=delta_days)
                elif target <= now:
                    target = target + datetime.timedelta(days=1)
                
                delta_seconds = (target - now).total_seconds()
                
                # Hatırlatıcı timer'ı kur
                def hatirlatici_callback():
                    try:
                        self.konus(f"Hatırlatıcı: {konu}")
                    except Exception:
                        pass
                
                timer = threading.Timer(delta_seconds, hatirlatici_callback)
                timer.daemon = True
                timer.start()
               
                # Metadata kaydet
                self.hatirlatici_timer = timer
                self.hatirlatici_time = target.isoformat()
                
                # Kullanıcıya onay mesajı
                gun_str = day_info if day_info else "bugün"
                mesaj = f"Tamam. '{konu}' için {gun_str} saat {hour:02d}:{minute:02d} hatırlatması ayarlandı."
                mesaj += f"\n(İlk hatırlatma: {target.strftime('%Y-%m-%d %H:%M')})"
                self.konus(mesaj)
                
                # Durumu sıfırla
                self.awaiting_hatirlatici = False
                self.hatirlatici_step = None
                self.hatirlatici_konu = None
                return
        
        except Exception as e:
            self.konus(f"Hatırlatıcı kurulum hatası: {e}")
            self.awaiting_hatirlatici = False
            self.hatirlatici_step = None
            self.hatirlatici_konu = None
    def not_al(self):

        self.konus("Hangi notu almak istiyorsunuz? Söyleyin.")
        self.awaiting_not = True  
    def process_not_response(self, cevap):

        try:
            if not cevap:
                return
            text = str(cevap).strip()
            lower = text.lower()
            if lower in ("hayır", "hayir", "iptal", "vazgeç", "vazgec", "olmaz"):
                self.konus("Tamam, not almayı iptal ettim.")
                self.awaiting_not = False
                return
            self.notlar.append(text)
            self.hafizayi_kaydet()
            self.konus(f"Not kaydedildi: '{text}'")
            self.awaiting_not = False
        except Exception as e:
            self.konus(f"Not işleme hatası: {e}")
            self.awaiting_not = False
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
