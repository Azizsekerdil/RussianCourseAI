# -*- coding: utf-8 -*-
"""Gomulu icerik paketleri: Kiril alfabesi, hal/fiil/hareket/sayi tablolari.

Her paket modul icinde bir veri sozlugu + tek bir `build()` finalizer'i seklinde
tutulur. Harici dosya bagimliligi yoktur.
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple

# ==========================================================================
# 1) KIRIL ALFABESI
# (harf, ad, ses degeri, el yazisi ipucu, turkce karsiligi/notu)
# ==========================================================================
ALPHABET: List[Tuple[str, str, str, str, str]] = [
    ("Аа", "а", "[a]", "tek kavisli, 'o' gibi baslar kuyrukla biter", "a"),
    ("Бб", "бэ", "[b]", "yukari cikan kancali govde", "b"),
    ("Вв", "вэ", "[v]", "iki karinli, Latin 'B' degildir", "v"),
    ("Гг", "гэ", "[g]", "ters 'L', el yazisinda Latin 'z' benzeri", "g"),
    ("Дд", "дэ", "[d]", "el yazisinda Latin 'g' gibi kuyruklu", "d"),
    ("Ее", "е", "[je]", "Latin 'e' ile ayni", "ye"),
    ("Ёё", "ё", "[jo]", "her zaman VURGULU, iki noktali", "yo"),
    ("Жж", "жэ", "[ʒ]", "bocek gibi, ortadan dikey cizgi", "j"),
    ("Зз", "зэ", "[z]", "rakam '3' benzeri", "z"),
    ("Ии", "и", "[i]", "el yazisinda Latin 'u' gibi", "i"),
    ("Йй", "и краткое", "[j]", "'и' + ustunde kisa yay", "y (kisa i)"),
    ("Кк", "ка", "[k]", "Latin 'k' ama kucugu farkli", "k"),
    ("Лл", "эль", "[l]", "el yazisinda kucuk kanca ile baslar", "l"),
    ("Мм", "эм", "[m]", "el yazisinda kanca ile baslar, Latin 'm' degil", "m"),
    ("Нн", "эн", "[n]", "Latin 'H' gibi gorunur ama 'n' okunur", "n"),
    ("Оо", "о", "[o]", "tam daire", "o"),
    ("Пп", "пэ", "[p]", "Latin 'n' gibi el yazisinda", "p"),
    ("Рр", "эр", "[r]", "Latin 'p' gibi gorunur ama 'r' okunur", "r"),
    ("Сс", "эс", "[s]", "Latin 'c' gibi gorunur ama 's' okunur", "s"),
    ("Тт", "тэ", "[t]", "el yazisinda Latin 'm' gibi yazilir", "t"),
    ("Уу", "у", "[u]", "Latin 'y' benzeri", "u"),
    ("Фф", "эф", "[f]", "iki halkali dikey cizgi", "f"),
    ("Хх", "ха", "[x]", "Latin 'x', ama gırtlaktan 'h'", "h (sert)"),
    ("Цц", "цэ", "[ts]", "sag altta kuyruk", "ts"),
    ("Чч", "че", "[tʃ]", "rakam '4' benzeri", "c"),
    ("Шш", "ша", "[ʃ]", "uc dikey, kuyruksuz", "s (kalin)"),
    ("Щщ", "ща", "[ʃʲː]", "'ш' + sag altta kuyruk", "sc (ince uzun)"),
    ("Ъъ", "твёрдый знак", "-", "sert isaret, ses yok", "ayirici"),
    ("Ыы", "ы", "[ɨ]", "'ь' + 'и', Turkcede yok", "i (kalin)"),
    ("Ьь", "мягкий знак", "-", "yumusak isaret, onceki sessizi inceltir", "inceltici"),
    ("Ээ", "э", "[e]", "ters 'з' gibi", "e"),
    ("Юю", "ю", "[ju]", "'i' + 'o' birlesik", "yu"),
    ("Яя", "я", "[ja]", "ters Latin 'R'", "ya"),
]

CONFUSABLE: List[Tuple[str, str, str]] = [
    ("ш", "щ", "щ ince ve uzundur: шар (top) / щи (lahana corbasi)"),
    ("б", "в", "б = b, в = v: был (idi) / выл (uludu)"),
    ("и", "й", "й kisa yarim seslidir: мои (benimkiler) / мой (benim)"),
    ("ь", "ъ", "ь inceltir, ъ ayirir: семья (aile) / съел (yedi)"),
    ("н", "п", "н = n, п = p: нос (burun) / пост (oruc)"),
    ("р", "п", "р = r, п = p: рот (agiz) / пот (ter)"),
    ("с", "е", "с = s, е = ye: сон (uyku) / ел (yedi)"),
    ("ц", "ч", "ц = ts, ч = c: цена (fiyat) / чай (cay)"),
    ("э", "е", "э bastan e, е bastan ye: это (bu) / ел (yedi)"),
    ("ы", "и", "ы kalin, и ince: мыть (yikamak) / милый (sevimli)"),
]

# ==========================================================================
# 2) HAL LAB (Падежи)
# ==========================================================================
CASES: List[Dict[str, Any]] = [
    {"code": "nom", "ru": "Именительный", "tr": "Yalin hal", "q": "кто? что?",
     "use": "Ozne. Sozlukteki temel bicim.",
     "ex": ("Это студент.", "Bu bir ogrenci."),
     "endings": {"m": "-", "f": "-а / -я", "n": "-о / -е", "pl": "-ы / -и / -а"}},
    {"code": "gen", "ru": "Родительный", "tr": "-in hali (iyelik)", "q": "кого? чего?",
     "use": "Sahiplik, yokluk (нет), 2-4 sayilari, без/для/от/до edatlari.",
     "ex": ("У меня нет времени.", "Zamanim yok."),
     "endings": {"m": "-а / -я", "f": "-ы / -и", "n": "-а / -я", "pl": "- / -ов / -ей"}},
    {"code": "dat", "ru": "Дательный", "tr": "-e hali (yonelme)", "q": "кому? чему?",
     "use": "Dolayli nesne, к / по edatlari, yas kaliplari (мне 20 лет).",
     "ex": ("Я иду к врачу.", "Doktora gidiyorum."),
     "endings": {"m": "-у / -ю", "f": "-е / -и", "n": "-у / -ю", "pl": "-ам / -ям"}},
    {"code": "acc", "ru": "Винительный", "tr": "-i hali (belirtme)", "q": "кого? что?",
     "use": "Dogrudan nesne; в/на + yon bildirimi.",
     "ex": ("Я читаю книгу.", "Kitabi okuyorum."),
     "endings": {"m": "cansiz=yalin / canli=gen", "f": "-у / -ю", "n": "yalin gibi",
                 "pl": "cansiz=yalin / canli=gen"}},
    {"code": "ins", "ru": "Творительный", "tr": "ile hali (arac)", "q": "кем? чем?",
     "use": "Arac, с (birlikte), meslek (быть врачом).",
     "ex": ("Я пишу ручкой.", "Kalemle yaziyorum."),
     "endings": {"m": "-ом / -ем", "f": "-ой / -ей", "n": "-ом / -ем", "pl": "-ами / -ями"}},
    {"code": "pre", "ru": "Предложный", "tr": "-de hali (bulunma)", "q": "о ком? о чём? где?",
     "use": "YALNIZCA edatla: в / на / о / при.",
     "ex": ("Я живу в Москве.", "Moskovada yasiyorum."),
     "endings": {"m": "-е", "f": "-е / -и", "n": "-е", "pl": "-ах / -ях"}},
]

# ornek isim cekimleri: kelime -> hal kodu -> bicim
NOUN_DECLENSION: Dict[str, Dict[str, str]] = {
    "стол (m, cansiz)": {"nom": "стол", "gen": "стола", "dat": "столу",
                         "acc": "стол", "ins": "столом", "pre": "столе"},
    "студент (m, canli)": {"nom": "студент", "gen": "студента", "dat": "студенту",
                           "acc": "студента", "ins": "студентом", "pre": "студенте"},
    "книга (f)": {"nom": "книга", "gen": "книги", "dat": "книге",
                  "acc": "книгу", "ins": "книгой", "pre": "книге"},
    "неделя (f, yumusak)": {"nom": "неделя", "gen": "недели", "dat": "неделе",
                            "acc": "неделю", "ins": "неделей", "pre": "неделе"},
    "окно (n)": {"nom": "окно", "gen": "окна", "dat": "окну",
                 "acc": "окно", "ins": "окном", "pre": "окне"},
    "море (n, yumusak)": {"nom": "море", "gen": "моря", "dat": "морю",
                          "acc": "море", "ins": "морем", "pre": "море"},
    "дверь (f, -ь)": {"nom": "дверь", "gen": "двери", "dat": "двери",
                      "acc": "дверь", "ins": "дверью", "pre": "двери"},
}

PRONOUN_DECLENSION: Dict[str, Dict[str, str]] = {
    "я": {"nom": "я", "gen": "меня", "dat": "мне", "acc": "меня", "ins": "мной", "pre": "обо мне"},
    "ты": {"nom": "ты", "gen": "тебя", "dat": "тебе", "acc": "тебя", "ins": "тобой", "pre": "о тебе"},
    "он": {"nom": "он", "gen": "его", "dat": "ему", "acc": "его", "ins": "им", "pre": "о нём"},
    "она": {"nom": "она", "gen": "её", "dat": "ей", "acc": "её", "ins": "ей", "pre": "о ней"},
    "мы": {"nom": "мы", "gen": "нас", "dat": "нам", "acc": "нас", "ins": "нами", "pre": "о нас"},
    "вы": {"nom": "вы", "gen": "вас", "dat": "вам", "acc": "вас", "ins": "вами", "pre": "о вас"},
    "они": {"nom": "они", "gen": "их", "dat": "им", "acc": "их", "ins": "ими", "pre": "о них"},
}

PREPOSITION_CASE: List[Tuple[str, str, str]] = [
    ("в / на (nerede?)", "pre", "в доме, на столе"),
    ("в / на (nereye?)", "acc", "в дом, на стол"),
    ("из / с (nereden?)", "gen", "из дома, со стола"),
    ("у", "gen", "у меня, у окна"),
    ("без", "gen", "без сахара"),
    ("для", "gen", "для тебя"),
    ("до", "gen", "до завтра"),
    ("от", "gen", "от друга"),
    ("к", "dat", "к врачу"),
    ("по", "dat", "по улице"),
    ("с (ile)", "ins", "с другом"),
    ("над / под / за / перед", "ins", "над столом, под столом"),
    ("о / об", "pre", "о работе"),
    ("при", "pre", "при мне"),
]

# ==========================================================================
# 3) FIIL LAB (Вид / Спряжение)
# ==========================================================================
CONJUGATION: Dict[str, Dict[str, Any]] = {
    "читать (1. cekim)": {
        "type": 1, "aspect": "несов.",
        "present": {"я": "читаю", "ты": "читаешь", "он/она": "читает",
                    "мы": "читаем", "вы": "читаете", "они": "читают"},
        "past": {"он": "читал", "она": "читала", "оно": "читало", "они": "читали"},
        "future": "буду читать / будешь читать ...",
        "imper": "читай! / читайте!",
    },
    "говорить (2. cekim)": {
        "type": 2, "aspect": "несов.",
        "present": {"я": "говорю", "ты": "говоришь", "он/она": "говорит",
                    "мы": "говорим", "вы": "говорите", "они": "говорят"},
        "past": {"он": "говорил", "она": "говорила", "оно": "говорило", "они": "говорили"},
        "future": "буду говорить ...",
        "imper": "говори! / говорите!",
    },
    "писать (1. cekim, kok degisimi)": {
        "type": 1, "aspect": "несов.",
        "present": {"я": "пишу", "ты": "пишешь", "он/она": "пишет",
                    "мы": "пишем", "вы": "пишете", "они": "пишут"},
        "past": {"он": "писал", "она": "писала", "оно": "писало", "они": "писали"},
        "future": "буду писать ...",
        "imper": "пиши! / пишите!",
    },
    "написать (tamamlanmis)": {
        "type": 1, "aspect": "сов.",
        "present": {"-": "tamamlanmis fiilin SIMDIKI zamani YOKTUR"},
        "past": {"он": "написал", "она": "написала", "оно": "написало", "они": "написали"},
        "future": "напишу, напишешь, напишет, напишем, напишете, напишут",
        "imper": "напиши! / напишите!",
    },
    "заниматься (donuslu)": {
        "type": 1, "aspect": "несов.",
        "present": {"я": "занимаюсь", "ты": "занимаешься", "он/она": "занимается",
                    "мы": "занимаемся", "вы": "занимаетесь", "они": "занимаются"},
        "past": {"он": "занимался", "она": "занималась", "оно": "занималось",
                 "они": "занимались"},
        "future": "буду заниматься ...",
        "imper": "занимайся! / занимайтесь!",
    },
}

ASPECT_RULES = [
    ("несовершенный (tamamlanmamis)", "surec, tekrar, aliskanlik",
     "Я читал книгу вчера. = Dun kitap okudum (surec)."),
    ("совершенный (tamamlanmis)", "tek seferlik, sonuclanmis eylem",
     "Я прочитал книгу. = Kitabi bitirdim (sonuc var)."),
    ("Kural", "Tamamlanmis fiilin SIMDIKI zamani yoktur",
     "прочитаю = gelecek zaman, 'okuyorum' degil."),
]

# ==========================================================================
# 4) HAREKET FIILLERI LAB
# ==========================================================================
MOTION_VERBS: List[Dict[str, str]] = [
    {"uni": "идти", "multi": "ходить", "mode": "yaya",
     "uni_ex": "Я иду в школу (simdi, tek yon).",
     "multi_ex": "Я хожу в школу (her gun, gidip gelme)."},
    {"uni": "ехать", "multi": "ездить", "mode": "arac",
     "uni_ex": "Я еду в Москву (simdi yolda).",
     "multi_ex": "Я езжу в Москву каждый год (tekrarli)."},
    {"uni": "бежать", "multi": "бегать", "mode": "kosma",
     "uni_ex": "Он бежит домой.", "multi_ex": "Он бегает по утрам."},
    {"uni": "лететь", "multi": "летать", "mode": "ucus",
     "uni_ex": "Самолёт летит в Анкару.", "multi_ex": "Я часто летаю."},
    {"uni": "нести", "multi": "носить", "mode": "tasima (elde)",
     "uni_ex": "Я несу сумку.", "multi_ex": "Я ношу очки."},
]

MOTION_PREFIXES: List[Tuple[str, str, str]] = [
    ("при-", "varis", "прийти = gelmek, приехать = (araclа) gelmek"),
    ("у-", "ayrilis (geri donmemek)", "уйти = gitmek/ayrilmak"),
    ("в- / во-", "iceri", "войти = iceri girmek"),
    ("вы-", "disari", "выйти = disari cikmak"),
    ("под-", "yaklasma", "подойти = yaklasmak"),
    ("от-", "uzaklasma", "отойти = uzaklasmak"),
    ("пере-", "karsiya gecme", "перейти = karsiya gecmek"),
    ("до-", "-e kadar varma", "дойти = yuruyerek ulasmak"),
    ("за-", "ugrama", "зайти = ugramak"),
    ("об-", "etrafini dolasma", "обойти = dolanmak"),
]

# ==========================================================================
# 5) SAYI & OLCU LAB
# ==========================================================================
NUMBER_AGREEMENT: List[Tuple[str, str, str]] = [
    ("1 (и 21, 31, 101...)", "YALIN tekil", "один стол, одна книга, двадцать один стол"),
    ("2, 3, 4 (и 22, 33...)", "GENITIV TEKIL", "два стола, три книги, четыре окна"),
    ("5-20, 25, 100...", "GENITIV COGUL", "пять столов, десять книг, сто окон"),
    ("0 ve kesirler", "GENITIV COGUL/TEKIL", "ноль градусов, 1,5 часа"),
]

TIME_PATTERNS: List[Tuple[str, str]] = [
    ("Saat kac?", "Сколько сейчас времени? / Который час?"),
    ("Saat 1", "Час (bir 'один' denmez)"),
    ("Saat 2-4", "два часа, три часа, четыре часа"),
    ("Saat 5-12", "пять часов, десять часов"),
    ("Saat kacta?", "в час, в два часа, в пять часов"),
    ("Bugunun tarihi", "Какое сегодня число? - Сегодня пятое мая."),
    ("Hangi tarihte?", "Пятого мая (genitiv)"),
    ("Yas", "Мне двадцать лет. / Ему двадцать один год. / Ей двадцать два года."),
    ("Para", "один рубль, два рубля, пять рублей"),
]

# ==========================================================================
# 6) SOZ DIZIMI - basit etiketleyici (pymorphy3 varsa daha isabetli)
# ==========================================================================
POS_LABELS = {
    "noun": "isim", "verb": "fiil", "adj": "sifat", "pron": "zamir",
    "prep": "edat", "adv": "zarf", "num": "sayi", "part": "edat/parcacik",
    "int": "unlem", "conj": "baglac", "?": "bilinmiyor",
}

_KNOWN_PREPS = {"в", "на", "с", "к", "о", "об", "от", "до", "для", "без",
                "под", "над", "за", "при", "по", "из", "у", "про", "через"}
_KNOWN_PRONS = {"я", "ты", "он", "она", "оно", "мы", "вы", "они", "это", "этот",
                "мой", "твой", "наш", "ваш", "его", "её", "их", "кто", "что"}
_KNOWN_CONJ = {"и", "а", "но", "или", "что", "чтобы", "если", "когда", "потому"}


def tag_word(word: str) -> str:
    """Kelimenin sozcuk turunu tahmin et.

    pymorphy3 kurulu ise onu kullanir; degilse sonek/sozluk tabanli basit
    kural kumesiyle calisir (yaklasik ama her zaman calisir).
    """
    w = (word or "").strip().lower()
    if not w:
        return "?"
    try:
        import pymorphy3                       # type: ignore
        global _MORPH
        try:
            _MORPH
        except NameError:
            _MORPH = pymorphy3.MorphAnalyzer()
        p = _MORPH.parse(w)[0]
        tag = str(p.tag.POS or "").lower()
        table = {"noun": "noun", "verb": "verb", "infn": "verb", "adjf": "adj",
                 "adjs": "adj", "prtf": "adj", "npro": "pron", "prep": "prep",
                 "advb": "adv", "numr": "num", "prcl": "part", "intj": "int",
                 "conj": "conj"}
        return table.get(tag, "?")
    except Exception:
        pass

    if w in _KNOWN_PREPS:
        return "prep"
    if w in _KNOWN_PRONS:
        return "pron"
    if w in _KNOWN_CONJ:
        return "conj"
    if w.endswith(("ый", "ий", "ой", "ая", "яя", "ую", "юю", "ое", "ее", "ые", "ие",
                   "ому", "ыми", "ого", "его")):
        return "adj"
    if w.endswith(("ть", "ться", "ла", "ло", "ли", "ал", "ял", "ил",
                   "аю", "яю", "ею", "ешь", "ёшь", "ишь", "ает", "яет", "еет",
                   "ает", "ит", "ают", "яют", "еют", "ят", "ете", "ите", "ится")):
        return "verb"
    if w.endswith(("о", "е")) and len(w) > 4:
        return "adv"
    if w.endswith(("а", "я", "ы", "и", "у", "ю", "ом", "ем", "ой", "ах", "ях", "ов", "ей")):
        return "noun"
    return "noun"


def parse_sentence(sentence: str) -> List[Tuple[str, str]]:
    """Cumleyi kelimelere ayirip (kelime, tur_etiketi) ciftleri dondur."""
    import re
    words = re.findall(r"[\wЀ-ӿ'-]+", sentence or "", flags=re.UNICODE)
    return [(w, tag_word(w)) for w in words]


# ==========================================================================
# ALISTIRMA URETICILERI (her lab icin)
# ==========================================================================
def build_case_exercises(n: int = 10, rng: random.Random = None) -> List[Dict[str, Any]]:
    """Hal Lab alistirmalari: bir isim + hal sorulur, dogru bicim istenir."""
    rng = rng or random.Random()
    items = []
    words = list(NOUN_DECLENSION.items())
    codes = [c["code"] for c in CASES]
    labels = {c["code"]: f"{c['ru']} ({c['tr']})" for c in CASES}
    for _ in range(n):
        name, forms = rng.choice(words)
        code = rng.choice(codes)
        correct = forms[code]
        pool = [f[code] for _, f in words if f[code] != correct]
        rng.shuffle(pool)
        opts = pool[:3] + [correct]
        rng.shuffle(opts)
        items.append({
            "topic": f"case.{code}",
            "prompt": f"{name}  ->  {labels[code]}",
            "answer": correct,
            "options": opts,
            "explain": next(c["use"] for c in CASES if c["code"] == code),
        })
    return items


def build_verb_exercises(n: int = 10, rng: random.Random = None) -> List[Dict[str, Any]]:
    """Fiil Lab alistirmalari: sahis + fiil verilir, cekim istenir."""
    rng = rng or random.Random()
    items = []
    pairs = [(name, d) for name, d in CONJUGATION.items()
             if d["aspect"] == "несов." and "-" not in d["present"]]
    for _ in range(n):
        name, data = rng.choice(pairs)
        person, form = rng.choice(list(data["present"].items()))
        pool = [f for _, d in pairs for f in d["present"].values() if f != form]
        rng.shuffle(pool)
        opts = pool[:3] + [form]
        rng.shuffle(opts)
        items.append({
            "topic": "verb.present",
            "prompt": f"{name.split(' ')[0]}  ->  {person}",
            "answer": form,
            "options": opts,
            "explain": f"{name}: {data['aspect']}, {data['type']}. cekim",
        })
    return items


def build_motion_exercises(n: int = 8, rng: random.Random = None) -> List[Dict[str, Any]]:
    """Hareket Fiilleri Lab: tek yon mu tekrarli mi?"""
    rng = rng or random.Random()
    items = []
    for _ in range(n):
        v = rng.choice(MOTION_VERBS)
        if rng.random() < 0.5:
            prompt, answer, other = v["uni_ex"], v["uni"], v["multi"]
            explain = "Tek yon / su an devam eden hareket -> однонаправленный"
        else:
            prompt, answer, other = v["multi_ex"], v["multi"], v["uni"]
            explain = "Tekrarli / gidip gelme -> разнонаправленный"
        items.append({
            "topic": "motion",
            "prompt": prompt.replace(answer, "____", 1) if answer in prompt else prompt,
            "answer": answer,
            "options": rng.sample([answer, other], 2),
            "explain": explain,
        })
    return items


def build_number_exercises(n: int = 8, rng: random.Random = None) -> List[Dict[str, Any]]:
    """Sayi & Olcu Lab: sayi-isim uyumu."""
    rng = rng or random.Random()
    forms = {
        "стол": {"nom": "стол", "gen_sg": "стола", "gen_pl": "столов"},
        "книга": {"nom": "книга", "gen_sg": "книги", "gen_pl": "книг"},
        "рубль": {"nom": "рубль", "gen_sg": "рубля", "gen_pl": "рублей"},
        "час": {"nom": "час", "gen_sg": "часа", "gen_pl": "часов"},
        "год": {"nom": "год", "gen_sg": "года", "gen_pl": "лет"},
    }
    items = []
    for _ in range(n):
        noun, f = rng.choice(list(forms.items()))
        num = rng.choice([1, 2, 3, 4, 5, 7, 10, 21, 22, 25])
        last, last2 = num % 10, num % 100
        if last == 1 and last2 != 11:
            answer, rule = f["nom"], "1 ile biten -> YALIN tekil"
        elif last in (2, 3, 4) and last2 not in (12, 13, 14):
            answer, rule = f["gen_sg"], "2-4 ile biten -> GENITIV tekil"
        else:
            answer, rule = f["gen_pl"], "5-20 ve digerleri -> GENITIV cogul"
        opts = list({f["nom"], f["gen_sg"], f["gen_pl"]})
        rng.shuffle(opts)
        items.append({
            "topic": "numbers",
            "prompt": f"{num} ____  ({noun})",
            "answer": answer,
            "options": opts,
            "explain": rule,
        })
    return items


def build_cyrillic_exercises(n: int = 12, rng: random.Random = None) -> List[Dict[str, Any]]:
    """Kiril Lab: harf -> ses degeri eslestirme."""
    rng = rng or random.Random()
    items = []
    for _ in range(n):
        letter, name, sound, hint, tr = rng.choice(ALPHABET)
        pool = [a[2] for a in ALPHABET if a[2] != sound and a[2] != "-"]
        rng.shuffle(pool)
        opts = pool[:3] + [sound]
        rng.shuffle(opts)
        items.append({
            "topic": "cyrillic",
            "prompt": f"{letter}  ({name})",
            "answer": sound,
            "options": opts,
            "explain": f"{letter} = {sound} ~ '{tr}'. El yazisi: {hint}",
        })
    return items


LABS: Dict[str, Dict[str, Any]] = {
    "case":    {"title": "Hal Lab (Падежи)", "build": build_case_exercises},
    "verb":    {"title": "Fiil Lab (Вид / Спряжение)", "build": build_verb_exercises},
    "motion":  {"title": "Hareket Fiilleri Lab", "build": build_motion_exercises},
    "numbers": {"title": "Sayi & Olcu Lab", "build": build_number_exercises},
}


def build(lab: str, n: int = 10, rng: random.Random = None) -> List[Dict[str, Any]]:
    """Tek finalizer: lab kodu verilir, alistirma listesi doner."""
    spec = LABS.get(lab)
    if not spec:
        return []
    return spec["build"](n, rng)


# ==========================================================================
# TELAFFUZ / VURGU
# ==========================================================================
REDUCTION_RULES = [
    ("о -> [a]", "Vurgusuz 'о' [a] okunur",
     "молоко = [məlako] - sadece son 'о' vurgulu ve tam [o]"),
    ("е / я -> [i]", "Vurgusuz 'е' ve 'я' [i]'ye yaklasir",
     "язык = [jizɨk], тебя = [tibʲa]"),
    ("Son sessiz sertlesir", "Kelime sonundaki sesli sessiz sertlesir",
     "хлеб = [хлеп], друг = [друк]"),
    ("Ё her zaman vurgulu", "'ё' harfi bulundugu hecede vurguyu tasir",
     "тёплый, ёлка"),
    ("Sessiz benzesmesi", "Sessiz ciftlerinde ilki ikinciye uyar",
     "всё = [фсё], сделать = [зделать]"),
]

IPA_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "je", "ё": "jo",
    "ж": "ʒ", "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ц": "ts", "ч": "tʃ", "ш": "ʃ", "щ": "ʃʲː",
    "ъ": "", "ы": "ɨ", "ь": "ʲ", "э": "e", "ю": "ju", "я": "ja",
}


def rough_ipa(word: str, stress_pos: int = -1) -> str:
    """Kaba IPA cevirisi; vurgusuz 'о' -> [ə] indirgemesini uygular."""
    from rca_common import strip_stress, VOWELS
    w = strip_stress(word or "").lower()
    out = []
    for i, ch in enumerate(w):
        base = IPA_MAP.get(ch, ch)
        if ch in VOWELS and i != stress_pos:
            if ch == "о":
                base = "ə" if i < stress_pos - 1 or stress_pos < 0 else "a"
            elif ch in ("е", "я"):
                base = "i"
        if i == stress_pos:
            base = "ˈ" + base
        out.append(base)
    return "[" + "".join(out) + "]"
