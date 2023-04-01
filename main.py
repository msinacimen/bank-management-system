import sqlite3
import tkinter as tk
from datetime import timedelta, datetime
from random import randint
import calendar
import os.path
from tkinter import END
from tkinter.messagebox import showinfo
import networkx as nx

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
database = os.path.join(THIS_FOLDER, 'test_database')
conn = sqlite3.connect(database)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = 1")

# başlar başlamaz tarihi alıyoruz
c.execute('''SELECT CurrentDate
          FROM Date''')
data = c.fetchall()[0][0]
time = datetime.strptime(data, '%Y-%m-%d').date()

# 1 ay süre arttırımı için gerekli yapı
daysinmonth = calendar.monthrange(time.year, time.month)[1]

# # 1 ay arttırma kodu
# time += timedelta(days=daysinmonth)
# # tarih update fonksiyonu
# c.execute('''UPDATE Date
#           SET CurrentDate = ?''', (time,))

def ay_farki(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

def zaman_arttir(zaman):
    print(zaman)
    istenen_zaman = time
    for i in range(zaman):
        istenen_zaman = istenen_zaman + (timedelta(days=daysinmonth))
    return istenen_zaman


def deadlock(x):
    c.execute(f'''
            SELECT kaynak
            FROM islemler
            ORDER BY islem_no DESC
            LIMIT {x}''')
    giris = c.fetchall()
    c.execute(f'''
           SELECT hedef
           FROM islemler
           ORDER BY islem_no DESC
           LIMIT {x}''')
    sonuc = c.fetchall()
    print(giris)
    print(sonuc)
    test = [giris, sonuc]
    edges = []
    for i in range(int(x)):
        edges.append([test[0][i], test[1][i]])
    G = nx.DiGraph(edges)
    cycles = []
    for cycle in nx.simple_cycles(G):
        print(cycle)
        cycles.append(cycle)
    return cycles

def kontrol():
    global time
    # 1 ay arttırma kodu
    time = zaman_arttir(1)
    # tarih update fonksiyonu
    c.execute('''UPDATE Date
              SET CurrentDate = ?''', (time, ))
    # tüm kredileri al
    c.execute('''
            SELECT *
            FROM krediler''')
    data = c.fetchall()
    for satir in data: # [( 1 ), ( b )]
        print(satir)
        tc = satir[0]
        c.execute('''
                SELECT faiz, gecikme_faizi, toplam_bakiye
                FROM mudur''')
        data = c.fetchall()
        faiz = float(data[0][0])
        gecikme_faiz = float(data[0][1])
        her_ay = float(satir[6])
        bu_ay_faiz = float(satir[5])
        bu_ay_para = float(satir[4])
        yeni_ay = her_ay
        yeni_faiz = her_ay * faiz / 100
        yeni_toplam = float(satir[3]) + yeni_faiz
        kredi_tutar = float(satir[3])
        sure = satir[0][2]
        print(sure)
        # bitis_date = datetime.strptime(sure, '%Y-%m-%d').date()
        # if bitis_date <= time:
        #     c.execute(f'''
        #             DELETE FROM krediler
        #             WHERE krediyi_ceken = {tc}''')
        if kredi_tutar <= 0:
            c.execute(f'''
                    DELETE FROM krediler
                    WHERE krediyi_ceken = {tc}''')
        if bu_ay_para != 0 or bu_ay_faiz != 0:
            yeni_ay += bu_ay_para
            yeni_faiz += bu_ay_faiz + (bu_ay_para * gecikme_faiz / 100)
        c.execute(f'''
                UPDATE krediler
                SET kredi_tutari = {yeni_toplam},
                    bu_ayki = {yeni_ay},
                    bu_ayki_faiz = {yeni_faiz}
                WHERE krediyi_ceken = {tc}''')
    c.execute('''
                SELECT toplam_bakiye
                FROM mudur''')
    toplam_bak = c.fetchall()[0][0]
    c.execute('''
                SELECT calisan_maasi
                FROM mudur''')
    calisan_maas = c.fetchall()[0][0]
    c.execute(f'''SELECT COUNT(tc_kimlik)
                  FROM kullanici
                  WHERE kullanici.turu=2''')
    calisan_say = int(c.fetchall()[0][0])
    toplam_gider = calisan_maas * calisan_say
    c.execute('''
            SELECT SUM(bu_ayki_faiz), COUNT(krediyi_ceken)
            FROM krediler''')
    data = c.fetchall()
    if data[0][1]:
        toplam_gelir = float(data[0][0])
        yeni_bakiye = toplam_bak + toplam_gelir - toplam_gider
    else:
        yeni_bakiye = toplam_bak - toplam_gider
    c.execute(f'''
            UPDATE mudur
            SET toplam_bakiye = {yeni_bakiye}
            ''')
    return time


def genel_durum():
    pencere = tk.Tk()
    pencere.geometry('800x600')
    pencere.iconbitmap(resim)
    pencere.title('Genel Durum')
    text = tk.Text(pencere)
    text.grid(row=5, column=0)
    c.execute('''
            SELECT *
            FROM mudur''')
    data = c.fetchall()
    text.insert('1.0', "Faiz - Gecikme Faizi - Çalışan Maaşı  -  Toplam Bakiye\n")
    text.insert('2.0' ,'\n'.join(str(x) for x in data))
    def degerleri_degis(text, data):
        yeni_faiz = faiz.get()
        yeni_gecikme = gecikme_faizi.get()
        yeni_maas = calisan_maasi.get()
        if len(yeni_faiz) == 0:
            yeni_faiz = data[0][0]
        if len(yeni_gecikme) == 0:
            yeni_gecikme = data[0][1]
        if len(yeni_maas) == 0:
            yeni_maas = data[0][2]
        params = (yeni_faiz, yeni_gecikme, yeni_maas)
        c.execute(f'''
                UPDATE mudur
                SET faiz = ?,
                gecikme_faizi = ?,
                calisan_maasi = ?''', params)
        text.delete('1.0', END)
        text.insert('1.0', "Faiz - Gecikme Faizi - Çalışan Maaşı  -  Toplam Bakiye\n")
        text.insert('2.0' ,'\n'.join(str(x) for x in data))

    c.execute(f'''SELECT COUNT(tc_kimlik)
                  FROM kullanici
                  WHERE kullanici.turu=2''')
    calisan_say = int(c.fetchall()[0][0])
    toplam_gider = data[0][2] * calisan_say

    c.execute('''
            SELECT SUM(bu_ayki_faiz), COUNT(krediyi_ceken)
            FROM krediler''')
    if c.fetchall()[0][1] != 0:
        toplam_gelir = float(c.fetchall()[0][0])
    else:
        toplam_gelir = 0
    text.insert('3.0', f"\nGelir: {toplam_gelir}")

    text.insert('4.0', f"\nGiderler: {toplam_gider}, Çalışan Sayısı: {calisan_say}")

    tk.Label(pencere, text="Faiz").grid(row=0, column=0)
    faiz = tk.Entry(pencere)
    faiz.grid(row=0, column=1)
    tk.Label(pencere, text="Gecikme Faizi").grid(row=1, column=0)
    gecikme_faizi = tk.Entry(pencere)
    gecikme_faizi.grid(row=1, column=1)
    tk.Label(pencere, text="Çalışan Maaşı").grid(row=2, column=0)
    calisan_maasi = tk.Entry(pencere)
    calisan_maasi.grid(row=2, column=1)
    tk.Button(pencere, text="Değerleri Değiştir", command=lambda :degerleri_degis(text, data)).grid(row=4, column=0)


def yeni_para_birimi():
    pencere = tk.Tk()
    pencere.geometry('300x300')
    pencere.iconbitmap(resim)
    pencere.title('Para Birimi Ekle')

    def para_birim():
        birim_isim = donusum_isim.get()
        birim_donusum = birim_oran.get()
        c.execute(f'''
              INSERT INTO  hesap_tur_kodu(isim, donusum_orani) 
              VALUES 
              (?, ?)''', (birim_isim, birim_donusum))

    def para_guncelle():
        yeni_oran = birim_oran.get()
        print(yeni_oran)
        birim_isim = str(x_val.get())
        print(birim_isim)
        isim_temiz = birim_isim.replace('(','').replace(')','').replace('\'','').replace(',','')
        print(isim_temiz)
        c.execute('''
                UPDATE hesap_tur_kodu
                SET donusum_orani = ?
                WHERE isim = ?''', (yeni_oran, isim_temiz))


    c.execute('''
            SELECT isim
            FROM hesap_tur_kodu''')
    data = c.fetchall()
    tk.Label(pencere, text="Birim İsmi").grid(row=0, column=0)
    donusum_isim= tk.Entry(pencere)
    donusum_isim.grid(row=0, column=1)
    tk.Label(pencere, text="Dönüşüm Oranı").grid(row=1, column=0)
    birim_oran = tk.Entry(pencere)
    birim_oran.grid(row=1, column=1)
    tk.Button(pencere, text="Yeni Para Birimi Ekle", command=lambda: para_birim()).grid(row=2, column=0)
    tk.Label(pencere, text="Birimi güncelle").grid(row=3, column=0)
    birim_oran= tk.Entry(pencere)
    birim_oran.grid(row=3, column=1)
    tk.Label(pencere, text="Guncellemek istediğiniz değer?").grid(row=4, column=0)
    x_val = tk.StringVar()
    x_val.set(data[0])
    x_drop = tk.OptionMenu(pencere, x_val, *data)
    x_drop.configure(width=15, fg= "white",highlightthickness=0)
    x_drop.grid(row=4,column=1, padx=5, pady=5)
    tk.Button(pencere, text="Birimi Güncelle", command=lambda: para_guncelle()).grid(row=5, column=0)

def hesaplari_gor(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('1400x600')
    pencere.iconbitmap(resim)
    pencere.title('Hesapların')
    text = tk.Text(pencere, width=600, height=1400)
    text.pack()
    text.insert('1.0', "iban    -   hesap turu   -   bakiye\n")
    c.execute(f'''
              SELECT h.iban, tur.isim, h.bakiye
              FROM hesap AS h, kullanici_hesap AS bag, hesap_tur_kodu AS tur
              WHERE bag.iban = h.iban
              AND h.hesap_turu = tur.kod
              AND bag.tc_kimlik = {tc_kimlik}''')
    data = c.fetchall()
    text.insert('2.1', '\n'.join(str(x) for x in data))
    return data

def bilgileri_gor(tc_kimlik):
    print("Ad Soyad  -  Adres  -  Telefon Numarası  -  E-Posta  -  Rol")
    c.execute(f'''SELECT ad_soyad, adres, tel_no, eposta, hesap_tipi
              FROM kullanici, kullanici_turleri
              WHERE tur = turu
              AND tc_kimlik = {tc_kimlik}''')
    data = c.fetchall()
    print('\n'.join(str(x) for x in data))
    return data

def kredi_ode(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('800x600')
    pencere.iconbitmap(resim)
    pencere.title('Krediler')
    c.execute(f'''
              SELECT baslangic, bitis, kredi_tutari, bu_ayki, bu_ayki_faiz
              FROM krediler
              WHERE krediyi_ceken = {tc_kimlik}''')
    data = c.fetchall()
    print(data)
    text = tk.Text(pencere)
    text.grid(row=3, column=0)
    def ode(tc_kimlik):
        tutar = float(para.get())
        tutarvebirim = str(tutar) + 'Turk Lirasi'
        c.execute(f'''
                SELECT kredi_tutari, bu_ayki, bu_ayki_faiz
                FROM krediler
                WHERE krediyi_ceken = {tc_kimlik}''')
        data = c.fetchall()
        kredi_tutar = float(data[0][0])
        bu_ayki = float(data[0][1])
        bu_ayki_faiz =float(data[0][2])
        if bu_ayki_faiz == 0:
            if tutar > bu_ayki:
                bu_ayki = 0
                tutar -= bu_ayki
                kredi_tutar -= tutar
            else:
                bu_ayki = bu_ayki - tutar
                kredi_tutar -= tutar
        elif bu_ayki_faiz != 0 and tutar > bu_ayki_faiz:
            bu_ayki_faiz = 0
            tutar -= bu_ayki_faiz
            if tutar > bu_ayki:
                bu_ayki = 0
                tutar -= bu_ayki
                kredi_tutar -= tutar
            else:
                bu_ayki = bu_ayki - tutar
                kredi_tutar -= tutar
        else:
            bu_ayki_faiz -= tutar
            kredi_tutar -= tutar
        c.execute(f'''
                UPDATE krediler
                SET kredi_tutari = {kredi_tutar},
                    bu_ayki = {bu_ayki},
                    bu_ayki_faiz = {bu_ayki_faiz}
                WHERE krediyi_ceken = {tc_kimlik}''')
        c.execute(f'''INSERT INTO islemler(kaynak, hedef, islem, tutar, tarih)
                      VALUES
                      ({tc_kimlik}, "Banka", "4", ?, ?)''', (tutarvebirim, time))

    text.insert('1.0', "Başlangıç - Bitiş - Kredi Tutarı - Bu ay ödenmesi gereken  - Bu ayki faiz tutarı\n")
    text.insert('2.1' ,'\n'.join(str(x) for x in data))
    tk.Label(pencere, text="Tutar").grid(row=0, column=0)
    para = tk.Entry(pencere)
    para.grid(row=0, column=1)
    tk.Button(pencere, text="İşlemi Onayla", command=lambda :ode(tc_kimlik)).grid(row=1, column=0)

def para_yuklemecekme(tip, tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('800x600')
    pencere.iconbitmap(resim)
    pencere.title('Para Yükle/Çek')
    c.execute(f'''
              SELECT h.iban, tur.isim, h.bakiye
              FROM hesap AS h, kullanici_hesap AS bag, hesap_tur_kodu AS tur
              WHERE bag.iban = h.iban
              AND h.hesap_turu = tur.kod
              AND bag.tc_kimlik = {tc_kimlik}''')
    data = c.fetchall()
    text = tk.Text(pencere)
    text.grid(row=3, column=0)
    def islem(tip, tc_kimlik):
        tutar = float(para.get())
        KayHed = str(iban.get())
        c.execute(f'''
                SELECT bakiye
                FROM hesap
                WHERE iban = {KayHed}''', )
        KayHed_bakiye = c.fetchall()[0][0]
        # Para Yatırma
        if tip == 1:
            print("Paraniz yatırlıyor")
            TutarveBirim = str(tutar) + " Turk Lirasi"
            c.execute(f'''
                      SELECT tur.donusum_orani, tur.isim
                      FROM hesap AS h, hesap_tur_kodu AS tur
                      WHERE h.hesap_turu = tur.kod
                      AND h.iban = {KayHed}''')
            data = c.fetchall()
            donusum_orani = data[0][0]
            hedef_bakiye_birim = str(KayHed_bakiye) + " " + data[0][1]
            gidenpara = tutar / donusum_orani
            c.execute(f'''INSERT INTO islemler(kaynak, hedef, islem, tutar, hedef_bakiye, tarih)
                      VALUES
                      ({tc_kimlik}, {KayHed}, "2", ?, ?, ?)''', (TutarveBirim, hedef_bakiye_birim, time))
            c.execute(f'''UPDATE hesap
                      SET bakiye = bakiye + {gidenpara}
                      WHERE iban = {KayHed}''')
        # Para Cekme
        elif tip == 2:
            print("Paraniz cekiliyor")
            c.execute(f'''
                      SELECT tur.isim
                      FROM hesap AS h, hesap_tur_kodu AS tur
                      WHERE h.hesap_turu = tur.kod
                      AND h.iban = {KayHed}''')
            kaynak_tur = c.fetchall()[0][0]
            TutarveBirim = str(tutar) + " " + kaynak_tur
            bakiyebirim = str(KayHed_bakiye) + " " + kaynak_tur
            c.execute(f'''INSERT INTO islemler(kaynak, hedef, islem, tutar, kaynak_bakiye, tarih)
                      VALUES
                      ({KayHed}, {tc_kimlik}, "3", ?, ?, ?)''', (TutarveBirim, bakiyebirim, time))
            c.execute(f'''UPDATE hesap
                      SET bakiye = bakiye - {tutar} 
                      WHERE iban = {KayHed}''')

    text.insert('1.0', "İban  -  Para Birimi  -  Bakiye\n")
    text.insert('2.1' ,'\n'.join(str(x) for x in data))
    tk.Label(pencere, text="Tutar").grid(row=0, column=0)
    para = tk.Entry(pencere)
    para.grid(row=0, column=1)
    tk.Label(pencere, text="iban").grid(row=1, column=0)
    iban = tk.Entry(pencere)
    iban.grid(row=1, column=1)
    tk.Button(pencere, text="İşlemi Onayla", command=lambda :islem(tip, tc_kimlik)).grid(row=2, column=0)

def para_transfer(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('1400x600')
    pencere.iconbitmap(resim)
    pencere.title('Para Gönderme')
    text = tk.Text(pencere)
    text.grid(row=0, column=0)
    text.insert('1.0', "iban    -   hesap turu   -   bakiye\n")
    c.execute(f'''
                  SELECT h.iban, tur.isim, h.bakiye
                  FROM hesap AS h, kullanici_hesap AS bag, hesap_tur_kodu AS tur
                  WHERE bag.iban = h.iban
                  AND h.hesap_turu = tur.kod
                  AND bag.tc_kimlik = {tc_kimlik}''')
    data = c.fetchall()
    text.insert('2.1', '\n'.join(str(x) for x in data))
    def para_transferic(tc_kimlik):
        kaynak = girilen_kaynak.get()
        print(kaynak)
        c.execute(f'''SELECT iban 
                      FROM kullanici_hesap 
                      WHERE iban = {kaynak}
                      AND tc_kimlik = {tc_kimlik}''')
        data = c.fetchall()
        if len(data):
            # para yollancak hesap secimi
            hedef = girilen_hedef.get()
            c.execute(f'''SELECT iban 
                          FROM kullanici_hesap 
                          WHERE iban = {hedef}''')
            data = c.fetchall()
            if len(data):
                tutar = girilen_tutar.get()
                tutar=float(tutar)
                print(tutar)
                c.execute(f'''SELECT bakiye
                              FROM hesap
                              WHERE iban = {kaynak}''')
                data = c.fetchall()[0][0]
                if data > tutar:
                    # yeterli bakiye varsa yolla
                    print("paraniz aktariliyor...")
                    para_aktarimi(kaynak, hedef, tutar, data)
                else:
                    tk.messagebox.showinfo("Eksik Bakiye", "Bakiyeniz Yetersiz")
            else:
                tk.messagebox.showinfo("Iban bulunamadı", "Böyle bir IBAN mevcut değil!")
        else:
            tk.messagebox.showinfo("Hesabınız Bulunamadı", "Böyle bir hesabınız yok!")

    tk.Label(pencere, text="Hangi Hesap?").grid(row=3, column=0)
    girilen_kaynak = tk.Entry(pencere)
    girilen_kaynak.grid(row=4, column=0)
    tk.Label(pencere, text="Karşı Hesap?").grid(row=5, column=0)
    girilen_hedef = tk.Entry(pencere)
    girilen_hedef.grid(row=6, column=0)
    tk.Label(pencere, text="Tutar:").grid(row=7, column=0)
    girilen_tutar = tk.Entry(pencere)
    girilen_tutar.grid(row=8, column=0)
    tk.Button(pencere, text="Para Transfer", command=lambda: para_transferic(tc_kimlik)).grid(row=9, column=0)


def para_aktarimi(kaynak, hedef, tutar, kaynak_bakiye):
    print("para aktarimi")
    c.execute(f'''SELECT bakiye
              FROM hesap
              WHERE iban = {hedef}''')
    hedef_bakiye = c.fetchall()[0][0]
    c.execute(f'''
              SELECT tur.donusum_orani, tur.isim
              FROM hesap AS h, hesap_tur_kodu AS tur
              WHERE h.hesap_turu = tur.kod
              AND h.iban = {kaynak}''')
    data = c.fetchall()
    kaynak_donusum = data[0][0]
    kaynak_tur = data[0][1]
    c.execute(f'''
              SELECT tur.donusum_orani, tur.isim
              FROM hesap AS h, hesap_tur_kodu AS tur
              WHERE h.hesap_turu = tur.kod
              AND h.iban = {hedef}''')
    stutar = str(tutar)
    data = c.fetchall()
    hedef_donusum = data[0][0]
    hedef_tur = data[0][1]
    TutarveBirim = stutar + " " + kaynak_tur
    kaynak_bakiye_birim = str(kaynak_bakiye) + " " + kaynak_tur
    hedef_bakiye_birim = str(hedef_bakiye) + " " + hedef_tur
    GelenPara = tutar * kaynak_donusum / hedef_donusum
    print(TutarveBirim, GelenPara)
    c.execute(f'''INSERT INTO islemler(kaynak, hedef, islem, tutar, kaynak_bakiye, hedef_bakiye, tarih)
              VALUES
              ({kaynak}, {hedef}, "1", ?, ?, ?, ?)''', (TutarveBirim, kaynak_bakiye_birim, hedef_bakiye_birim, time))
    c.execute(f'''UPDATE hesap
              SET bakiye = bakiye - {tutar}
              WHERE iban = {kaynak}''')
    c.execute(f'''UPDATE hesap
              SET bakiye = bakiye + {GelenPara}
              WHERE iban = {hedef}''')


def bilgi_gorguncelle(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('1400x600')
    pencere.iconbitmap(resim)
    pencere.title('Bilgi Görüntüleme-Güncelleme')
    text = tk.Text(pencere)
    text.grid(row=0, column=0)
    text.insert('1.0', "Ad Soyad    -    Adres    -    Telefon Numarası    -    E-Posta   -   TC Kimlik\n")
    c.execute(f'''SELECT ad_soyad, adres, tel_no, eposta, tc_kimlik
                  FROM kullanici, kullanici_turleri
                  WHERE tur = turu
                  AND tc_kimlik = {tc_kimlik}''')
    data = c.fetchall()
    text.insert('2.1', '\n'.join(str(x) for x in data))
    text.insert('5.0', "\n\n\nAd Soyad için 1 -  Adres için 2  -  Telefon Numarası için 3  -  E-Posta için 4  Seçiniz \n")

    def bilgi_guncelle(tc_kimlik):
        secim = int(girilen_secim.get())
        yeniveri = str(girilen_yeniveri.get())
        data = ("ad_soyad", "adres", "tel_no", "eposta")
        c.execute(f'''UPDATE kullanici
                    SET {data[secim-1]} = ?
                    WHERE tc_kimlik = {tc_kimlik}''', (yeniveri, ))
        c.execute(f'''SELECT ad_soyad, adres, tel_no, eposta
                          FROM kullanici, kullanici_turleri
                          WHERE tur = turu
                          AND tc_kimlik = {tc_kimlik}''')
        data = c.fetchall()
        text.insert('9.0', "Bilgiler Güncellendi\n")
        text.insert('10.0', '\n'.join(str(x) for x in data))


    tk.Label(pencere, text="Değiştirmek İstediğiniz Veri No'su").grid(row=5, column=0)
    girilen_secim = tk.Entry(pencere)
    girilen_secim.grid(row=6, column=0)
    tk.Label(pencere, text="Yeni Veri").grid(row=7, column=0)
    girilen_yeniveri = tk.Entry(pencere)
    girilen_yeniveri.grid(row=8, column=0)
    tk.Button(pencere, text="Bilgi Güncelle", command=lambda: bilgi_guncelle(tc_kimlik)).grid(row=9,column=0)


def aylik_ozet(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('1400x600')
    pencere.iconbitmap(resim)
    pencere.title('Aylık Özet')
    text = tk.Text(pencere, width=600, height=1400)
    text.pack()
    aysayisi = 1
    sure = time - (timedelta(days=daysinmonth) * (aysayisi - 1))
    c.execute(f'''SELECT i.kaynak, i.hedef, k.tur, i.tutar, i.tarih
              FROM islemler AS i, islem_tur_kodu AS k
              WHERE k.kod = i.islem
              AND ((i.kaynak = (SELECT iban
                   FROM kullanici_hesap
                   WHERE tc_kimlik = {tc_kimlik}) OR
                   i.hedef = (SELECT iban
                   FROM kullanici_hesap
                   WHERE tc_kimlik = {tc_kimlik}))
              OR (i.kaynak = {tc_kimlik} OR i.hedef = {tc_kimlik}))
              AND i.tarih >= ? ''', (sure, ))
    data = c.fetchall()
    text.insert('1.0', "kaynak  -  hedef  -  işlem türü  -  tutar  -  tarih\n")
    text.insert('2.1' ,'\n'.join(str(x) for x in data))

def SonXislem(x):
    pencere = tk.Tk()
    pencere.geometry('300x100')
    pencere.iconbitmap(resim)
    pencere.title('Son İşlemler')

    def sonislemler(x):
        pencere = tk.Tk()
        pencere.geometry('1400x600')
        pencere.iconbitmap(resim)
        pencere.title('Son İşlemler')
        text = tk.Text(pencere, width=600, height=1400)
        text.pack()
        x = kacislem.get()
        c.execute(f'''
                  SELECT islem_no, kaynak, hedef, tur, tutar, kaynak_bakiye, hedef_bakiye, tarih
                  FROM islemler, islem_tur_kodu
                  WHERE islem = kod
                  ORDER BY islem_no DESC
                  LIMIT {x}''')
        data = c.fetchall()
        cycles = deadlock(x)
        text.insert('1.0', "islem no -- kaynak -- hedef -- islem -- tutar -- kaynak bakiye -- hedef bakiye -- tarih\n")
        text.insert('2.1' ,'\n'.join(str(x) for x in data))
        text.insert('100.1' ,f'\nDeadLock Simülasyonu\nDeadlock Sayısı: {len(cycles)}\n')
        text.insert('101.1' ,f'\n'.join(str(x) for x in cycles))
        return data

    kacislem = tk.Entry(pencere)
    kacislem.grid(row=0, column=0)
    tk.Button(pencere, text="İşlemleri Gör", command=lambda :sonislemler(x)).grid(row=1, column=0)

def kullanici_ekle(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('400x500')
    pencere.iconbitmap(resim)
    pencere.title('Kullanıcı Ekle')

    def musteri_ekle(tc_kimlik):
        yeni_tc = girilen_tc.get()
        print(yeni_tc)
        yeni_ad = girilen_ad.get()
        print(yeni_ad)
        yeni_adres = girilen_adres.get()
        print(yeni_adres)
        yeni_tel = girilen_tel.get()
        print(yeni_tel)
        yeni_eposta = girilen_eposta.get()
        print(yeni_eposta)
        print(type(yeni_eposta))
        yeni_sifre = girilen_sifre.get()
        print(yeni_sifre)
        params = (yeni_tc, yeni_ad, yeni_adres, yeni_tel, yeni_eposta, yeni_sifre)
        c.execute(f'''
                  INSERT INTO kullanici(tc_kimlik, ad_soyad, adres, tel_no, eposta, sifre)
                  VALUES
                  (?, ?, ?, ?, ?, ?)''', params)
        # temsilci sayısını alma
        c.execute('''
                  SELECT COUNT(temsilci_tc), temsilci_tc
                  FROM musteri_temsilci
                  GROUP BY temsilci_tc
                  ORDER BY COUNT(temsilci_tc) ASC''')
        data = c.fetchall()
        print(data[0][1])
        c.execute(f'''
                  SELECT turu
                  FROM kullanici
                  WHERE tc_kimlik = {tc_kimlik}''')
        tur = int(c.fetchall()[0][0])
        if tur == 1:
            print("müşteri kullanıcı ekleyemez!")
            return
        # temsilci ise ekleyen ona ekle
        if tur == 2:
            temsilci_tc = tc_kimlik
        # müdür ise ekleyen en az olana ekle
        if tur == 3:
            temsilci_tc = data[0][1]
        c.execute(f'''
                  INSERT INTO musteri_temsilci(temsilci_tc, kullanici_tc)
                  VALUES
                  (?, ?)''', (temsilci_tc, yeni_tc))

    tk.Label(pencere, text="Kullanıcı TC").grid(row=0, column=0)
    girilen_tc = tk.Entry(pencere)
    girilen_tc.grid(row=0, column=1)
    tk.Label(pencere, text="Kullanıcı Adı").grid(row=1, column=0)
    girilen_ad = tk.Entry(pencere)
    girilen_ad.grid(row=1, column=1)
    tk.Label(pencere, text="Kullanıcı Adresi").grid(row=2, column=0)
    girilen_adres = tk.Entry(pencere)
    girilen_adres.grid(row=2, column=1)
    tk.Label(pencere, text="Kullanıcı E-Postası").grid(row=3, column=0)
    girilen_tel = tk.Entry(pencere)
    girilen_tel.grid(row=3, column=1)
    tk.Label(pencere, text="Kullanıcı Telefon Numarası").grid(row=4, column=0)
    girilen_eposta = tk.Entry(pencere)
    girilen_eposta.grid(row=4, column=1)
    tk.Label(pencere, text="Kullanıcı Şifresi").grid(row=5, column=0)
    girilen_sifre = tk.Entry(pencere)
    girilen_sifre.grid(row=5, column=1)
    tk.Button(pencere, text="Kullanıcı Ekle", command=lambda :musteri_ekle(tc_kimlik)).grid(row=6, column=0)

def temsilci_ekle(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('400x500')
    pencere.iconbitmap(resim)
    pencere.title('Temsilci Ekle')

    def musteri_ekle(tc_kimlik):
        yeni_tc = girilen_tc.get()
        print(yeni_tc)
        yeni_ad = girilen_ad.get()
        print(yeni_ad)
        yeni_adres = girilen_adres.get()
        print(yeni_adres)
        yeni_tel = girilen_tel.get()
        print(yeni_tel)
        yeni_eposta = girilen_eposta.get()
        print(yeni_eposta)
        print(type(yeni_eposta))
        yeni_sifre = girilen_sifre.get()
        print(yeni_sifre)
        params = (yeni_tc, yeni_ad, yeni_adres, yeni_tel, yeni_eposta, yeni_sifre)
        c.execute(f'''
                  INSERT INTO kullanici(tc_kimlik, ad_soyad, adres, tel_no, eposta, turu, sifre)
                  VALUES
                  (?, ?, ?, ?, ?, 2, ?)''', params)
        c.execute(f'''
                  INSERT INTO musteri_temsilci(temsilci_tc, kullanici_tc)
                  VALUES
                  (?, ?)''', (yeni_tc, yeni_tc))

    tk.Label(pencere, text="Temsilci TC").grid(row=0, column=0)
    girilen_tc = tk.Entry(pencere)
    girilen_tc.grid(row=0, column=1)
    tk.Label(pencere, text="Temsilci Adı").grid(row=1, column=0)
    girilen_ad = tk.Entry(pencere)
    girilen_ad.grid(row=1, column=1)
    tk.Label(pencere, text="Temsilci Adresi").grid(row=2, column=0)
    girilen_adres = tk.Entry(pencere)
    girilen_adres.grid(row=2, column=1)
    tk.Label(pencere, text="Temsilci E-Postası").grid(row=3, column=0)
    girilen_tel = tk.Entry(pencere)
    girilen_tel.grid(row=3, column=1)
    tk.Label(pencere, text="Temsilci Telefon Numarası").grid(row=4, column=0)
    girilen_eposta = tk.Entry(pencere)
    girilen_eposta.grid(row=4, column=1)
    tk.Label(pencere, text="Temsilci Şifresi").grid(row=5, column=0)
    girilen_sifre = tk.Entry(pencere)
    girilen_sifre.grid(row=5, column=1)
    tk.Button(pencere, text="Temsilci Ekle", command=lambda :musteri_ekle(tc_kimlik)).grid(row=6, column=0)

def hesap_acma_talebi(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('800x600')
    pencere.iconbitmap(resim)
    pencere.title('Hesap Açma Talebi ')
    text = tk.Text(pencere)
    text.grid(row=2, column=0)
    c.execute('''
              SELECT kod, isim
              FROM hesap_tur_kodu
              ''')
    data = c.fetchall()
    def acma_talep():
        yeni_hesap_tur = int(hesap_tur.get())
        c.execute(f'''
                  INSERT INTO talepler(talep_eden, talep_id, degisken_1)
                  VALUES
                  ({tc_kimlik}, 1, {yeni_hesap_tur})''')
        text.insert('10.0', "\nHesap Açma Talebi Oluşturuldu")

    text.insert('1.0', "Kod  -  İsim\n")
    text.insert('2.1' ,'\n'.join(str(x) for x in data))
    tk.Label(pencere, text="Açmak istediğiniz hesabın kodunu giriniz").grid(row=0, column=0)
    hesap_tur = tk.Entry(pencere)
    hesap_tur.grid(row=0, column=1)
    tk.Button(pencere, text="Talep için tıklayın", command=lambda :acma_talep()).grid(row=1, column=0)


def hesap_silme_talebi(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('800x600')
    pencere.iconbitmap(resim)
    pencere.title('Hesap Silme Talebi ')
    text = tk.Text(pencere)
    text.grid(row=2, column=0)
    c.execute(f'''
              SELECT h.iban, tur.isim, h.bakiye
              FROM hesap AS h, kullanici_hesap AS bag, hesap_tur_kodu AS tur
              WHERE bag.iban = h.iban
              AND h.hesap_turu = tur.kod
              AND bag.tc_kimlik = {tc_kimlik}''')
    data = c.fetchall()
    def silme_talep():
        silinmek_istenen_iban = int(iban.get())
        c.execute(f'''SELECT bakiye 
              FROM hesap 
              WHERE iban = {silinmek_istenen_iban}''')
        bakiye = c.fetchall()[0][0]
        if bakiye == 0:
            text.insert('10.0', "\nsectiginiz hesabın silinmesi için talep oluşturuluyor")
            c.execute(f'''
                      INSERT INTO talepler(talep_eden, talep_id, degisken_1)
                      VALUES
                      ({tc_kimlik}, 2, {silinmek_istenen_iban})''')
        else:
            text.insert('10.0', "\nhesapta bakiye mevcut silim talebi iptal edildi!")
            return
    text.insert('1.0', "İban  -  Hesap Türü  -  Bakiye\n")
    text.insert('2.1' ,'\n'.join(str(x) for x in data))
    tk.Label(pencere, text="Silmek istediğiniz hesap türünün ibanını giriniz").grid(row=0, column=0)
    iban = tk.Entry(pencere)
    iban.grid(row=0, column=1)
    tk.Button(pencere, text="Talep için tıklayın", command=lambda :silme_talep()).grid(row=1, column=0)

def kredi_talebi(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('400x200')
    pencere.iconbitmap(resim)
    pencere.title('Kredi Talebi ')

    def kredi_talep(tc_kimlik):
        talep_miktar = kredi_miktar.get()
        talep_sure = kredi_sure.get()
        c.execute(f'''
                  INSERT INTO talepler(talep_eden, talep_id, degisken_1, degisken_2)
                  VALUES
                  ({tc_kimlik}, 3, {talep_miktar}, {talep_sure})''')
        print("kredi talep edildi!")
        pencere.destroy()


    tk.Label(pencere, text="İstediğiniz kredi miktarını girin").grid(row=0, column=0)
    kredi_miktar = tk.Entry(pencere)
    kredi_miktar.grid(row=0, column=1)
    tk.Label(pencere, text="İstediğiniz kredi süresini ay olarak girin").grid(row=1, column=0)
    kredi_sure = tk.Entry(pencere)
    kredi_sure.grid(row=1, column=1)
    tk.Button(pencere, text="Talep için tıklayın", command=lambda :kredi_talep(tc_kimlik)).grid(row=2, column=0)


def talep_incele(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('800x600')
    pencere.iconbitmap(resim)
    pencere.title('Talep incele')
    text = tk.Text(pencere)
    text.grid(row=3, column=0)
    c.execute(f'''
              SELECT t.talep_eden, tur.istek, t.degisken_1, t.degisken_2, t.talep_auto_inc
              FROM talepler AS t, talep_tur AS tur, musteri_temsilci AS mt
              WHERE t.talep_id = tur.id
              AND t.talep_eden = mt.kullanici_tc
              AND mt.temsilci_tc = {tc_kimlik}''')
    data = c.fetchall()
    def talep_onay(data):
        test = talep_numara.get()
        if len(test):
            secim = int(test)
            secim -= 1
            if data[secim][1] == "hesap açma":
                # degisken_1 == yeni_hesap_tur
                print("Hesap Açılıyor")
                yeni_iban = ''.join(str(randint(0, 9)) for _ in range(7))
                c.execute('''
                          SELECT iban
                          FROM hesap''')
                data_iban = c.fetchall()
                for i in range(len(data_iban)):
                    # Yeni iban databasede varsa sıfırdan başlat random işlemini
                    if yeni_iban == data_iban[i]:
                        yeni_iban = ''.join(str(randint(0, 9)) for _ in range(7))
                        i = 0
                    # eğer Yeni ibanın ilk karakteri 0sa sıfırdan başlat random işlemini
                    if yeni_iban[0] == 0:
                        yeni_iban = ''.join(str(randint(0, 9)) for _ in range(7))
                        i = 0
                c.execute(f'''INSERT INTO hesap(iban, hesap_turu)
                          VALUES
                          ({yeni_iban}, {data[secim][2]})
                          ''')
                c.execute(f'''INSERT INTO kullanici_hesap(iban, tc_kimlik)
                          VALUES
                          ({yeni_iban}, {data[secim][0]})''')
                c.execute(f'''
                          DELETE FROM talepler
                          WHERE talep_auto_inc = {data[secim][4]}
                          ''')
            elif data[secim][1] == "hesap silme":
                # degisken_1 == iban
                print("Hesap Siliniyor")
                c.execute(f'''
                          DELETE FROM hesap
                          WHERE iban = {data[secim][2]}
                          ''')
                c.execute(f'''
                          DELETE FROM kullanici_hesap
                          WHERE iban = {data[secim][2]}''')
                c.execute(f'''
                          DELETE FROM talepler
                          WHERE talep_auto_inc = {data[secim][4]}
                          ''')
            elif data[secim][1] == "kredi talebi":
                # degisken - 1 kredi miktarı
                # degisken - 2 kredi süresi
                print("kredi veriliyor")
                c.execute('''
                        SELECT faiz
                        FROM mudur''')
                faiz = float(c.fetchall()[0][0] / 100)
                kredi_miktar = int(data[secim][2])
                kredi_sure = int(data[secim][3])
                bitis_time = zaman_arttir(kredi_sure)
                kredi_tutar = kredi_miktar + (kredi_miktar / kredi_sure * faiz)
                bu_ayki = float(kredi_miktar / kredi_sure)
                bu_ayki_faiz = float(kredi_miktar / kredi_sure * faiz)
                c.execute(f'''
                        INSERT INTO krediler(krediyi_ceken, baslangic, bitis, kredi_tutari, bu_ayki, bu_ayki_faiz, her_ay)
                        VALUES
                        (?, ?, ?, ?, ?, ?, ?)''', (data[secim][0], time, bitis_time, kredi_tutar, bu_ayki, bu_ayki_faiz, bu_ayki))
                c.execute(f'''
                        SELECT * 
                        FROM krediler''')
                print(c.fetchall())
                c.execute(f'''
                          DELETE FROM talepler
                          WHERE talep_auto_inc = {data[secim][4]}
                          ''')

    def talep_red(data):
        red = int(talep_numara.get())
        c.execute(f'''
        DELETE FROM talepler
        WHERE talep_auto_inc = {data[red-1][4]}
                ''')

    text.insert('1.0', "   Talep Eden  -  İstek\n")
    a = 1
    for i in data:
        text.insert('10.0',f"{a} - {i[0]}  {i[1]}  {i[2]}  {i[3]}\n")
        a += 1
    tk.Label(pencere, text="Onaylamak ya da reddetmek istediğiniz talebin numarası").grid(row=0, column=0)
    talep_numara = tk.Entry(pencere)
    talep_numara.grid(row=0, column=1)
    tk.Button(pencere, text="Onaylamak için tıklayın", command=lambda :talep_onay(data)).grid(row=1, column=0)
    tk.Button(pencere, text="Reddetmek için tıklayın", command=lambda: talep_red(data)).grid(row=1, column=1)


def kullanicilari_listele(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('1400x600')
    pencere.iconbitmap(resim)
    pencere.title('Temsilcinin Kullanıcılarını Görüntüleme')
    text = tk.Text(pencere)
    text.grid(row=0, column=0)
    text.insert('1.0', "Ad Soyad    -    Adres    -    Telefon Numarası    -    E-Posta   -   TC Kimlik\n")
    c.execute(f'''SELECT ad_soyad, adres, tel_no, eposta, tc_kimlik
                  FROM kullanici, musteri_temsilci
                  WHERE temsilci_tc = {tc_kimlik}
                  AND kullanici.tc_kimlik = musteri_temsilci.kullanici_tc''')
    data = c.fetchall()
    text.insert('2.1', '\n'.join(str(x) for x in data))
    text.insert('5.0', "\n\n\nAd Soyad için 1 -  Adres için 2  -  Telefon Numarası için 3  -  E-Posta için 4  Seçiniz \n")
    def kullanicilari_guncelle():
        tc = girilen_tc.get()
        secim = int(girilen_secim.get())
        yeniveri = str(girilen_yeniveri.get())
        data = ("ad_soyad", "adres", "tel_no", "eposta")
        c.execute(f'''UPDATE kullanici
                            SET {data[secim - 1]} = ?
                            WHERE tc_kimlik = {tc}''', (yeniveri,))
        text.insert('10.0', "Bilgi Güncellendi\n")
        text.insert('11.0', '\n'.join(str(x) for x in data))

    def kullanicilari_sil():
        silincek_tc = silinen_tc.get()
        c.execute("PRAGMA foreign_keys = 0")
        c.execute(f'''
                DELETE FROM hesap
                WHERE iban IN(SELECT iban
                FROM kullanici_hesap
                WHERE tc_kimlik = {silincek_tc})''')
        c.execute(f'''
                DELETE FROM kullanici_hesap
                WHERE tc_kimlik = {silincek_tc}''')
        c.execute(f'''
                DELETE FROM kullanici
                WHERE tc_kimlik = {silincek_tc}''')
        c.execute(f'''
                DELETE FROM talepler
                WHERE talep_eden = {silincek_tc}''')
        c.execute(f'''
                DELETE FROM krediler
                WHERE krediyi_ceken = {silincek_tc}''')
        c.execute(f'''
                DELETE FROM musteri_temsilci
                WHERE kullanici_tc = {silincek_tc}''')
        c.execute("PRAGMA foreign_keys = 1")
        text.insert('10.0', "Veri Silindi\n")

    def musteriler_icin_hesap():
        tc = str(musteri_tc.get())
        c.execute(f'''SELECT tc_kimlik
                      FROM kullanici, musteri_temsilci
                      WHERE temsilci_tc = {tc_kimlik}
                      AND kullanici.tc_kimlik = musteri_temsilci.kullanici_tc''')
        data = c.fetchall()
        print(data)
        for i in data:
            for j in i:
                if tc == str(j):
                    hesaplari_gor(tc)
    def aylik_ozetcagir():
        tc = str(ozet_tc.get())
        aylik_ozet(tc)
    tk.Label(pencere, text="Değiştirmek İstediğiniz Kullanıcın TC'si").grid(row=3, column=0)
    girilen_tc = tk.Entry(pencere)
    girilen_tc.grid(row=4, column=0)
    tk.Label(pencere, text="Değiştirmek İstediğiniz Veri No'su").grid(row=5, column=0)
    girilen_secim = tk.Entry(pencere)
    girilen_secim.grid(row=6, column=0)
    tk.Label(pencere, text="Yeni Veri").grid(row=7, column=0)
    girilen_yeniveri = tk.Entry(pencere)
    girilen_yeniveri.grid(row=8, column=0)
    tk.Label(pencere, text="Silinecek Kullanıcının TC'si").grid(row=3, column=1)
    silinen_tc = tk.Entry(pencere)
    silinen_tc .grid(row=4, column=1)
    tk.Label(pencere, text="Kullanıcının Hesaplarını Gör").grid(row=3, column=2)
    musteri_tc = tk.Entry(pencere)
    musteri_tc .grid(row=4, column=2)
    tk.Label(pencere, text="Kullanıcının Aylık Özetini Gör").grid(row=3, column=3)
    ozet_tc = tk.Entry(pencere)
    ozet_tc.grid(row=4, column=3)
    tk.Button(pencere, text="Bilgi Güncelle", command=lambda: kullanicilari_guncelle()).grid(row=9,column=0)
    tk.Button(pencere, text="Kullanıcı Sil", command=lambda: kullanicilari_sil()).grid(row=9, column=1)
    tk.Button(pencere, text="Kullanıcının Hesaplarını Gör", command=lambda: musteriler_icin_hesap()).grid(row=9, column=2)
    tk.Button(pencere, text="Kullanıcının Aylık Özetini Gör", command=lambda: aylik_ozetcagir()).grid(row=9, column=3)



def kullanicilari_listeleMudur(tc_kimlik):
    pencere = tk.Tk()
    pencere.geometry('1000x600')
    pencere.iconbitmap(resim)
    pencere.title('Müdürün Kullanıcılarını Görüntüleme')
    text = tk.Text(pencere)
    text.grid(row=0, column=0)
    text.insert('1.0', "Ad Soyad    -    Adres    -    Telefon Numarası    -    E-Posta   -   TC Kimlik ")
    c.execute(f'''SELECT DISTINCT ad_soyad, adres, tel_no, eposta, tc_kimlik
                      FROM kullanici''')
    data = c.fetchall()
    text.insert('2.1', '\n'.join(str(x) for x in data))
    text.insert('20.0', "\n\n\nAd Soyad için 1 -  Adres için 2  -  Telefon Numarası için 3  -  E-Posta için 4  Seçiniz \n")
    def kullanicilari_guncelleMudur():
        tc = girilen_tc.get()
        secim = int(girilen_secim.get())
        yeniveri = str(girilen_yeniveri.get())
        data = ("ad_soyad", "adres", "tel_no", "eposta")
        c.execute(f'''UPDATE kullanici
                            SET {data[secim - 1]} = ?
                            WHERE tc_kimlik = {tc}''', (yeniveri,))
        text.insert('10.0', "Bilgi Güncellendi\n")
        text.insert('11.0', '\n'.join(str(x) for x in data))

    def kullanicilari_silMudur():
        silincek_tc = silinen_tc.get()
        c.execute("PRAGMA foreign_keys = 0")
        c.execute(f'''
                DELETE FROM hesap
                WHERE iban IN(SELECT iban
                FROM kullanici_hesap
                WHERE tc_kimlik = {silincek_tc})''')
        c.execute(f'''
                DELETE FROM kullanici_hesap
                WHERE tc_kimlik = {silincek_tc}''')
        c.execute(f'''
                DELETE FROM kullanici
                WHERE tc_kimlik = {silincek_tc}''')
        c.execute(f'''
                DELETE FROM talepler
                WHERE talep_eden = {silincek_tc}''')
        c.execute(f'''
                DELETE FROM krediler
                WHERE krediyi_ceken = {silincek_tc}''')
        c.execute(f'''
                DELETE FROM musteri_temsilci
                WHERE kullanici_tc = {silincek_tc}''')
        c.execute("PRAGMA foreign_keys = 1")
        text.insert('10.0', "Veri Silindi\n")
    tk.Label(pencere, text="Değiştirmek İstediğiniz Kullanıcın TC'si").grid(row=3, column=0)
    girilen_tc = tk.Entry(pencere)
    girilen_tc.grid(row=4, column=0)
    tk.Label(pencere, text="Değiştirmek İstediğiniz Veri No'su").grid(row=5, column=0)
    girilen_secim = tk.Entry(pencere)
    girilen_secim.grid(row=6, column=0)
    tk.Label(pencere, text="Yeni Veri").grid(row=7, column=0)
    girilen_yeniveri = tk.Entry(pencere)
    girilen_yeniveri.grid(row=8, column=0)
    tk.Label(pencere, text="Silinecek Kullanıcının TC'si").grid(row=3, column=1)
    silinen_tc = tk.Entry(pencere)
    silinen_tc .grid(row=4, column=1)
    tk.Button(pencere, text="Bilgi Güncelle", command=lambda: kullanicilari_guncelleMudur()).grid(row=9,column=0)
    tk.Button(pencere, text="Kullanıcı Sil", command=lambda: kullanicilari_silMudur()).grid(row=9, column=1)

def calisan_goruntule():
    pencere = tk.Tk()
    pencere.geometry('1400x600')
    pencere.iconbitmap(resim)
    pencere.title('Çalışan Görüntüleme')
    text = tk.Text(pencere)
    text.grid(row=0, column=0)
    text.insert('1.0', "Ad Soyad    -    Adres    -    Telefon Numarası    -    E-Posta   -   TC Kimlik\n")
    c.execute(f'''SELECT DISTINCT ad_soyad, adres, tel_no, eposta, tc_kimlik
                          FROM kullanici
                          WHERE kullanici.turu=2''')
    data = c.fetchall()
    text.insert('2.1', '\n'.join(str(x) for x in data))

resim = os.path.join(THIS_FOLDER, 'bank_app_icon.ico')

def menuMudur(tc_kimlik):
    pencere = tk.Tk()
    pencere.iconbitmap(resim)
    pencere.geometry('450x250')
    pencere.title('KoüBank Yönetim Sistemi')
    tk.Button(pencere, text="Genel Durum Görüntüle", command=lambda: genel_durum()).grid(row=0, column=0)
    tk.Button(pencere, text="Son X İslem", command=lambda: SonXislem(x=5)).grid(row=0, column=1)
    tk.Button(pencere, text="Müşteri Listele",command=lambda :kullanicilari_listeleMudur(tc_kimlik)).grid(row=0, column=2)
    tk.Button(pencere, text="Müşteri Ekle", command=lambda: kullanici_ekle(tc_kimlik)).grid(row=1, column=0)
    tk.Button(pencere, text="Temsilci Ekle", command=lambda: temsilci_ekle(tc_kimlik)).grid(row=2, column=1)
    tk.Button(pencere, text="Çalışan Görüntüle",command=lambda: calisan_goruntule()).grid(row=1, column=1)
    tk.Button(pencere, text="Yeni Para Birimi Ekle", command=lambda: yeni_para_birimi()).grid(row=1, column=2)
    tk.Button(pencere, text="Sistemi Bir Ay İlerlet", command=lambda: kontrol()).grid(row=2, column=0)
    tk.Button(pencere, text="Çıkış Yap", command=pencere.destroy).grid(row=2, column=2)

def menuTemsilci(tc_kimlik):
    pencere = tk.Tk()
    pencere.iconbitmap(resim)
    pencere.geometry('450x250')
    pencere.title('KoüBank Temsilci Sistemi')
    tk.Button(pencere, text="Hesap Açma Talebi Oluştur", command=lambda: hesap_acma_talebi(tc_kimlik)).grid(row=0, column=0)
    tk.Button(pencere, text="Hesap Silme Talebi Oluştur", command=lambda: hesap_silme_talebi(tc_kimlik)).grid(row=0, column=1)
    tk.Button(pencere, text="Kredi Talebi Oluştur", command=lambda: kredi_talebi(tc_kimlik)).grid(row=0, column=2)
    tk.Button(pencere, text="Para Transfer", command=lambda: para_transfer(tc_kimlik)).grid(row=1, column=0)
    tk.Button(pencere, text="Para çek", command=lambda: para_yuklemecekme(2, tc_kimlik)).grid(row=1, column=1)
    tk.Button(pencere, text="Para Yatır", command=lambda: para_yuklemecekme(1, tc_kimlik)).grid(row=1, column=2)
    tk.Button(pencere, text="Kredi Görüntüle", command=lambda: kredi_ode(tc_kimlik)).grid(row=2, column=0)
    tk.Button(pencere, text="Bilgi Gör/Güncelle",command=lambda: bilgi_gorguncelle(tc_kimlik)).grid(row=2, column=1)
    tk.Button(pencere, text="Hesaplarını Gör", command=lambda: hesaplari_gor(tc_kimlik)).grid(row=2, column=2)
    tk.Button(pencere, text="Aylık Özet", command=lambda: aylik_ozet(tc_kimlik)).grid(row=3, column=0)
    tk.Button(pencere, text="Müşteri Listele", command=lambda: kullanicilari_listele(tc_kimlik)).grid(row=3, column=1)
    tk.Button(pencere, text="Talepleri Kontrol Et", command=lambda :talep_incele(tc_kimlik)).grid(row=3, column=2)
    tk.Button(pencere, text="Çıkış Yap", command=pencere.destroy).grid(row=5, column=0)

def menuMusteri(tc_kimlik):
    pencere = tk.Tk()
    pencere.iconbitmap(resim)
    pencere.geometry('450x250')
    pencere.title('KoüBank Müşteri Sistemi')
    tk.Button(pencere, text="Hesap Açma Talebi Oluştur", command=lambda: hesap_acma_talebi(tc_kimlik)).grid(row=0, column=0)
    tk.Button(pencere, text="Hesap Silme Talebi Oluştur", command=lambda: hesap_silme_talebi(tc_kimlik)).grid(row=0, column=1)
    tk.Button(pencere, text="Kredi Talebi Oluştur", command=lambda: kredi_talebi(tc_kimlik)).grid(row=0, column=2)
    tk.Button(pencere, text="Para Transfer", command=lambda: para_transfer(tc_kimlik)).grid(row=1, column=0)
    tk.Button(pencere, text="Para çek", command=lambda: para_yuklemecekme(2, tc_kimlik)).grid(row=1, column=1)
    tk.Button(pencere, text="Para Yatır", command=lambda: para_yuklemecekme(1, tc_kimlik)).grid(row=1, column=2)
    tk.Button(pencere, text="Kredi Görüntüle", command=lambda: kredi_ode(tc_kimlik)).grid(row=2, column=0)
    tk.Button(pencere, text="Bilgi Gör/Güncelle",command=lambda: bilgi_gorguncelle(tc_kimlik)).grid(row=2, column=1)
    tk.Button(pencere, text="Hesaplarını Gör", command=lambda: hesaplari_gor(tc_kimlik)).grid(row=2, column=2)
    tk.Button(pencere, text="Aylık Özet", command=lambda: aylik_ozet(tc_kimlik)).grid(row=3, column=1)
    tk.Button(pencere, text="Çıkış Yap", command=pencere.destroy).grid(row=4, column=0)


pencere = tk.Tk()
pencere.geometry('400x150')
pencere.iconbitmap(resim)
pencere.title('KoüBank Giriş Sistemi')

#username label and text entry box
usernameLabel = tk.Label(pencere, text="Kullanıcı TC").grid(row=0, column=0)
username = tk.StringVar()
usernameEntry = tk.Entry(pencere, textvariable=username).grid(row=0, column=1)

#password label and password entry box
passwordLabel = tk.Label(pencere,text="Şifre").grid(row=1, column=0)
password = tk.StringVar()
passwordEntry = tk.Entry(pencere, textvariable=password, show='*').grid(row=1, column=1)

def get_texts():
    global username
    tc_kimlik = username.get()
    global password
    sifre = password.get()
    print(tc_kimlik)
    print(sifre)
    c.execute(f'''
          SELECT tc_kimlik
          FROM kullanici
          WHERE tc_kimlik = {tc_kimlik}''')
    if len(c.fetchall()):
        c.execute(f'''
              SELECT sifre
              FROM kullanici
              WHERE tc_kimlik = {tc_kimlik}''')
        if sifre == c.fetchall()[0][0]:
            c.execute(f'''
                SELECT turu
                FROM kullanici
                WHERE tc_kimlik = {tc_kimlik}''')
            turu = int(c.fetchall()[0][0])
            print(turu)
            if turu == 1:
                menuMusteri(tc_kimlik)
            if turu == 2:
                menuTemsilci(tc_kimlik)
            elif turu == 3:
                menuMudur(tc_kimlik)
    else:
        tk.messagebox.showinfo("Giriş Başarısız", "Hatalı Giriş Yaptınız!")

# lambda:[get_texts(), mudurMenu()
#login button

loginButton = tk.Button(pencere, text="Giriş Yap", command=get_texts).grid(row=4, column=0)

pencere.mainloop()

secim = input("veriler database e aktarılsın mı? 1 , 0 emin değilseniz 0 basın")
if secim:
    conn.commit()
