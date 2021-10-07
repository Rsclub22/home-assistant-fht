# Home-assistant-fht
FHEM Connector for FHT Heating devices

## Requires manual setup via FHEM-Webapi
## Requires FHEM to work
## Setup
The FHEM Connector needs to be cloned into the custom_components folder

## Configuration
# Example
see example_configuration.yaml

climate:
  - platform: fht_heating
    address: "<ip address of fhem here>:<port for the api server>"
    dev_name: "<Name of the FHEM Device>"
