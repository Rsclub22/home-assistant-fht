import logging
import re

import requests
from bs4 import BeautifulSoup


_LOGGER = logging.getLogger(__name__)


class Fht:
    def __init__(self, address, dev_name):
        self.address = address
        self.dev_name = dev_name
        self._cached_values = {}

    def get_cached_value(self, key):
        if key in self._cached_values:
            return self._cached_values[key]
        return self.get_value(key)

    def _fetch_detail(self):
        url = f"http://{self.address}/fhem?detail={self.dev_name}"
        response = requests.get(url)
        return BeautifulSoup(response.text, "lxml")

    def get_value(self, key):
        soup = self._fetch_detail()
        element = soup.find("div", {"informid": f"{self.dev_name}-{key}"})
        state = None
        if element and element.text:
            text = element.text.strip()
            match = re.search(r"-?\d+(?:\.\d+)?", text)
            state = match.group(0) if match else text
        else:
            url = (
                "http://%s/fhem?cmd.%s=list %s %s"
                % (self.address, self.dev_name, self.dev_name, key)
            )
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "lxml")
            content = soup.find("div", {"id": "content"})
            text = content.find("pre").text if content else ""
            match = re.search(rf"{key}\\s+(-?\d+(?:\.\d+)?)", text)
            state = match.group(1) if match else None
        self._cached_values[key] = state
        return state

    def set_value(self, key, value):
        url = (
            "http://%s/fhem?cmd.%s=set %s %s %s"
            % (self.address, self.dev_name, self.dev_name, key, value)
        )
        requests.get(url)
        self._cached_values[key] = str(value)
