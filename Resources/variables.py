import os
import sys
import wx


constants = dict()
constants["VERSION"] = "1.0.1"
constants["YEAR"] = "2022"
constants["PLATFORM"] = sys.platform
constants["OSX_BUILD_WITH_JACK_SUPPORT"] = False
constants["WIN_TITLE"] = "Zyne_B"
constants["PREF_FILE_NAME"] = ".Zyne_Brc"
constants["DEFAULT_ZY_NAME"] = "default.zy"

# Change working directory if App is running 'frozen' (by e.g. pyinstaller)
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

if '/Zyne_B.app' in os.getcwd():
    constants["RESOURCES_PATH"] = os.getcwd()
    currentw = os.getcwd()
    spindex = currentw.index('/Zyne_B.app')
    os.chdir(currentw[:spindex])
else:
    constants["RESOURCES_PATH"] = os.path.join(os.getcwd(), 'Resources')

if not os.path.isdir(constants["RESOURCES_PATH"]) and constants["PLATFORM"] == "win32":
    constants["RESOURCES_PATH"] = os.path.join(os.getenv("ProgramFiles"), "Zyne_B", "Resources")

constants["ID"] = {
    "New": 1000, "Open": 1001, "Save": 1002, "SaveAs": 1003, "Export": 1004,
    "Quit": wx.ID_EXIT, "Prefs": wx.ID_PREFERENCES, "MidiLearn": 1007, "Run": 1008,
    "ResetKeyboard": 1009, "ExportChord": 1010, "Retrig": 1011, "ExportTracks": 1012,
    "ExportChordTracks": 1013, "UpdateModules": 2000, "CheckoutModules": 2001,
    "Modules": 1100, "About": wx.ID_ABOUT, "Tutorial": 6000, "MidiLearnHelp": 6001,
    "ExportHelp": 6002, "CloseTut": 7000, "CloseHelp": 7001, "CloseLFO": 7002,
    "DeSelect": 9998, "Select": 9999, "Uniform": 10000, "Triangular": 10001,
    "Minimum": 10002, "Jitter": 10003, "Duplicate": 10100,
    "NewInstance": 1014
}

constants["VAR_PREF_LABELS"] = {
    "AUDIO_HOST": "Audio host API",
    "AUTO_OPEN": 'Auto open default or last synth',
    "BITS": 'Exported sample type',
    "CUSTOM_MODULES_PATH": 'User-defined modules location',
    "EXPORT_PATH": 'Prefered path for exported samples',
    "FORMAT": 'Exported soundfile format',
    "MIDI_INTERFACE": 'Prefered Midi interface',
    "OUTPUT_DRIVER": 'Prefered output driver',
    "POLY": 'Keyboard polyphony',
    "PYO_PRECISION": 'Internal sample precision',
    "SLIDERPORT": "Slider's portamento in seconds",
    "SR": 'Sampling rate',
}

constants["VAR_CHOICES"] = {
    "AUTO_OPEN": ['None', 'Default', 'Last Saved'],
    "BITS": ['16', '24', '32'],
    "FORMAT": ['wav', 'aif'],
    "POLY": list(map(str, range(1, 21))),
    "PYO_PRECISION": ['single', 'double'],
    "SR": ['44100', '48000', '96000'],
    "CHANNEL": list(map(str, range(16))),
}

vars = dict()
vars["AUDIO_HOST"] = "Portaudio"
vars["AUTO_OPEN"] = "Default"
vars["BITS"] = 24
vars["CUSTOM_MODULES_PATH"] = ""
vars["EXPORT_PATH"] = ""
vars["FORMAT"] = 'wav'
vars["LAST_SAVED"] = ""
vars["LEARNINGSLIDER"] = None
vars["MIDILEARN"] = False
vars["MIDI_INTERFACE"] = ""
vars["OUTPUT_DRIVER"] = ""
vars["POLY"] = 5
vars["PYO_PRECISION"] = "double"
vars["SLIDERPORT"] = 0.05
vars["SR"] = 48000

vars["EXTERNAL_MODULES"] = {}
vars["MIDIPITCH"] = None
vars["MIDIVELOCITY"] = 0.707
vars["MIDI_ACTIVE"] = 0
vars["NOTEONDUR"] = 1.0
vars["VIRTUAL"] = False

vars["PREF_FILE_SETTINGS"] = {}

def readPreferencesFile():
    preffile = os.path.join(os.path.expanduser("~"), constants["PREF_FILE_NAME"])
    if os.path.isfile(preffile):
        with open(preffile, "r", encoding="utf-8") as f:
            lines = f.readlines()
            pref_rel_version = int(lines[0].split()[3].split(".")[1])
            cur_rel_version = int(constants["VERSION"].split(".")[1])
            if lines[0].startswith("### Zyne_B"):
                if pref_rel_version != cur_rel_version:
                    print("Zyne_B preferences out-of-date, using default values.")
                else:
                    for line in lines[1:]:
                        if line:
                            key, val = map(str.strip, line.split("="))
                            if key == "AUDIO_HOST" and constants["PLATFORM"] == "darwin" \
                                    and not constants["OSX_BUILD_WITH_JACK_SUPPORT"] \
                                    and val in ["Jack", "Coreaudio"]:
                                vars[key] = "Portaudio"
                                vars["PREF_FILE_SETTINGS"][key] = vars[key]
                            elif key in ["SR", "POLY", "BITS"]:
                                vars[key] = int(val)
                                vars["PREF_FILE_SETTINGS"][key] = vars[key]
                            elif key in ["SLIDERPORT"]:
                                vars[key] = float(val)
                                vars["PREF_FILE_SETTINGS"][key] = vars[key]
                            elif key == "AUDIO_HOST" and constants["PLATFORM"] == "darwin" \
                                    and not constants["OSX_BUILD_WITH_JACK_SUPPORT"] \
                                    and val in ["Jack", "Coreaudio"]:
                                vars[key] = "Portaudio"
                                vars["PREF_FILE_SETTINGS"][key] = vars[key]
                            else:
                                vars[key] = val
                                vars["PREF_FILE_SETTINGS"][key] = vars[key]
            else:
                print("Zyne_B preferences out-of-date, using default values.")
