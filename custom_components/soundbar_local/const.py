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

# Options: inputs offered in the source list, and custom names for the
# HDMI inputs (e.g. the console plugged into one of them).
CONF_SOURCES = "sources"
CONF_HDMI1_NAME = "hdmi1_name"
CONF_HDMI2_NAME = "hdmi2_name"
NAME_OPTIONS = {"HDMI_IN1": CONF_HDMI1_NAME, "HDMI_IN2": CONF_HDMI2_NAME}

# Inputs the bar reports but that cannot be selected from here: a phone
# starts them. Shown by name, never offered in the source list.
REPORTED_SOURCES = {
    "WIFI_AIRPLAY": "AirPlay",
}

# Every sound mode code the line uses -> name shown in Home Assistant.
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

# Modes a model really applies, when known. Checked on a HW-Q990D: MOVIE and
# CLEARVOICE are refused, MUSIC, DTS_VIRTUAL_X and NIGHT are acknowledged but
# ignored. Models not listed get every mode in SOUND_MODES.
SOUND_MODES_BY_MODEL = {
    "HW-Q990D": ["ADAPTIVE", "STANDARD", "SURROUND", "GAME"],
}
