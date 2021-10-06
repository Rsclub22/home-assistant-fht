import sys
import logging
import requests
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

class Fht:
    cached_values = {}
    def __init__(self, address, dev_name):
        self.address = address
        self.dev_name = dev_name

    def get_cached_value(self, key):
        if key in self.cached_values:
            return self.cached_values[key]
        else:
            return get_value(key)

    def get_value(self, key):
        url = "http://%s/fhem?cmd.%s=list %s %s" % (self.address, self.dev_name, self.dev_name, key)
        response = requests.get(url)
        response = BeautifulSoup(response.text, "lxml")
        state = response.find("div", {"id": "content"})
        state = state.find("pre").text[-7:-1].replace(" ", "")
        self.cached_values[key] = state
        return state

    def set_value(self, key, value):
        url = "http://%s/fhem?cmd.%s=set %s %s %s" % (self.address, self.dev_name, self.dev_name, key, value)
        requests.get(url)
