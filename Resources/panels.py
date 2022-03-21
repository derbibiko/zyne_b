"""
Copyright 2009-2015 Olivier Belanger - modifications by Hans-Jörg Bibiko 2022
"""
import copy
import math
import os
import random
import time
import wx
import Resources.variables as vars
from Resources.audio import *
from Resources.widgets import *
from Resources.utils import toLog
import wx.richtext as rt

# is used mainly for dragging the LFOFrame on Linux (?) and hovering on Windows (?)
from wx.lib.stattext import GenStaticText

HEADTITLE_BACK_COLOUR = "#9999A0"

WAVE_TITLES = {0: "Sine", 1: "Ramp", 2: "Sawtooth", 3: "Square", 4: "Triangle",
               5: "Pulse", 6: "Bipolar Pulse", 7: "Sample and Hold"}


# Param values are: init, min, max, is_int, is_log
MODULES = {
            "FM": { "title": "Frequency Modulation", "synth": FmSynth,
                    "p1": ["FM Ratio", 2, 1, 12, False, False],
                    "p2": ["FM Index", 5, 0, 40, False, False],
                    "p3": ["Lowpass Cutoff", 2000, 100, 18000, False, True],
                    },
            "Additive": { "title": "Additive Synthesis", "synth": AddSynth,
                    "p1": ["Transposition", 0, -36, 36, True, False],
                    "p2": ["Spread", 1, 0.001, 2, False, True],
                    "p3": ["Feedback", 0, 0, 1, False, False]
                    },
            "Wind": { "title": "Wind Synthesis", "synth": WindSynth,
                    "p1": ["Rand frequency", 1, 0.01, 20, False, True],
                    "p2": ["Rand Depth", .1, .001, .25, False, False],
                    "p3": ["Filter Q", 5, 1, 20, False, False]
                    },
            "SquareMod": { "title": "Square Modulation", "synth": SquareMod,
                    "p1": ["Harmonics", 10, 1, 40, True, False],
                    "p2": ["LFO Frequency", 1, .001, 20, False, False],
                    "p3": ["LFO Amplitude", 1, 0, 1, False, False]
                    },
            "SawMod": { "title": "Sawtooth Modulation", "synth": SawMod,
                    "p1": ["Harmonics", 10, 1, 40, True, False],
                    "p2": ["LFO Frequency", 1, .001, 20, False, False],
                    "p3": ["LFO Amplitude", 1, 0, 1, False, False]
                    },
            "Pulsar": { "title": "Pulsar Synthesis", "synth": PulsarSynth,
                    "p1": ["Harmonics", 10, 1, 20, True, False],
                    "p2": ["Transposition", 0, -36, 36, True, False],
                    "p3": ["LFO Frequency", 1, .02, 200, False, True],
                    },
            "Ross": { "title": "Rossler Attractors", "synth": Ross,
                    "p1": ["Chaos", 0.5, 0., 1., False, False],
                    "p2": ["Chorus Depth", .001, .001, .125, False, True],
                    "p3": ["Lowpass Cutoff", 5000, 100, 15000, False, True]
                    },
            "Wave": { "title": "Waveform Synthesis", "synth": Wave,
                    "p1": ["Waveform", 0, 0, 7, True, False],
                    "p2": ["Transposition", 0, -36, 36, True, False],
                    "p3": ["Sharpness", 0.5, 0., 1., False, False],
                    "slider_title_dicts": [
                        {0: "Ramp (saw up)", 1: "Sawtooth", 2: "Square", 3: "Triangle",
                         4: "Pulse", 5: "Bipolar pulse", 6: "Sample and Hold", 7: "Modulated sine"},
                        None,
                        None]
                    },
            "PluckedString": { "title": "Plucked String Synth", "synth": PluckedString,
                    "p1": ["Transposition", 0, -48, 0, True, False],
                    "p2": ["Duration", 30, .25, 60, False, False],
                    "p3": ["Chorus Depth", .001, .001, .125, False, True]
                    },
            "Reson": { "title": "Resonators Synthesis", "synth": Reson,
                    "p1": ["Transposition", 0, -36, 36, True, False],
                    "p2": ["Chorus Depth", .001, .001, .125, False, True],
                    "p3": ["Lowpass Cutoff", 5000, 100, 10000, False, True]
                    },
            "CrossFM": { "title": "Cross FM Modulation", "synth": CrossFmSynth,
                    "p1": ["FM Ratio", 2, 1, 12, False, False],
                    "p2": ["FM Index 1", 2, 0, 40, False, False],
                    "p3": ["FM Index 2", 2, 0, 40, False, False],
                    },
            "OTReson": { "title": "Out of tune Resonators", "synth": OTReson,
                    "p1": ["Transposition", 0, -36, 36, True, False],
                    "p2": ["Detune", .01, .0001, 1, False, True],
                    "p3": ["Lowpass Cutoff", 5000, 100, 10000, False, True]
                    },
            "InfiniteRev": { "title": "Infinite Reverb", "synth": InfiniteRev,
                    "p1": ["Transposition", 0, -36, 36, True, False],
                    "p2": ["Brightness", 5, 0, 100, True, False],
                    "p3": ["Lowpass Cutoff", 10000, 100, 15000, False, True]
                    },
            "Degradation": { "title": "Wave Degradation", "synth": Degradation,
                    "p1": ["Bit Depth", 6, 2, 8, False, True],
                    "p2": ["SR Scale", .1, 0.001, .5, False, True],
                    "p3": ["Lowpass Cutoff", 10000, 100, 15000, False, True]
                    },
            "PulseWidthMod": { "title": "Pulse Width Modulation", "synth": PulseWidthModulation,
                    "p1": ["Detune", 0, 0, 1, True, False],
                    "p2": ["Duty Cycle", 0.5, 0.01, 0.99, False, False],
                    "p3": ["Lowpass Cutoff", 10000, 100, 15000, False, True]
                   },
            "VoltageControlledOsc": { "title": "Voltage Controlled Osc", "synth": VoltageControlledOsc,
                    "p1": ["Transposition", 0, -36, 36, True, False],
                    "p2": ["Shape", 0.5, 0, 1, False, False],
                    "p3": ["Lowpass Cutoff", 10000, 100, 15000, False, True]
                   },
            "Sampler": { "title": "Sampler", "synth": ZB_Sampler,
                    "p1": ["Loop Start Time (normalized)", 0., 0., 1., False, False],
                    "p2": ["Loop Duration (normalized)", 0., 0., 1., False, False],
                    "p3": ["Pitch", 1., 0., 4., False, False]
            }
}

LFO_CONFIG = {"p1": ["Speed", 4, .01, 1000, False, True],
              "p2": ["Waveform", 0, 0, 7, True, False],
              "p3": ["Jitter", 0, 0, 1, False, False],
              "p4": ["Sharpness", 0.5, 0, 1, False, False]}

LFO_INIT = {"state": False, "params": [.001, .1, .7, 1, 1, .1, 4, 0, 0, .5],
            "ctl_params": [None, None, None, None, None, None, None, None, None, None], "shown": False}


def get_lfo_init():
    return copy.deepcopy(LFO_INIT)


class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filename):
        self.window.GetTopLevelParent().openfile(filename[0])
        return True


class MySamplerDropTarget(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filename):
        self.window.SetSamples(filename[0])
        return True


class HelpFrame(wx.Frame):
    def __init__(self, parent, id, title, size, subtitle, lines, from_module=True):
        wx.Frame.__init__(self, parent, id, title, size=(750, 530))
        self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        self.SetForegroundColour(vars.constants["FORECOLOUR"])
        self.SetSize(self.FromDIP(self.GetSize()))
        self.menubar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        self.fileMenu.Append(vars.constants["ID"]["CloseHelp"], 'Close...\tCtrl+W')
        self.Bind(wx.EVT_MENU, self.onClose, id=vars.constants["ID"]["CloseHelp"])
        if from_module:
            self.menubar.Append(self.fileMenu, "&Module Info")
        else:
            self.menubar.Append(self.fileMenu, "&Help")
        self.SetMenuBar(self.menubar)

        self.rtc = rt.RichTextCtrl(self, style=wx.VSCROLL | wx.HSCROLL | wx.RAISED_BORDER)
        self.rtc.SetEditable(False)

        caret = self.rtc.GetCaret()
        caret.Hide()

        font = self.rtc.GetFont()
        newfont = wx.Font(font.GetPointSize(), wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        if newfont.IsOk():
            self.rtc.SetFont(newfont)

        self.rtc.Freeze()
        self.rtc.BeginSuppressUndo()
        self.rtc.BeginParagraphSpacing(0, 20)
        self.rtc.BeginBold()
        if vars.constants["IS_WIN"] or vars.constants["IS_LINUX"]:
            self.rtc.BeginFontSize(12)
        else:
            self.rtc.BeginFontSize(16)
        self.rtc.WriteText(subtitle)
        if not from_module:
            self.rtc.Newline()
        self.rtc.EndFontSize()
        self.rtc.EndBold()
        self.rtc.Newline()
        for line in lines:
            self.rtc.WriteText(line)
            if not from_module:
                self.rtc.Newline()
        self.rtc.Newline()
        self.rtc.EndParagraphSpacing()
        self.rtc.EndSuppressUndo()
        self.rtc.Thaw()
        wx.CallAfter(self.rtc.SetFocus)

    def onClose(self, evt):
        self.Destroy()


class LFOFrame(wx.Frame):
    def __init__(self, parent, synth, label, which, module):
        wx.Frame.__init__(self, parent, -1, style=wx.FRAME_FLOAT_ON_PARENT | wx.BORDER_NONE | wx.FRAME_TOOL_WINDOW)
        self.parent = parent
        self.module = module
        self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        self.SetForegroundColour(vars.constants["FORECOLOUR"])

        if vars.constants["IS_MAC"]:
            close_accel = wx.ACCEL_CMD
        else:
            close_accel = wx.ACCEL_CTRL
        self.SetAcceleratorTable(wx.AcceleratorTable([
                (wx.ACCEL_CTRL, ord("N"), vars.constants["ID"]["New"]),
                (wx.ACCEL_CTRL, ord("O"), vars.constants["ID"]["Open"]),
                (wx.ACCEL_CTRL, ord("S"), vars.constants["ID"]["Save"]),
                (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("S"), vars.constants["ID"]["SaveAs"]),
                (wx.ACCEL_CTRL, ord("E"), vars.constants["ID"]["Export"]),
                (wx.ACCEL_CTRL, ord("M"), vars.constants["ID"]["MidiLearn"]),
                (wx.ACCEL_CTRL, ord(","), vars.constants["ID"]["Prefs"]),
                (wx.ACCEL_CTRL, ord("G"), vars.constants["ID"]["Uniform"]),
                (wx.ACCEL_CTRL, ord("K"), vars.constants["ID"]["Triangular"]),
                (wx.ACCEL_CTRL, ord("L"), vars.constants["ID"]["Minimum"]),
                (wx.ACCEL_CTRL, ord("J"), vars.constants["ID"]["Jitter"]),
                (wx.ACCEL_CTRL, ord("Q"), vars.constants["ID"]["Quit"]),
                (close_accel, ord("W"), vars.constants["ID"]["CloseLFO"]),
        ]))
        self.Bind(wx.EVT_MENU, self.parent.onNew, id=vars.constants["ID"]["New"])
        self.Bind(wx.EVT_MENU, self.parent.onOpen, id=vars.constants["ID"]["Open"])
        self.Bind(wx.EVT_MENU, self.parent.onSave, id=vars.constants["ID"]["Save"])
        self.Bind(wx.EVT_MENU, self.parent.onSaveAs, id=vars.constants["ID"]["SaveAs"])
        self.Bind(wx.EVT_MENU, self.parent.onExport, id=vars.constants["ID"]["Export"])
        self.Bind(wx.EVT_MENU, self.onMidiLearnMode, id=vars.constants["ID"]["MidiLearn"])
        self.Bind(wx.EVT_MENU, self.parent.onPreferences, id=vars.constants["ID"]["Prefs"])
        self.Bind(wx.EVT_MENU, self.parent.onGenerateValues, id=vars.constants["ID"]["Uniform"], id2=vars.constants["ID"]["Jitter"])
        self.Bind(wx.EVT_MENU, self.parent.onQuit, id=vars.constants["ID"]["Quit"])
        self.Bind(wx.EVT_MENU, self.onClose, id=vars.constants["ID"]["CloseLFO"])
        self.mouseOffset = (0, 0)
        self.which = which
        self.panel = LFOPanel(self, "LFO", f"{label} LFO", synth,
                              LFO_CONFIG["p1"], LFO_CONFIG["p2"], LFO_CONFIG["p3"], LFO_CONFIG["p4"], which)
        self.panel.title.Bind(wx.EVT_LEFT_DOWN, self.onMouseDown)
        self.panel.title.Bind(wx.EVT_LEFT_UP, self.onMouseUp)
        self.panel.title.Bind(wx.EVT_MOTION, self.onMotion)
        self.synth = synth
        self.SetSize(self.FromDIP(wx.Size(267, 350)))
        self.SetMaxSize(self.GetSize())
        self.Layout()

    def onClose(self, evt):
        self.Hide()

    def onMidiLearnMode(self, evt):
        self.parent.onMidiLearnModeFromLfoFrame()

    def onMouseDown(self, evt):
        cornerPos = evt.GetPosition()
        offsetPos = self.panel.title.GetPosition()
        self.mouseOffset = (offsetPos[0]+cornerPos[0], offsetPos[1]+cornerPos[1])
        self.panel.title.CaptureMouse()

    def onMouseUp(self, evt):
        self.mouseOffset = (0, 0)
        if self.panel.title.HasCapture():
            self.panel.title.ReleaseMouse()
        wx.GetTopLevelWindows()[0].Raise()

    def onMotion(self, evt):
        if self.panel.title.HasCapture():
            pos = wx.GetMousePosition()
            self.SetPosition((pos[0] - self.mouseOffset[0], pos[1] - self.mouseOffset[1]))

    def get(self):
        params = [slider.GetValue() for slider in self.panel.sliders]
        ctl_params = [slider.midictlnumber for slider in self.panel.sliders]
        return params, ctl_params

    def set(self, params, ctl_params):
        for i, p in enumerate(params):
            slider = self.panel.sliders[i]
            slider.SetValue(p)
        slider_idx = 0
        for i, ctl_param in enumerate(ctl_params):
            slider = self.panel.sliders[i]
            slider.setMidiCtlNumber(ctl_param)
            if ctl_param is not None and vars.vars["MIDI_ACTIVE"]:
                if 'knobRadius' in slider.__dict__:
                    mini = slider.getMinValue()
                    maxi = slider.getMaxValue()
                    value = slider.GetValue()
                    if slider.log:
                        norm_init = toLog(value, mini, maxi)
                        slider.midictl = Midictl(ctl_param, 0, 1.0, norm_init)
                    else:
                        slider.midictl = Midictl(ctl_param, mini, maxi, value)
                    slider.trigFunc = TrigFunc(self.synth._midi_metro, slider.valToWidget)
                else:
                    if self.panel.synth._params[self.which] is not None:
                        self.panel.synth._params[self.which].assignLfoMidiCtl(ctl_param, slider, slider_idx)
                    slider_idx += 1


class LFOButton(GenStaticText):
    def __init__(self, parent, label=" LFO ", synth=None, which=0, callback=None):
        GenStaticText.__init__(self, parent, -1, label=label, style=wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE)
        self.parent = parent
        self.synth = synth
        self.which = which
        self.state = False
        self.callback = callback
        self.onStateBackColour = wx.Colour("#2F68D9")
        self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        self.SetForegroundColour(vars.constants["FORECOLOUR"])

        self.font, psize = self.GetFont(), self.GetFont().GetPointSize()

        self.font.SetFamily(wx.FONTFAMILY_TELETYPE)
        if not vars.constants["IS_WIN"]:
            self.font.SetWeight(wx.FONTWEIGHT_BOLD)
            self.font.SetPointSize(psize - 3)

        self.SetFont(self.font)

        self.Bind(wx.EVT_ENTER_WINDOW, self.hover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.leave)
        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.MouseRightDown)
        self.SetToolTip(wx.ToolTip("Click to enable, Right-Click to open controls"))

    def setState(self, state):
        self.state = state
        self.parent.lfo_frames[self.which].panel.synth = self.synth
        if self.state:
            self.SetBackgroundColour(self.onStateBackColour)
            self.SetForegroundColour(wx.WHITE)
        else:
            self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
            self.SetForegroundColour(vars.constants["FORECOLOUR"])
        self.callback(self.which, self.state)

    def hover(self, evt):
        if self.state:
            self.SetForegroundColour(vars.constants["BACKCOLOUR"])
            self.SetBackgroundColour(self.onStateBackColour)
        else:
            self.SetForegroundColour(vars.constants["BACKCOLOUR"])
            self.SetBackgroundColour(self.onStateBackColour)
        wx.CallAfter(self.Refresh)

    def leave(self, evt):
        if self.state:
            self.SetForegroundColour(wx.WHITE)
            self.SetBackgroundColour(self.onStateBackColour)
        else:
            self.SetForegroundColour(vars.constants["FORECOLOUR"])
            self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        wx.CallAfter(self.Refresh)

    def MouseRightDown(self, evt):
        self.parent.lfo_frames[self.which].panel.synth = self.synth
        pos = wx.GetMousePosition()
        self.parent.lfo_frames[self.which].SetPosition((pos[0]+5, pos[1]+5))
        self.parent.lfo_frames[self.which].Show()
        evt.Skip()

    def MouseDown(self, evt):
        if self.state:
            self.state = False
            self.SetForegroundColour(vars.constants["FORECOLOUR"])
            self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        else:
            self.state = True
            self.SetForegroundColour(wx.WHITE)
            self.SetBackgroundColour(self.onStateBackColour)
        self.Refresh()
        self.callback(self.which, self.state)


class ServerPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE)
        self.parent = parent
        self.SetSize(self.FromDIP(wx.Size(230, 500)))
        self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        self.SetForegroundColour(vars.constants["FORECOLOUR"])
        self.fileformat = vars.vars["FORMAT"]
        self.sampletype = vars.vars["BITS"]
        self.virtualNotePressed = {}
        self.virtualvoice = 0
        self.keyboardShown = 0
        self.serverSettings = []
        self.selected_output_driver_name = None
        self.selected_midi_interface_name = None

        self.mainBox = wx.BoxSizer(wx.VERTICAL)

        self.font, psize = self.GetFont(), self.GetFont().GetPointSize()
        if not vars.constants["IS_WIN"]:
            self.font.SetPointSize(psize-1)

        self.fsserver = FSServer()

        dropTarget = MyFileDropTarget(self)
        self.SetDropTarget(dropTarget)

        self.title = ZB_HeadTitle(self, "Server Controls")
        self.mainBox.Add(self.title, 0, wx.BOTTOM | wx.EXPAND, self.FromDIP(4))

        self.driverText = wx.StaticText(self, id=-1, label="Output Driver")
        self.mainBox.Add(self.driverText, 0, wx.LEFT, 4)

        font, psize = self.driverText.GetFont(), self.driverText.GetFont().GetPointSize()
        font.SetPointSize(psize-2)
        w, h = font.GetPixelSize()
        popsize = wx.Size((-1, h + self.FromDIP(12)))
        butsize = wx.Size((125, h + self.FromDIP(12)))

        if vars.constants["IS_MAC"]:
            self.driverText.SetFont(font)

        if vars.vars["AUDIO_HOST"] != "Jack":
            preferedDriver = vars.vars["OUTPUT_DRIVER"]
            self.driverList, self.driverIndexes = get_output_devices()
            self.defaultDriver = get_default_output()
            self.popupDriver = wx.Choice(self, id=-1, choices=self.driverList, size=popsize)
            if preferedDriver and preferedDriver in self.driverList:
                driverIndex = self.driverIndexes[self.driverList.index(preferedDriver)]
                self.fsserver.shutdown()
                self.fsserver.setOutputDevice(driverIndex)
                self.fsserver.boot()
                self.popupDriver.SetStringSelection(preferedDriver)
                self.selected_output_driver_name = preferedDriver
            elif self.defaultDriver:
                drivename = self.driverList[self.defaultDriver]
                self.popupDriver.SetStringSelection(drivename)
                self.selected_output_driver_name = drivename
            self.popupDriver.Bind(wx.EVT_CHOICE, self.changeDriver)
        else:
            self.popupDriver = wx.Choice(self, id=-1, choices=[], size=popsize)
            self.popupDriver.Disable()
        self.mainBox.Add(self.popupDriver, 0, wx.EXPAND | wx.ALL, 2)

        preferedInterface = vars.vars["MIDI_INTERFACE"]
        self.interfaceText = wx.StaticText(self, id=-1, label="Midi interface")
        if vars.constants["IS_MAC"]:
            self.interfaceText.SetFont(font)
        self.mainBox.Add(self.interfaceText, 0, wx.TOP | wx.LEFT, 4)
        self.interfaceList, self.interfaceIndexes = get_midi_input_devices()
        if len(self.interfaceList) > 0:
            self.interfaceList.append("Virtual Keyboard")
            self.defaultInterface = get_midi_default_input()
            self.popupInterface = wx.Choice(self, id=-1, choices=self.interfaceList, size=popsize)
            if preferedInterface and preferedInterface in self.interfaceList:
                if preferedInterface != "Virtual Keyboard":
                    interfaceIndex = self.interfaceIndexes[self.interfaceList.index(preferedInterface)]
                    self.fsserver.shutdown()
                    self.fsserver.setMidiInputDevice(interfaceIndex)
                    self.fsserver.boot()
                else:
                    wx.CallAfter(self.prepareForVirtualKeyboard)
                self.popupInterface.SetStringSelection(preferedInterface)
                self.selected_midi_interface_name = preferedInterface
            elif self.defaultInterface:
                self.fsserver.shutdown()
                self.fsserver.setMidiInputDevice(self.defaultInterface)
                self.fsserver.boot()
                interfacename = self.interfaceList[self.defaultInterface]
                self.popupInterface.SetStringSelection(interfacename)
                self.selected_midi_interface_name = interfacename
        else:
            self.popupInterface = wx.Choice(self, id=-1, choices=["No interface", "Virtual Keyboard"], size=popsize)
            self.popupInterface.SetSelection(1)
            wx.CallAfter(self.prepareForVirtualKeyboard)
        self.popupInterface.Bind(wx.EVT_CHOICE, self.changeInterface)
        self.mainBox.Add(self.popupInterface, 0, wx.EXPAND | wx.ALL, 2)

        row1Box = wx.BoxSizer(wx.HORIZONTAL)

        srBox = wx.BoxSizer(wx.VERTICAL)
        self.srText = wx.StaticText(self, id=-1, label="Sample Rate")
        srBox.Add(self.srText, 0, wx.TOP | wx.LEFT, 4)
        self.popupSr = wx.Choice(self, id=-1, choices=["44100", "48000", "96000"], size=popsize)
        srBox.Add(self.popupSr, 0, wx.EXPAND | wx.ALL, 2)
        self.popupSr.SetStringSelection(str(vars.vars["SR"]))
        self.serverSettings.append(self.popupSr.GetSelection())
        self.popupSr.Bind(wx.EVT_CHOICE, self.changeSr)
        polyBox = wx.BoxSizer(wx.VERTICAL)
        self.polyText = wx.StaticText(self, id=-1, label="Polyphony")
        polyBox.Add(self.polyText, 0, wx.TOP | wx.LEFT, 4)
        self.popupPoly = wx.Choice(self, id=-1, choices=[str(i) for i in range(1, 21)], size=popsize)
        polyBox.Add(self.popupPoly, 0, wx.EXPAND | wx.ALL, 2)
        self.popupPoly.SetStringSelection(str(vars.vars["POLY"]))
        self.serverSettings.append(self.popupPoly.GetSelection())
        self.popupPoly.Bind(wx.EVT_CHOICE, self.changePoly)

        row1Box.Add(srBox, 1)
        row1Box.Add(polyBox, 1)
        self.mainBox.Add(row1Box, 0, wx.EXPAND | wx.TOP, 2)

        row2Box = wx.BoxSizer(wx.HORIZONTAL)

        bitBox = wx.BoxSizer(wx.VERTICAL)
        self.bitText = wx.StaticText(self, id=-1, label="Bits")
        bitBox.Add(self.bitText, 0, wx.TOP | wx.LEFT, 4)
        self.popupBit = wx.Choice(self, id=-1, choices=["16", "24", "32"], size=popsize)
        bitBox.Add(self.popupBit, 0, wx.EXPAND | wx.ALL, 2)
        self.popupBit.SetStringSelection(str(vars.vars["BITS"]))
        self.serverSettings.append(self.popupBit.GetSelection())
        self.popupBit.Bind(wx.EVT_CHOICE, self.changeBit)
        formatBox = wx.BoxSizer(wx.VERTICAL)
        self.formatText = wx.StaticText(self, id=-1, label="Audio File Format")
        formatBox.Add(self.formatText, 0, wx.TOP | wx.LEFT, 4)
        self.popupFormat = wx.Choice(self, id=-1, choices=["wav", "aif"], size=popsize)
        formatBox.Add(self.popupFormat, 0, wx.EXPAND | wx.ALL, 2)
        self.popupFormat.SetStringSelection(vars.vars["FORMAT"])
        self.serverSettings.append(self.popupFormat.GetSelection())
        self.popupFormat.Bind(wx.EVT_CHOICE, self.changeFormat)

        row2Box.Add(bitBox, 1)
        row2Box.Add(formatBox, 1)
        self.mainBox.Add(row2Box, 0, wx.EXPAND | wx.TOP, 2)

        row3Box = wx.BoxSizer(wx.HORIZONTAL)

        onBox = wx.BoxSizer(wx.VERTICAL)
        self.onOffText = wx.StaticText(self, id=-1, label="Audio")
        onBox.Add(self.onOffText, 0, wx.TOP | wx.LEFT, 4)
        self.onOff = wx.ToggleButton(self, id=-1, label="on / off", size=butsize)
        onBox.Add(self.onOff, 0, wx.EXPAND | wx.ALL, 2)
        self.onOff.Bind(wx.EVT_TOGGLEBUTTON, self.handleAudio)
        recBox = wx.BoxSizer(wx.VERTICAL)
        self.recText = wx.StaticText(self, id=-1, label="Record to disk")
        recBox.Add(self.recText, 0, wx.TOP | wx.LEFT, 4)
        self.rec = wx.ToggleButton(self, id=-1, label="start / stop", size=butsize)
        recBox.Add(self.rec, 0, wx.EXPAND | wx.ALL, 2)
        self.rec.Bind(wx.EVT_TOGGLEBUTTON, self.handleRec)

        row3Box.Add(onBox, 1)
        row3Box.Add(recBox, 1)
        self.mainBox.Add(row3Box, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 2)

        self.textAmp = wx.StaticText(self, id=-1, label="Global Amplitude (dB)")
        self.mainBox.Add(self.textAmp, 0, wx.TOP | wx.LEFT, 4)
        self.sliderAmp = ZyneB_ControlSlider(self, -60, 18, 0, outFunction=self.changeAmp)
        self.mainBox.Add(self.sliderAmp, 0, wx.EXPAND | wx.ALL, 2)
        self.serverSettings.append(1.0)
        self.meter = ZB_VuMeter(self)
        self.mainBox.Add(self.meter, 0, wx.EXPAND | wx.ALL, 2)
        self.setAmpCallable()

        self.ppEqTitle = ZB_HeadTitle(self, "4 Bands Equalizer", togcall=self.handleOnOffEq)
        self.onOffEq = self.ppEqTitle.toggle
        self.mainBox.Add(self.ppEqTitle, 0, wx.EXPAND | wx.BOTTOM, 4)

        self.mainBox.AddSpacer(4)

        eqFreqBox = wx.BoxSizer(wx.HORIZONTAL)
        self.knobEqF1 = ZB_ControlKnob(self, 40, 250, 100, label=' Freq 1', outFunction=self.changeEqF1)
        eqFreqBox.Add(self.knobEqF1, 0, wx.LEFT | wx.RIGHT, 20)
        self.knobEqF2 = ZB_ControlKnob(self, 300, 1000, 500, label=' Freq 2', outFunction=self.changeEqF2)
        eqFreqBox.Add(self.knobEqF2, 0, wx.LEFT | wx.RIGHT, 20)
        self.knobEqF3 = ZB_ControlKnob(self, 1200, 5000, 2000, label=' Freq 3', outFunction=self.changeEqF3)
        eqFreqBox.Add(self.knobEqF3, 0, wx.LEFT | wx.RIGHT, 20)

        self.mainBox.Add(eqFreqBox, 0, wx.CENTER)

        eqGainBox = wx.BoxSizer(wx.HORIZONTAL)
        self.knobEqA1 = ZB_ControlKnob(self, -40, 18, 0, label='B1 gain', outFunction=self.changeEqA1)
        eqGainBox.Add(self.knobEqA1, 0, wx.LEFT | wx.RIGHT, 10)
        self.knobEqA2 = ZB_ControlKnob(self, -40, 18, 0, label='B2 gain', outFunction=self.changeEqA2)
        eqGainBox.Add(self.knobEqA2, 0, wx.LEFT | wx.RIGHT, 10)
        self.knobEqA3 = ZB_ControlKnob(self, -40, 18, 0, label='B3 gain', outFunction=self.changeEqA3)
        eqGainBox.Add(self.knobEqA3, 0, wx.LEFT | wx.RIGHT, 10)
        self.knobEqA4 = ZB_ControlKnob(self, -40, 18, 0, label='B4 gain', outFunction=self.changeEqA4)
        eqGainBox.Add(self.knobEqA4, 0, wx.LEFT | wx.RIGHT, 10)

        self.mainBox.Add(eqGainBox, 0, wx.CENTER | wx.BOTTOM)

        self.ppRevTitle = ZB_HeadTitle(self, "8 Delay Lines FDN Reverberation", togcall=self.handleOnOffRev)
        self.onOffRev = self.ppRevTitle.toggle
        self.mainBox.Add(self.ppRevTitle, 0, wx.EXPAND | wx.BOTTOM, 4)

        revBox = wx.BoxSizer(wx.HORIZONTAL)
        self.knobRevBal = ZB_ControlKnob(self, 0, 1, .5, label='Dry/Wet', outFunction=self.changeRevBal)
        revBox.Add(self.knobRevBal, 0, wx.LEFT | wx.RIGHT, 2)
        self.knobRevRefGain = ZB_ControlKnob(self, -40, 18, -3, label='Ref.Gain', outFunction=self.changeRevRefGain)
        revBox.Add(self.knobRevRefGain, 0, wx.LEFT | wx.RIGHT, 2)
        self.knobRevInPos = ZB_ControlKnob(self, 0., 1., .5, label='L/R Mix', outFunction=self.changeRevInPos)
        revBox.Add(self.knobRevInPos, 0, wx.LEFT | wx.RIGHT, 2)
        self.knobRevTime = ZB_ControlKnob(self, 0.01, 10, 1, label='Time', outFunction=self.changeRevTime)
        revBox.Add(self.knobRevTime, 0, wx.LEFT | wx.RIGHT, 2)
        self.knobRevRoomSize = ZB_ControlKnob(self, 0.25, 4.0, 1, label='Size', outFunction=self.changeRevRoomSize)
        revBox.Add(self.knobRevRoomSize, 0, wx.LEFT | wx.RIGHT, 2)
        self.knobRevCutOff = ZB_ControlKnob(self, 100, 10000, 5000, label='Cutoff', outFunction=self.changeRevCutOff)
        revBox.Add(self.knobRevCutOff, 0, wx.LEFT | wx.RIGHT, 2)

        self.mainBox.Add(revBox, 0, wx.CENTER)

        self.ppCompTitle = ZB_HeadTitle(self, "Dynamic Compressor", togcall=self.handleOnOffComp)
        self.onOffComp = self.ppCompTitle.toggle
        self.mainBox.Add(self.ppCompTitle, 0, wx.EXPAND | wx.BOTTOM, 4)

        self.mainBox.AddSpacer(4)

        cpKnobBox = wx.BoxSizer(wx.HORIZONTAL)
        self.knobComp1 = ZB_ControlKnob(self, -60, 0, -3, label=' Thresh', outFunction=self.changeComp1)
        cpKnobBox.Add(self.knobComp1, 0, wx.LEFT | wx.RIGHT, 10)
        self.knobComp2 = ZB_ControlKnob(self, 1, 10, 2, label=' Ratio', outFunction=self.changeComp2)
        cpKnobBox.Add(self.knobComp2, 0, wx.LEFT | wx.RIGHT, 10)
        self.knobComp3 = ZB_ControlKnob(self, 0.001, 0.5, 0.01, label='Risetime', outFunction=self.changeComp3)
        cpKnobBox.Add(self.knobComp3, 0, wx.LEFT | wx.RIGHT, 10)
        self.knobComp4 = ZB_ControlKnob(self, 0.01, 1, .1, label='Falltime', outFunction=self.changeComp4)
        cpKnobBox.Add(self.knobComp4, 0, wx.LEFT | wx.RIGHT, 10)

        self.mainBox.Add(cpKnobBox, 0, wx.CENTER)

        if not vars.constants["IS_WIN"]:
            # reduce font for OSX and linux display
            objs = [self.srText, self.popupSr, self.polyText, self.popupPoly, self.bitText,
                    self.popupBit, self.formatText, self.popupFormat,
                    self.onOffText, self.onOff, self.recText, self.rec, self.textAmp]
            if not vars.constants["IS_MAC"]:
                objs += [self.driverText, self.popupDriver, self.interfaceText, self.popupInterface]
            font, psize = self.popupPoly.GetFont(), self.popupPoly.GetFont().GetPointSize()
            font.SetPointSize(psize-2)
            for obj in objs:
                obj.SetFont(font)

        self.footer = ZB_HeadTitle(self, "")
        self.footer.SetBackgroundColour("#777780")
        self.mainBox.Add(self.footer, 0, wx.BOTTOM | wx.EXPAND, 4)

        self.SetSizerAndFit(self.mainBox)
        # self.SetMinSize(self.GetSize())

        self.popups = [self.popupDriver, self.popupInterface, self.popupSr, self.popupPoly, self.popupBit, self.popupFormat]
        self.popupsLearn = self.popups + [self.onOff, self.rec]
        self.widgets = [self.knobEqF1, self.knobEqF2, self.knobEqF3, self.knobEqA1, self.knobEqA2,
                        self.knobEqA3, self.knobEqA4, self.knobComp1, self.knobComp2, self.knobComp3, self.knobComp4,
                        self.knobRevInPos, self.knobRevTime, self.knobRevCutOff, self.knobRevBal, self.knobRevRoomSize, self.knobRevRefGain]

        self.menuIds = [vars.constants["ID"]["New"], vars.constants["ID"]["Open"], vars.constants["ID"]["MidiLearn"],
                        vars.constants["ID"]["Export"], vars.constants["ID"]["ExportChord"], vars.constants["ID"]["ExportTracks"],
                        vars.constants["ID"]["ExportChordTracks"], vars.constants["ID"]["Quit"],
                        vars.constants["ID"]["UpdateModules"], vars.constants["ID"]["CheckoutModules"]]

    def start(self):
        self.fsserver.start()

    def stop(self):
        self.fsserver.stop()

    def shutdown(self):
        self.fsserver.shutdown()

    def boot(self):
        self.fsserver.boot()

    def setAmpCallable(self):
        self.fsserver.setAmpCallable(self.meter)

    def setRecordOptions(self, dur, filename):
        fileformats = {"wav": 0, "aif": 1}
        if self.fileformat in fileformats:
            fileformat = fileformats[self.fileformat]
        else:
            fileformat = self.fileformat
        sampletypes = {16: 0, 24: 1, 32: 3}
        if self.sampletype in sampletypes:
            sampletype = sampletypes[self.sampletype]
        else:
            sampletype = self.sampletype
        self.fsserver.recordOptions(dur, filename, fileformat, sampletype)

    def reinitServer(self, sliderport, audio, serverSettings, postProcSettings):
        vars.vars["SLIDERPORT"] = sliderport
        self.fsserver.shutdown()
        self.fsserver.reinit(audio=audio)
        self.fsserver.boot()
        self.setServerSettings(serverSettings)
        self.setPostProcSettings(postProcSettings)

    def getSelectedOutputDriverName(self):
        return self.selected_output_driver_name

    def getSelectedMidiInterfaceName(self):
        return self.selected_midi_interface_name

    def getExtensionFromFileFormat(self):
        return {0: "wav", 1: "aif"}.get(self.fileformat, "wav")

    def prepareForVirtualKeyboard(self):
        evt = wx.CommandEvent(wx.EVT_CHOICE.typeId, self.popupInterface.GetId())
        evt.SetString("Virtual Keyboard")
        self.changeInterface(evt)

    def resetVirtualKeyboard(self, resetDisplay=True):
        if resetDisplay:
            self.keyboard.reset()
        else:
            modules = self.GetTopLevelParent().modules
            for pit, voice in self.virtualNotePressed.items():
                for module in modules:
                    synth = module.synth
                    synth._virtualpit[voice].setValue(pit)
                    synth._trigamp[voice].setValue(0)
            self.virtualNotePressed = {}
        self.virtualvoice = 0

    def retrigVirtualNotes(self):
        notes = self.keyboard.getCurrentNotes()
        self.resetVirtualKeyboard(resetDisplay=False)
        for note in notes:
            wx.CallLater(50, self.onKeyboard, note)

    def onKeyboard(self, note):
        try:
            pit = note[0]
            vel = note[1] / 127.
            voice = None
            if vel > 0 and pit not in self.virtualNotePressed.keys():
                vals = self.virtualNotePressed.values()
                for i in range(vars.vars["POLY"]):
                    if i not in vals:
                        break
                voice = self.virtualNotePressed[pit] = self.virtualvoice = i
            elif vel == 0 and pit in self.virtualNotePressed.keys():
                voice = self.virtualNotePressed[pit]
                del self.virtualNotePressed[pit]
            for module in self.GetTopLevelParent().modules:
                synth = module.synth
                if (synth.channel == 0 or synth.channel == note[2]) \
                        and pit >= synth.first \
                        and pit <= synth.last \
                        and (note[1] == 0 or
                            (note[1] >= synth.firstVel and note[1] <= synth.lastVel)):
                    synth._virtualpit[voice].setValue(pit)
                    synth._trigamp[voice].setValue(vel)

        except Exception as e:
            print('keyboard reset due to error', e)
            self.keyboard.reset()

    def handleAudio(self, evt):
        modules = self.GetTopLevelParent().modules
        if evt.GetInt() == 1:
            for popup in self.popups:
                popup.Disable()
            for menuId in self.menuIds:
                menuItem = self.GetTopLevelParent().menubar.FindItemById(menuId)
                if menuItem is not None:
                    menuItem.Enable(False)
            self.start()
            if self.keyboardShown:
                self.GetTopLevelParent().keyboard.SetFocus()
        else:
            self.fsserver._stRev.reset()
            for popup in self.popups:
                if popup != self.popupDriver or vars.vars["AUDIO_HOST"] != "Jack":
                    popup.Enable()
            for menuId in self.menuIds:
                menuItem = self.GetTopLevelParent().menubar.FindItemById(menuId)
                if menuItem is not None:
                    menuItem.Enable(True)
            wx.CallAfter(self.meter.setRms, *[0 for i in range(self.meter.numSliders)])
            self.setDriverSetting()

    def handleRec(self, evt):
        if evt.GetInt() == 1:
            ext = self.getExtensionFromFileFormat()
            path = os.path.join(os.path.expanduser("~"), "Desktop", f"zyne_live_rec.{ext}")
            if os.path.isfile(path):
                for i in range(1, 1000):
                    path = os.path.join(os.path.expanduser("~"), "Desktop", f"zyne_live_rec_{i}.{ext}")
                    if not os.path.isfile(path):
                        break
                else:
                    self.rec.SetValue(0)
                    wx.MessageBox("Could not generate a new file name for recording")
                    return
            self.setRecordOptions(dur=-1, filename=path)
            self.fsserver.recstart()
        else:
            self.fsserver.recstop()

    def changeAmp(self, value):
        self.fsserver.setAmp(math.pow(10.0, float(value) * 0.05))

    def getServerSettings(self):
        return [self.popupSr.GetSelection(), self.popupPoly.GetSelection(),
                self.popupBit.GetSelection(), self.popupFormat.GetSelection(),
                self.sliderAmp.GetValue()]

    def getPostProcSettings(self):
        dic = {}
        dic["EQ"] = [self.onOffEq.GetValue(), self.knobEqF1.GetValue(),
                     self.knobEqF2.GetValue(), self.knobEqF3.GetValue(),
                     self.knobEqA1.GetValue(), self.knobEqA2.GetValue(),
                     self.knobEqA3.GetValue(), self.knobEqA4.GetValue()]
        dic["Rev"] = [self.onOffRev.GetValue(),
                      self.knobRevBal.GetValue(), self.knobRevRefGain.GetValue(), self.knobRevInPos.GetValue(),
                      self.knobRevTime.GetValue(), self.knobRevRoomSize.GetValue(), self.knobRevCutOff.GetValue()]
        dic["Comp"] = [self.onOffComp.GetValue(), self.knobComp1.GetValue(),
                       self.knobComp2.GetValue(), self.knobComp3.GetValue(),
                       self.knobComp4.GetValue()]
        return dic

    def setServerSettings(self, serverSettings):
        popups = [self.popupSr, self.popupPoly, self.popupBit, self.popupFormat]
        self.setPoly(serverSettings[1]+1)
        for i, popup in enumerate(popups):
            val = serverSettings[i]
            popup.SetSelection(val)
            evt = wx.CommandEvent(wx.EVT_CHOICE.typeId, popup.GetId())
            evt.SetInt(val)
            popup.ProcessEvent(evt)
        amp = serverSettings[4]
        self.sliderAmp.SetValue(amp)
        self.resetVirtualKeyboard()

    def setPostProcSettings(self, postProcSettings):
        eq = postProcSettings["EQ"]
        comp = postProcSettings["Comp"]
        rev = postProcSettings.get("Rev", [False, 0.5, -3.0, 0.5, 1.0, 1.0, 5000.0])

        widgets = [self.onOffEq, self.knobEqF1, self.knobEqF2, self.knobEqF3,
                   self.knobEqA1, self.knobEqA2, self.knobEqA3, self.knobEqA4]
        for i, widget in enumerate(widgets):
            if i == 0:
                val = eq[i]
                widget.SetValue(val)
                evt = wx.CommandEvent(wx.EVT_CHECKBOX.typeId, widget.GetId())
                evt.SetInt(val)
                widget.ProcessEvent(evt)
            else:
                widget.SetValue(eq[i])

        widgets = [self.onOffRev, self.knobRevBal, self.knobRevRefGain, self.knobRevInPos,
                   self.knobRevTime, self.knobRevRoomSize, self.knobRevCutOff]
        for i, widget in enumerate(widgets):
            if i == 0:
                val = rev[i]
                widget.SetValue(val)
                evt = wx.CommandEvent(wx.EVT_CHECKBOX.typeId, widget.GetId())
                evt.SetInt(val)
                widget.ProcessEvent(evt)
            else:
                widget.SetValue(rev[i])

        widgets = [self.onOffComp, self.knobComp1, self.knobComp2, self.knobComp3, self.knobComp4]
        for i, widget in enumerate(widgets):
            if i == 0:
                val = comp[i]
                widget.SetValue(val)
                evt = wx.CommandEvent(wx.EVT_CHECKBOX.typeId, widget.GetId())
                evt.SetInt(val)
                widget.ProcessEvent(evt)
            else:
                widget.SetValue(comp[i])

    def setDriverSetting(self, func=None, val=0):
        mainframe = self.GetTopLevelParent()
        mainframe.panel.Freeze()
        if vars.vars["VIRTUAL"]:
            self.resetVirtualKeyboard()
        modules, params, lfo_params, ctl_params = self.GetTopLevelParent().getModulesAndParams()
        postProcSettings = self.getPostProcSettings()
        mainframe.deleteAllModules()
        self.shutdown()
        if func is not None:
            func(val)
        self.boot()
        mainframe.setModulesAndParams(modules, params, lfo_params, ctl_params)
        self.setPostProcSettings(postProcSettings)
        mainframe.panel.Thaw()
        if self.keyboardShown:
            mainframe.keyboard.SetFocus()
        else:
            self.SetFocus()

    def setDriverByString(self, s):
        self.driverList, self.driverIndexes = get_output_devices()
        if s in self.driverList:
            evt = wx.CommandEvent()
            idx = self.driverIndexes[self.driverList.index(s)]
            evt.SetInt(idx - 1)
            evt.SetString(s)
            self.changeDriver(evt)
            self.popupDriver.SetStringSelection(s)

    def changeDriver(self, evt):
        if vars.vars["AUDIO_HOST"] != "Jack":
            self.setDriverSetting(self.fsserver.setOutputDevice, self.driverIndexes[evt.GetInt()])
            self.selected_output_driver_name = evt.GetString()

    def setInterfaceByString(self, s):
        self.interfaceList, self.interfaceIndexes = get_midi_input_devices()
        if s in self.interfaceList:
            evt = wx.CommandEvent()
            idx = self.interfaceIndexes[self.interfaceList.index(s)]
            evt.SetInt(idx - 1)
            evt.SetString(s)
            self.changeInterface(evt)
            self.popupInterface.SetStringSelection(s)

    def changeInterface(self, evt):
        mainFrame = self.GetTopLevelParent()
        try:
            vars.vars["VIRTUAL"] = False
            if evt.GetString() in self.interfaceList:
                index = self.interfaceList.index(evt.GetString())
                self.selected_midi_interface_name = evt.GetString()
            else:
                index = 999
            self.setDriverSetting(self.fsserver.setMidiInputDevice, self.interfaceIndexes[index])
            if self.keyboardShown:
                self.keyboardShown = 0
                self.keyboard.reset()
                mainFrame.showKeyboard(False)
        except IndexError:
            vars.vars["VIRTUAL"] = True
            if not self.keyboardShown:
                self.keyboardShown = 1
                self.setDriverSetting()
                mainFrame.showKeyboard()

    def changeSr(self, evt):
        if evt.GetInt() == 0:
            sr = 44100
        elif evt.GetInt() == 1:
            sr = 48000
        else:
            sr = 96000
        self.setDriverSetting(self.fsserver.setSamplingRate, sr)

    def setPoly(self, poly):
        vars.vars["POLY"] = poly
        self.keyboard.setPoly(poly)

    def changePoly(self, evt):
        vars.vars["POLY"] = evt.GetInt() + 1
        self.keyboard.setPoly(vars.vars["POLY"])
        self.setDriverSetting()

    def changeBit(self, evt):
        if evt.GetString():
            self.sampletype = int(evt.GetString())

    def changeFormat(self, evt):
        self.fileformat = evt.GetInt()

    # EQ controls ###
    def handleOnOffEq(self, evt):
        if evt.GetInt() == 1:
            self.fsserver.onOffEq(1)
        else:
            self.fsserver.onOffEq(0)

    def changeEqF1(self, x):
        self.fsserver.setEqFreq(0, x)

    def changeEqF2(self, x):
        self.fsserver.setEqFreq(1, x)

    def changeEqF3(self, x):
        self.fsserver.setEqFreq(2, x)

    def changeEqA1(self, x):
        self.fsserver.setEqGain(0, math.pow(10.0, x * 0.05))

    def changeEqA2(self, x):
        self.fsserver.setEqGain(1, math.pow(10.0, x * 0.05))

    def changeEqA3(self, x):
        self.fsserver.setEqGain(2, math.pow(10.0, x * 0.05))

    def changeEqA4(self, x):
        self.fsserver.setEqGain(3, math.pow(10.0, x * 0.05))

    # Reverb controls ###
    def handleOnOffRev(self, evt):
        if evt.GetInt() == 1:
            self.fsserver.onOffRev(1)
        else:
            self.fsserver.onOffRev(0)

    def changeRevInPos(self, x):
        self.fsserver.setRevParam("inpos", x)

    def changeRevTime(self, x):
        self.fsserver.setRevParam("time", x)

    def changeRevCutOff(self, x):
        self.fsserver.setRevParam("cutoff", x)

    def changeRevBal(self, x):
        self.fsserver.setRevParam("bal", x)

    def changeRevRoomSize(self, x):
        self.fsserver.setRevParam("size", x)

    def changeRevRefGain(self, x):
        self.fsserver.setRevParam("refgain", x)

    # Compressor controls ###
    def handleOnOffComp(self, evt):
        if evt.GetInt() == 1:
            self.fsserver.onOffComp(1)
        else:
            self.fsserver.onOffComp(0)

    def changeComp1(self, x):
        self.fsserver.setCompParam("thresh", x)

    def changeComp2(self, x):
        self.fsserver.setCompParam("ratio", x)

    def changeComp3(self, x):
        self.fsserver.setCompParam("risetime", x)

    def changeComp4(self, x):
        self.fsserver.setCompParam("falltime", x)

    def midiLearn(self, state):
        mainFrame = self.GetTopLevelParent()
        learnColour = wx.Colour("#DEDEDE")
        gbcolour = vars.constants["BACKCOLOUR"]
        if state:
            self.SetBackgroundColour(learnColour)
            for widget in self.widgets:
                widget.setBackgroundColour(learnColour)
            for popup in self.popupsLearn:
                popup.Disable()
            mainFrame.menubar.FindItemById(vars.constants["ID"]["Run"]).Enable(False)
            self.fsserver.startMidiLearn()
        else:
            self.SetBackgroundColour(gbcolour)
            for widget in self.widgets:
                widget.setBackgroundColour(gbcolour)
            for popup in self.popupsLearn:
                popup.Enable()
            mainFrame.menubar.FindItemById(vars.constants["ID"]["Run"]).Enable(True)
            self.fsserver.stopMidiLearn()
            wx.CallAfter(self.setDriverSetting)
        wx.CallAfter(self.Refresh)
        if self.keyboardShown:
            mainFrame.keyboard.SetFocus()
        else:
            self.SetFocus()


class BasePanel(wx.Panel):
    def __init__(self, parent, name, title, synth, p1, p2, p3, from_lfo=False):
        wx.Panel.__init__(self, parent, style=wx.BORDER_THEME)
        self.parent = parent
        self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        self.SetForegroundColour(vars.constants["FORECOLOUR"])
        self.from_lfo = from_lfo
        self.sliders = []
        self.labels = []
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.name = name
        self.title = title

    def updateSliderTitle(self, idx, x):
        if hasattr(self, "slider_title_dicts") and self.slider_title_dicts[idx - 1] is not None:
            sep = "  -  "
            prefix = self.labels[idx].GetLabel().split(sep)[0]
            try:
                t = self.slider_title_dicts[idx - 1][int(x)]
                self.labels[idx].SetLabel(f"{prefix}{sep}{t}")
            except Exception as e:
                self.labels[idx].SetLabel(prefix)
            wx.CallAfter(self.labels[idx].Refresh)

    def SetSamples(self, path):
        defaultLabel = "No Samples - Drop Folder or Double-Click"
        fontSizeDelta = 2
        if self.synth.isSampler:
            s = ""
            if len(path) > 0:
                loaded = self.synth.loadSamples(path)
                if loaded:
                    s = os.path.split(self.synth.path)[1]
                    self.GetTopLevelParent().refreshOutputSignal()
                    self.reinitLFOS(self.getLFOParams(), True)
            if len(s) > 0:
                if self.pathText.GetLabel() == defaultLabel:
                    psize = self.pathText.GetFont().GetPointSize()
                    font = wx.Font(psize + fontSizeDelta, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
                    self.pathText.SetFont(font)
                s = s.replace('_', ' ')
            else:
                s = defaultLabel
                psize = self.pathText.GetFont().GetPointSize()
                font = wx.Font(psize - fontSizeDelta, wx.FONTFAMILY_DEFAULT, wx.ITALIC, wx.NORMAL)
                self.pathText.SetFont(font)
            if len(s) > 40:
                self.pathText.SetLabel(s[:40].strip() + '..')
                self.pathText.SetToolTip(wx.ToolTip(s))
            else:
                self.pathText.SetLabel(s)
            self.sizer.Fit(self)
            self.sizer.Layout()

    def createAdsrKnobs(self):
        self.knobSizerTop = wx.BoxSizer(wx.HORIZONTAL)
        self.knobDel = ZyneB_ControlKnob(self, 0, 60.0, 0, label='Delay', outFunction=self.changeDelay)
        self.knobSizerTop.Add(self.knobDel, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobAtt = ZyneB_ControlKnob(self, 0.001, 60.0, 0.001, log=True, label='Attack', outFunction=self.changeAttack)
        self.knobSizerTop.Add(self.knobAtt, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobDec = ZyneB_ControlKnob(self, 0.001, 60.0, 0.1, log=True, label='Decay', outFunction=self.changeDecay)
        self.knobSizerTop.Add(self.knobDec, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobSus = ZyneB_ControlKnob(self, 0.001, 1.0, 0.7, label='Sustain', outFunction=self.changeSustain)
        self.knobSizerTop.Add(self.knobSus, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobRel = ZyneB_ControlKnob(self, 0.001, 60.0, 1.0, log=True, label='Release', outFunction=self.changeRelease)
        self.knobSizerTop.Add(self.knobRel, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobExp = ZyneB_ControlKnob(self, 0.001, 3.0, 1.0, label='Slope', outFunction=self.changeExponent)
        self.knobSizerTop.Add(self.knobExp, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobSizerTop.Layout()
        self.sizer.Add(self.knobSizerTop, 0, wx.CENTER, 0)

        self.knobSizerBottom = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer.Add(self.knobSizerBottom, 0, wx.CENTER, 0)

        self.sliders.extend(
            [self.knobDel, self.knobAtt, self.knobDec, self.knobSus, self.knobRel, self.knobExp])

    def createTriggerSettings(self):

        self.triggerSizer = wx.BoxSizer(wx.VERTICAL)

        if self.synth.isSampler:
            self.row0Sizer = wx.BoxSizer(wx.HORIZONTAL)

            self.trigLoopmode = ZB_ControlKnob(self, 0, 4, 0, size=(116, 74), label='Loop Mode',
                                              integer=True, outFunction=self.SetLoopmode,
                                              displayFunction=self.SetLoopmodeDisplay)
            self.row0Sizer.Add(self.trigLoopmode, 0, wx.LEFT | wx.RIGHT, self.FromDIP(12))

            self.trigXfade = ZB_ControlKnob(self, 0, 50, 10, size=(116, 74), label='X-Fade (%)',
                                                    integer=False, outFunction=self.SetXFade)
            self.row0Sizer.Add(self.trigXfade, 0, wx.LEFT | wx.RIGHT , self.FromDIP(12))

            self.triggerSizer.Add(self.row0Sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)

            self.pathText = wx.StaticText(self, id=-1, label="")
            self.SetSamples("")
            self.pathText.Bind(wx.EVT_LEFT_DCLICK, self.openSamples)
            self.triggerSizer.Add(self.pathText, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, self.FromDIP(12))

            dropTarget = MySamplerDropTarget(self)
            self.SetDropTarget(dropTarget)


        self.row1Sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.trigChannel = ZB_ControlKnob(self, 0, 15, 0, size=(58, 74), label='Channel',
                                          integer=True, outFunction=self.SetChannel)
        self.row1Sizer.Add(self.trigChannel, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, self.FromDIP(2))

        self.trigVelRange = ZB_ControlRangeKnob(self, 1, 127, (1, 127), size=(58, 74), label='Vel Range',
                                                integer=True, outFunction=self.SetVelRange)
        self.row1Sizer.Add(self.trigVelRange, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, self.FromDIP(2))

        self.trigKeyRange = ZB_ControlRangeKnob(self, 0, 127, (0, 127), size=(58, 74), label='Key Range',
                                                integer=True, outFunction=self.SetKeyRange)
        self.row1Sizer.Add(self.trigKeyRange, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, self.FromDIP(2))

        self.trigFirstKey = ZB_ControlKnob(self, 0, 127, 0, size=(58, 74), label='First Key',
                                          integer=True, outFunction=self.SetFirstKeyPitch)
        self.row1Sizer.Add(self.trigFirstKey, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, self.FromDIP(2))

        self.triggerSizer.Add(self.row1Sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.sizer.Add(self.triggerSizer, 0, wx.BOTTOM | wx.LEFT | wx.TOP | wx.CENTER, self.FromDIP(2))
        self.sizer.Layout()

    def createSlider(self, label, value, minValue, maxValue, integer, log, callback, i=-1):
        height = 14 if vars.constants["IS_MAC"] else 16
        text = wx.StaticText(self, id=-1, label=label, size=self.FromDIP(wx.Size(-1, height)))
        self.labels.append(text)
        font, psize = text.GetFont(), text.GetFont().GetPointSize()
        if not vars.constants["IS_WIN"]:
            font.SetPointSize(psize-2)
        text.SetFont(font)
        self.sizer.Add(text, 0, wx.LEFT, self.FromDIP(5))
        self.sizer.AddSpacer(self.FromDIP(2))
        hsizer = wx.FlexGridSizer(0, 2, 3, 3)
        hsizer.AddGrowableCol(0)
        slider = ZyneB_ControlSlider(self, minValue, maxValue, value, log=log,
                                     integer=integer, outFunction=callback, label=label)
        if self.from_lfo or integer or self.synth.isSampler:
            hsizer.Add(slider, 0, wx.CENTER | wx.ALL | wx.EXPAND, 0)
        else:
            button = LFOButton(self, synth=self.synth, which=i, callback=self.startLFO)
            lfo_frame = LFOFrame(self.GetTopLevelParent(), self.synth, label, i, self)
            self.buttons[i] = button
            self.lfo_frames[i] = lfo_frame
            hsizer.Add(slider, 0, wx.CENTER | wx.ALL | wx.EXPAND, 0)
            hsizer.Add(button, 0, wx.TOP, self.FromDIP(3) if vars.constants["IS_MAC"] else self.FromDIP(1))
        self.sizer.Add(hsizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 3)
        self.sizer.AddSpacer(2)
        self.sliders.append(slider)
        return slider

    def hoverX(self, evt):
        self.close.SetBackgroundColour("#CCCCCC")
        self.Refresh()

    def leaveX(self, evt):
        self.close.SetBackgroundColour(HEADTITLE_BACK_COLOUR)
        self.Refresh()

    def MouseDown(self, evt):
        if not self.from_lfo:
            for frame in self.lfo_frames:
                if frame is not None:
                    if frame.IsShown():
                        frame.Hide()
            self.GetTopLevelParent().deleteModule(self)
        else:
            win = self.GetTopLevelParent()
            win.Hide()

    def setBackgroundColour(self, col):
        self.SetBackgroundColour(col)
        for slider in self.sliders:
            slider.setBackgroundColour(col)
        for but in self.buttons:
            if but is not None:
                but.SetBackgroundColour(col)
        self.Refresh()

    def openSamples(self, evt):
        dlg = wx.DirDialog(self, "Choose Folder with Samples...", style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path != "":
                self.SetSamples(path)
        dlg.Destroy()


class GenericPanel(BasePanel):
    def __init__(self, parent, name, title, synth, p1, p2, p3, slider_title_dicts=None):
        BasePanel.__init__(self, parent, name, title, synth, p1, p2, p3)
        self.parent = parent
        self.name, self.synth = name, synth([p1, p2, p3])
        self.mute = 1
        self.lfo_sliders = [get_lfo_init(), get_lfo_init(), get_lfo_init(), get_lfo_init(), get_lfo_init()]
        self.buttons = [None, None, None, None, None]
        self.lfo_frames = [None, None, None, None, None]
        self.channel = 0
        self.first = 0
        self.last = 127
        self.firstkey_pitch = 0
        self.loopmode = 0
        self.xfade = 0
        self.firstVel = 0
        self.lastVel = 127
        self.path = ""

        if slider_title_dicts is not None:
            self.slider_title_dicts = slider_title_dicts

        self.headPanel = wx.Panel(self)
        self.headPanel.SetBackgroundColour(HEADTITLE_BACK_COLOUR)

        self.titleSizer = wx.FlexGridSizer(1, 4, 5, 5)
        self.titleSizer.AddGrowableCol(2)

        if vars.constants["IS_WIN"]:
            self.close = wx.StaticText(self.headPanel, -1, label=" X ")
        else:
            self.close = GenStaticText(self.headPanel, -1, label=" X ")
        self.close.Bind(wx.EVT_ENTER_WINDOW, self.hoverX)
        self.close.Bind(wx.EVT_LEAVE_WINDOW, self.leaveX)
        self.close.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.close.SetToolTip(wx.ToolTip("Delete module"))

        if vars.constants["IS_WIN"]:
            self.info = wx.StaticText(self.headPanel, -1, label=" ? ")
        else:
            self.info = GenStaticText(self.headPanel, -1, label=" ? ")
        self.info.Bind(wx.EVT_ENTER_WINDOW, self.hoverInfo)
        self.info.Bind(wx.EVT_LEAVE_WINDOW, self.leaveInfo)
        self.info.Bind(wx.EVT_LEFT_DOWN, self.MouseDownInfo)
        self.info.SetToolTip(wx.ToolTip("Show module's infos"))

        if len(title) < 23:
            self.title = wx.StaticText(self.headPanel, id=-1, label=title)
        else:
            self.title = wx.StaticText(self.headPanel, id=-1, label=title[:23].strip() + '..')
            self.title.SetToolTip(wx.ToolTip(title))

        if vars.constants["IS_WIN"]:
            self.corner = wx.StaticText(self.headPanel, -1, label=" M|S ")
        else:
            self.corner = GenStaticText(self.headPanel, -1, label=" M|S ")
        # self.corner = wx.StaticText(self.headPanel, id=-1, label=" M|S ")
        self.corner.SetToolTip(wx.ToolTip("Mute / Solo. Click to toggle mute, Right+Click to toggle solo"))
        self.corner.Bind(wx.EVT_LEFT_DOWN, self.MouseDownCorner)
        self.corner.Bind(wx.EVT_RIGHT_DOWN, self.MouseRightDownCorner)
        self.corner.Bind(wx.EVT_ENTER_WINDOW, self.hoverCorner)
        self.corner.Bind(wx.EVT_LEAVE_WINDOW, self.leaveCorner)

        self.titleSizer.AddMany([
            (self.close, 0, wx.TOP | wx.LEFT, 2),
            (self.info, 0, wx.TOP | wx.LEFT, 2),
            (self.title, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.RIGHT | wx.LEFT, 2),
            (self.corner, 0, wx.TOP | wx.RIGHT, 2)])
        self.headPanel.SetSizerAndFit(self.titleSizer)
        self.sizer.Add(self.headPanel, 0, wx.BOTTOM | wx.EXPAND, 1)

        self.font = self.close.GetFont()
        if not vars.constants["IS_WIN"]:
            ptsize = self.font.GetPointSize()
            self.font.SetPointSize(ptsize - 2)
        for obj in [self.close, self.info, self.title, self.corner]:
            obj.SetFont(self.font)
            obj.SetForegroundColour(wx.WHITE)

        self.sizer.AddSpacer(8)

        self.createAdsrKnobs()

        self.sizer.AddSpacer(1)

        self.sliderAmp = self.createSlider("Amplitude", 1, 0.0001, 2, False, False, self.changeAmp, 0)
        self.tmp_amplitude = 1

        if p1[0] == "Transposition":
            self.createSlider(p1[0], p1[1], p1[2], p1[3], p1[4], p1[5], self.changeTranspo, 1)
        else:
            self.sliderP1 = self.createSlider(p1[0], p1[1], p1[2], p1[3], p1[4], p1[5], self.changeP1, 1)

        if p2[0] == "Transposition":
            self.createSlider(p2[0], p2[1], p2[2], p2[3], p2[4], p2[5], self.changeTranspo, 2)
        else:
            self.sliderP2 = self.createSlider(p2[0], p2[1], p2[2], p2[3], p2[4], p2[5], self.changeP2, 2)

        if p3[0] == "Transposition":
            self.createSlider(p3[0], p3[1], p3[2], p3[3], p3[4], p3[5], self.changeTranspo, 3)
        else:
            self.sliderP3 = self.createSlider(p3[0], p3[1], p3[2], p3[3], p3[4], p3[5], self.changeP3, 3)

        self.sliderPan = self.createSlider("Panning", .5, 0, 1, False, False, self.changePan, 4)

        if not vars.constants["IS_MAC"]:
            self.sizer.AddSpacer(4)

        self.createTriggerSettings()

        if not vars.constants["IS_MAC"]:
            self.sizer.AddSpacer(2)

        self.SetSizer(self.sizer)
        self.Layout()

    def SetLoopmodeDisplay(self, val):
        displayDict = {0: 'No Loop', 1: 'Loop forward', 2: 'Loop backward',
                       3: 'Loop back and forth', 4: 'Sustain Loop'}
        try:
            return displayDict[int(val)]
        except Exception:
            return val

    def SetLoopmode(self, x):
        if self.synth.isSampler:
            self.synth.SetLoopmode(x)
            self.loopmode = x

    def SetXFade(self, x):
        if self.synth.isSampler:
            self.synth.SetXFade(x)
            self.xfade = x

    def SetChannel(self, ch):
        self.channel = int(ch)
        self.synth.SetChannel(self.channel)

    def SetVelRange(self, r):
        self.synth.SetFirstVel(r[0])
        self.firstVel = r[0]
        self.synth.SetLastVel(r[1])
        self.lastVel = r[1]

    def SetKeyRange(self, r):
        self.synth.SetFirst(r[0])
        self.first = r[0]
        self.synth.SetLast(r[1])
        self.last = r[1]

    def SetFirstKeyPitch(self, x):
        old = self.synth.firstkey_pitch
        self.synth.SetFirstKeyPitch(x)
        self.synth._transpo.value = self.synth._transpo.value - old + x - self.first
        self.firstkey_pitch = x

    def changeP1(self, x):
        self.updateSliderTitle(1, x)
        self.synth.set(1, x)

    def changeP2(self, x):
        self.updateSliderTitle(2, x)
        self.synth.set(2, x)

    def changeP3(self, x):
        self.updateSliderTitle(3, x)
        self.synth.set(3, x)

    def changeTranspo(self, x):
        self.synth._transpo.value = x + self.synth.firstkey_pitch

    def changeDelay(self, x):
        self.synth.amp.delay = x

    def changeAttack(self, x):
        self.synth.amp.attack = x

    def changeDecay(self, x):
        self.synth.amp.decay = x

    def changeSustain(self, x):
        self.synth.amp.sustain = x

    def changeRelease(self, x):
        self.synth.amp.release = x

    def changeExponent(self, x):
        self.synth.amp.setExp(float(x))

    def changeAmp(self, x):
        self.synth._rawamp.value = x

    def changePan(self, x):
        self.synth._panner.set(x)

    def hoverCorner(self, evt):
        col = {0: "#0000CC", 1: "white", 2: "#FFAA00"}[self.mute]
        self.corner.SetForegroundColour(col)
        self.corner.SetBackgroundColour("#CCCCCC")
        self.Refresh()

    def leaveCorner(self, evt):
        col = {0: "#0000FF", 1: "white", 2: "#FF7700"}[self.mute]
        self.corner.SetForegroundColour(col)
        self.corner.SetBackgroundColour(HEADTITLE_BACK_COLOUR)
        self.Refresh()

    def MouseDownCorner(self, evt):
        if self.mute:
            self.setMute(0)
        else:
            self.setMute(1)
        self.Refresh()

    def MouseRightDownCorner(self, evt):
        if self.mute <= 1:
            self.setMute(2)
        elif self.mute == 2:
            self.setMute(1)
            for module in self.GetTopLevelParent().modules:
                if module != self:
                    module.setMute(1)
        self.Refresh()

    def hoverInfo(self, evt):
        self.info.SetBackgroundColour("#CCCCCC")
        self.Refresh()

    def leaveInfo(self, evt):
        self.info.SetBackgroundColour(HEADTITLE_BACK_COLOUR)
        self.Refresh()

    def MouseDownInfo(self, evt):
        if self.synth.__doc__ is not None:
            if vars.constants["IS_LINUX"]:
                size = (850, 600)
            else:
                size = (850, 600)
            lines = self.synth.__doc__.splitlines(True)
            win = HelpFrame(self.GetTopLevelParent(), -1, title="Module info", size=size,
                            subtitle=f"Info about {self.name} module.", lines=lines)
            win.CenterOnParent()
            win.Show(True)
        else:
            wx.LogMessage(f"No info for {self.name} module.")

    def setMute(self, mute):
        if mute == 2:
            for module in self.GetTopLevelParent().modules:
                if module != self:
                    module.setMute(0)
            self.corner.SetForegroundColour("#FF7700")
            self.synth._lfo_amp.play()
            self.sliderAmp.SetValue(self.tmp_amplitude)
            self.sliderAmp.Enable()
        elif mute == 1:
            self.corner.SetForegroundColour("white")
            self.synth._lfo_amp.play()
            self.sliderAmp.SetValue(self.tmp_amplitude)
            self.sliderAmp.Enable()
        elif mute == 0 and self.mute != 0:
            self.tmp_amplitude = self.sliderAmp.GetValue()
            self.corner.SetForegroundColour("#0000FF")
            self.synth._lfo_amp.stop()
            self.sliderAmp.SetValue(0.0001)
            self.sliderAmp.Disable()
        self.mute = mute
        self.Refresh()

    def getLFOParams(self):
        lfo_params = []
        for i in range(len(self.buttons)):
            if self.buttons[i] is None:
                lfo_params.append(get_lfo_init())
            else:
                if self.lfo_frames[i].IsShown():
                    offset = self.GetTopLevelParent().GetPosition()
                    pos = self.lfo_frames[i].GetPosition()
                    shown = (pos[0] - offset[0], pos[1] - offset[1])
                else:
                    shown = False
                params, ctl_params = self.lfo_frames[i].get()
                lfo_params.append({"state": self.buttons[i].state, "params": params,
                                   "ctl_params": ctl_params, "shown": shown})
        return lfo_params

    def startLFO(self, which, x):
        self.lfo_sliders[which]["state"] = x
        if which == 0:
            if x:
                self.synth._lfo_amp.play()
            else:
                self.synth._lfo_amp.stop()
        else:
            self.synth._params[which].start_lfo(x)

    def reinitLFOS(self, lfo_param, ctl_binding=True):
        self.lfo_sliders = lfo_param
        for i, lfo_conf in enumerate(self.lfo_sliders):
            if self.buttons[i] is not None:
                self.lfo_frames[i].panel.synth = self.buttons[i].synth
                state = lfo_conf["state"]
                self.startLFO(i, state)
                self.buttons[i].setState(state)
                if lfo_conf["shown"]:
                    offset = self.GetTopLevelParent().GetPosition()
                    pos = (lfo_conf["shown"][0] + offset[0], lfo_conf["shown"][1] + offset[1])
                    self.lfo_frames[i].SetPosition(pos)
                    self.lfo_frames[i].Show()
                if ctl_binding:
                    ctl_params = lfo_conf["ctl_params"]
                else:
                    ctl_params = [None] * len(self.lfo_frames[i].panel.sliders)
                if len(lfo_conf["params"]) == 10:  # old zy
                    lfo_conf["params"] = lfo_conf["params"][:5] + [1.] + lfo_conf["params"][5:]
                self.lfo_frames[i].set(lfo_conf["params"], ctl_params)

    def generateUniform(self):
        for i, slider in enumerate(self.sliders):
            if i == 0:
                continue
            mini = slider.getMinValue()
            maxi = slider.getMaxValue()
            if slider.integer:
                val = random.randint(mini, maxi)
            else:
                if i == 5:
                    val = random.uniform(.25, 1.5)
                elif i in [1, 2, 4]:
                    val = random.uniform(0.0, 4.0)
                else:
                    val = random.uniform(mini, maxi)
            slider.SetValue(val)
        for i, button in enumerate(self.buttons):
            if button is not None:
                state = random.choice([0, 0, 0, 1])
                button.setState(state)
                button.Refresh()
                if state == 1:
                    for j, slider in enumerate(self.lfo_frames[i].panel.sliders):
                        if j == 0:
                            continue
                        mini = slider.getMinValue()
                        maxi = slider.getMaxValue()
                        if slider.integer:
                            val = random.randint(mini, maxi)
                        else:
                            if j == 6:
                                val = random.uniform(0, 1)
                                val **= 10.0
                                val *= (maxi - mini)
                                val += mini
                            elif j in [1, 2, 4]:
                                val = random.uniform(0.0, 4.0)
                            else:
                                val = random.uniform(mini, maxi)
                        slider.SetValue(val)

    def generateTriangular(self):
        for i, slider in enumerate(self.sliders):
            if i == 0:
                continue
            mini = slider.getMinValue()
            maxi = slider.getMaxValue()
            if slider.integer:
                v1 = random.randint(mini, maxi)
                v2 = random.randint(mini, maxi)
                val = int((v1 + v2) / 2)
            else:
                if i == 5:
                    val = random.triangular(.25, 1.5)
                elif i in [1, 2, 4]:
                    val = random.triangular(0.0, 4.0)
                else:
                    val = random.triangular(mini, maxi)
            slider.SetValue(val)
        for i, button in enumerate(self.buttons):
            if button is not None:
                state = random.choice([0, 0, 0, 1])
                button.setState(state)
                button.Refresh()
                if state == 1:
                    for j, slider in enumerate(self.lfo_frames[i].panel.sliders):
                        if j == 0:
                            continue
                        mini = slider.getMinValue()
                        maxi = slider.getMaxValue()
                        if slider.integer:
                            v1 = random.randint(mini, maxi)
                            v2 = random.randint(mini, maxi)
                            val = int((v1 + v2) / 2)
                        else:
                            if j == 6:
                                val = random.triangular(0, 1)
                                val **= 10.0
                                val *= (maxi - mini)
                                val += mini
                            elif j in [1, 2, 4]:
                                val = random.triangular(0.0, 4.0)
                            else:
                                val = random.triangular(mini, maxi)
                        slider.SetValue(val)

    def generateMinimum(self):
        for i, slider in enumerate(self.sliders):
            if i == 0:
                continue
            mini = slider.getMinValue()
            maxi = slider.getMaxValue()
            if slider.integer:
                val = min([random.randint(mini, maxi) for k in range(4)])
            else:
                if i == 5:
                    val = random.uniform(.25, 1.25)
                elif i in [1, 2, 4]:
                    val = min([random.uniform(0.0, 4.0) for k in range(4)])
                else:
                    val = min([random.uniform(mini, maxi) for k in range(4)])
            slider.SetValue(val)
        for i, button in enumerate(self.buttons):
            if button is not None:
                state = random.choice([0, 0, 0, 1])
                button.setState(state)
                button.Refresh()
                if state == 1:
                    for j, slider in enumerate(self.lfo_frames[i].panel.sliders):
                        if j == 0:
                            continue
                        mini = slider.getMinValue()
                        maxi = slider.getMaxValue()
                        if slider.integer:
                            val = min([random.randint(mini, maxi) for k in range(4)])
                        else:
                            if j == 5:
                                val = min([random.uniform(0, 1) for k in range(8)])
                                val **= 10.0
                                val *= (maxi - mini)
                                val += mini
                            elif j in [1, 2, 4]:
                                val = min([random.uniform(0.0, 4.0) for k in range(4)])
                            else:
                                val = min([random.uniform(mini, maxi) for k in range(4)])
                        slider.SetValue(val)

    def jitterize(self):
        for i, slider in enumerate(self.sliders):
            if i == 0:
                continue
            mini = slider.getMinValue()
            maxi = slider.getMaxValue()
            if not slider.integer:
                off = random.uniform(.96, 1.04)
                val = slider.GetValue() * off
                if val < mini:
                    val = mini
                elif val > maxi:
                    val = maxi
                slider.SetValue(val)
        for i, button in enumerate(self.buttons):
            if button is not None:
                if button.state:
                    for j, slider in enumerate(self.lfo_frames[i].panel.sliders):
                        if j == 0:
                            continue
                        mini = slider.getMinValue()
                        maxi = slider.getMaxValue()
                        if slider.integer:
                            off = random.randint(-1, 1)
                            val = slider.GetValue() + off
                            if val < mini:
                                val = mini
                            elif val > maxi:
                                val = maxi
                        else:
                            off = random.uniform(.95, 1.05)
                            val = slider.GetValue() * off
                            if val < mini:
                                val = mini
                            elif val > maxi:
                                val = maxi
                        slider.SetValue(val)


class LFOPanel(BasePanel):
    def __init__(self, parent, name, title, synth, p1, p2, p3, p4, which):
        BasePanel.__init__(self, parent, name, title, synth, p1, p2, p3, from_lfo=True)
        self.parent = parent
        self.name, self.synth = name, synth
        self.which = which

        self.headPanel = wx.Panel(self)
        self.headPanel.SetBackgroundColour(HEADTITLE_BACK_COLOUR)

        self.titleSizer = wx.FlexGridSizer(1, 3, 5, 5)
        self.titleSizer.AddGrowableCol(1)

        if vars.constants["IS_WIN"]:
            self.close = wx.StaticText(self.headPanel, -1, label=" X ")
        else:
            self.close = GenStaticText(self.headPanel, -1, label=" X ")
        self.close.Bind(wx.EVT_ENTER_WINDOW, self.hoverX)
        self.close.Bind(wx.EVT_LEAVE_WINDOW, self.leaveX)
        self.close.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.close.SetToolTip(wx.ToolTip("Close window"))

        if vars.constants["IS_WIN"]:
            self.minfo = wx.StaticText(self.headPanel, -1, label=" ? ")
        else:
            self.minfo = GenStaticText(self.headPanel, -1, label=" ? ")
        self.minfo.Bind(wx.EVT_ENTER_WINDOW, self.hoverInfo)
        self.minfo.Bind(wx.EVT_LEAVE_WINDOW, self.leaveInfo)
        self.minfo.Bind(wx.EVT_LEFT_DOWN, self.MouseDownInfo)
        self.minfo.SetToolTip(wx.ToolTip("Click to highlight parent module"))

        if vars.constants["IS_WIN"]:
            self.title = wx.StaticText(self.headPanel, -1, label=title)
        else:
            self.title = GenStaticText(self.headPanel, -1, label=title)
        self.title.SetToolTip(wx.ToolTip("Move window"))

        self.titleSizer.AddMany([
            (self.close, 0, wx.TOP | wx.LEFT, 2),
            (self.title, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.RIGHT | wx.LEFT, 2),
            (self.minfo, 0, wx.TOP | wx.RIGHT, 2)])

        self.headPanel.SetSizerAndFit(self.titleSizer)
        self.sizer.Add(self.headPanel, 0, wx.BOTTOM | wx.EXPAND, 1)

        self.font = self.close.GetFont()

        if not vars.constants["IS_WIN"]:
            ptsize = self.font.GetPointSize()
            self.font.SetPointSize(ptsize - 2)
        for obj in [self.close, self.title, self.minfo]:
            obj.SetFont(self.font)
            obj.SetForegroundColour(wx.WHITE)

        self.createAdsrKnobs()

        self.sizer.AddSpacer(1)

        self.sliderAmp = self.createSlider("Amplitude", .1, 0, 1, False, False, self.changeAmp)
        self.sliderP1 = self.createSlider(p1[0], p1[1], p1[2], p1[3], p1[4], p1[5], self.changeP1)
        self.sliderP2 = self.createSlider(p2[0], p2[1], p2[2], p2[3], p2[4], p2[5], self.changeP2)
        self.sliderP3 = self.createSlider(p3[0], p3[1], p3[2], p3[3], p3[4], p3[5], self.changeP3)
        self.sliderP4 = self.createSlider(p4[0], p4[1], p4[2], p4[3], p4[4], p4[5], self.changeP4)

        self.SetSizer(self.sizer)
        self.Layout()

    def hoverInfo(self, evt):
        self.minfo.SetBackgroundColour("#CCCCCC")
        self.Refresh()

    def leaveInfo(self, evt):
        self.minfo.SetBackgroundColour(HEADTITLE_BACK_COLOUR)
        self.Refresh()

    def MouseDownInfo(self, evt):
        old_col = self.parent.module.GetBackgroundColour()
        self.parent.module.setBackgroundColour((43, 96, 200))
        wx.CallLater(80, self.parent.module.setBackgroundColour, old_col)

    def changeP1(self, x):
        if self.which == 0:
            self.synth._params[self.which].setSpeed(x)
        else:
            self.synth._params[self.which].lfo.setSpeed(x)

    def changeP2(self, x):
        if self.which == 0:
            self.synth._params[self.which].setType(x)
        else:
            self.synth._params[self.which].lfo.setType(int(x))
        try:
            t = WAVE_TITLES[int(x)]
        except Exception as e:
            t = ""
        wx.CallAfter(self.labels[2].SetLabel, f"Waveform  -  {t}")
        wx.CallAfter(self.Refresh)

    def changeP3(self, x):
        if self.which == 0:
            self.synth._params[self.which].setJitter(x)
        else:
            self.synth._params[self.which].lfo.setJitter(x)

    def changeP4(self, x):
        if self.which == 0:
            self.synth._params[self.which].setSharp(x)
        else:
            self.synth._params[self.which].lfo.setSharp(x)

    def changeDelay(self, x):
        if self.which == 0:
            self.synth.amp.delay = x
        else:
            self.synth._params[self.which].lfo.amp.delay = x

    def changeAttack(self, x):
        if self.which == 0:
            self.synth.amp.attack = x
        else:
            self.synth._params[self.which].lfo.amp.attack = x

    def changeDecay(self, x):
        if self.which == 0:
            self.synth.amp.decay = x
        else:
            self.synth._params[self.which].lfo.amp.decay = x

    def changeSustain(self, x):
        if self.which == 0:
            self.synth.amp.sustain = x
        else:
            self.synth._params[self.which].lfo.amp.sustain = x

    def changeRelease(self, x):
        if self.which == 0:
            self.synth.amp.release = x
        else:
            self.synth._params[self.which].lfo.amp.release = x

    def changeExponent(self, x):
        if self.which == 0:
            self.synth.amp.exp = float(x)
        else:
            self.synth._params[self.which].lfo.amp.exp = float(x)

    def changeAmp(self, x):
        if self.which == 0:
            self.synth._params[self.which].setAmp(x)
        else:
            self.synth._params[self.which].lfo.setAmp(x)


class GraphicalEnvelop(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE)
