"""
Copyright 2009-2015 Olivier Belanger - modifications by Hans-Jörg Bibiko 2022
"""
import copy
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
            "Wind": { "title": "Wind Synthesis I", "synth": WindSynth,
                    "p1": ["Rand Frequency", 1, 0.01, 20, False, True],
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

LFO_CONFIG = {"p1": ["Frequency", 4, .01, 1000, False, True],
              "p2": ["Waveform", 0, 0, 7, True, False],
              "p3": ["Jitter", 0, 0, 1, False, False],
              "p4": ["Sharpness", 0.5, 0, 1, False, False]}

LFO_INIT = {"state": False, "params": [.001, .1, .7, 1, 1, .1, 4, 0, 0, .5],
            "ctl_params": [None, None, None, None, None, None, None, None, None, None], "shown": False}


def get_lfo_init():
    return copy.deepcopy(LFO_INIT)


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
        self.which = which
        self.synth = synth
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

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel = LFOPanel(self, "LFO", f"{label} LFO", synth,
                              LFO_CONFIG["p1"], LFO_CONFIG["p2"], LFO_CONFIG["p3"], LFO_CONFIG["p4"], which)
        self.panel.title.Bind(wx.EVT_LEFT_DOWN, self.onMouseDown)
        self.panel.title.Bind(wx.EVT_LEFT_UP, self.onMouseUp)
        self.panel.title.Bind(wx.EVT_MOTION, self.onMotion)
        self.sizer.Add(self.panel, 1, wx.ALL | wx.EXPAND, 0)

        self.sizer.AddSpacer(2)

        self.sizer.SetSizeHints(self)
        self.SetSizer(self.sizer)
        self.panel.Fit()
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
        self.triggers = []
        self.keytriggers = []
        self.mainFrame = self.GetTopLevelParent()
        self.envmode = 0  # 0 := DASDR, 1 := Graphical DADSR
        self.graphAtt_pts = [(0., 0.), (.2, 0.9), (.25, 0.4), (.5, 0.4), (.7, 0.3), (1., .5)]
        self.graphRel_pts = [(0., .5), (.2, 0.4), (.4, .6), (1., 0.)]
        self.gdadsron = None
        self.sampler_path_text_ptsize = None

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
        if self.synth.isSampler:
            loaded = False
            s = "No Samples - Drop Folder or Double-Click"
            pt = self.pathText
            if self.sampler_path_text_ptsize is None:
                self.sampler_path_text_ptsize = pt.GetFont().GetPointSize() - 2
            if len(path.strip()) > 0:
                loaded = self.synth.loadSamples(path)
                if loaded:
                    s = os.path.split(self.synth.path)[1]
                    self.mainFrame.refreshOutputSignal()
                    self.reinitLFOS(self.getLFOParams(), True)
            pt.SetFont(wx.Font(self.sampler_path_text_ptsize + int(loaded),
                               wx.FONTFAMILY_DEFAULT, wx.NORMAL if loaded else wx.ITALIC, wx.NORMAL))
            s = s.replace('_', ' ')
            if len(s) > 40:
                pt.SetLabel(s[:38].strip() + '..')
                pt.SetToolTip(wx.ToolTip(s))
            else:
                pt.SetLabel(s)
            self.sizer.Fit(self)
            self.sizer.Layout()

    def createAdsrKnobs(self):
        self.attGrapher = ZB_Grapher(self, size=(-1, self.FromDIP(60)), label='Att')
        self.sizer.Add(self.attGrapher, 0, wx.CENTER | wx.EXPAND, 0)
        self.attGrapher.Bind(wx.EVT_LEAVE_WINDOW, self.leaveGraph)

        self.relGrapher = ZB_Grapher(self, size=(-1, self.FromDIP(60)), label='Rel')
        self.sizer.Add(self.relGrapher, 0, wx.CENTER | wx.EXPAND, 0)
        self.relGrapher.Bind(wx.EVT_LEAVE_WINDOW, self.leaveGraph)
        self.synth.graphAttAmp.initPanel(grapher=self.attGrapher)
        self.synth.graphRelAmp.initPanel(grapher=self.relGrapher)
        self.synth.graphAttAmp.SetList(self.graphAtt_pts)
        self.synth.graphRelAmp.SetList(self.graphRel_pts)


        self.sizer.AddSpacer(4)

        self.knobSizerG = wx.BoxSizer(wx.HORIZONTAL)

        self.knobAttDur = ZyneB_ControlKnob(self, 0.01, 120.0, 1.0, log=True, label='Att Dur', outFunction=self.changeGAttDur, precision=2)
        self.knobSizerG.Add(self.knobAttDur, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobGAttExp = ZyneB_ControlKnob(self, 0.001, 15.0, 0.38, log=True, label='Slope', outFunction=self.changeGAttExp)
        self.knobSizerG.Add(self.knobGAttExp, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobGAttMode = ZB_ControlKnob(self, 0, 3, 0, integer=True, label='Mode', outFunction=self.changeGAttMode,
                                           displayFunction=self.SetGrapherModeDisplay)
        self.knobSizerG.Add(self.knobGAttMode, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobRelDur = ZyneB_ControlKnob(self, 0.01, 120.0, 1.0, log=True, label='Rel Dur', outFunction=self.changeGRelDur, precision=2)
        self.knobSizerG.Add(self.knobRelDur, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobGRelExp = ZyneB_ControlKnob(self, 0.001, 15.0, 0.38, log=True, label='Slope', outFunction=self.changeGRelExp)
        self.knobSizerG.Add(self.knobGRelExp, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobGRelMode = ZB_ControlKnob(self, 0, 3, 0, integer=True, label='Mode', outFunction=self.changeGRelMode,
                                           displayFunction=self.SetGrapherModeDisplay)
        self.knobSizerG.Add(self.knobGRelMode, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT, 0)
        self.knobSizerG.Layout()
        self.sizer.Add(self.knobSizerG, 0, wx.CENTER, 0)

        self.gdadsr_knobs = [self.attGrapher, self.relGrapher, self.knobAttDur, self.knobRelDur, self.knobGAttExp, self.knobGRelExp,
                             self.knobGAttMode, self.knobGRelMode]
        for o in self.gdadsr_knobs:
            o.Hide()

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
        self.dadsr_knobs = [self.knobDel, self.knobAtt, self.knobDec, self.knobSus, self.knobRel, self.knobExp]

        self.knobSizerBottom = wx.BoxSizer(wx.HORIZONTAL)
        self.copyDadsr = wx.StaticText(self, id=-1, label="C")
        font, psize = self.copyDadsr.GetFont(), self.copyDadsr.GetFont().GetPointSize()
        font = wx.Font(psize-2, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        self.copyDadsr.SetFont(font)
        self.copyDadsr.Bind(wx.EVT_LEFT_DOWN, self.copyDADSR)
        self.copyDadsr.SetToolTip(wx.ToolTip("Copy DADSR settings"))
        self.copyDadsr.Bind(wx.EVT_ENTER_WINDOW, self.hoverX)
        self.copyDadsr.Bind(wx.EVT_LEAVE_WINDOW, self.leaveX)
        self.knobSizerBottom.Add(self.copyDadsr, 0, wx.LEFT | wx.RIGHT, 3)

        self.pasteDadsr = wx.StaticText(self, id=-1, label="P")
        self.pasteDadsr.SetFont(font)
        self.pasteDadsr.Bind(wx.EVT_LEFT_DOWN, self.pasteDADSR)
        self.pasteDadsr.SetToolTip(wx.ToolTip("Paste DADSR settings"))
        self.pasteDadsr.Bind(wx.EVT_ENTER_WINDOW, self.hoverX)
        self.pasteDadsr.Bind(wx.EVT_LEAVE_WINDOW, self.leaveX)
        self.knobSizerBottom.Add(self.pasteDadsr, 0, wx.LEFT | wx.RIGHT, 3)

        if self.synth.isSampler or (self.from_lfo and self.which == 0):
            pass
        else:
            self.modeDadsr = wx.StaticText(self, id=-1, label="M")
            self.modeDadsr.SetFont(font)
            self.modeDadsr.Bind(wx.EVT_LEFT_DOWN, self.toggleEnvMode)
            self.modeDadsr.SetToolTip(wx.ToolTip("Switch DADSR mode"))
            self.modeDadsr.Bind(wx.EVT_ENTER_WINDOW, self.hoverX)
            self.modeDadsr.Bind(wx.EVT_LEAVE_WINDOW, self.leaveX)
            self.knobSizerBottom.Add(self.modeDadsr, 0, wx.LEFT | wx.RIGHT, 3)

        self.knobSizerBottom.Layout()
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
            self.row0Sizer.Add(self.trigLoopmode, 0, wx.LEFT | wx.RIGHT, 0)

            self.trigXfade = ZB_ControlKnob(self, 0, 50, 10, size=(116, 74), label='X-Fade (%)',
                                                    integer=False, outFunction=self.SetXFade)
            self.row0Sizer.Add(self.trigXfade, 0, wx.LEFT | wx.RIGHT, 0)

            self.triggerSizer.Add(self.row0Sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)

            self.pathText = wx.StaticText(self, id=-1, label="")
            self.pathText.Bind(wx.EVT_LEFT_DCLICK, self.openSamples)
            self.triggerSizer.Add(self.pathText, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

            self.triggerSizer.AddSpacer(self.FromDIP(8))

            dropTarget = MySamplerDropTarget(self)
            self.SetDropTarget(dropTarget)

            self.triggers.extend([self.trigLoopmode, self.trigXfade])

            self.SetSamples("")

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

        self.keytriggers.extend([self.trigChannel, self.trigVelRange, self.trigKeyRange, self.trigFirstKey])
        self.triggers.extend(self.keytriggers)

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
        if self.from_lfo or integer or (self.synth.isSampler and i in [1, 2]):
            hsizer.Add(slider, 0, wx.CENTER | wx.ALL | wx.EXPAND, 0)
        else:
            button = LFOButton(self, synth=self.synth, which=i, callback=self.startLFO)
            lfo_frame = LFOFrame(self.mainFrame, self.synth, label, i, self)
            self.buttons[i] = button
            self.lfo_frames[i] = lfo_frame
            hsizer.Add(slider, 0, wx.CENTER | wx.ALL | wx.EXPAND, 0)
            hsizer.Add(button, 0, wx.TOP, self.FromDIP(3) if vars.constants["IS_MAC"] else self.FromDIP(1))
        self.sizer.Add(hsizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 3)
        self.sizer.AddSpacer(2)
        self.sliders.append(slider)
        return slider

    def setEnvMode(self, mode):
        self.envmode = mode
        self.handleEnvMode()

    def toggleEnvMode(self, evt):
        if self.envmode == 0:
            self.envmode = 1
        else:
            self.envmode = 0
        self.handleEnvMode()

    def handleEnvMode(self):
        if self.envmode == 1:
            self.copyDadsr.SetToolTip(wx.ToolTip("Copy DADSR settings - Click from Att, Shift-Click from Rel"))
            self.pasteDadsr.SetToolTip(wx.ToolTip("Paste DADSR settings - Click to Att, Shift-Click to Rel"))
            if self.from_lfo:
                graphAttAmp = self.synth._params[self.which].lfo.graphAttAmp
                graphRelAmp = self.synth._params[self.which].lfo.graphRelAmp
                self.synth._params[self.which].lfo.normamp.stop()
                graphAttAmp.initPanel(size=(self.GetSize()[0], self.FromDIP(60)))
                graphRelAmp.initPanel(size=(self.GetSize()[0], self.FromDIP(60)))
            else:
                graphAttAmp = self.synth.graphAttAmp
                graphRelAmp = self.synth.graphRelAmp
                self.synth.normamp.stop()
                graphAttAmp.initPanel(size=(self.GetSize()[0], self.FromDIP(60)))
                graphRelAmp.initPanel(size=(self.GetSize()[0], self.FromDIP(60)))
            for o in self.gdadsr_knobs:
                o.Show()
            for o in self.dadsr_knobs:
                o.Hide()
            graphAttAmp.show()
            graphRelAmp.show()

            if vars.vars["MIDIPITCH"] is None:
                self.gdadsron = TrigFunc(Change(self.synth._trigamp), self.triggerGdadsr, arg=list(range(vars.vars["POLY"])))
            else:
                self.gdadsron = TrigFunc(self.synth._firsttrig, self.triggerGdadsrOn, arg=list(range(len(self.synth.pitch))))
                self.gdadsroff = TrigFunc(self.synth._secondtrig, self.triggerGdadsrOff, arg=list(range(len(self.synth.pitch))))
        else:
            self.copyDadsr.SetToolTip(wx.ToolTip("Copy DADSR settings"))
            self.pasteDadsr.SetToolTip(wx.ToolTip("Paste DADSR settings"))
            if self.from_lfo:
                graphAttAmp = self.synth._params[self.which].lfo.graphAttAmp
                graphRelAmp = self.synth._params[self.which].lfo.graphRelAmp
                self.synth._params[self.which].lfo.normamp.play()
            else:
                graphAttAmp = self.synth.graphAttAmp
                graphRelAmp = self.synth.graphRelAmp
                self.synth.normamp.play()
            graphAttAmp.stop()
            graphRelAmp.stop()
            for o in self.gdadsr_knobs:
                o.Hide()
            for o in self.dadsr_knobs:
                o.Show()
            graphAttAmp.hide()
            graphRelAmp.hide()

            self.gdadsron = None
            self.gdadsroff = None

        if self.from_lfo:
            wx.CallAfter(wx.GetTopLevelWindows()[0].OnSize, wx.CommandEvent())
        else:
            wx.CallAfter(self.mainFrame.OnSize, wx.CommandEvent())

        if vars.vars["VIRTUAL"]:
            wx.GetTopLevelWindows()[0].serverPanel.keyboard.SetFocus()

    def triggerGdadsrOff(self, voice):
        if self.from_lfo:
            self.synth._params[self.which].lfo.graphAttAmp._base_objs[voice].stop()
            self.synth._params[self.which].lfo.graphRelAmp._base_objs[voice].play()
        else:
            self.synth.graphAttAmp._base_objs[voice].stop()
            self.synth.graphRelAmp._base_objs[voice].play()

    def triggerGdadsrOn(self, voice):
        if self.from_lfo:
            self.synth._params[self.which].lfo.graphAttAmp._base_objs[voice].play()
            self.synth._params[self.which].lfo.graphRelAmp._base_objs[voice].stop()
        else:
            self.synth.graphAttAmp._base_objs[voice].play()
            self.synth.graphRelAmp._base_objs[voice].stop()

    def triggerGdadsr(self, voice):
        if not hasattr(self, 'synth'):
            return
        vel = self.synth._trigamp.get(all=True)[voice]
        if self.from_lfo:
            if vel > 0.:
                self.synth._params[self.which].lfo.graphRelAmp._base_objs[voice].stop()
                self.synth._params[self.which].lfo.graphAttAmp._base_objs[voice].play()
            else:
                self.synth._params[self.which].lfo.graphAttAmp._base_objs[voice].stop()
                self.synth._params[self.which].lfo.graphRelAmp._base_objs[voice].play()
        else:
            if vel > 0.:
                self.synth.graphRelAmp._base_objs[voice].stop()
                self.synth.graphAttAmp._base_objs[voice].play()
            else:
                self.synth.graphAttAmp._base_objs[voice].stop()
                self.synth.graphRelAmp._base_objs[voice].play()

    def copyDADSR(self, evt):
        if self.envmode == 1:
            if self.from_lfo:
                if evt.ShiftDown():
                    s = self.synth._params[self.which].lfo.graphRelAmp
                else:
                    s = self.synth._params[self.which].lfo.graphAttAmp
            else:
                if evt.ShiftDown():
                    s = self.synth.graphRelAmp
                else:
                    s = self.synth.graphAttAmp
            vars.vars["DADSR_CLIPBOARD"] = ('GDADSR', s.getPoints(), s.exp)
        else:
            if self.from_lfo:
                s = self.synth._params[self.which].lfo.normamp
            else:
                s = self.synth.normamp
            vars.vars["DADSR_CLIPBOARD"] = ('DADSR', s.delay, s.attack, s.decay, s.sustain, s.release, s.exp)

    def pasteDADSR(self, evt):
        if vars.vars["DADSR_CLIPBOARD"] is None:
            return
        try:
            if  vars.vars["DADSR_CLIPBOARD"][0] == 'DADSR':
                self.knobDel.SetValue(vars.vars["DADSR_CLIPBOARD"][1])
                self.knobAtt.SetValue(vars.vars["DADSR_CLIPBOARD"][2])
                self.knobDec.SetValue(vars.vars["DADSR_CLIPBOARD"][3])
                self.knobSus.SetValue(vars.vars["DADSR_CLIPBOARD"][4])
                self.knobRel.SetValue(vars.vars["DADSR_CLIPBOARD"][5])
                self.knobExp.SetValue(vars.vars["DADSR_CLIPBOARD"][6])
            elif vars.vars["DADSR_CLIPBOARD"][0] == 'GDADSR':
                if self.from_lfo:
                    if evt.ShiftDown():
                        s = self.synth._params[self.which].lfo.graphRelAmp
                    else:
                        s = self.synth._params[self.which].lfo.graphAttAmp
                else:
                    if evt.ShiftDown():
                        s = self.synth.graphRelAmp
                    else:
                        s = self.synth.graphAttAmp
                s.SetList(vars.vars["DADSR_CLIPBOARD"][1])
                if evt.ShiftDown():
                    self.knobGRelExp.SetValue(vars.vars["DADSR_CLIPBOARD"][2])
                    self.knobRelDur.SetValue(s.duration)
                else:
                    self.knobGAttExp.SetValue(vars.vars["DADSR_CLIPBOARD"][2])
                    self.knobAttDur.SetValue(s.duration)
        except Exception as e:
            print('pasteDADSR: ', e)

    def leaveGraph(self, evt):
        evt.GetEventObject().OnLeave(evt)

    def hoverX(self, evt):
        evt.GetEventObject().SetBackgroundColour("#CCCCCC")
        self.Refresh()

    def leaveX(self, evt):
        evt.GetEventObject().SetBackgroundColour(wx.NullColour)
        self.Refresh()

    def MouseDown(self, evt):
        if not self.from_lfo:
            for frame in self.lfo_frames:
                if frame is not None:
                    if frame.IsShown():
                        frame.Hide()
            self.mainFrame.deleteModule(self)
        else:
            win = self.mainFrame
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

    def getModuleParams(self):
        gdadsr = None
        gAtt = self.synth.graphAttAmp
        gRel = self.synth.graphRelAmp
        gdadsr = [
                    self.envmode, gAtt.getPoints(), gRel.getPoints(), gAtt.exp, gRel.exp,
                    gAtt.duration, gRel.duration, gAtt.mode, gRel.mode
                ]
        return [self.name, self.mute,
                    self.channel, self.firstVel, self.lastVel,
                    self.first, self.last, self.firstkey_pitch,
                    self.loopmode, self.xfade, self.synth.path if self.synth.isSampler else "", 
                    gdadsr
                ]


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
        self.headPanel.SetBackgroundColour(vars.constants["HEADTITLE_BACKGROUND_COLOUR"])

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
        self.info.Bind(wx.EVT_ENTER_WINDOW, self.hoverX)
        self.info.Bind(wx.EVT_LEAVE_WINDOW, self.leaveX)
        self.info.Bind(wx.EVT_LEFT_DOWN, self.MouseDownInfo)
        self.info.SetToolTip(wx.ToolTip("Show module's infos"))

        if len(title) < 23:
            self.title = wx.StaticText(self.headPanel, id=-1, label=title)
        else:
            self.title = wx.StaticText(self.headPanel, id=-1, label=title[:23].strip() + '..')
            self.title.SetToolTip(wx.ToolTip(title))

        self.title.Bind(wx.EVT_LEFT_DOWN, self.selectModule)

        if vars.constants["IS_WIN"]:
            self.corner = wx.StaticText(self.headPanel, -1, label=" M|S ")
        else:
            self.corner = GenStaticText(self.headPanel, -1, label=" M|S ")
        self.corner.SetToolTip(wx.ToolTip("Mute / Solo. Click to toggle mute, Right+Click to toggle solo"))
        self.corner.Bind(wx.EVT_LEFT_DOWN, self.MouseDownCorner)
        self.corner.Bind(wx.EVT_RIGHT_DOWN, self.MouseRightDownCorner)
        self.corner.Bind(wx.EVT_ENTER_WINDOW, self.hoverX)
        self.corner.Bind(wx.EVT_LEAVE_WINDOW, self.leaveX)

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

        self.createAdsrKnobs()

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
        self.Fit()
        self.Layout()

    def SetLoopmodeDisplay(self, val):
        displayDict = {0: 'No Loop', 1: 'Loop forward', 2: 'Loop backward',
                       3: 'Loop back and forth', 4: 'Sustain Loop'}
        try:
            return displayDict[int(val)]
        except Exception:
            return val

    def SetGrapherModeDisplay(self, val):
        displayDict = {0: 'Exp', 1: 'Exp\nLoop', 2: 'Exp Inv', 3: 'Exp Inv\nLoop'}
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
        self.synth.normamp.delay = x

    def changeAttack(self, x):
        self.synth.normamp.attack = x

    def changeDecay(self, x):
        self.synth.normamp.decay = x

    def changeSustain(self, x):
        self.synth.normamp.sustain = x

    def changeRelease(self, x):
        self.synth.normamp.release = x

    def changeExponent(self, x):
        self.synth.normamp.setExp(float(x))

    def changeGAttDur(self, x):
        self.synth.graphAttAmp.setDuration(x)
        wx.CallAfter(self.attGrapher.Refresh)

    def changeGRelDur(self, x):
        self.synth.graphRelAmp.setDuration(x)
        wx.CallAfter(self.relGrapher.Refresh)

    def changeGAttMode(self, x):
        self.synth.graphAttAmp.setMode(x)

    def changeGRelMode(self, x):
        self.synth.graphRelAmp.setMode(x)

    def changeGAttExp(self, x):
        self.synth.graphAttAmp.exp = x
        self.attGrapher.exp = x
        wx.CallAfter(self.attGrapher.Refresh)

    def changeGRelExp(self, x):
        self.synth.graphRelAmp.exp = x
        self.relGrapher.exp = x
        wx.CallAfter(self.relGrapher.Refresh)

    def changeAmp(self, x):
        self.synth._rawamp.value = x

    def changePan(self, x):
        self.synth._panner.set(x)

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
            for module in self.mainFrame.modules:
                if module != self:
                    module.setMute(1)
        self.Refresh()

    def MouseDownInfo(self, evt):
        if self.synth.__doc__ is not None:
            if vars.constants["IS_LINUX"]:
                size = (850, 600)
            else:
                size = (850, 600)
            lines = self.synth.__doc__.splitlines(True)
            win = HelpFrame(self.mainFrame, -1, title="Module info", size=size,
                            subtitle=f"Info about {self.name} module.", lines=lines)
            win.CenterOnParent()
            win.Show(True)
        else:
            wx.LogMessage(f"No info for {self.name} module.")

    def selectModule(self, evt):
        if self.mainFrame.serverPanel.onOff.GetValue():
            return
        for i, module in enumerate(self.mainFrame.modules):
            if module == self:
                evt = wx.CommandEvent()
                if self.mainFrame.selected == i:
                    self.mainFrame.clearSelection(evt)
                    break
                evt.SetInt(i)
                self.mainFrame.selectNextModule(evt)
                break

    def setMute(self, mute):
        if mute == 2:
            for module in self.mainFrame.modules:
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
                    offset = self.mainFrame.GetPosition()
                    pos = self.lfo_frames[i].GetPosition()
                    shown = (pos[0] - offset[0], pos[1] - offset[1])
                else:
                    shown = False
                gdadsr = None
                if i > 0 and hasattr(self.synth._params[i].lfo, 'graphAttAmp') and self.synth._params[i].lfo.graphAttAmp.grapher is not None:
                    gAtt = self.synth._params[i].lfo.graphAttAmp
                    gRel = self.synth._params[i].lfo.graphRelAmp
                    gdadsr = (self.lfo_frames[i].panel.envmode, gAtt.getPoints(), gRel.getPoints(), gAtt.exp, gRel.exp,
                              gAtt.duration, gRel.duration, gAtt.mode, gRel.mode)
                params, ctl_params = self.lfo_frames[i].get()
                lfo_params.append({"state": self.buttons[i].state, "params": params, "gdadsr": gdadsr,
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
            envmode = self.lfo_frames[which].panel.envmode
            self.synth._params[which].start_lfo(x, envmode)

    def reinitLFOS(self, lfo_param, ctl_binding=True):
        self.lfo_sliders = lfo_param
        for i, lfo_conf in enumerate(self.lfo_sliders):
            if self.buttons[i] is not None:
                self.lfo_frames[i].panel.synth = self.buttons[i].synth
                state = lfo_conf["state"]
                self.buttons[i].setState(state)
                if lfo_conf["shown"]:
                    offset = self.mainFrame.GetPosition()
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
                if i > 0 and lfo_conf.get("gdadsr", None) is not None:
                    envmode, graphAtt_pts, graphRel_pts, graphAtt_exp, graphRel_exp, \
                    graphAtt_dur, graphRel_dur, graphAtt_mode, graphRel_mode = lfo_conf["gdadsr"]
                    self.synth._params[i].lfo.graphAttAmp.SetList(graphAtt_pts)
                    self.synth._params[i].lfo.graphRelAmp.SetList(graphRel_pts)
                    panel = self.lfo_frames[i].panel
                    panel.setEnvMode(envmode)
                    panel.knobGAttExp.SetValue(graphAtt_exp)
                    panel.knobGRelExp.SetValue(graphRel_exp)
                    panel.knobAttDur.SetValue(graphAtt_dur)
                    panel.knobRelDur.SetValue(graphRel_dur)
                    panel.knobGAttMode.SetValue(graphAtt_mode)
                    panel.knobGRelMode.SetValue(graphRel_mode)
                self.startLFO(i, state)

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
        self.headPanel.SetBackgroundColour(vars.constants["HEADTITLE_BACKGROUND_COLOUR"])

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
        self.minfo.Bind(wx.EVT_ENTER_WINDOW, self.hoverX)
        self.minfo.Bind(wx.EVT_LEAVE_WINDOW, self.leaveX)
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

        self.sliderAmp = self.createSlider("Amplitude", .1, 0, 1, False, False, self.changeAmp)
        self.sliderP1 = self.createSlider(p1[0], p1[1], p1[2], p1[3], p1[4], p1[5], self.changeP1)
        self.sliderP2 = self.createSlider(p2[0], p2[1], p2[2], p2[3], p2[4], p2[5], self.changeP2)
        self.sliderP3 = self.createSlider(p3[0], p3[1], p3[2], p3[3], p3[4], p3[5], self.changeP3)
        self.sliderP4 = self.createSlider(p4[0], p4[1], p4[2], p4[3], p4[4], p4[5], self.changeP4)

        if self.which > 0:
            self.synth._params[self.which].lfo.graphAttAmp.initPanel(grapher=self.attGrapher)
            self.synth._params[self.which].lfo.graphRelAmp.initPanel(grapher=self.relGrapher)
            self.synth._params[self.which].lfo.graphAttAmp.SetList(self.graphAtt_pts)
            self.synth._params[self.which].lfo.graphRelAmp.SetList(self.graphRel_pts)

        self.SetSizer(self.sizer)
        self.Fit()
        self.Layout()

    def MouseDownInfo(self, evt):
        p = self.parent.module.headPanel
        old_col = p.GetBackgroundColour()
        p.SetBackgroundColour(vars.constants["HIGHLIGHT_COLOUR"])
        p.Refresh()
        wx.CallLater(80, p.SetBackgroundColour, old_col)
        wx.CallLater(100, p.Refresh)

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
            self.synth.normamp.delay = x
        else:
            self.synth._params[self.which].lfo.normamp.delay = x

    def changeAttack(self, x):
        if self.which == 0:
            self.synth.normamp.attack = x
        else:
            self.synth._params[self.which].lfo.normamp.attack = x

    def changeDecay(self, x):
        if self.which == 0:
            self.synth.normamp.decay = x
        else:
            self.synth._params[self.which].lfo.normamp.decay = x

    def changeSustain(self, x):
        if self.which == 0:
            self.synth.normamp.sustain = x
        else:
            self.synth._params[self.which].lfo.normamp.sustain = x

    def changeRelease(self, x):
        if self.which == 0:
            self.synth.normamp.release = x
        else:
            self.synth._params[self.which].lfo.normamp.release = x

    def changeExponent(self, x):
        if self.which == 0:
            self.synth.normamp.exp = float(x)
        else:
            self.synth._params[self.which].lfo.normamp.exp = float(x)

    def changeAmp(self, x):
        if self.which == 0:
            self.synth._params[self.which].setAmp(x)
        else:
            self.synth._params[self.which].lfo.setAmp(x)

    def changeGAttDur(self, x):
        if self.which == 0:
            pass
        else:
            self.synth._params[self.which].lfo.graphAttAmp.setDuration(x)
            wx.CallAfter(self.attGrapher.Refresh)

    def changeGRelDur(self, x):
        if self.which == 0:
            pass
        else:
            self.synth._params[self.which].lfo.graphRelAmp.setDuration(x)
            wx.CallAfter(self.relGrapher.Refresh)

    def changeGAttMode(self, x):
        if self.which == 0:
            pass
        else:
            self.synth._params[self.which].lfo.graphAttAmp.setMode(x)

    def changeGRelMode(self, x):
        if self.which == 0:
            pass
        else:
            self.synth._params[self.which].lfo.graphRelAmp.setMode(x)

    def changeGAttExp(self, x):
        if self.which == 0:
            pass
        else:
            self.synth._params[self.which].lfo.graphAttAmp.exp = x
            self.attGrapher.exp = x
            wx.CallAfter(self.attGrapher.Refresh)

    def changeGRelExp(self, x):
        if self.which == 0:
            pass
        else:
            self.synth._params[self.which].lfo.graphRelAmp.exp = x
            self.relGrapher.exp = x
            wx.CallAfter(self.relGrapher.Refresh)

    def SetGrapherModeDisplay(self, val):
        displayDict = {0: 'Exp', 1: 'Exp\nLoop', 2: 'Exp Inv', 3: 'Exp Inv\nLoop'}
        try:
            return displayDict[int(val)]
        except Exception:
            return val


