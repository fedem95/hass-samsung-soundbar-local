# Samsung Soundbar **Local** – Home Assistant Integration

> **Local IP control for 2024-line Samsung Wi-Fi soundbars**
> HW-Q990D · HW-Q800D · HW-QS730D · HW-S800D · HW-S801D · HW-S700D · HW-S60D · HW-S61D · HW-LS60D

Fork of [ZtF/hass-samsung-soundbar-local](https://github.com/ZtF/hass-samsung-soundbar-local), reworked in 2.0 (see [What changed in 2.0](#what-changed-in-20)).

---

## What is it?

`soundbar_local` talks **directly** to your 2024 Samsung soundbar over the LAN (HTTPS on TCP 1516, the JSON-RPC API used by the SmartThings app).
No cloud, no SmartThings integration in Home Assistant: everything stays on your network.

| Entity | What it does |
|--------|--------------|
| Media player | power on/off, volume set/step/mute, input, sound mode; the current codec as an attribute |
| Buttons | subwoofer level up / down |

The bar answers in standby too, so the media player shows **off** when the bar is off and **unavailable** only when it cannot be reached.

Inputs: TV (eARC), TV (ARC), HDMI 1, HDMI 2, Optical, Bluetooth, Wi-Fi.
Sound modes: Adaptive, Standard, Surround, Game, Movie, Music, Clear Voice, DTS Virtual:X.

---

## Requirements

* Home Assistant 2025.4 or newer
* The soundbar added to the **SmartThings app**, connected to Wi-Fi, with **"IP control" enabled** in its settings
* Home Assistant must reach the bar on TCP 1516 (allow it in your firewall if the bar lives on an IoT VLAN)

---

## Installation

### HACS

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/fedem95/hass-samsung-soundbar-local`, category **Integration**.
2. Install **Samsung Soundbar Local** and restart Home Assistant.

### Manual

Copy `custom_components/soundbar_local` into `<config>/custom_components/` and restart Home Assistant.

### Setup

**Settings → Devices & Services → + Add Integration → Samsung Soundbar Local**, enter the soundbar's IP address.
The flow checks that the bar answers before creating the entry.

Upgrading from the original integration keeps your entities: domain and unique ids are unchanged.

---

## What changed in 2.0

* **Token renewal**: when the bar refuses the access token (after a reboot, for example) a new one is requested and the call is retried, instead of failing until Home Assistant restarts.
* **Mandatory `Accept: application/json` header**: the bar answers `400 Bad Request` without it.
* **Direct volume and mute**: `volumeControl` / `muteControl` set the value in one call instead of pressing volume up/down N times.
* **Standby is off, not unavailable**; errors from the bar are typed and surface as unavailable or as a failed action.
* **Connection check in the config flow**, device named after the model (`Samsung HW-Q990D`), readable input and sound mode names, English and Italian translations.
* Modern Home Assistant APIs (`runtime_data`, typed coordinator, `asyncio.timeout`, `ConfigFlowResult`); the folder name now matches the `soundbar_local` domain.
* Tests (`pytest` with `pytest-homeassistant-custom-component`).

## API notes

Observed on a HW-Q990D: `<name>Control` methods read the value when called without it and set it when called with it (`volumeControl` takes an integer, `muteControl` a boolean, `powerControl` `powerOn`/`powerOff`). A missing or expired token is answered with a bare `{"code": -32700, "message": "Parse error"}`. Details in [`api.py`](custom_components/soundbar_local/api.py).
