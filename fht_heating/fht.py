import logging
import time
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote

_LOGGER = logging.getLogger(__name__)

# Cache-Timeout nur fürs LESEN
CACHE_DURATION = 120  # Sekunden


class Fht:
    """
    HTTP-Helper für FHEM:
      - Autodetektion des Basis-Pfads (/, /fhem, /fhem/)
      - Lesen mit einfachem Cache, Schreiben IMMER direkt
      - Nach Write: betroffenen Key aus Cache invalidieren
    """

    def __init__(self, address: str, dev_name: str) -> None:
        self.address = address.strip()          # z.B. "192.168.8.111:8086" oder "http://host:port"
        self.dev_name = dev_name.strip()        # z.B. "FHT_1c50"
        self._cached_values: dict[str, str | float | None] = {}
        self._cache_times: dict[str, float] = {}
        self._base_path = None                  # wird on-demand autodetektiert

    # ---------- Public API ----------

    def get_value(self, key: str, *, force: bool = False):
        """Wert holen. force=True => Cache ignorieren."""
        if not force:
            if key in self._cached_values and (time.time() - self._cache_times.get(key, 0) < CACHE_DURATION):
                return self._cached_values[key]

        val = self._read_from_fhem(key)
        self._cached_values[key] = val
        self._cache_times[key] = time.time()
        return val

    def set_value(self, key: str, value, *, bypass_cache: bool = True):
        """Direkter Write (kein Optimismus). Danach Cache-Key invalidieren."""
        url = self._build_set_url(key, value)
        _LOGGER.debug("FHT set: %s", url)
        r = requests.get(url, timeout=5)
        r.raise_for_status()

        # Cache für den Key invalidieren
        self._cached_values.pop(key, None)
        self._cache_times.pop(key, None)
        return True

    # ---------- Internals ----------

    def _base_http(self) -> str:
        # address kann host[:port] sein oder schon http(s)://...
        a = self.address
        if a.startswith("http://") or a.startswith("https://"):
            return a.rstrip("/")
        return f"http://{a}"

    def _detect_base_path(self) -> str:
        """Finde funktionierenden Pfadpräfix für FHEM-Frontend."""
        if self._base_path:
            return self._base_path

        base = self._base_http()
        candidates = [
            "",          # -> http://host:port
            "/fhem",     # -> http://host:port/fhem
            "/fhem/",    # -> http://host:port/fhem/
        ]

        last_err = None
        for cand in candidates:
            test_url = f"{base}{cand}/?detail={quote(self.dev_name)}"
            try:
                r = requests.get(test_url, timeout=5)
                if r.status_code == 200:
                    self._base_path = cand or ""   # kann leer sein
                    _LOGGER.info("fht_heating: detected FHEM base path '%s' (url ok: %s)", self._base_path or "/", test_url)
                    return self._base_path
                last_err = f"HTTP {r.status_code}"
            except Exception as e:
                last_err = str(e)

        raise requests.HTTPError(f"Unable to detect FHEM base path on {base} (last: {last_err})")

    def _detail_url(self) -> str:
        bp = self._detect_base_path()
        return f"{self._base_http()}{bp}/?detail={quote(self.dev_name)}"

    def _set_url(self, key: str, value) -> str:
        """
        Standard-Set-Form:
          set <device> <key> <value>
        Bei Presets wie holiday_short schicken wir genau den String.
        """
        bp = self._detect_base_path()
        cmd = f"set {self.dev_name} {key} {value}"
        return f"{self._base_http()}{bp}/?cmd={quote(cmd)}&XHR=1"

    def _build_set_url(self, key: str, value) -> str:
        return self._set_url(key, value)

    def _read_from_fhem(self, key: str):
        """Lade Detailseite und extrahiere Key-Wert möglichst robust."""
        url = self._detail_url()
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        html = r.text

        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)

        # measured-temp: Zahl (optional °C)
        if key == "measured-temp":
            m = re.search(r"measured[-\s]?temp[:\s]+([0-9]+(?:\.[0-9]+)?)", text, re.I)
            if m:
                return m.group(1)

        if key == "desired-temp":
            m = re.search(r"desired[-\s]?temp[:\s]+([0-9]+(?:\.[0-9]+)?)", text, re.I)
            if m:
                return m.group(1)

        if key == "actuator":
            m = re.search(r"actuator[:\s]+([0-9]+(?:\.[0-9]+)?)\s*%?", text, re.I)
            if m:
                return m.group(1) + "%"

        if key == "mode":
            m = re.search(r"mode[:\s]+([a-z_]+)", text, re.I)
            if m:
                return m.group(1).lower()

        # window: steht bei dir simpel als "window  open|closed"
        if key == "window":
            m = re.search(r"\bwindow\s+(open|closed)\b", text, re.I)
            if m:
                return m.group(1).lower()

        _LOGGER.debug("FHT read: no match for key=%s on %s (url=%s)", key, self.dev_name, url)
        return None
