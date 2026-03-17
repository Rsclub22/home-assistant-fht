import logging
import time
import threading
import requests
import re
from urllib.parse import quote

_LOGGER = logging.getLogger(__name__)

# Cache-Timeout nur fürs LESEN
CACHE_DURATION = 120  # Sekunden


class Fht:
    """
    HTTP-Helper für FHEM:
      - Autodetektion des Basis-Pfads (/, /fhem, /fhem/)
      - Lesen via jsonlist2 JSON-API mit globalem Readings-Cache
      - Schreiben IMMER direkt; danach Readings-Cache invalidieren
    """

    def __init__(self, address: str, dev_name: str) -> None:
        self.address = address.strip()          # z.B. "192.168.8.111:8086" oder "http://host:port"
        self.dev_name = dev_name.strip()        # z.B. "FHT_1c50"
        self._readings_cache: dict[str, str] = {}
        self._readings_cache_time: float = 0
        self._last_fetch_attempt: float = 0     # Zeitpunkt des letzten Fetch-Versuchs (auch bei Fehler)
        self._base_path = None                  # wird on-demand autodetektiert
        self._base_path_lock = threading.Lock()  # schützt _detect_base_path
        self._readings_lock = threading.Lock()   # schützt _get_all_readings

    # ---------- Public API ----------

    def get_value(self, key: str, *, force: bool = False):
        """Wert holen. force=True => Cache ignorieren."""
        readings = self._get_all_readings(force=force)
        if key not in readings:
            # We don't log missing keys here to save logs. FHT devices
            # often omit schedule readings to save airtime/battery.
            return None
        return self._parse_value(key, readings[key])

    def set_value(self, key: str, value, *, bypass_cache: bool = True):
        """Direkter Write (kein Optimismus). Danach Readings-Cache invalidieren."""
        url = self._build_set_url(key, value)
        _LOGGER.debug("FHT set: %s", url)
        r = requests.get(url, timeout=5)
        r.raise_for_status()

        # Gesamten Readings-Cache invalidieren
        self._readings_cache = {}
        self._readings_cache_time = 0
        return True

    # ---------- Internals ----------

    def _base_http(self) -> str:
        a = self.address
        if a.startswith("http://") or a.startswith("https://"):
            return a.rstrip("/")
        return f"http://{a}"

    def _detect_base_path(self) -> str:
        """Finde funktionierenden Pfadpräfix für FHEM-Frontend."""
        if self._base_path is not None:
            return self._base_path

        with self._base_path_lock:
            # Double-check after acquiring lock: another thread may have detected it already
            if self._base_path is not None:
                return self._base_path

            base = self._base_http()
            candidates = [
                "/fhem",     # -> http://host:port/fhem
            ]

            last_err = None
            for cand in candidates:
                cmd = f"jsonlist2 {self.dev_name}"
                test_url = f"{base}{cand}?cmd={quote(cmd)}&XHR=1"
                try:
                    r = requests.get(test_url, timeout=5)
                    if r.status_code == 200:
                        # Verify the response is actually JSON and contains Results
                        data = r.json()
                        if "Results" in data:
                            self._base_path = cand
                            _LOGGER.info("fht_heating: detected FHEM base path '%s' (url ok: %s)",
                                         self._base_path or "/", test_url)
                            return self._base_path
                        else:
                            last_err = "JSON missing 'Results'"
                    else:
                        last_err = f"HTTP {r.status_code}"
                except Exception as e:
                    last_err = str(e)

            raise requests.HTTPError(f"Unable to detect FHEM base path on {base} (last: {last_err})")

    def _jsonlist2_url(self) -> str:
        bp = self._detect_base_path()
        cmd = f"jsonlist2 {self.dev_name}"
        return f"{self._base_http()}{bp}?cmd={quote(cmd)}&XHR=1"

    def _set_url(self, key: str, value) -> str:
        bp = self._detect_base_path()
        cmd = f"set {self.dev_name} {key} {value}"
        return f"{self._base_http()}{bp}?cmd={quote(cmd)}&XHR=1"

    def _build_set_url(self, key: str, value) -> str:
        return self._set_url(key, value)

    def _get_all_readings(self, force: bool = False) -> dict[str, str]:
        """Alle Readings holen (gecacht). force=True => Cache ignorieren."""
        if not force and (time.time() - self._readings_cache_time) < CACHE_DURATION:
            return self._readings_cache

        with self._readings_lock:
            # Double-check after acquiring lock: another thread may have just refreshed the cache
            if not force and (time.time() - self._readings_cache_time) < CACHE_DURATION:
                return self._readings_cache

            # Retry-Throttle: nach einem fehlgeschlagenen Fetch kurz warten bevor erneut versucht wird.
            # Verhindert, dass alle wartenden Threads nach einem Fehler sofort nacheinander retrien.
            if not force and (time.time() - self._last_fetch_attempt) < 10:
                return self._readings_cache

            self._last_fetch_attempt = time.time()
            url = self._jsonlist2_url()
            try:
                r = requests.get(url, timeout=5)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                _LOGGER.error("FHT jsonlist2 failed for %s: %s", self.dev_name, e)
                return self._readings_cache  # Alten Cache zurückgeben bei Fehler

            results = data.get("Results", [])
            if not results:
                _LOGGER.warning("FHT jsonlist2: no Results for %s (url=%s)", self.dev_name, url)
                return {}

            raw_readings = results[0].get("Readings", {})
            readings = {k: v.get("Value", "") for k, v in raw_readings.items() if isinstance(v, dict)}
            _LOGGER.debug("FHT jsonlist2: got %d readings for %s", len(readings), self.dev_name)

            self._readings_cache = readings
            self._readings_cache_time = time.time()
            return readings

    def _parse_value(self, key: str, raw: str):
        """Extrahiert den nutzbaren Wert aus dem FHEM-Readings-String."""
        if key in ("measured-temp", "desired-temp", "day-temp", "night-temp"):
            m = re.search(r"([0-9]+(?:\.[0-9]+)?)", raw)
            return m.group(1) if m else None

        if key == "actuator":
            m = re.search(r"([0-9]+(?:\.[0-9]+)?)", raw)
            return (m.group(1) + "%") if m else None

        if key == "mode":
            m = re.search(r"([a-z_]+)", raw.strip(), re.I)
            return m.group(1).lower() if m else None

        if key == "window":
            m = re.search(r"\b(open|closed)\b", raw, re.I)
            return m.group(1).lower() if m else None

        # Schedule-Keys (mon-from1, tue-to2, …) und sonstige: Zeit oder Zahl
        m = re.search(r"([0-9]+(?:\.[0-9]+)?(?::[0-9]+)?)", raw)
        return m.group(1) if m else raw.strip() or None
