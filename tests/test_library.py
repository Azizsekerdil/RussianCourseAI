# -*- coding: utf-8 -*-
"""Kaynak Merkezi: katalog butunlugu, lisans zorunlulugu ve ice aktarici testleri."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rca import library as L

# Kabul edilen lisanslar - baska hicbir sey katalogda yer alamaz
OPEN_LICENSES = {"PD-USGOV", "PD-MARK", "CC-BY-SA-4.0", "CC-BY-2.0-FR", "CC-VARIES"}


def test_every_resource_has_a_known_open_license():
    """Katalogdaki HER kaynagin lisansi tanimli ve acik olmali."""
    assert L.CATALOG
    for r in L.CATALOG:
        assert r.license in OPEN_LICENSES, f"{r.rid}: bilinmeyen lisans {r.license}"
        assert r.license in L.LICENSES, r.rid
        info = r.license_info()
        assert info["short"] and info.get("note")


def test_resource_ids_are_unique():
    """Kimlikler benzersizdir."""
    ids = [r.rid for r in L.CATALOG]
    assert len(ids) == len(set(ids))


def test_downloadable_entries_are_complete():
    """Indirilebilir kayitlarin dosya adi, boyutu ve https adresi vardir."""
    for r in L.CATALOG:
        if r.kind in ("ebook", "audio", "data"):
            assert r.filename, r.rid
            assert r.size_mb > 0, r.rid
            assert r.url.startswith("https://"), r.rid
            assert r.downloadable


def test_link_entries_are_not_downloadable():
    """Web/video kayitlari dosya olarak indirilmez, yalnizca acilir."""
    for r in L.CATALOG:
        if r.kind in ("link", "video"):
            assert not r.downloadable, r.rid


def test_share_alike_entries_declare_attribution():
    """CC BY-SA ve CC BY kaynaklari atif metni tasimalidir."""
    for r in L.CATALOG:
        if r.license in ("CC-BY-SA-4.0", "CC-BY-2.0-FR") and r.downloadable:
            assert r.attribution, f"{r.rid}: atif metni eksik"


def test_kind_labels_cover_all_kinds():
    """Her tur icin arayuz etiketi tanimlidir."""
    kinds = {r.kind for r in L.CATALOG}
    assert kinds <= set(L.KIND_LABELS)


def test_by_kind_filters():
    """Tur filtresi calisir."""
    assert len(L.by_kind()) == len(L.CATALOG)
    for kind in ("ebook", "audio", "data", "link", "video"):
        assert all(r.kind == kind for r in L.by_kind(kind))
    assert L.by_kind("ebook")


def test_get_returns_none_for_unknown():
    """Bilinmeyen kimlik None dondurur."""
    assert L.get("yok-boyle") is None
    assert L.get(L.CATALOG[0].rid) is L.CATALOG[0]


def test_target_path_uses_subdir(tmp_path):
    """Indirme yolu alt klasoru kullanir."""
    r = L.get("fsi-fast-1")
    target = r.target(tmp_path)
    assert target.parent.name == "E-Kitaplar"
    assert target.name.endswith(".pdf")


def test_license_file_written_once(tmp_path):
    """LISANS.txt yazilir ve ayni kayit iki kez eklenmez."""
    r = L.get("or-nouns")
    L.write_license_file(r, tmp_path)
    L.write_license_file(r, tmp_path)
    text = (tmp_path / "LISANS.txt").read_text(encoding="utf-8")
    assert text.count(f"[{r.filename}]") == 1
    assert "CC BY-SA 4.0" in text
    assert r.attribution in text


def test_license_file_accumulates_entries(tmp_path):
    """Ayni klasordeki farkli dosyalar ayri kayit olur."""
    L.write_license_file(L.get("or-nouns"), tmp_path)
    L.write_license_file(L.get("or-verbs"), tmp_path)
    text = (tmp_path / "LISANS.txt").read_text(encoding="utf-8")
    assert "openrussian_isimler.tsv" in text and "openrussian_fiiller.tsv" in text


def test_stress_parser():
    """OpenRussian'in tirnakli vurgu gosterimi indekse cevrilir."""
    assert L._stress_from_accented("челове'к") == ("человек", 5)
    assert L._stress_from_accented("бу'дьте") == ("будьте", 1)
    assert L._stress_from_accented("дом") == ("дом", -1)
    assert L._stress_from_accented("") == ("", -1)


@pytest.fixture()
def repos(tmp_path):
    """Izole veritabani."""
    os.environ["RCA_HOME"] = str(tmp_path)
    for name in list(sys.modules):
        if name == "rca_common" or name.startswith("rca."):
            del sys.modules[name]
    from rca.db import Database, Repos
    db = Database(tmp_path / "lib.db")
    yield Repos(db)
    db.close()


def _write_noun_tsv(path: Path) -> None:
    """Kucuk bir OpenRussian isim dosyasi uret."""
    header = ("bare\taccented\ttranslations_en\ttranslations_de\tgender\tpartner\t"
              "animate\tindeclinable\tsg_only\tpl_only\tsg_nom\tsg_gen\tsg_dat\t"
              "sg_acc\tsg_inst\tsg_prep\tpl_nom\tpl_gen\tpl_dat\tpl_acc\tpl_inst\tpl_prep")
    rows = [
        "человек\tчелове'к\tperson, people; man\tMensch\tm\t\t1\t0\t0\t0\t"
        "челове'к\tчелове'ка\tчелове'ку\tчелове'ка\tчелове'ком\tчелове'ке\t"
        "лю'ди\tлюде'й\tлю'дям\tлюде'й\tлюдьми'\tлю'дях",
        "год\tго'д\tyear\tJahr\tm\t\t0\t0\t0\t0\tго'д\tго'да\tго'ду\tго'д\t"
        "го'дом\tгоду'\tлета'\tле'т\tлета'м\tлета'\tлета'ми\tлета'х",
        "\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t",
    ]
    path.write_text("\n".join([header] + rows), encoding="utf-8")


def test_import_openrussian_adds_words_with_stress(repos, tmp_path):
    """Ice aktarma kelimeleri, vurguyu ve cinsiyeti dogru yazar."""
    src = tmp_path / "openrussian_isimler.tsv"
    _write_noun_tsv(src)
    before = repos.words.count()
    stats = L.import_openrussian(src, repos, limit=100, deck="Test OR")
    assert stats["added"] == 2
    assert stats["skipped"] == 1                 # bos satir atlanir
    assert repos.words.count() == before + 2

    row = repos.db.one("SELECT * FROM words WHERE ru_norm='человек' AND tags='Test OR'")
    assert row is not None
    assert row["stress_pos"] == 5
    assert row["pos"] == "noun-m"
    assert "person" in row["en"]
    assert row["tr"]                              # TR alani EN ile dolduruldu
    assert "род." in row["example_ru"]            # cekim ozeti orneklendi


def test_import_openrussian_respects_limit(repos, tmp_path):
    """limit parametresi en sik N kelimeyi alir."""
    src = tmp_path / "openrussian_isimler.tsv"
    _write_noun_tsv(src)
    stats = L.import_openrussian(src, repos, limit=1, deck="Limitli")
    assert stats["added"] == 1
    rows = repos.words.all(deck="Limitli")
    assert len(rows) == 1
    assert rows[0]["freq_rank"] == 1


def test_import_can_leave_tr_empty(repos, tmp_path):
    """fill_tr_with_en kapaliyken Turkce alani bos birakilir."""
    src = tmp_path / "openrussian_isimler.tsv"
    _write_noun_tsv(src)
    L.import_openrussian(src, repos, limit=5, deck="Bos TR", fill_tr_with_en=False)
    rows = repos.words.all(deck="Bos TR")
    assert rows and all(not r["tr"] for r in rows)


def test_downloader_cancel_flag():
    """Iptal bayragi kurulur."""
    d = L.Downloader()
    assert not d.cancelled.is_set()
    d.cancel()
    assert d.cancelled.is_set()
