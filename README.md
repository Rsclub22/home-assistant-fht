# home-assistant-fht
## from: https://github.com/Rsclub22
FHEM Connector for FHT Heating devices (connected via FHEM)

## Requires FHEM to work
You can find FHEM here: https://fhem.de/
## Requires manual setup via FHEM-WEBapi
Setup for the FHEM WEBapi here: https://github.com/Rsclub22/home-assistant-fht#fhem-webapi

**IMPORTANT:** The WEBapi needs to be accessable without a password
# Setup
The FHEM Connector needs to be cloned into the custom_components folder
Download the FHEM Connector here: https://github.com/Rsclub22/home-assistant-fht/releases/download/v0.2/fht_heating.zip
and unzip it in your `custom_components` directory. If it doesn't exist create the directory with `mkdir custom_components` and change the permissions with `chmod 751 custom_components` and `chown -R homeassistant custom_components`

## FHEM WEBapi
Run these commands to open the WEBapi from FHEM
replace `<your-homeassistant-ip-here>`with the IP of your Home-Assistant Instance
```bash
define WEBapi FHEMWEB 8086 global
attr WEBapi csrfToken none
attr WEBapi allowfrom <your-homeassistant-ip-here>

```
**IMPORTANT:** The WEBapi needs to be accessabile without a password

# Configuration
## Example
see `example_configuration.yaml` (https://github.com/Rsclub22/home-assistant-fht/blob/main/example_configuration.yaml)
and then put the files into your configuration.yaml

# Thanks to
Thanks a lot to https://github.com/tarek-yashi for writing the plugin.
