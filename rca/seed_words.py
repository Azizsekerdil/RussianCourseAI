# -*- coding: utf-8 -*-
"""Gomulu A1 Rusca baslangic destesi.

Kayit bicimi: (ru, tr, en, stress_pos, pos, freq_rank, deck, example_ru, example_tr)
stress_pos = vurgulu sesli harfin 0-tabanli indeksi (-1 = bilinmiyor / tek hece)
"""
from __future__ import annotations

from typing import List, Tuple

SeedWord = Tuple[str, str, str, int, str, int, str, str, str]

A1_WORDS: List[SeedWord] = [
    ("привет", "merhaba", "hi", 3, "int", 120, "A1 Temel", "Привет, как дела?", "Merhaba, nasilsin?"),
    ("здравствуйте", "merhaba (resmi)", "hello", 5, "int", 200, "A1 Temel", "Здравствуйте, я Азиз.", "Merhaba, ben Aziz."),
    ("спасибо", "tesekkurler", "thank you", 3, "int", 150, "A1 Temel", "Спасибо большое!", "Cok tesekkurler!"),
    ("пожалуйста", "lutfen / rica ederim", "please", 3, "int", 180, "A1 Temel", "Дайте, пожалуйста, воду.", "Lutfen su verin."),
    ("да", "evet", "yes", 1, "part", 30, "A1 Temel", "Да, конечно.", "Evet, tabii."),
    ("нет", "hayir", "no", 1, "part", 35, "A1 Temel", "Нет, спасибо.", "Hayir, tesekkurler."),
    ("извините", "affedersiniz", "excuse me", 4, "int", 320, "A1 Temel", "Извините, где метро?", "Affedersiniz, metro nerede?"),
    ("до свидания", "hosca kal", "goodbye", 6, "int", 400, "A1 Temel", "До свидания, до завтра.", "Hosca kal, yarin gorusuruz."),
    ("как", "nasil", "how", 1, "adv", 25, "A1 Temel", "Как тебя зовут?", "Adin ne?"),
    ("что", "ne", "what", 2, "pron", 10, "A1 Temel", "Что это?", "Bu ne?"),
    ("кто", "kim", "who", 2, "pron", 40, "A1 Temel", "Кто там?", "Kim var orada?"),
    ("где", "nerede", "where", 2, "adv", 45, "A1 Temel", "Где ты живёшь?", "Nerede yasiyorsun?"),
    ("когда", "ne zaman", "when", 3, "adv", 60, "A1 Temel", "Когда ты придёшь?", "Ne zaman geleceksin?"),
    ("почему", "neden", "why", 5, "adv", 90, "A1 Temel", "Почему ты грустный?", "Neden uzgunsun?"),
    ("сколько", "ne kadar / kac", "how many", 1, "adv", 110, "A1 Temel", "Сколько это стоит?", "Bu ne kadar?"),
    ("я", "ben", "I", 0, "pron", 5, "Zamirler", "Я студент.", "Ben ogrenciyim."),
    ("ты", "sen", "you", 1, "pron", 8, "Zamirler", "Ты дома?", "Evde misin?"),
    ("он", "o (erkek)", "he", 1, "pron", 12, "Zamirler", "Он врач.", "O doktor."),
    ("она", "o (kadin)", "she", 2, "pron", 14, "Zamirler", "Она учительница.", "O ogretmen."),
    ("оно", "o (notr)", "it", 2, "pron", 70, "Zamirler", "Оно большое.", "O buyuk."),
    ("мы", "biz", "we", 1, "pron", 20, "Zamirler", "Мы друзья.", "Biz arkadasiz."),
    ("вы", "siz", "you (pl)", 1, "pron", 18, "Zamirler", "Вы говорите по-русски?", "Rusca konusuyor musunuz?"),
    ("они", "onlar", "they", 2, "pron", 22, "Zamirler", "Они студенты.", "Onlar ogrenci."),
    ("мой", "benim", "my", 2, "pron", 55, "Zamirler", "Это мой дом.", "Bu benim evim."),
    ("твой", "senin", "your", 3, "pron", 95, "Zamirler", "Твой телефон здесь.", "Telefonun burada."),
    ("этот", "bu", "this", 0, "pron", 33, "Zamirler", "Этот человек мой друг.", "Bu adam arkadasim."),
    ("дом", "ev", "house", 1, "noun-m", 65, "Gunluk Hayat", "Мой дом большой.", "Evim buyuk."),
    ("квартира", "daire", "flat", 5, "noun-f", 300, "Gunluk Hayat", "Я живу в квартире.", "Dairede yasiyorum."),
    ("город", "sehir", "city", 1, "noun-m", 85, "Gunluk Hayat", "Москва - большой город.", "Moskova buyuk bir sehir."),
    ("улица", "sokak", "street", 1, "noun-f", 210, "Gunluk Hayat", "Улица очень длинная.", "Sokak cok uzun."),
    ("машина", "araba", "car", 2, "noun-f", 190, "Gunluk Hayat", "Это моя машина.", "Bu benim arabam."),
    ("работа", "is", "work", 2, "noun-f", 130, "Gunluk Hayat", "Я иду на работу.", "Ise gidiyorum."),
    ("школа", "okul", "school", 2, "noun-f", 175, "Gunluk Hayat", "Дети идут в школу.", "Cocuklar okula gidiyor."),
    ("книга", "kitap", "book", 1, "noun-f", 160, "Gunluk Hayat", "Я читаю книгу.", "Kitap okuyorum."),
    ("стол", "masa", "table", 2, "noun-m", 230, "Gunluk Hayat", "Книга на столе.", "Kitap masanin ustunde."),
    ("стул", "sandalye", "chair", 2, "noun-m", 480, "Gunluk Hayat", "Сядь на стул.", "Sandalyeye otur."),
    ("окно", "pencere", "window", 2, "noun-n", 250, "Gunluk Hayat", "Открой окно.", "Pencereyi ac."),
    ("дверь", "kapi", "door", 1, "noun-f", 240, "Gunluk Hayat", "Дверь закрыта.", "Kapi kapali."),
    ("телефон", "telefon", "phone", 5, "noun-m", 260, "Gunluk Hayat", "Где мой телефон?", "Telefonum nerede?"),
    ("деньги", "para", "money", 1, "noun-pl", 145, "Gunluk Hayat", "У меня нет денег.", "Param yok."),
    ("время", "zaman", "time", 2, "noun-n", 50, "Gunluk Hayat", "Сколько времени?", "Saat kac?"),
    ("день", "gun", "day", 1, "noun-m", 75, "Gunluk Hayat", "Хорошего дня!", "Iyi gunler!"),
    ("ночь", "gece", "night", 1, "noun-f", 105, "Gunluk Hayat", "Спокойной ночи.", "Iyi geceler."),
    ("утро", "sabah", "morning", 1, "noun-n", 155, "Gunluk Hayat", "Доброе утро!", "Gunaydin!"),
    ("вечер", "aksam", "evening", 1, "noun-m", 165, "Gunluk Hayat", "Добрый вечер!", "Iyi aksamlar!"),
    ("год", "yil", "year", 1, "noun-m", 42, "Gunluk Hayat", "Мне двадцать лет.", "Yirmi yasindayim."),
    ("вода", "su", "water", 3, "noun-f", 140, "Yiyecek", "Дайте воды, пожалуйста.", "Lutfen su verin."),
    ("хлеб", "ekmek", "bread", 2, "noun-m", 290, "Yiyecek", "Я купил хлеб.", "Ekmek aldim."),
    ("молоко", "sut", "milk", 5, "noun-n", 310, "Yiyecek", "Молоко в холодильнике.", "Sut buzdolabinda."),
    ("чай", "cay", "tea", 2, "noun-m", 280, "Yiyecek", "Хочешь чай?", "Cay ister misin?"),
    ("кофе", "kahve", "coffee", 1, "noun-m", 275, "Yiyecek", "Один кофе, пожалуйста.", "Bir kahve lutfen."),
    ("мясо", "et", "meat", 1, "noun-n", 330, "Yiyecek", "Я не ем мясо.", "Et yemiyorum."),
    ("рыба", "balik", "fish", 1, "noun-f", 340, "Yiyecek", "Рыба очень вкусная.", "Balik cok lezzetli."),
    ("суп", "corba", "soup", 2, "noun-m", 420, "Yiyecek", "Суп горячий.", "Corba sicak."),
    ("яблоко", "elma", "apple", 1, "noun-n", 450, "Yiyecek", "Я ем яблоко.", "Elma yiyorum."),
    ("сыр", "peynir", "cheese", 2, "noun-m", 470, "Yiyecek", "Сыр на столе.", "Peynir masada."),
    ("соль", "tuz", "salt", 1, "noun-f", 490, "Yiyecek", "Передай соль.", "Tuzu uzat."),
    ("ресторан", "restoran", "restaurant", 6, "noun-m", 360, "Yiyecek", "Пойдём в ресторан.", "Restorana gidelim."),
    ("магазин", "magaza", "shop", 5, "noun-m", 265, "Yiyecek", "Магазин закрыт.", "Magaza kapali."),
    ("быть", "olmak", "to be", 1, "verb", 3, "Fiiller", "Я хочу быть врачом.", "Doktor olmak istiyorum."),
    ("делать", "yapmak", "to do", 1, "verb", 52, "Fiiller", "Что ты делаешь?", "Ne yapiyorsun?"),
    ("говорить", "konusmak", "to speak", 5, "verb", 58, "Fiiller", "Я говорю по-русски.", "Rusca konusuyorum."),
    ("знать", "bilmek", "to know", 1, "verb", 62, "Fiiller", "Я не знаю.", "Bilmiyorum."),
    ("думать", "dusunmek", "to think", 1, "verb", 78, "Fiiller", "Я думаю о тебе.", "Seni dusunuyorum."),
    ("хотеть", "istemek", "to want", 3, "verb", 68, "Fiiller", "Я хочу есть.", "Yemek istiyorum."),
    ("мочь", "-ebilmek", "can", 1, "verb", 72, "Fiiller", "Я могу помочь.", "Yardim edebilirim."),
    ("видеть", "gormek", "to see", 1, "verb", 88, "Fiiller", "Я вижу тебя.", "Seni goruyorum."),
    ("слышать", "duymak", "to hear", 1, "verb", 190, "Fiiller", "Ты слышишь музыку?", "Muzigi duyuyor musun?"),
    ("читать", "okumak", "to read", 3, "verb", 195, "Fiiller", "Я читаю книгу.", "Kitap okuyorum."),
    ("писать", "yazmak", "to write", 3, "verb", 185, "Fiiller", "Он пишет письмо.", "Mektup yaziyor."),
    ("есть", "yemek", "to eat", 1, "verb", 100, "Fiiller", "Я ем суп.", "Corba yiyorum."),
    ("пить", "icmek", "to drink", 1, "verb", 205, "Fiiller", "Я пью чай.", "Cay iciyorum."),
    ("спать", "uyumak", "to sleep", 2, "verb", 215, "Fiiller", "Он спит.", "O uyuyor."),
    ("работать", "calismak", "to work", 3, "verb", 125, "Fiiller", "Я работаю в банке.", "Bankada calisiyorum."),
    ("жить", "yasamak", "to live", 1, "verb", 115, "Fiiller", "Я живу в Стамбуле.", "Istanbulda yasiyorum."),
    ("любить", "sevmek", "to love", 3, "verb", 135, "Fiiller", "Я люблю тебя.", "Seni seviyorum."),
    ("купить", "satin almak", "to buy", 3, "verb", 220, "Fiiller", "Я хочу купить хлеб.", "Ekmek almak istiyorum."),
    ("помогать", "yardim etmek", "to help", 5, "verb", 235, "Fiiller", "Помоги мне!", "Bana yardim et!"),
    ("идти", "gitmek (yaya, tek yon)", "to go on foot", 3, "verb-motion", 80, "Hareket Fiilleri", "Я иду домой.", "Eve gidiyorum."),
    ("ходить", "gitmek (yaya, tekrarli)", "to go habitually", 1, "verb-motion", 82, "Hareket Fiilleri", "Я хожу в школу.", "Okula giderim."),
    ("ехать", "gitmek (arac, tek yon)", "to go by vehicle", 1, "verb-motion", 84, "Hareket Fiilleri", "Я еду в Москву.", "Moskovaya gidiyorum."),
    ("ездить", "gitmek (arac, tekrarli)", "to travel habitually", 1, "verb-motion", 86, "Hareket Fiilleri", "Я езжу на работу.", "Ise giderim."),
    ("бежать", "kosmak (tek yon)", "to run", 3, "verb-motion", 340, "Hareket Fiilleri", "Он бежит домой.", "Eve kosuyor."),
    ("прийти", "gelmek", "to arrive", 4, "verb-motion", 170, "Hareket Fiilleri", "Он пришёл поздно.", "Gec geldi."),
    ("уйти", "ayrilmak", "to leave", 2, "verb-motion", 200, "Hareket Fiilleri", "Она ушла.", "O gitti."),
    ("хороший", "iyi", "good", 3, "adj", 92, "Sifatlar", "Хороший день!", "Iyi gun!"),
    ("плохой", "kotu", "bad", 4, "adj", 148, "Sifatlar", "Плохая погода.", "Kotu hava."),
    ("большой", "buyuk", "big", 4, "adj", 96, "Sifatlar", "Большой город.", "Buyuk sehir."),
    ("маленький", "kucuk", "small", 1, "adj", 152, "Sifatlar", "Маленькая собака.", "Kucuk kopek."),
    ("новый", "yeni", "new", 1, "adj", 98, "Sifatlar", "Новый телефон.", "Yeni telefon."),
    ("старый", "eski / yasli", "old", 1, "adj", 158, "Sifatlar", "Старый друг.", "Eski dost."),
    ("красивый", "guzel", "beautiful", 3, "adj", 168, "Sifatlar", "Красивая девушка.", "Guzel kiz."),
    ("быстрый", "hizli", "fast", 1, "adj", 245, "Sifatlar", "Быстрый поезд.", "Hizli tren."),
    ("тёплый", "ilik", "warm", 1, "adj", 355, "Sifatlar", "Тёплая вода.", "Ilik su."),
    ("холодный", "soguk", "cold", 4, "adj", 285, "Sifatlar", "Холодный чай.", "Soguk cay."),
    ("один", "bir", "one", 3, "num", 15, "Sayilar", "Один билет, пожалуйста.", "Bir bilet lutfen."),
    ("два", "iki", "two", 2, "num", 28, "Sayilar", "У меня два брата.", "Iki kardesim var."),
    ("три", "uc", "three", 2, "num", 38, "Sayilar", "Три часа.", "Saat uc."),
    ("четыре", "dort", "four", 3, "num", 66, "Sayilar", "Четыре книги.", "Dort kitap."),
    ("пять", "bes", "five", 1, "num", 44, "Sayilar", "Пять минут.", "Bes dakika."),
    ("шесть", "alti", "six", 1, "num", 108, "Sayilar", "Шесть дней.", "Alti gun."),
    ("семь", "yedi", "seven", 1, "num", 112, "Sayilar", "Семь лет.", "Yedi yil."),
    ("восемь", "sekiz", "eight", 1, "num", 122, "Sayilar", "Восемь часов.", "Saat sekiz."),
    ("девять", "dokuz", "nine", 1, "num", 128, "Sayilar", "Девять рублей.", "Dokuz ruble."),
    ("десять", "on", "ten", 1, "num", 118, "Sayilar", "Десять человек.", "On kisi."),
    ("сто", "yuz", "hundred", 2, "num", 138, "Sayilar", "Сто рублей.", "Yuz ruble."),
    ("тысяча", "bin", "thousand", 1, "num", 142, "Sayilar", "Тысяча лет.", "Bin yil."),
    ("в", "-de / -e (icinde)", "in / to", -1, "prep", 1, "Edatlar", "Я в доме.", "Evdeyim."),
    ("на", "-de / -e (ustunde)", "on / to", -1, "prep", 2, "Edatlar", "Книга на столе.", "Kitap masada."),
    ("с", "ile / -den", "with / from", -1, "prep", 4, "Edatlar", "Я с другом.", "Arkadasimlayim."),
    ("без", "-siz", "without", 1, "prep", 46, "Edatlar", "Чай без сахара.", "Sekersiz cay."),
    ("для", "icin", "for", 2, "prep", 56, "Edatlar", "Это для тебя.", "Bu senin icin."),
    ("о", "hakkinda", "about", -1, "prep", 6, "Edatlar", "Я думаю о работе.", "Is hakkinda dusunuyorum."),
    ("к", "-e dogru", "towards", -1, "prep", 16, "Edatlar", "Я иду к врачу.", "Doktora gidiyorum."),
    ("от", "-den", "from", 1, "prep", 26, "Edatlar", "Письмо от друга.", "Arkadastan mektup."),
    ("до", "-e kadar", "until", 1, "prep", 36, "Edatlar", "До завтра.", "Yarina kadar."),
    ("под", "altinda", "under", 1, "prep", 76, "Edatlar", "Кот под столом.", "Kedi masanin altinda."),
]

# Gorunus ciftleri: (tamamlanmamis, tamamlanmis, tamamlanmisin TR karsiligi)
# Tamamlanmis uye bankada yoksa seed sirasinda otomatik eklenir.
ASPECT_PAIRS = [
    ("делать", "сделать", "yapmak (bitirmek)"),
    ("читать", "прочитать", "okumak (bitirmek)"),
    ("писать", "написать", "yazmak (bitirmek)"),
    ("говорить", "сказать", "soylemek (bir kez)"),
    ("покупать", "купить", "satin almak (bitirmek)"),
    ("помогать", "помочь", "yardim etmek (bir kez)"),
    ("видеть", "увидеть", "gormek (fark etmek)"),
    ("есть", "съесть", "yemek (bitirmek)"),
    ("пить", "выпить", "icmek (bitirmek)"),
    ("учить", "выучить", "ogrenmek (ezberlemek)"),
]


def count() -> int:
    """Gomulu destedeki kelime sayisi."""
    return len(A1_WORDS)


def decks() -> list:
    """Seed verisindeki deste adlari (gorunum sirasini korur)."""
    out = []
    for w in A1_WORDS:
        if w[6] not in out:
            out.append(w[6])
    return out
