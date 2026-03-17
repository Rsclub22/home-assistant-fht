# home-assistant-fht

FHEM Connector for FHT Heating devices (connected via FHEM)

## Compatibility

This integration supports Home Assistant 2025.1.0 and later.

## Requires FHEM to work

You can find FHEM here: https://fhem.de/

## Requires manual setup via FHEM-WEBapi

**IMPORTANT:** The WEBapi needs to be accessible without a password.

Setup instructions: [FHEM WEBapi](#fhem-webapi)

---

# Setup

## HACS (Recommended)

You can install this integration via HACS as a Custom Repository:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Rsclub22&repository=home-assistant-fht)

1. Go to HACS → Integrations → 3-dot menu (top right) → Custom repositories.
2. Add the URL `https://github.com/Rsclub22/home-assistant-fht` and choose `Integration` as category.
3. Click **ADD**.
4. Search for **FHT Heating** in HACS and click **Download**.
5. Restart Home Assistant.

## Manual Setup

Copy the `fht_heating` folder into your Home Assistant `custom_components` directory:

```bash
mkdir -p custom_components
chmod 751 custom_components
chown -R homeassistant custom_components
```

Then copy the contents of `custom_components/fht_heating/` from this repository into `<config>/custom_components/fht_heating/`.

---

## FHEM WEBapi

Run these commands in FHEM to open the WEBapi.
Replace `<your-homeassistant-ip>` with the IP address of your Home Assistant instance:

```bash
define WEBapi FHEMWEB 8086 global
attr WEBapi csrfToken none
attr WEBapi allowfrom <your-homeassistant-ip>
```

**IMPORTANT:** The WEBapi must be accessible without a password.

---

# Configuration

Add the integration via the Home Assistant UI: **Settings → Devices & Services → Add Integration → FHT Heating**.

<img width="575" height="347" alt="image" src="https://github.com/user-attachments/assets/b48d863b-4d24-4252-a28a-aa22892c1f9b" />

- **Address**: Full URL to the FHEM WEBapi, e.g. `http://192.168.1.100:8086`
- **Device name**: The FHEM device name, e.g. `FHT_1c50`

<img width="575" height="347" alt="image" src="https://github.com/user-attachments/assets/bc3e7368-4763-4ca4-85fd-e6bd080fffa7" />

To add more devices go to **Settings → Devices & Services → FHT Heating → Configure** and choose **Add device**.
<img width="336" height="170" alt="image" src="https://github.com/user-attachments/assets/d769f8d8-16fc-467d-8e49-d55fd549d67f" />
<img width="1177" height="210" alt="image" src="https://github.com/user-attachments/assets/c4770e9b-5408-44e8-a66c-c9f8ed66f9c1" />
<img width="595" height="291" alt="image" src="https://github.com/user-attachments/assets/b2acab3c-f856-46d6-afbb-388bc8754287" />
<img width="595" height="291" alt="image" src="https://github.com/user-attachments/assets/7395fe5a-1f41-4628-b712-63bff2c1d495" />



When adding devices, the combination of FHEM address and device name is used as the unique identifier, so multiple devices under the same FHEM server are fully supported.

---

# Entities

Each FHT device exposes the following entities in Home Assistant:

| Entity | Type | Description |
|---|---|---|
| Thermostat | `climate` | Current & target temperature, HVAC mode |
| Window Sensor | `binary_sensor` | Open/closed state of the FHT window contact |
| Mode | `select` | FHT operating mode (auto / manual / holiday) |
| Day Temperature | `number` | Day setpoint temperature |
| Night Temperature | `number` | Night setpoint temperature |
| Mon–Sun From1/To1/From2/To2 | `time` | Weekly schedule slots |

---

# Services

### `fht_heating.set_schedule`

Sets the full weekly schedule and temperature setpoints in one call (batches FHEM commands to save radio airtime).

Fields: `device_id`, `day_temp`, `night_temp`, `mon_from1`, `mon_to1`, … `sun_from2`, `sun_to2`

See `custom_components/fht_heating/services.yaml` for the full field reference.

---

# Legacy YAML configuration

For older YAML-based setups see `example_configuration.yaml`.
The recommended way is the UI config flow described above.

---

# Thanks to

Thanks a lot to [@multilan-tarek](https://github.com/multilan-tarek) for writing the original plugin.
