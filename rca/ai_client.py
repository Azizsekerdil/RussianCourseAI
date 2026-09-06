# -*- coding: utf-8 -*-
"""OpenAI uyumlu sohbet istemcisi (LM Studio yerel ucu + alternatif uzak uclar).

- Yalnizca stdlib kullanir (urllib) - harici bagimlilik yok.
- Model bulunamazsa ozellik COKMEZ; profil kurulu modellere karsi cozumlenir.
- Istek metinleri hicbir yerde saklanmaz; yalnizca token sayaclari defterlenir.
- Internet cagrisi yalnizca kullanici alternatif ucu (NIM / OpenRouter / Groq...)
  Ayarlar'dan acikca acarsa yapilir; ayni istemci sinifi api_key ile calisir.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional

import rca_common as C
from rca.i18n import SYSTEM_PROMPTS

TIMEOUT_LIST = 3.0
TIMEOUT_CHAT = 180.0
REACH_CACHE_S = 30.0                       # erisilebilirlik sonucu bu kadar sure onbellekte kalir


class AIError(Exception):
    """AI katmanindaki beklenen hatalar (baglanti yok, model yok...)."""


class AIClient:
    """OpenAI uyumlu bir uca (LM Studio ya da uzak servis) konusan ince istemci."""

    def __init__(self, base: str = None, token_logger: Callable = None,
                 api_key: str = None, model: str = "") -> None:
        self._base = (base or C.LMSTUDIO_BASE).rstrip("/")
        self._models: List[str] = []
        self._checked_at = 0.0
        self._online = False
        self.token_logger = token_logger      # (model, task, ptok, ctok, ms, ok) -> None
        # Yerel uc anahtar istemez; LM Studio "lm-studio" yer tutucusunu yok sayar.
        # Uzak uclarda gercek anahtar verilir; bos anahtarla baslik hic gonderilmez.
        self.api_key = "lm-studio" if api_key is None else (api_key or "")
        self.model = model or ""              # sabit model (uzak uclar icin); bos => profil cozumu
        self.last_model = ""                  # son sohbet isteginde kullanilan model
        self.last_error = ""                  # son basarisiz model listesi denemesinin nedeni

    # -- yapilandirma ------------------------------------------------------
    @property
    def base(self) -> str:
        return self._base

    @base.setter
    def base(self, value: str) -> None:
        """Adres degisince erisilebilirlik onbellegini sifirla."""
        new = (value or C.LMSTUDIO_BASE).rstrip("/")
        if new != self._base:
            self._base = new
            self.reset_cache()

    def configure(self, base: str = None, api_key: str = None, model: str = None) -> None:
        """Ayarlar kaydedilince istemciyi yerinde guncelle (base / anahtar / model)."""
        if base is not None:
            self.base = base
        if api_key is not None and api_key != self.api_key:
            self.api_key = api_key
            self.reset_cache()
        if model is not None:
            self.model = model or ""

    def reset_cache(self) -> None:
        self._models = []
        self._checked_at = 0.0
        self._online = False

    def _headers(self, extra: Dict[str, str] = None) -> Dict[str, str]:
        h: Dict[str, str] = {}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        if extra:
            h.update(extra)
        return h

    # -- kesif -------------------------------------------------------------
    def models(self, force: bool = False) -> List[str]:
        """Kurulu model kimliklerini dondur; ulasilamazsa bos liste."""
        if not force and self._models and (time.time() - self._checked_at) < REACH_CACHE_S:
            return self._models
        self._checked_at = time.time()
        try:
            req = urllib.request.Request(f"{self.base}/v1/models", headers=self._headers())
            with urllib.request.urlopen(req, timeout=TIMEOUT_LIST) as r:
                data = json.loads(r.read().decode("utf-8"))
            self._models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
            self._online = True
            self.last_error = ""
        except Exception as e:                                  # noqa: BLE001
            self._models = []
            self._online = False
            self.last_error = str(e)
        return self._models

    def is_online(self) -> bool:
        """Uc erisilebilir mi? (model listesi yeniden sorgulanabilir)"""
        self.models()
        return self._online

    def reachable(self, max_age: float = REACH_CACHE_S) -> bool:
        """Ucuz erisilebilirlik denetimi: son `max_age` saniye icindeki sonuc kullanilir.

        `models()` yalnizca basarili sonucu onbellekler; burada basarisiz sonuc da
        onbellekte tutulur ki sozluk her aramada 3 saniyelik bir denemeye takilmasin.
        """
        if self._checked_at and (time.time() - self._checked_at) < max_age:
            return self._online
        self.models(force=True)
        return self._online

    def resolve(self, task: str) -> Optional[str]:
        """Gorev icin en uygun kurulu modeli sec.

        Sabit bir model tanimliysa (uzak uclar) dogrudan o kullanilir. Aksi halde
        once profil listesindeki tercih sirasi, sonra ad benzerligi, en son
        kurulu ilk model denenir. Hicbiri yoksa None.
        """
        if self.model:
            return self.model
        installed = self.models()
        if not installed:
            return None
        prefs = C.MODEL_PROFILES.get(task, C.MODEL_PROFILES["chat"])
        low = {m.lower(): m for m in installed}
        for p in prefs:
            if p.lower() in low:
                return low[p.lower()]
        for p in prefs:
            for m in installed:
                if p.split("-")[0].lower() in m.lower():
                    return m
        if task == "vision":
            for m in installed:
                if any(k in m.lower() for k in ("vl", "vision", "llava")):
                    return m
            return None                      # gorsel modeli yoksa zorlamayiz
        return installed[0]

    # -- sohbet ------------------------------------------------------------
    def chat(self, messages: List[Dict[str, str]], task: str = "chat",
             temperature: float = 0.3, max_tokens: int = 800,
             model: str = None, timeout: float = None) -> str:
        """Sohbet tamamlama iste ve yalnizca metni dondur.

        Baglanti yoksa veya model bulunamazsa AIError firlatir - cagiran taraf
        bunu kullaniciya sakin bir mesajla gosterir.
        """
        mdl = model or self.resolve(task)
        if not mdl:
            raise AIError("model-yok")
        self.last_model = mdl
        payload = {
            "model": mdl,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base}/v1/chat/completions", data=body,
            headers=self._headers({"Content-Type": "application/json"}))
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout or TIMEOUT_CHAT) as r:
                data = json.loads(r.read().decode("utf-8"))
        except urllib.error.URLError as e:
            self._log(mdl, task, 0, 0, int((time.time() - t0) * 1000), False)
            raise AIError(f"baglanti: {e}") from e
        except Exception as e:
            self._log(mdl, task, 0, 0, int((time.time() - t0) * 1000), False)
            raise AIError(str(e)) from e

        ms = int((time.time() - t0) * 1000)
        usage = data.get("usage") or {}
        self._log(mdl, task, int(usage.get("prompt_tokens", 0)),
                  int(usage.get("completion_tokens", 0)), ms, True)
        try:
            return (data["choices"][0]["message"]["content"] or "").strip()
        except Exception:
            return ""

    def _log(self, model: str, task: str, ptok: int, ctok: int, ms: int, ok: bool) -> None:
        """Token defterine yaz (istek metni yazilmaz)."""
        if self.token_logger:
            try:
                self.token_logger(model, task, ptok, ctok, ms, ok)
            except Exception:
                pass

    # -- yuksek seviye gorevler -------------------------------------------
    def explain(self, text: str, ui_lang: str = "tr", context: str = "") -> str:
        """Secili Rusca metni acikla (dilbilgisi + ceviri)."""
        sysmsg = SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS["tr"])
        user = f"Su Rusca parcayi acikla:\n\n{text}"
        if context:
            user += f"\n\nBaglam:\n{context}"
        user += ("\n\nSirasiyla ver: 1) ceviri 2) kelime kelime cozumleme "
                 "3) gecen dilbilgisi kurallarinin adi 4) benzer bir ornek cumle.")
        return self.chat([{"role": "system", "content": sysmsg},
                          {"role": "user", "content": user}], task="grammar")

    def translate(self, text: str, direction: str = "ru2tr", ui_lang: str = "tr") -> str:
        """Metni cevir. direction: ru2tr | tr2ru"""
        target = "Turkce" if direction == "ru2tr" else "Rusca"
        sysmsg = SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS["tr"])
        user = (f"Asagidaki metni {target} diline cevir. Yalnizca ceviriyi ver, "
                f"aciklama ekleme.\n\n{text}")
        return self.chat([{"role": "system", "content": sysmsg},
                          {"role": "user", "content": user}],
                         task="translate", temperature=0.1)

    def correct(self, sentence: str, ui_lang: str = "tr") -> str:
        """Yazi duzeltici: hatayi isaretle, kurali adlandir, dogrusunu ver."""
        sysmsg = SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS["tr"])
        user = (
            "Ogrencinin yazdigi Rusca cumle asagida. Su bicimde yanit ver:\n"
            "HATA: (yanlis parca)\n"
            "KURAL: (ihlal edilen kuralin adi, orn. 'винительный падеж')\n"
            "DOGRU: (duzeltilmis cumle, vurgu isaretli)\n"
            "NEDEN: (bir cumlelik aciklama)\n"
            "Hata yoksa sadece 'DOGRU: <cumle>' yaz.\n\n"
            f"Cumle: {sentence}")
        return self.chat([{"role": "system", "content": sysmsg},
                          {"role": "user", "content": user}],
                         task="correct", temperature=0.1)

    def roleplay(self, scenario: str, level: str, history: List[Dict[str, str]],
                 ui_lang: str = "tr") -> str:
        """Rol yapma diyalogu - CEFR seviyesine gore kelime sinirlamasi."""
        sysmsg = (
            f"{SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS['tr'])}\n"
            f"Simdi bir rol yapma alistirmasi yonetiyorsun. Senaryo: {scenario}. "
            f"Ogrencinin seviyesi {level}. YALNIZCA {level} seviyesine uygun kelime ve "
            f"yapi kullan. Kisa cumleler kur (en fazla 2 cumle), her yanitin sonunda "
            f"ogrenciye bir soru sor. Rusca konus.")
        msgs = [{"role": "system", "content": sysmsg}] + history
        return self.chat(msgs, task="dialogue", temperature=0.7, max_tokens=300)

    def session_report(self, history: List[Dict[str, str]], ui_lang: str = "tr") -> str:
        """Konusma oturumu sonu raporu: hata dokumu + 5 kelime."""
        sysmsg = SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS["tr"])
        convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        user = ("Asagidaki diyalogda ogrencinin yaptigi hatalari listele "
                "(hata -> kural -> dogrusu). Sonra ogrenmesi gereken 5 kelimeyi "
                "'RU - TR' bicimde ver.\n\n" + convo)
        return self.chat([{"role": "system", "content": sysmsg},
                          {"role": "user", "content": user}], task="grammar")

    def describe_image(self, image_b64: str, prompt: str, ui_lang: str = "tr") -> str:
        """Gorsel/OCR gorevi - vision profili yoksa AIError."""
        mdl = self.resolve("vision")
        if not mdl:
            raise AIError("vision-model-yok")
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
        ]
        return self.chat([{"role": "system", "content": SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS["tr"])},
                          {"role": "user", "content": content}],
                         task="vision", model=mdl)


def approx_tokens(text: str) -> int:
    """Kaba token tahmini (usage bilgisi gelmezse defter icin)."""
    return max(1, len(text or "") // 3)


# --------------------------------------------------------------------------
# Saglayici secimi (sozluk)
# --------------------------------------------------------------------------
_LOCAL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "::1", "host.docker.internal")


def needs_key(base: str) -> bool:
    """Adres bir anahtar gerektirir mi? Yerel / ozel ag adresleri gerektirmez."""
    try:
        host = (urllib.parse.urlsplit(base or "").hostname or "").lower()
    except Exception:                                           # noqa: BLE001
        return True
    if not host:
        return True
    if host in _LOCAL_HOSTS or host.endswith(".local") or host.endswith(".lan"):
        return False
    parts = host.split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        a, b = int(parts[0]), int(parts[1])
        if a == 10 or (a == 192 and b == 168) or (a == 172 and 16 <= b <= 31):
            return False
    return True


def alt_usable(settings: Dict[str, Any], alt: "AIClient") -> bool:
    """Alternatif uc kullanilabilir mi: acik + (anahtar var ya da anahtar istemeyen adres)."""
    if alt is None or not settings.get("alt_enabled", False):
        return False
    return bool(alt.api_key) or not needs_key(alt.base)


def resolve_dict_provider(settings: Dict[str, Any], local: "AIClient",
                          alt: "AIClient") -> Optional["AIClient"]:
    """Sozluk icin kullanilacak istemciyi sec (ya da None).

    dict_ai politikasi:
      off   -> None
      local -> yerel uc ulasilabiliyorsa yerel, degilse None
      alt   -> alternatif uc acik + anahtar (ya da anahtarsiz adres) ise alternatif, degilse None
      auto  -> yerel ulasilabiliyorsa yerel; degilse alternatif (acik ise); degilse None
    Genel "AI ozellikleri" kapaliysa her durumda None. Erisilebilirlik GET /v1/models
    ile olculur ve ~30 sn onbellekte tutulur; bu cagri ag beklemesi icerebilir,
    arayuz thread'inden degil arka plandan cagrilmalidir.
    """
    if not settings.get("ai_enabled", True):
        return None
    policy = settings.get("dict_ai") or "auto"
    if policy == "off":
        return None
    if policy == "local":
        return local if (local is not None and local.reachable()) else None
    if policy == "alt":
        return alt if alt_usable(settings, alt) else None
    if local is not None and local.reachable():
        return local
    return alt if alt_usable(settings, alt) else None
