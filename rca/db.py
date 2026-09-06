# -*- coding: utf-8 -*-
"""SQLite semasi, gocler ve repository siniflari.

Arayuz katmani asla dogrudan SQL yazmaz; her erisim buradaki repository
siniflari uzerinden yapilir.
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence

import rca_common as C
from rca.seed_words import A1_WORDS, ASPECT_PAIRS
from rca.srs import SRSState

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    cefr TEXT DEFAULT 'A1',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ru TEXT NOT NULL,
    ru_norm TEXT NOT NULL,
    tr TEXT DEFAULT '',
    en TEXT DEFAULT '',
    stress_pos INTEGER DEFAULT -1,
    pos TEXT DEFAULT '',
    aspect_pair_id INTEGER,
    freq_rank INTEGER DEFAULT 9999,
    audio TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    example_ru TEXT DEFAULT '',
    example_tr TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_words_norm ON words(ru_norm);
CREATE INDEX IF NOT EXISTS idx_words_tags ON words(tags);

CREATE TABLE IF NOT EXISTS word_progress (
    profile_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    box INTEGER DEFAULT 0,
    easiness REAL DEFAULT 2.5,
    interval INTEGER DEFAULT 0,
    repetition INTEGER DEFAULT 0,
    due_date TEXT,
    correct INTEGER DEFAULT 0,
    wrong INTEGER DEFAULT 0,
    last_seen TEXT,
    starred INTEGER DEFAULT 0,
    PRIMARY KEY (profile_id, word_id)
);
CREATE INDEX IF NOT EXISTS idx_wp_due ON word_progress(profile_id, due_date);

CREATE TABLE IF NOT EXISTS grammar_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    lab TEXT NOT NULL,
    level TEXT DEFAULT 'A1'
);

CREATE TABLE IF NOT EXISTS topic_progress (
    profile_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    correct INTEGER DEFAULT 0,
    wrong INTEGER DEFAULT 0,
    last_seen TEXT,
    PRIMARY KEY (profile_id, topic_id)
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    prompt TEXT NOT NULL,
    answer TEXT NOT NULL,
    options TEXT DEFAULT '',
    topic_code TEXT DEFAULT '',
    level TEXT DEFAULT 'A1',
    source TEXT DEFAULT 'builtin'
);

CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    total INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    kinds TEXT DEFAULT '',
    score REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS exam_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,
    word_id INTEGER,
    kind TEXT,
    prompt TEXT,
    expected TEXT,
    given TEXT,
    is_correct INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS packs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    version TEXT DEFAULT '1',
    author TEXT DEFAULT '',
    installed_at TEXT NOT NULL,
    word_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pdf_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    pdf_path TEXT NOT NULL,
    page INTEGER NOT NULL,
    kind TEXT DEFAULT 'note',
    payload TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_notes_pdf ON pdf_notes(pdf_path, page);

CREATE TABLE IF NOT EXISTS resource_state (
    profile_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    done INTEGER DEFAULT 0,
    PRIMARY KEY (profile_id, path)
);

CREATE TABLE IF NOT EXISTS token_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    day TEXT NOT NULL,
    model TEXT NOT NULL,
    task TEXT NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    ms INTEGER DEFAULT 0,
    ok INTEGER DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_token_day ON token_log(day);

CREATE TABLE IF NOT EXISTS study_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    day TEXT NOT NULL,
    activity TEXT NOT NULL,
    correct INTEGER DEFAULT 0,
    wrong INTEGER DEFAULT 0,
    seconds INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_study_day ON study_log(profile_id, day);

CREATE TABLE IF NOT EXISTS dict_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ru TEXT NOT NULL,
    en TEXT NOT NULL,
    pos TEXT DEFAULT '',
    extra TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'user',
    example TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    tr TEXT NOT NULL DEFAULT '',
    UNIQUE(ru, en)
);
"""

# Onceki surumlerde olusmus tablolara eklenecek sutunlar (eklemeli goc):
# tablo -> [(sutun, tanim)]
COLUMN_MIGRATIONS = {
    "dict_entries": [
        ("source", "TEXT NOT NULL DEFAULT 'user'"),
        ("example", "TEXT NOT NULL DEFAULT ''"),
        ("note", "TEXT NOT NULL DEFAULT ''"),
        ("tr", "TEXT NOT NULL DEFAULT ''"),          # Turkce karsilik (v1.2)
    ],
}


# --------------------------------------------------------------------------
# Baglanti
# --------------------------------------------------------------------------
class Database:
    """Tek dosyalik SQLite baglantisi. Thread-safe (tek kilit)."""

    def __init__(self, path=None) -> None:
        C.ensure_dirs()
        self.path = str(path or C.DB_PATH)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.migrate()

    # -- alt yapi ---------------------------------------------------------
    def execute(self, sql: str, args: Sequence = ()) -> sqlite3.Cursor:
        """Tek bir SQL cumlesi calistir ve imleci dondur."""
        with self._lock:
            cur = self.conn.execute(sql, args)
            self.conn.commit()
            return cur

    def query(self, sql: str, args: Sequence = ()) -> List[sqlite3.Row]:
        """SELECT calistir ve satirlari dondur."""
        with self._lock:
            return self.conn.execute(sql, args).fetchall()

    def one(self, sql: str, args: Sequence = ()) -> Optional[sqlite3.Row]:
        """Tek satir dondur (yoksa None)."""
        rows = self.query(sql, args)
        return rows[0] if rows else None

    def migrate(self) -> None:
        """Semayi olustur / guncelle ve ilk acilista seed verisini yukle."""
        with self._lock:
            self.conn.executescript(DDL)
            self.conn.commit()
        self._add_missing_columns()
        cur = self.one("SELECT value FROM meta WHERE key='schema_version'")
        if cur is None:
            self.execute("INSERT INTO meta(key,value) VALUES('schema_version',?)",
                         (str(SCHEMA_VERSION),))
        if self.one("SELECT 1 FROM words LIMIT 1") is None:
            self.seed()

    def columns(self, table: str) -> List[str]:
        """Tablonun sutun adlari (PRAGMA table_info)."""
        return [str(r[1]) for r in self.query(f"PRAGMA table_info({table})")]

    def _add_missing_columns(self) -> None:
        """Eski veritabanlarina eksik sutunlari ekle (yalnizca ALTER TABLE ADD COLUMN)."""
        for table, specs in COLUMN_MIGRATIONS.items():
            try:
                have = set(self.columns(table))
            except sqlite3.Error:
                continue
            if not have:
                continue
            for col, ddl in specs:
                if col in have:
                    continue
                try:
                    self.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
                except sqlite3.Error:
                    pass                                        # ayni anda eklenmis olabilir

    def seed(self) -> int:
        """Gomulu A1 destesini ve gorunus ciftlerini yukle. Eklenen kelime sayisini dondurur."""
        now = datetime.now().isoformat(timespec="seconds")
        rows = []
        for (ru, tr, en, stress, pos, freq, deck, ex_ru, ex_tr) in A1_WORDS:
            rows.append((ru, C.normalize_ru(ru), tr, en, stress, pos, freq, deck,
                         ex_ru, ex_tr, now))
        with self._lock:
            self.conn.executemany(
                "INSERT INTO words(ru,ru_norm,tr,en,stress_pos,pos,freq_rank,tags,"
                "example_ru,example_tr,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)", rows)
            self.conn.commit()
        # gorunus ciftlerini bagla; eksik olan tamamlanmis uyeyi de ekle
        added = len(rows)
        for impf, perf, perf_tr in ASPECT_PAIRS:
            a = self.one("SELECT id FROM words WHERE ru_norm=?", (C.normalize_ru(impf),))
            if not a:
                continue
            b = self.one("SELECT id FROM words WHERE ru_norm=?", (C.normalize_ru(perf),))
            if not b:
                cur = self.execute(
                    "INSERT INTO words(ru,ru_norm,tr,en,stress_pos,pos,freq_rank,tags,"
                    "example_ru,example_tr,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (perf, C.normalize_ru(perf), perf_tr, "", -1, "verb", 999,
                     "Fiiller", "", "", now))
                bid = int(cur.lastrowid)
                added += 1
            else:
                bid = int(b["id"])
            self.execute("UPDATE words SET aspect_pair_id=? WHERE id=?", (bid, a["id"]))
            self.execute("UPDATE words SET aspect_pair_id=? WHERE id=?", (a["id"], bid))
        return added

    def close(self) -> None:
        """Baglantiyi kapat."""
        try:
            self.conn.close()
        except Exception:
            pass


# --------------------------------------------------------------------------
# Repositoryler
# --------------------------------------------------------------------------
class ProfileRepo:
    """Ogrenci profilleri."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def all(self) -> List[Dict[str, Any]]:
        """Tum profiller."""
        return [dict(r) for r in self.db.query("SELECT * FROM profiles ORDER BY id")]

    def create(self, name: str, cefr: str = "A1") -> int:
        """Yeni profil olustur; ad zaten varsa mevcut id'yi dondur."""
        row = self.db.one("SELECT id FROM profiles WHERE name=?", (name,))
        if row:
            return int(row["id"])
        cur = self.db.execute(
            "INSERT INTO profiles(name,cefr,created_at) VALUES(?,?,?)",
            (name, cefr, datetime.now().isoformat(timespec="seconds")))
        return int(cur.lastrowid)

    def ensure_default(self) -> int:
        """En az bir profil olmasini garanti et ve id'sini dondur."""
        rows = self.all()
        if rows:
            return int(rows[0]["id"])
        return self.create("Ogrenci")

    def delete(self, pid: int) -> None:
        """Profili ve ona bagli ilerlemeyi sil."""
        for table in ("word_progress", "topic_progress", "resource_state", "study_log"):
            self.db.execute(f"DELETE FROM {table} WHERE profile_id=?", (pid,))
        self.db.execute("DELETE FROM profiles WHERE id=?", (pid,))

    def set_cefr(self, pid: int, cefr: str) -> None:
        """Profilin CEFR seviyesini guncelle."""
        self.db.execute("UPDATE profiles SET cefr=? WHERE id=?", (cefr, pid))


class WordRepo:
    """Kelime bankasi ve sozluk sorgulari."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def all(self, deck: str = "", limit: int = 0) -> List[Dict[str, Any]]:
        """Kelimeleri dondur; deck verilirse yalnizca o desteyi."""
        sql = "SELECT * FROM words"
        args: List[Any] = []
        if deck:
            sql += " WHERE tags=?"
            args.append(deck)
        sql += " ORDER BY freq_rank, ru"
        if limit:
            sql += f" LIMIT {int(limit)}"
        return [dict(r) for r in self.db.query(sql, args)]

    def get(self, wid: int) -> Optional[Dict[str, Any]]:
        """Id ile kelime getir."""
        r = self.db.one("SELECT * FROM words WHERE id=?", (wid,))
        return dict(r) if r else None

    def search(self, text: str, limit: int = 100) -> List[Dict[str, Any]]:
        """TR / RU / EN uzerinde arama; Rusca icin yo ve vurgu normalize edilir."""
        q = (text or "").strip()
        if not q:
            return []
        norm = C.normalize_ru(q)
        like = f"%{q.lower()}%"
        rows = self.db.query(
            "SELECT * FROM words WHERE ru_norm LIKE ? OR lower(tr) LIKE ? OR lower(en) LIKE ? "
            "ORDER BY freq_rank LIMIT ?",
            (f"%{norm}%", like, like, limit))
        return [dict(r) for r in rows]

    def decks(self) -> List[str]:
        """Mevcut deste adlari."""
        return [r["tags"] for r in self.db.query(
            "SELECT DISTINCT tags FROM words WHERE tags<>'' ORDER BY tags")]

    def add(self, ru: str, tr: str, en: str = "", stress_pos: int = -1, pos: str = "",
            deck: str = "Ozel", example_ru: str = "", example_tr: str = "",
            freq_rank: int = 9999) -> int:
        """Yeni kelime ekle; ayni ru_norm varsa mevcut id'yi dondur."""
        norm = C.normalize_ru(ru)
        row = self.db.one("SELECT id FROM words WHERE ru_norm=? AND tags=?", (norm, deck))
        if row:
            return int(row["id"])
        cur = self.db.execute(
            "INSERT INTO words(ru,ru_norm,tr,en,stress_pos,pos,freq_rank,tags,"
            "example_ru,example_tr,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (ru, norm, tr, en, stress_pos, pos, freq_rank, deck, example_ru, example_tr,
             datetime.now().isoformat(timespec="seconds")))
        return int(cur.lastrowid)

    def update(self, wid: int, **fields) -> None:
        """Belirtilen alanlari guncelle."""
        allowed = {"ru", "tr", "en", "stress_pos", "pos", "tags", "example_ru",
                   "example_tr", "freq_rank", "audio"}
        sets, args = [], []
        for k, v in fields.items():
            if k in allowed:
                sets.append(f"{k}=?")
                args.append(v)
        if "ru" in fields:
            sets.append("ru_norm=?")
            args.append(C.normalize_ru(str(fields["ru"])))
        if not sets:
            return
        args.append(wid)
        self.db.execute(f"UPDATE words SET {', '.join(sets)} WHERE id=?", args)

    def delete(self, wid: int) -> None:
        """Kelimeyi ve ilerleme kayitlarini sil."""
        self.db.execute("DELETE FROM word_progress WHERE word_id=?", (wid,))
        self.db.execute("DELETE FROM words WHERE id=?", (wid,))

    def count(self) -> int:
        """Toplam kelime sayisi."""
        r = self.db.one("SELECT COUNT(*) c FROM words")
        return int(r["c"]) if r else 0


class ProgressRepo:
    """Kelime ilerlemesi ve aralikli tekrar kuyrugu."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def state(self, profile_id: int, word_id: int) -> SRSState:
        """Kelimenin SRS durumunu dondur; kayit yoksa varsayilan."""
        r = self.db.one("SELECT * FROM word_progress WHERE profile_id=? AND word_id=?",
                        (profile_id, word_id))
        if not r:
            return SRSState()
        due = _parse_date(r["due_date"]) or date.today()
        return SRSState(easiness=float(r["easiness"] or 2.5), interval=int(r["interval"] or 0),
                        repetition=int(r["repetition"] or 0), box=int(r["box"] or 0), due=due)

    def save(self, profile_id: int, word_id: int, st: SRSState, correct_inc: int = 0,
             wrong_inc: int = 0) -> None:
        """SRS durumunu yaz ve dogru/yanlis sayaclarini artir."""
        self.db.execute(
            "INSERT INTO word_progress(profile_id,word_id,box,easiness,interval,repetition,"
            "due_date,correct,wrong,last_seen) VALUES(?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(profile_id,word_id) DO UPDATE SET box=excluded.box,"
            "easiness=excluded.easiness,interval=excluded.interval,"
            "repetition=excluded.repetition,due_date=excluded.due_date,"
            "correct=word_progress.correct+?,wrong=word_progress.wrong+?,"
            "last_seen=excluded.last_seen",
            (profile_id, word_id, st.box, st.easiness, st.interval, st.repetition,
             st.due.isoformat(), correct_inc, wrong_inc, date.today().isoformat(),
             correct_inc, wrong_inc))

    def due_words(self, profile_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Tekrar vakti gelmis kelimeler (en eski once)."""
        today = date.today().isoformat()
        rows = self.db.query(
            "SELECT w.*, p.box, p.due_date, p.correct, p.wrong FROM words w "
            "JOIN word_progress p ON p.word_id=w.id "
            "WHERE p.profile_id=? AND p.due_date<=? ORDER BY p.due_date LIMIT ?",
            (profile_id, today, limit))
        return [dict(r) for r in rows]

    def new_words(self, profile_id: int, limit: int = 20, deck: str = "") -> List[Dict[str, Any]]:
        """Hic denenmemis kelimeler (frekans sirasina gore)."""
        sql = ("SELECT w.* FROM words w LEFT JOIN word_progress p "
               "ON p.word_id=w.id AND p.profile_id=? WHERE p.word_id IS NULL")
        args: List[Any] = [profile_id]
        if deck:
            sql += " AND w.tags=?"
            args.append(deck)
        sql += " ORDER BY w.freq_rank LIMIT ?"
        args.append(limit)
        return [dict(r) for r in self.db.query(sql, args)]

    def wrong_words(self, profile_id: int, limit: int = 30) -> List[Dict[str, Any]]:
        """En cok yanlis yapilan kelimeler."""
        rows = self.db.query(
            "SELECT w.*, p.correct, p.wrong FROM words w JOIN word_progress p "
            "ON p.word_id=w.id WHERE p.profile_id=? AND p.wrong>p.correct "
            "ORDER BY p.wrong DESC LIMIT ?", (profile_id, limit))
        return [dict(r) for r in rows]

    def starred(self, profile_id: int) -> List[Dict[str, Any]]:
        """Favori kelimeler."""
        rows = self.db.query(
            "SELECT w.* FROM words w JOIN word_progress p ON p.word_id=w.id "
            "WHERE p.profile_id=? AND p.starred=1 ORDER BY w.ru", (profile_id,))
        return [dict(r) for r in rows]

    def toggle_star(self, profile_id: int, word_id: int) -> bool:
        """Favori durumunu tersine cevir ve yeni durumu dondur."""
        r = self.db.one("SELECT starred FROM word_progress WHERE profile_id=? AND word_id=?",
                        (profile_id, word_id))
        if r is None:
            self.db.execute(
                "INSERT INTO word_progress(profile_id,word_id,starred,due_date,last_seen) "
                "VALUES(?,?,1,?,?)",
                (profile_id, word_id, date.today().isoformat(), date.today().isoformat()))
            return True
        new = 0 if int(r["starred"] or 0) else 1
        self.db.execute("UPDATE word_progress SET starred=? WHERE profile_id=? AND word_id=?",
                        (new, profile_id, word_id))
        return bool(new)

    def dashboard(self, profile_id: int) -> Dict[str, int]:
        """Bugun panosu sayilari - kural tabanli, AI cagrisi yok."""
        today = date.today().isoformat()
        def _c(sql: str, args: Sequence) -> int:
            r = self.db.one(sql, args)
            return int(r["c"]) if r else 0
        return {
            "due": _c("SELECT COUNT(*) c FROM word_progress WHERE profile_id=? AND due_date<=?",
                      (profile_id, today)),
            "wrong": _c("SELECT COUNT(*) c FROM word_progress WHERE profile_id=? AND wrong>correct",
                        (profile_id,)),
            "new": _c("SELECT COUNT(*) c FROM words w LEFT JOIN word_progress p "
                      "ON p.word_id=w.id AND p.profile_id=? WHERE p.word_id IS NULL",
                      (profile_id,)),
            "learned": _c("SELECT COUNT(*) c FROM word_progress WHERE profile_id=? AND box>=3",
                          (profile_id,)),
            "seen": _c("SELECT COUNT(*) c FROM word_progress WHERE profile_id=? AND "
                       "(correct+wrong)>0", (profile_id,)),
        }


class StudyRepo:
    """Gunluk calisma kayitlari, seri (streak) ve istatistikler."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def log(self, profile_id: int, activity: str, correct: int = 0, wrong: int = 0,
            seconds: int = 0) -> None:
        """Bir calisma olayini gunlukle."""
        self.db.execute(
            "INSERT INTO study_log(profile_id,day,activity,correct,wrong,seconds) "
            "VALUES(?,?,?,?,?,?)",
            (profile_id, date.today().isoformat(), activity, correct, wrong, seconds))

    def daily(self, profile_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Son N gunun gunluk toplamlari (bos gunler 0 ile doldurulur)."""
        start = (date.today() - timedelta(days=days - 1)).isoformat()
        rows = self.db.query(
            "SELECT day, SUM(correct) c, SUM(wrong) w, SUM(seconds) s FROM study_log "
            "WHERE profile_id=? AND day>=? GROUP BY day", (profile_id, start))
        table = {r["day"]: dict(r) for r in rows}
        out = []
        for i in range(days):
            d = (date.today() - timedelta(days=days - 1 - i)).isoformat()
            r = table.get(d)
            out.append({"day": d, "correct": int(r["c"] or 0) if r else 0,
                        "wrong": int(r["w"] or 0) if r else 0,
                        "seconds": int(r["s"] or 0) if r else 0})
        return out

    def streak(self, profile_id: int) -> int:
        """Kesintisiz calisma gunu sayisi."""
        rows = self.db.query(
            "SELECT DISTINCT day FROM study_log WHERE profile_id=? ORDER BY day DESC",
            (profile_id,))
        days = [r["day"] for r in rows]
        if not days:
            return 0
        n, cur = 0, date.today()
        dayset = set(days)
        if cur.isoformat() not in dayset:
            cur = cur - timedelta(days=1)
            if cur.isoformat() not in dayset:
                return 0
        while cur.isoformat() in dayset:
            n += 1
            cur -= timedelta(days=1)
        return n

    def totals(self, profile_id: int) -> Dict[str, int]:
        """Tum zamanlarin toplami."""
        r = self.db.one(
            "SELECT COALESCE(SUM(correct),0) c, COALESCE(SUM(wrong),0) w, "
            "COALESCE(SUM(seconds),0) s FROM study_log WHERE profile_id=?", (profile_id,))
        return {"correct": int(r["c"]), "wrong": int(r["w"]), "seconds": int(r["s"])}


class ExamRepo:
    """Sinav oturumlari ve cevaplari."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def start(self, profile_id: int, kinds: str) -> int:
        """Yeni sinav oturumu ac."""
        cur = self.db.execute(
            "INSERT INTO exams(profile_id,started_at,kinds) VALUES(?,?,?)",
            (profile_id, datetime.now().isoformat(timespec="seconds"), kinds))
        return int(cur.lastrowid)

    def answer(self, exam_id: int, word_id, kind: str, prompt: str, expected: str,
               given: str, ok: bool) -> None:
        """Tek bir cevabi kaydet."""
        self.db.execute(
            "INSERT INTO exam_answers(exam_id,word_id,kind,prompt,expected,given,is_correct) "
            "VALUES(?,?,?,?,?,?,?)",
            (exam_id, word_id, kind, prompt, expected, given, 1 if ok else 0))

    def finish(self, exam_id: int) -> Dict[str, Any]:
        """Sinavi kapat, puani hesapla ve ozet dondur."""
        r = self.db.one(
            "SELECT COUNT(*) t, COALESCE(SUM(is_correct),0) c FROM exam_answers WHERE exam_id=?",
            (exam_id,))
        total, correct = int(r["t"]), int(r["c"])
        score = round(100.0 * correct / total, 1) if total else 0.0
        self.db.execute(
            "UPDATE exams SET finished_at=?, total=?, correct=?, score=? WHERE id=?",
            (datetime.now().isoformat(timespec="seconds"), total, correct, score, exam_id))
        return {"total": total, "correct": correct, "score": score}

    def history(self, profile_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Son sinavlar (yeni -> eski)."""
        rows = self.db.query(
            "SELECT * FROM exams WHERE profile_id=? AND finished_at IS NOT NULL "
            "ORDER BY id DESC LIMIT ?", (profile_id, limit))
        return [dict(r) for r in rows]

    def wrong_answers(self, exam_id: int) -> List[Dict[str, Any]]:
        """Bu sinavdaki yanlislar."""
        rows = self.db.query(
            "SELECT * FROM exam_answers WHERE exam_id=? AND is_correct=0", (exam_id,))
        return [dict(r) for r in rows]


class TokenRepo:
    """AI istek defteri. Istek METINLERI saklanmaz - yalnizca sayaclar."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def log(self, model: str, task: str, prompt_tokens: int, completion_tokens: int,
            ms: int = 0, ok: bool = True) -> None:
        """Bir AI cagrisini kaydet."""
        now = datetime.now()
        self.db.execute(
            "INSERT INTO token_log(ts,day,model,task,prompt_tokens,completion_tokens,"
            "total_tokens,ms,ok) VALUES(?,?,?,?,?,?,?,?,?)",
            (now.isoformat(timespec="seconds"), now.date().isoformat(), model, task,
             prompt_tokens, completion_tokens, prompt_tokens + completion_tokens, ms,
             1 if ok else 0))

    def summary(self) -> Dict[str, Dict[str, int]]:
        """Bugun / 7 gun / 30 gun / tum zamanlar kartlari."""
        out: Dict[str, Dict[str, int]] = {}
        spans = {"today": 0, "7d": 6, "30d": 29, "all": None}
        for key, back in spans.items():
            if back is None:
                r = self.db.one("SELECT COUNT(*) n, COALESCE(SUM(total_tokens),0) t FROM token_log")
            else:
                since = (date.today() - timedelta(days=back)).isoformat()
                r = self.db.one("SELECT COUNT(*) n, COALESCE(SUM(total_tokens),0) t "
                                "FROM token_log WHERE day>=?", (since,))
            out[key] = {"calls": int(r["n"]), "tokens": int(r["t"])}
        return out

    def grouped(self, by: str = "model", limit: int = 50) -> List[Dict[str, Any]]:
        """Modele / ise / gune gore gruplu tablo."""
        col = {"model": "model", "task": "task", "day": "day"}.get(by, "model")
        rows = self.db.query(
            f"SELECT {col} k, COUNT(*) calls, COALESCE(SUM(total_tokens),0) tokens, "
            f"COALESCE(AVG(ms),0) avg_ms FROM token_log GROUP BY {col} "
            f"ORDER BY tokens DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]

    def all_rows(self) -> List[Dict[str, Any]]:
        """CSV disa aktarim icin tum kayitlar."""
        return [dict(r) for r in self.db.query("SELECT * FROM token_log ORDER BY id")]


class NoteRepo:
    """PDF notlari ve isaretlemeleri."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, profile_id: int, pdf_path: str, page: int, kind: str, payload: str) -> int:
        """Not / isaretleme ekle."""
        cur = self.db.execute(
            "INSERT INTO pdf_notes(profile_id,pdf_path,page,kind,payload,created_at) "
            "VALUES(?,?,?,?,?,?)",
            (profile_id, pdf_path, page, kind, payload,
             datetime.now().isoformat(timespec="seconds")))
        return int(cur.lastrowid)

    def for_page(self, pdf_path: str, page: int) -> List[Dict[str, Any]]:
        """Belirli sayfanin notlari."""
        rows = self.db.query(
            "SELECT * FROM pdf_notes WHERE pdf_path=? AND page=? ORDER BY id",
            (pdf_path, page))
        return [dict(r) for r in rows]

    def clear_page(self, pdf_path: str, page: int) -> None:
        """Sayfadaki tum notlari sil."""
        self.db.execute("DELETE FROM pdf_notes WHERE pdf_path=? AND page=?", (pdf_path, page))


class ResourceRepo:
    """Kurs kaynaklari 'bitirdim' isaretleri."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def done_set(self, profile_id: int) -> set:
        """Bitmis olarak isaretlenmis yollarin kumesi."""
        return {r["path"] for r in self.db.query(
            "SELECT path FROM resource_state WHERE profile_id=? AND done=1", (profile_id,))}

    def toggle(self, profile_id: int, path: str) -> bool:
        """Bitirdim isaretini tersine cevir."""
        r = self.db.one("SELECT done FROM resource_state WHERE profile_id=? AND path=?",
                        (profile_id, path))
        new = 0 if (r and int(r["done"])) else 1
        self.db.execute(
            "INSERT INTO resource_state(profile_id,path,done) VALUES(?,?,?) "
            "ON CONFLICT(profile_id,path) DO UPDATE SET done=excluded.done",
            (profile_id, path, new))
        return bool(new)


class TopicRepo:
    """Dilbilgisi konu ilerlemesi."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def ensure(self, code: str, title: str, lab: str, level: str = "A1") -> int:
        """Konu kaydini garanti et ve id dondur."""
        r = self.db.one("SELECT id FROM grammar_topics WHERE code=?", (code,))
        if r:
            return int(r["id"])
        cur = self.db.execute(
            "INSERT INTO grammar_topics(code,title,lab,level) VALUES(?,?,?,?)",
            (code, title, lab, level))
        return int(cur.lastrowid)

    def record(self, profile_id: int, code: str, correct: int, wrong: int) -> None:
        """Konu icin dogru/yanlis sayaclarini artir."""
        r = self.db.one("SELECT id FROM grammar_topics WHERE code=?", (code,))
        if not r:
            return
        tid = int(r["id"])
        self.db.execute(
            "INSERT INTO topic_progress(profile_id,topic_id,correct,wrong,last_seen) "
            "VALUES(?,?,?,?,?) ON CONFLICT(profile_id,topic_id) DO UPDATE SET "
            "correct=topic_progress.correct+?, wrong=topic_progress.wrong+?, "
            "last_seen=excluded.last_seen",
            (profile_id, tid, correct, wrong, date.today().isoformat(), correct, wrong))

    def weak(self, profile_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """En zayif konular (en az 3 deneme yapilmis olanlar)."""
        rows = self.db.query(
            "SELECT t.title, t.code, p.correct, p.wrong FROM grammar_topics t "
            "JOIN topic_progress p ON p.topic_id=t.id WHERE p.profile_id=? "
            "AND (p.correct+p.wrong)>=3 ORDER BY "
            "(CAST(p.correct AS REAL)/(p.correct+p.wrong)) ASC LIMIT ?",
            (profile_id, limit))
        out = []
        for r in rows:
            tot = int(r["correct"]) + int(r["wrong"])
            out.append({"title": r["title"], "code": r["code"],
                        "pct": round(100.0 * int(r["correct"]) / tot, 1) if tot else 0.0,
                        "total": tot})
        return out


# --------------------------------------------------------------------------
def _parse_date(value) -> Optional[date]:
    """ISO tarih metnini date'e cevir; basarisizsa None."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception:
        return None


class DictRepo:
    """Kullanicinin sozluge ekledigi / ice aktardigi ve AI'dan kaydedilen maddeler.

    `source` sutunu maddenin kokenini tutar: 'user' (ekleme / ice aktarim) ya da 'ai'.
    `tr` sutunu istege bagli Turkce karsiligi tutar ('' = henuz yok).
    """

    SOURCE_USER = "user"
    SOURCE_AI = "ai"

    def __init__(self, db: Database) -> None:
        self.db = db

    def all(self, source: str = None) -> List[Dict[str, Any]]:
        """Tum maddeler (source verilirse yalnizca o kaynak); 'source' alani dahil."""
        if source:
            return [dict(r) for r in self.db.query(
                "SELECT * FROM dict_entries WHERE source=? ORDER BY ru", (source,))]
        return [dict(r) for r in self.db.query("SELECT * FROM dict_entries ORDER BY ru")]

    def count(self, source: str = None) -> int:
        if source:
            row = self.db.one("SELECT COUNT(*) AS n FROM dict_entries WHERE source=?", (source,))
        else:
            row = self.db.one("SELECT COUNT(*) AS n FROM dict_entries")
        return int(row["n"]) if row else 0

    def count_by_source(self) -> Dict[str, int]:
        """{'user': n, 'ai': m} - bos kaynaklar listede yer almaz."""
        return {str(r["source"]): int(r["n"]) for r in self.db.query(
            "SELECT source, COUNT(*) AS n FROM dict_entries GROUP BY source")}

    @staticmethod
    def entry_key(ru: str, en: str) -> tuple:
        """Satir kimligi: vurgu isaretsiz + kucuk harf baslik, kucuk harf Ingilizce.

        Bellekteki `Dictionary.key` ile ayni esdegerlik (tur haric): "дом"/"до'м" ve
        "Book"/"book" AYNI satirdir. Tablodaki UNIQUE(ru, en) ise bire bir metin
        karsilastirir; kopya ve doldurma kararlari bu anahtarla verilir.
        """
        from rca.dictionary import norm_query, split_stress
        return norm_query(split_stress(ru or "")[0]), norm_query(en or "")

    def _key_map(self) -> Dict[tuple, list]:
        """{entry_key: [id, tr]} - tum satirlar (ayni anahtarli birden cok satirda ilki)."""
        out: Dict[tuple, list] = {}
        for r in self.db.query("SELECT id, ru, en, tr FROM dict_entries ORDER BY id"):
            out.setdefault(self.entry_key(r["ru"], r["en"]), [int(r["id"]), r["tr"] or ""])
        return out

    def _matching_ids(self, ru: str, en: str) -> List[int]:
        key = self.entry_key(ru, en)
        return [int(r["id"]) for r in self.db.query("SELECT id, ru, en FROM dict_entries ORDER BY id")
                if self.entry_key(r["ru"], r["en"]) == key]

    def add_many(self, rows: Sequence[Sequence], source: str = SOURCE_USER) -> int:
        """(ru, en[, pos[, extra[, example[, note[, tr]]]]]) dizisini ekle; tekrarlari atla.

        Eklenen sayiyi dondurur. `source` tum satirlara uygulanir ('user' | 'ai').
        Ayni maddenin satiri (`entry_key`: vurgu ve buyuk/kucuk harf farksiz) zaten varsa
        yeniden eklenmez; ama gelen satir Turkce karsilik tasiyorsa ve saklanan satirin
        `tr` alani bossa o alan DOLDURULUR (kopya yerine guncelleme - AI'in sonradan
        buldugu Turkce gloss, saklanan satir vurgusuz ya da farkli buyuk/kucuk harfle
        yazilmis olsa da boyle islenir). Ayni toplu istekteki tekrarlar da ayni kurala uyar.
        """
        now = datetime.now().isoformat(timespec="seconds")
        src = source or self.SOURCE_USER

        def field(r, i):
            return (r[i] if len(r) > i and r[i] is not None else "")

        clean = [r for r in rows if r and r[0] and r[1]]
        if not clean:
            return 0
        added = 0
        with self.db._lock:
            seen = self._key_map()
            for r in clean:
                key, turkish = self.entry_key(r[0], r[1]), field(r, 6)
                hit = seen.get(key)
                if hit is None:
                    cur = self.db.conn.execute(
                        "INSERT OR IGNORE INTO dict_entries(ru,en,pos,extra,created_at,source,example,note,tr) "
                        "VALUES(?,?,?,?,?,?,?,?,?)",
                        (r[0], r[1], field(r, 2), field(r, 3), now, src, field(r, 4), field(r, 5), turkish))
                    if cur.rowcount:
                        seen[key] = [int(cur.lastrowid), turkish]
                        added += 1
                elif turkish and not hit[1]:
                    self.db.conn.execute("UPDATE dict_entries SET tr=? WHERE id=? AND tr=''", (turkish, hit[0]))
                    hit[1] = turkish
            self.db.conn.commit()
        return added

    def add(self, ru: str, en: str, pos: str = "", extra: str = "",
            source: str = SOURCE_USER, example: str = "", note: str = "", tr: str = "") -> int:
        return self.add_many([(ru, en, pos, extra, example, note, tr)], source=source)

    def set_tr(self, ru: str, en: str, tr: str, overwrite: bool = False) -> int:
        """Saklanan maddenin Turkce karsiligini yaz; guncellenen satir sayisini dondur.

        Satir `entry_key` ile bulunur (vurgu ve buyuk/kucuk harf farksiz). Varsayilan olarak
        yalnizca BOS tr alani doldurulur (kullanicinin yazdigi gloss ezilmez). 0 = satir yok
        (gomulu / OpenRussian maddesi) ya da alan zaten dolu.
        """
        if not tr:
            return 0
        ids = self._matching_ids(ru, en)
        if not ids:
            return 0
        marks = ",".join("?" * len(ids))
        sql = f"UPDATE dict_entries SET tr=? WHERE id IN ({marks})" + ("" if overwrite else " AND tr=''")
        return int(self.db.execute(sql, (tr, *ids)).rowcount or 0)

    def clear(self, source: str = None) -> None:
        """Tum maddeleri (ya da yalnizca verilen kaynagi) sil."""
        if source:
            self.db.execute("DELETE FROM dict_entries WHERE source=?", (source,))
        else:
            self.db.execute("DELETE FROM dict_entries")


class Repos:
    """Tum repositoryleri tek yerden tasiyan kolaylik kabi."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.profiles = ProfileRepo(db)
        self.words = WordRepo(db)
        self.progress = ProgressRepo(db)
        self.study = StudyRepo(db)
        self.exams = ExamRepo(db)
        self.tokens = TokenRepo(db)
        self.notes = NoteRepo(db)
        self.resources = ResourceRepo(db)
        self.topics = TopicRepo(db)
        self.dictionary = DictRepo(db)
