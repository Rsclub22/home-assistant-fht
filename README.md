# Home-assistant-fht
FHEM Connector for FHT Heating devices

## Requires manual setup via FHEM-Webapi
## Requires FHEM to work
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

# Configuration
## Example
see example_configuration.yaml

