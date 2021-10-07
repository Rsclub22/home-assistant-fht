# This is the README OF:
# home-assistant-fht
## from: https://github.com/Rsclub22
FHEM Connector for FHT Heating devices (connected via FHEM)

## Requires FHEM to work
You can find FHEM here: https://fhem.de/
## Requires manual setup via FHEM-WEBbapi
Setup for the FHEM WEBapi here: https://github.com/Rsclub22/home-assistant-fht#fhem-webapi

**IMPORTANT:** The WEBapi needs to be accesabile without a password
# Setup
The FHEM Connector needs to be cloned into the custom_components folder
## FHEM WEBapi
run these commands to open the WEBapi from FHEM
replace `<your-homeassitant-ip-here>`with the IP of your Home-Assitant Instance
```bash
define WEBapi FHEMWEB 8086 global
attr WEBapi csrfToken none
attr WEBapi allowFrom <your-homeassitant-ip-here>

```
**IMPORTANT:** The WEBapi needs to be accesabile without a password

# Configuration
## Example
see `example_configuration.yaml` (https://github.com/Rsclub22/home-assistant-fht/blob/main/example_configuration.yaml)
and then put the files into your configuration.yaml

# Thanks to
Thanks a lot to https://github.com/tarek-yashi for writing the plugin.
