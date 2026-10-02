"""Constants for Samsung Soundbar Local."""

from datetime import timedelta

DOMAIN = "soundbar_local"

SCAN_INTERVAL = timedelta(seconds=10)

# Input codes reported by the bar -> names shown in Home Assistant.
SOURCES = {
    "E_ARC": "TV (eARC)",
    "ARC": "TV (ARC)",
    "HDMI_IN1": "HDMI 1",
    "HDMI_IN2": "HDMI 2",
    "D_IN": "Optical",
    "BT": "Bluetooth",
    "WIFI_IDLE": "Wi-Fi",
}

SOUND_MODES = {
    "ADAPTIVE": "Adaptive",
    "STANDARD": "Standard",
    "SURROUND": "Surround",
    "GAME": "Game",
    "MOVIE": "Movie",
    "MUSIC": "Music",
    "CLEARVOICE": "Clear Voice",
    "DTS_VIRTUAL_X": "DTS Virtual:X",
}
