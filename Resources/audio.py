"""
Copyright 2009-2015 Olivier Belanger - modifications by Hans-Jörg Bibiko 2022
"""
import codecs
import math
import os
import random
import time
import Resources.variables as vars
from Resources.utils import *


if vars.vars["PYO_PRECISION"] == "single":
    from pyo import *
else:
    from pyo64 import *

from .pyotools import PWM, VCO


def get_output_devices():
    return pa_get_output_devices()


def get_default_output():
    return pa_get_default_output()


def get_midi_input_devices():
    return pm_get_input_devices()


def get_midi_default_input():
    return pm_get_default_input()


class GraphicalDelAdsr(Expseg):
    def __init__(self, list=[(0,0), (1,1)], loop=False, exp=0.38, inverse=False, initToFirstVal=False, mul=1, add=0, parent=None):

        Expseg.__init__(self, list=list, loop=loop, exp=exp, inverse=inverse, initToFirstVal=initToFirstVal, mul=mul, add=add)

        self.parent = parent

        self.xlen = float(self.getPoints()[-1][0])

        ymin = float(min([x[1] for x in self.getPoints()]))
        ymax = float(max([x[1] for x in self.getPoints()]))
        if ymin == ymax:
            self.yrange = (0, ymax)
        else:
            self.yrange = (ymin, ymax)

        for i in range(len( self.getPoints())):
            x = self.getPoints()[i][0] / float(self.xlen)
            y = (self.getPoints()[i][1] - float(self.yrange[0])) / (self.yrange[1] - self.yrange[0])
            self.getPoints()[i] = (x, y)

        if parent is not None:
            self.graph(parent)

    def hide(self):
        self.parent.Hide()
        if self.parent.parent.from_lfo:
            self.parent.parent.parent.Fit()

    def show(self):
        self.parent.Show()
        if self.parent.parent.from_lfo:
            self.parent.parent.parent.Fit()

    def SetList(self, pts):
        self.parent.graphAtt_pts = pts
        self.setList(pts)

    def setSize(self, size):
        self.parent.SetMinSize(size)
        self.parent.SetMaxSize(size)
        self.parent.Fit()
        self.parent.Layout()

    def initPanel(self, parent, size=None):
        self.parent = parent
        if size is not None:
            wx.CallAfter(self.setSize, size)
        self.parent.mode = 2
        self.parent.points = self.getPoints()
        self.parent.xlen = self.xlen
        self.parent.yrange = self.yrange
        self.parent.outFunction = self.SetList
        self.parent.inverse = self.inverse
        self.parent.exp = self.exp


class FSServer:
    def __init__(self):
        self.eqOn = False
        self.revOn = False
        self.compOn = False
        self.eqFreq = [100, 500, 2000]
        self.eqGain = [1, 1, 1, 1]
        self.wasMidiActive = False
        self.server = Server(duplex=0, audio=vars.vars["AUDIO_HOST"].lower())
        self.boot()

    def scanning(self, ctlnum, midichnl):
        if vars.vars["LEARNINGSLIDER"] is not None:
            vars.vars["LEARNINGSLIDER"].setMidiCtlNumber(ctlnum)
            vars.vars["LEARNINGSLIDER"].Enable()
            vars.vars["LEARNINGSLIDER"] = None
            self.scan.reset()

    def startMidiLearn(self):
        self.shutdown()
        self.boot()
        self.scan = CtlScan2(self.scanning, False)
        self.start()

    def stopMidiLearn(self):
        self.scan.reset()
        if hasattr(self, 'scan'):
            delattr(self, 'scan')
        self.stop()
        if vars.vars["LEARNINGSLIDER"] is not None:
            vars.vars["LEARNINGSLIDER"].setMidiCtlNumber(None)
            vars.vars["LEARNINGSLIDER"].Enable()
            vars.vars["LEARNINGSLIDER"] = None
        time.sleep(.025)
        self.start()

    def start(self):
        self.server.start()

    def stop(self):
        self.server.stop()

    def shutdown(self):
        for o in ["_outComp", "_compLevel", "_compDelay", "_outRevMix", "_outRev", "_stRev",
                  "_outEqMix", "_outEq", "_fbEq", "_fbEqAmps", "_outSigMix", "_outSig", "_modMix"]:
            if hasattr(self, o):
                delattr(self, o)
        self.server.shutdown()

    def boot(self):
        self.server.boot()

        self._modMix = Sig([0, 0])
        self._outSig = Sig(self._modMix).out()
        self._outSigMix = self._outSig.mix(1)

        self._fbEqAmps = SigTo(self.eqGain, time=.1, init=self.eqGain)
        self._fbEq = FourBand(self._outSig,
                              freq1=self.eqFreq[0], freq2=self.eqFreq[1],
                              freq3=self.eqFreq[2], mul=self._fbEqAmps).stop()
        self._outEq = Mix(self._fbEq, voices=2).stop()
        self._outEqMix = self._outEq.mix(1)

        self._stRev = STRev(self._outSig, inpos=[0.0, 1.0], revtime=2,
                            cutoff=5000, bal=0.25, roomSize=1).stop()
        self._outRev = self._stRev.mix(2).stop()
        self._outRevMix = self._outRev.mix(1)

        self._compLevel = Compress(self._outSigMix, thresh=-3, ratio=2, risetime=.01,
                                   falltime=.1, lookahead=0, knee=0.5, outputAmp=True).stop()
        self._compDelay = Delay(self._outSig, delay=0.005).stop()
        self._outComp = self._compDelay * self._compLevel
        self._outComp.stop()

        vars.vars["MIDI_ACTIVE"] = self.server.getMidiActive()

        if vars.constants["IS_MAC"] and self.server._audio not in ["offline"]:
            if self.wasMidiActive and vars.vars["MIDI_ACTIVE"] == 0:
                wx.MessageBox("Lost MIDI interface")

        if vars.vars["MIDI_ACTIVE"] == 1:
            self.wasMidiActive = True

    def reinit(self, audio):
        self.server.reinit(duplex=0, audio=audio.lower())

    def setAmpCallable(self, callable):
        self.server._server.setAmpCallable(callable)

    def recstart(self):
        self.server.recstart()

    def recstop(self):
        self.server.recstop()

    def setAmp(self, amp):
        self.server.amp = amp

    def setOutputDevice(self, device):
        if vars.vars["AUDIO_HOST"] != "Jack":
            self.server.setOutputDevice(device)

    def setMidiInputDevice(self, device):
        self.server.setMidiInputDevice(device)

    def setSamplingRate(self, sr):
        self.server.setSamplingRate(sr)

    def recordOptions(self, dur, filename, fileformat, sampletype):
        self.server.recordOptions(dur=dur, filename=filename, fileformat=fileformat, sampletype=sampletype)

    def onOffEq(self, state):
        self.eqOn = bool(state)
        self.handlePostProcChain()

    def setEqFreq(self, which, freq):
        self.eqFreq[which] = freq
        if which == 0:
            self._fbEq.freq1 = freq
        elif which == 1:
            self._fbEq.freq2 = freq
        elif which == 2:
            self._fbEq.freq3 = freq

    def setEqGain(self, which, gain):
        self.eqGain[which] = gain
        self._fbEqAmps.value = self.eqGain

    def onOffRev(self, state):
        if state == 1:
            self.revOn = True
        else:
            self._stRev.reset()
            self.revOn = False
        self.handlePostProcChain()

    def setRevParam(self, param, value):
        if param == "time":
            self._stRev.revtime = value
        elif param == "inpos":
            self._stRev.inpos = [value / 2, 1 - value / 2]
        elif param == "cutoff":
            self._stRev.cutoff = value
        elif param == "bal":
            self._stRev.bal = value
        elif param == "size":
            self._stRev.roomSize = value
        elif param == "refgain":
            self._stRev.firstRefGain = value

    def onOffComp(self, state):
        self.compOn = bool(state)
        self.handlePostProcChain()

    def setCompParam(self, param, value):
        if param == "thresh":
            self._compLevel.thresh = value
        elif param == "ratio":
            self._compLevel.ratio = value
        elif param == "risetime":
            self._compLevel.risetime = value
        elif param == "falltime":
            self._compLevel.falltime = value

    def handlePostProcChain(self):

        if not self.eqOn:
            self._fbEq.stop()
            self._outEq.stop()
        if not self.revOn:
            self._stRev.stop()
            self._outRev.stop()
        if not self.compOn:
            self._compLevel.stop()
            self._compDelay.stop()
        self._outSig.play()

        if not self.eqOn and not self.revOn and not self.compOn:
            self._outSig.out()

        elif self.eqOn and not self.revOn and not self.compOn:
            self._fbEq.play()
            self._outEq.out()

        elif not self.eqOn and self.revOn and not self.compOn:
            self._stRev.input = self._outSig
            self._stRev.play()
            self._outRev.out()

        elif not self.eqOn and not self.revOn and self.compOn:
            self._compLevel.input = self._outSigMix
            self._compDelay.input = self._outSig
            self._compLevel.play()
            self._compDelay.play()
            self._outComp.out()

        elif self.eqOn and self.revOn and not self.compOn:
            self._fbEq.play()
            self._outEq.play()
            self._stRev.input = self._outEq
            self._stRev.play()
            self._outRev.out()

        elif self.eqOn and self.revOn and self.compOn:
            self._fbEq.play()
            self._outEq.play()
            self._stRev.input = self._outEq
            self._stRev.play()
            self._outRev.play()
            self._compLevel.input = self._outRevMix
            self._compDelay.input = self._outRev
            self._compLevel.play()
            self._compDelay.play()
            self._outComp.out()

        elif not self.eqOn and self.revOn and self.compOn:
            self._stRev.input = self._outSig
            self._stRev.play()
            self._outRev.play()
            self._compLevel.input = self._outRevMix
            self._compDelay.input = self._outRev
            self._compLevel.play()
            self._compDelay.play()
            self._outComp.out()

        elif self.eqOn and not self.revOn and self.compOn:
            self._fbEq.play()
            self._outEq.play()
            self._compLevel.input = self._outEqMix
            self._compDelay.input = self._outEq
            self._compLevel.play()
            self._compDelay.play()
            self._outComp.out()


class CtlBind:
    def __init__(self):
        self.last_midi_val = 0.0
        self.lfo_last_midi_vals = [0.0, 0.0, 0.0, 0.0]

    def valToWidget(self):
        val = self.midictl.get()
        if val != self.last_midi_val:
            self.last_midi_val = val
            if self.widget.log:
                val = toExp(val, self.widget.getMinValue(), self.widget.getMaxValue())
            self.widget.setValue(val)

    def valToWidget0(self):
        val = self.lfo_midictl_0.get()
        is_log = self.lfo_widget_0.log
        if val != self.lfo_last_midi_vals[0]:
            self.lfo_last_midi_vals[0] = val
            if is_log:
                val = toExp(val, self.lfo_widget_0.getMinValue(), self.lfo_widget_0.getMaxValue())
            self.lfo_widget_0.setValue(val)

    def valToWidget1(self):
        val = self.lfo_midictl_1.get()
        is_log = self.lfo_widget_1.log
        if val != self.lfo_last_midi_vals[1]:
            self.lfo_last_midi_vals[1] = val
            if is_log:
                val = toExp(val, self.lfo_widget_1.getMinValue(), self.lfo_widget_1.getMaxValue())
            self.lfo_widget_1.setValue(val)

    def valToWidget2(self):
        val = self.lfo_midictl_2.get()
        is_log = self.lfo_widget_2.log
        if val != self.lfo_last_midi_vals[2]:
            self.lfo_last_midi_vals[2] = val
            if is_log:
                val = toExp(val, self.lfo_widget_2.getMinValue(), self.lfo_widget_2.getMaxValue())
            self.lfo_widget_2.setValue(val)

    def valToWidget3(self):
        val = self.lfo_midictl_3.get()
        is_log = self.lfo_widget_3.log
        if val != self.lfo_last_midi_vals[3]:
            self.lfo_last_midi_vals[3] = val
            if is_log:
                val = toExp(val, self.lfo_widget_3.getMinValue(), self.lfo_widget_3.getMaxValue())
            self.lfo_widget_3.setValue(val)

    def assignMidiCtl(self, ctl, widget):
        if not vars.vars["MIDI_ACTIVE"]:
            return
        mini = widget.getMinValue()
        maxi = widget.getMaxValue()
        value = widget.GetValue()
        self.widget = widget
        if widget.log:
            self.midictl = Midictl(ctl, 0, 1.0, toLog(value, mini, maxi))
        else:
            self.midictl = Midictl(ctl, mini, maxi, value)
        self.trigFunc = TrigFunc(self._midi_metro, self.valToWidget)

    def assignLfoMidiCtl(self, ctl, widget, i):
        if not vars.vars["MIDI_ACTIVE"]:
            return
        mini = widget.getMinValue()
        maxi = widget.getMaxValue()
        value = widget.GetValue()
        is_log = widget.log
        if i == 0:
            self.lfo_widget_0 = widget
            if is_log:
                self.lfo_midictl_0 = Midictl(ctl, 0, 1.0, toLog(value, mini, maxi))
            else:
                self.lfo_midictl_0 = Midictl(ctl, mini, maxi, value)
            self.lfo_trigFunc_0 = TrigFunc(self._midi_metro, self.valToWidget0)
        elif i == 1:
            self.lfo_widget_1 = widget
            if is_log:
                self.lfo_midictl_1 = Midictl(ctl, 0, 1.0, toLog(value, mini, maxi))
            else:
                self.lfo_midictl_1 = Midictl(ctl, mini, maxi, value)
            self.lfo_trigFunc_1 = TrigFunc(self._midi_metro, self.valToWidget1)
        elif i == 2:
            self.lfo_widget_2 = widget
            if is_log:
                self.lfo_midictl_2 = Midictl(ctl, 0, 1.0, toLog(value, mini, maxi))
            else:
                self.lfo_midictl_2 = Midictl(ctl, mini, maxi, value)
            self.lfo_trigFunc_2 = TrigFunc(self._midi_metro, self.valToWidget2)
        elif i == 3:
            self.lfo_widget_3 = widget
            if is_log:
                self.lfo_midictl_3 = Midictl(ctl, 0, 1.0, toLog(value, mini, maxi))
            else:
                self.lfo_midictl_3 = Midictl(ctl, mini, maxi, value)
            self.lfo_trigFunc_3 = TrigFunc(self._midi_metro, self.valToWidget3)

    def __del__(self):
        for key in list(self.__dict__.keys()):
            del self.__dict__[key]
        if hasattr(self, "trigFunc"):
            del self.trigFunc
        if hasattr(self, "lfo_trigFunc_0"):
            del self.lfo_trigFunc_0
        if hasattr(self, "lfo_trigFunc_1"):
            del self.lfo_trigFunc_1
        if hasattr(self, "lfo_trigFunc_2"):
            del self.lfo_trigFunc_2
        if hasattr(self, "lfo_trigFunc_3"):
            del self.lfo_trigFunc_3


class LFOSynth(CtlBind):
    def __init__(self, rng, trigger, midi_metro, lfo_config=None):
        CtlBind.__init__(self)
        self.lfo_type = 0
        self.last_sharp = 0.5
        self.trigger = trigger
        self._midi_metro = midi_metro
        self.rawamp = SigTo(.1, vars.vars["SLIDERPORT"], .1, mul=rng)
        self.graphAttAmp = GraphicalDelAdsr(list=[(0,1), (1,1)] * vars.vars["POLY"], loop=False, mul=self.rawamp).stop()
        self.graphRelAmp = GraphicalDelAdsr(list=[(0,1), (1,1)] * vars.vars["POLY"], loop=False, mul=self.rawamp).stop()
        self.normamp = MidiDelAdsr(self.trigger, delay=0, attack=5, decay=.1, sustain=.5, release=1, mul=self.rawamp)
        self.amp = self.normamp + self.graphAttAmp + self.graphRelAmp
        self.speed = SigTo(4, vars.vars["SLIDERPORT"], 4)
        self.jitter = SigTo(0, vars.vars["SLIDERPORT"], 0)
        self.freq = Randi(min=1-self.jitter, max=1+self.jitter, freq=1, mul=self.speed)
        self.lfo = LFO(freq=self.freq, sharp=.9, type=3).stop()
        self.sigout = Sig(self.lfo * self.amp).stop()

    def play(self):
        self.rawamp.play()
        self.graphAttAmp.stop()
        self.graphRelAmp.stop()
        self.normamp.play()
        self.speed.play()
        self.jitter.play()
        self.freq.play()
        self.lfo.play()
        self.sigout.play()

    def stop(self):
        self.rawamp.stop()
        self.graphAttAmp.stop()
        self.graphRelAmp.stop()
        self.normamp.stop()
        self.speed.stop()
        self.jitter.stop()
        self.freq.stop()
        self.lfo.stop()
        self.sigout.stop()

    def sig(self):
        return self.sigout

    def setSpeed(self, x):
        self.speed.value = x

    def setType(self, x):
        self.lfo_type = int((x - 1) % 8)
        if self.lfo_type == 7:
            self.lfo.sharp = 0
        else:
            self.lfo.sharp = self.last_sharp
        self.lfo.type = self.lfo_type

    def setJitter(self, x):
        self.jitter.value = x

    def setSharp(self, x):
        if self.lfo_type != 7:
            self.lfo.sharp = x
        self.last_sharp = x

    def setAmp(self, x):
        self.rawamp.value = x

    def __del__(self):
        for key in list(self.__dict__.keys()):
            del self.__dict__[key]


class Param(CtlBind):
    def __init__(self, parent, i, conf, lfo_trigger, midi_metro):
        CtlBind.__init__(self)
        self.parent = parent
        self._midi_metro = midi_metro
        self.init, self.mini, self.maxi, self.is_int, self.is_log = conf[1], conf[2], conf[3], conf[4], conf[5]
        rng = (self.maxi - self.mini)
        if self.is_int:
            self.slider = Sig(self.init)
            setattr(self.parent, f"p{i}", self.slider)
        else:
            self.lfo = LFOSynth(rng, lfo_trigger, midi_metro)
            self.slider = SigTo(self.init, vars.vars["SLIDERPORT"], self.init, add=self.lfo.sig())
            self.out = Clip(self.slider, self.mini, self.maxi)
            setattr(self.parent, f"p{i}", self.out)

    def set(self, x):
        self.slider.value = x

    def start_lfo(self, x):
        if x:
            self.lfo.play()
        else:
            self.lfo.stop()

    def __del__(self):
        for key in list(self.__dict__.keys()):
            del self.__dict__[key]


class Panner(CtlBind):
    def __init__(self, parent, lfo_trigger, midi_metro):
        CtlBind.__init__(self)
        self.parent = parent
        self.lfo_trigger = Ceil(lfo_trigger)
        self._midi_metro = midi_metro
        self.lfo = LFOSynth(0.5, self.lfo_trigger, midi_metro)
        self.slider = SigTo(0.5, vars.vars["SLIDERPORT"], 0.5, add=self.lfo.sig())
        self.clip = Clip(self.slider, 0., 1., mul=p_math_pi_2)
        self.amp_L = Cos(self.clip)
        self.amp_R = Sin(self.clip)

    def set(self, x):
        self.slider.value = x

    def start_lfo(self, x):
        if not x:
            self.lfo.stop()
        else:
            self.lfo.play()

    def __del__(self):
        for key in list(self.__dict__.keys()):
            del self.__dict__[key]


class ParamTranspo:
    def __init__(self, parent, midi_metro):
        self.parent = parent
        self._midi_metro = midi_metro
        self.last_midi_val = 0.0

    def valToWidget(self):
        val = self.midictl.get()
        if val != self.last_midi_val:
            self.last_midi_val = val
            self.widget.setValue(val)

    def assignMidiCtl(self, ctl, widget):
        self.widget = widget
        self.midictl = Midictl(ctl, -36, 36, widget.GetValue())
        self.trigFunc = TrigFunc(self._midi_metro, self.valToWidget)

    def __del__(self):
        for key in list(self.__dict__.keys()):
            del self.__dict__[key]


class Stereofy:
    def __init__(self, sig):
        self.sig = sig
        self.outL = Delay(self.sig, delay=0, maxdelay=0.06)
        self.outR = Delay(self.sig, delay=0, maxdelay=0.06)

    def split(self):
        if random.randint(0, 1):
            self.outL.delay = 0.05
        else:
            self.outR.delay = 0.05

    def unsplit(self):
        self.outL.delay = 0
        self.outR.delay = 0


class BaseSynth:
    def __init__(self, config,  mode=1):
        self.isSampler = False
        self.module_path = vars.vars["CUSTOM_MODULES_PATH"]
        self.export_path = vars.vars["EXPORT_PATH"]
        self.scaling = {1: 1, 2: 2, 3: 0}[mode]
        self.channel = 0
        self.first = 0
        self.last = 127
        self.centralKey = 60
        self.firstkey_pitch = 0
        self.firstVel = 0
        self.lastVel = 127
        self.loopmode = 0
        self.xfade = 0

        self._midi_metro = Metro(.1).play()
        self._rawamp = SigTo(1, vars.vars["SLIDERPORT"], 1)

        if vars.vars["MIDIPITCH"] is not None:
            self._note = Sig(vars.vars["MIDIPITCH"])
            self._transpo = Sig(value=0)
            self.pitch = Snap(self._note+self._transpo, choice=list(range(12)), scale=self.scaling)
            if mode == 1:
                if type(vars.vars["MIDIPITCH"]) is list:
                    _tmp_hz = [midiToHz(x) for x in vars.vars["MIDIPITCH"]]
                else:
                    _tmp_hz = midiToHz(vars.vars["MIDIPITCH"])
                self.pitch = Sig(_tmp_hz)
            elif mode == 2:
                if type(vars.vars["MIDIPITCH"]) is list:
                    _tmp_tr = [midiToTranspo(x) for x in vars.vars["MIDIPITCH"]]
                else:
                    _tmp_tr = midiToTranspo(vars.vars["MIDIPITCH"])
                self.pitch = Sig(_tmp_tr)
            elif mode == 3:
                self.pitch = Sig(vars.vars["MIDIPITCH"])
            self._firsttrig = Trig().play()
            self._secondtrig = Trig().play(delay=vars.vars["NOTEONDUR"])
            self._trigamp = Counter(Mix([self._firsttrig, self._secondtrig]), min=0, max=2, dir=1)
            self._lfo_amp = LFOSynth(.5, self._trigamp, self._midi_metro)
            self.amp = MidiDelAdsr(self._trigamp, delay=0, attack=.001, decay=.1, sustain=.5, release=1,
                                   mul=self._rawamp*vars.vars["MIDIVELOCITY"], add=self._lfo_amp.sig())
            self.trig = Trig().play()

        elif vars.vars["VIRTUAL"]:
            self._virtualpit = Sig([0.0]*vars.vars["POLY"])
            self._trigamp = Sig([0.0]*vars.vars["POLY"])
            self._transpo = Sig(value=0)
            self.pitch = Snap(self._virtualpit+self._transpo, choice=list(range(12)), scale=self.scaling)
            self._lfo_amp = LFOSynth(.5, self._trigamp, self._midi_metro)
            self.graphAttAmp = GraphicalDelAdsr(list=[(0,1), (1,1)]*vars.vars["POLY"], loop=False, mul=self._rawamp, add=self._lfo_amp.sig()).stop()
            self.graphRelAmp = GraphicalDelAdsr(list=[(0,1), (1,1)]*vars.vars["POLY"], loop=False, mul=self._rawamp, add=self._lfo_amp.sig()).stop()
            self.normamp = MidiDelAdsr(self._trigamp, delay=0, attack=.001, decay=.1, sustain=.5, release=1,
                                   mul=self._rawamp, add=self._lfo_amp.sig())
            self.amp = self.normamp + self.graphAttAmp + self.graphRelAmp
            self.trig = Thresh(self._trigamp)

        else:
            self._note = Notein(poly=vars.vars["POLY"], scale=0, channel=self.channel,
                                first=self.first, last=self.last)
            self._transpo = Sig(value=0)
            self.pitch = Snap(self._note["pitch"]+self._transpo, choice=list(range(12)), scale=self.scaling)
            self._velrange = Between(self._note["velocity"], min=self.firstVel/127, max=self.lastVel/127+0.01)
            self._trigamp = self._note["velocity"] * self._velrange
            self._lfo_amp = LFOSynth(.5, self._trigamp, self._midi_metro)
            self.amp = MidiDelAdsr(self._trigamp, delay=0, attack=.001, decay=.1, sustain=.5, release=1,
                                   mul=self._rawamp, add=self._lfo_amp.sig())
            self.trig = Thresh(self._trigamp)

        self._panner = Panner(self, self._trigamp, self._midi_metro)
        self.panL = self._panner.amp_L
        self.panR = self._panner.amp_R

        self._params = [self._lfo_amp, None, None, None, self._panner]
        for i, conf in enumerate(config):
            i1 = i + 1
            if conf[0] != "Transposition":
                self._params[i1] = Param(self, i1, conf, self._trigamp, self._midi_metro)
            else:
                self._params[i1] = ParamTranspo(self, self._midi_metro)

    def set(self, which, x):
        self._params[which].set(x)

    def SetChannel(self, ch):
        self.channel = int(ch)
        try:
            self._note.channel = self.channel
        except Exception:
            pass

    def SetFirst(self, x):
        self.first = int(x)
        try:
            self._note.first = self.first
        except Exception:
            pass

    def SetLast(self, x):
        self.last = int(x)
        try:
            self._note.last = self.last
        except Exception:
            pass

    def SetFirstKeyPitch(self, x):
        self.firstkey_pitch = int(x)

    def SetFirstVel(self, x):
        self.firstVel = int(x)
        try:
            self._velrange.min = self.firstVel/127
        except Exception:
            pass

    def SetLastVel(self, x):
        self.lastVel = int(x)
        try:
            self._velrange.max = self.lastVel/127 + 0.01
        except Exception:
            pass

    def __del__(self):
        for key in list(self.__dict__.keys()):
            del self.__dict__[key]


class CustomFM:
    def __init__(self, pitch, ratio, index, mul):
        self.fcar = pitch * ratio
        self.fmod = pitch
        self.amod = self.fmod*index
        self.mod = Sine(self.fmod, mul=self.amod)
        self.out = Sine(self.fcar+self.mod, mul=mul)


class FmSynth(BaseSynth):
    """
    Simple frequency modulation synthesis.

    With frequency modulation, the timbre of a simple waveform is changed by
    frequency modulating it with a modulating frequency that is also in the audio
    range, resulting in a more complex waveform and a different-sounding tone.

    Parameters:

        FM Ratio : Ratio between carrier frequency and modulation frequency.
        FM Index : Represents the number of sidebands on each side of the carrier frequency.
        Lowpass Cutoff : Cutoff frequency of the lowpass filter.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config,  mode=1)
        self.indexLine = self.amp * self.p2
        self.indexrnd = Randi(min=.95, max=1.05, freq=[random.uniform(.5, 2) for i in range(4)])
        self.norm_amp = self.amp * 0.1
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.fm1 = CustomFM(self.pitch, self.p1, self.indexLine*self.indexrnd[0], mul=self.leftamp)
        self.fm2 = CustomFM(self.pitch*.997, self.p1, self.indexLine*self.indexrnd[1], mul=self.rightamp)
        self.fm3 = CustomFM(self.pitch*.995, self.p1, self.indexLine*self.indexrnd[2], mul=self.leftamp)
        self.fm4 = CustomFM(self.pitch*1.002, self.p1, self.indexLine*self.indexrnd[3], mul=self.rightamp)

        #self.fm1 = FM(carrier=self.pitch, ratio=self.p1, index=self.indexLine*self.indexrnd[0], mul=self.leftamp)
        #self.fm2 = FM(carrier=self.pitch*.997, ratio=self.p1, index=self.indexLine*self.indexrnd[1], mul=self.rightamp)
        #self.fm3 = FM(carrier=self.pitch*.995, ratio=self.p1, index=self.indexLine*self.indexrnd[2], mul=self.leftamp)
        #self.fm4 = FM(carrier=self.pitch*1.002, ratio=self.p1, index=self.indexLine*self.indexrnd[3], mul=self.rightamp)

        self.filt1 = Biquadx(self.fm1.out+self.fm3.out, freq=self.p3, q=1, type=0, stages=2).mix()
        self.filt2 = Biquadx(self.fm2.out+self.fm4.out, freq=self.p3, q=1, type=0, stages=2).mix()
        self.out = Mix([self.filt1, self.filt2], voices=2)


class AddSynth(BaseSynth):
    """
    Additive synthesis.

    Additive synthesis created by the addition of four looped sine waves.

    Parameters:

        Transposition : Transposition, in semitones, of the pitches played on the keyboard.
        Spread : Spreading factor of the sine wave frequencies.
        Feedback : Amount of output signal sent back in the waveform calculation.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.fac = Pow(list(range(1, 6)), self.p2, mul=[random.uniform(.995, 1.005) for i in range(4)])
        self.feedrnd = Randi(min=.15, max=.25, freq=[random.uniform(.5, 2) for i in range(4)])
        self.norm_amp = self.amp * 0.1
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.sine1 = SineLoop(freq=self.pitch*self.fac[0], feedback=self.p3*self.feedrnd[0], mul=self.leftamp).mix()
        self.sine2 = SineLoop(freq=self.pitch*self.fac[1], feedback=self.p3*self.feedrnd[1], mul=self.rightamp).mix()
        self.sine3 = SineLoop(freq=self.pitch*self.fac[2], feedback=self.p3*self.feedrnd[2], mul=self.leftamp).mix()
        self.sine4 = SineLoop(freq=self.pitch*self.fac[3], feedback=self.p3*self.feedrnd[3], mul=self.rightamp).mix()
        self.out = Mix([self.sine1, self.sine2, self.sine3, self.sine4], voices=2)


class WindSynth(BaseSynth):
    """
    Wind synthesis.

    Simulation of the whistling of the wind with a white noise filtered by four
    bandpass filters.

    Parameters:

        Rand frequency : Speed of filter's frequency variations.
        Rand depth : Depth of filter's frequency variations.
        Filter Q : Inverse of the filter's bandwidth. Amplitude of the whistling.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.clpit = Clip(self.pitch, min=40, max=15000)
        self.norm_amp = self.p3 * .2
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.noise = Noise(mul=self.amp*self.norm_amp)
        self.dev = Randi(min=0.-self.p2, max=self.p2, freq=self.p1*[random.uniform(.75, 1.25) for i in range(4)], add=1)
        self.filt1 = Biquadx(self.noise, freq=self.clpit*self.dev[0], q=self.p3, type=2, stages=2, mul=self.leftamp).mix()
        self.filt2 = Biquadx(self.noise, freq=self.clpit*self.dev[1], q=self.p3, type=2, stages=2, mul=self.rightamp).mix()
        self.filt3 = Biquadx(self.noise, freq=self.clpit*self.dev[2], q=self.p3, type=2, stages=2, mul=self.leftamp).mix()
        self.filt4 = Biquadx(self.noise, freq=self.clpit*self.dev[3], q=self.p3, type=2, stages=2, mul=self.rightamp).mix()
        self.out = Mix([self.filt1, self.filt2, self.filt3, self.filt4], voices=2)


class SquareMod(BaseSynth):
    """
    Square waveform modulation.

    A square waveform, with control over the number of harmonics, which is modulated
    in amplitude by itself.

    Parameters:

        Harmonics : Number of harmonics of the waveform.
        LFO frequency : Speed of the LFO modulating the amplitude.
        LFO Amplitude : Depth of the LFO modulating the amplitude.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.table = SquareTable(order=10, size=2048)
        self.change = Change(self.p1)
        self.trigChange = TrigFunc(self.change, function=self.changeOrder)
        self.lfo = Osc(table=self.table, freq=self.p2, mul=self.p3*.1, add=.1)
        self.norm_amp = self.amp * self.lfo
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.osc1 = Osc(table=self.table, freq=self.pitch, mul=self.leftamp).mix()
        self.osc2 = Osc(table=self.table, freq=self.pitch*.994, mul=self.rightamp).mix()
        self.osc3 = Osc(table=self.table, freq=self.pitch*.998, mul=self.leftamp).mix()
        self.osc4 = Osc(table=self.table, freq=self.pitch*1.003, mul=self.rightamp).mix()
        self.out = Mix([self.osc1, self.osc2, self.osc3, self.osc4], voices=2)

    def changeOrder(self):
        order = int(self.p1.get())
        self.table.order = order


class SawMod(BaseSynth):
    """
    Sawtooth waveform modulation.

    A sawtooth waveform, with control over the number of harmonics, which is
    modulated in amplitude by itself.

    Parameters:

        Harmonics : Number of harmonics of the waveform.
        LFO frequency : Speed of the LFO modulating the amplitude.
        LFO Amplitude : Depth of the LFO modulating the amplitude.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.table = SawTable(order=10, size=2048)
        self.change = Change(self.p1)
        self.trigChange = TrigFunc(self.change, function=self.changeOrder)
        self.lfo = Osc(table=self.table, freq=self.p2, mul=self.p3*.1, add=.1)
        self.norm_amp = self.amp * self.lfo
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.osc1 = Osc(table=self.table, freq=self.pitch, mul=self.leftamp).mix()
        self.osc2 = Osc(table=self.table, freq=self.pitch*.995, mul=self.rightamp).mix()
        self.osc3 = Osc(table=self.table, freq=self.pitch*.998, mul=self.leftamp).mix()
        self.osc4 = Osc(table=self.table, freq=self.pitch*1.004, mul=self.rightamp).mix()
        self.out = Mix([self.osc1, self.osc2, self.osc3, self.osc4], voices=2)

    def changeOrder(self):
        order = int(self.p1.get())
        self.table.order = order


class PulsarSynth(BaseSynth):
    """
    Pulsar synthesis.

    Pulsar synthesis is a method of electronic music synthesis based on the generation of
    trains of sonic particles. Pulsar synthesis can produce either rhythms or tones as it
    criss‐crosses perceptual time spans.

    Parameters:

        Harmonics : Number of harmonics of the waveform table.
        Transposition : Transposition, in semitones, of the pitches played on the keyboard.
        LFO Frequency : Speed of the LFO modulating the ratio waveform / silence.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.table = SawTable(order=10, size=2048)
        self.change = Change(self.p1)
        self.trigChange = TrigFunc(self.change, function=self.changeOrder)
        self.env = HannTable()
        self.lfo = Sine(freq=self.p3, mul=.25, add=.7)
        self.norm_amp = self.amp * 0.2
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.pulse1 = Pulsar(table=self.table, env=self.env, freq=self.pitch, frac=self.lfo, mul=self.leftamp).mix()
        self.pulse2 = Pulsar(table=self.table, env=self.env, freq=self.pitch*.998, frac=self.lfo, mul=self.rightamp).mix()
        self.pulse3 = Pulsar(table=self.table, env=self.env, freq=self.pitch*.997, frac=self.lfo, mul=self.leftamp).mix()
        self.pulse4 = Pulsar(table=self.table, env=self.env, freq=self.pitch*1.002, frac=self.lfo, mul=self.rightamp).mix()
        self.out = Mix([self.pulse1, self.pulse2, self.pulse3, self.pulse4], voices=2)

    def changeOrder(self):
        order = int(self.p1.get())
        self.table.order = order


class Ross(BaseSynth):
    """
    Rossler attractor.

    The Rossler attractor is a system of three non-linear ordinary differential equations.
    These differential equations define a continuous-time dynamical system that exhibits
    chaotic dynamics associated with the fractal properties of the attractor.

    Parameters:

        Chaos : Intensity of the chaotic behavior.
        Chorus depth : Depth of the deviation between the left and right channels.
        Lowpass Cutoff : Cutoff frequency of the lowpass filter.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.rosspit = Clip(self.pitch / 5000. + 0.25, min=0., max=1.)
        self.deviation = Randi(min=0.-self.p2, max=self.p2, freq=[random.uniform(2, 4) for i in range(2)], add=1)
        self.norm_amp = self.amp * 0.3
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.ross1 = Rossler(pitch=self.rosspit*self.deviation[0], chaos=self.p1, stereo=True, mul=self.leftamp)
        self.ross2 = Rossler(pitch=self.rosspit*self.deviation[1], chaos=self.p1, stereo=True, mul=self.rightamp)
        self.eq1 = EQ(self.ross1, freq=260, q=25, boost=-12)
        self.eq2 = EQ(self.ross2, freq=260, q=25, boost=-12)
        self.filt1 = Biquad(self.eq1, freq=self.p3).mix()
        self.filt2 = Biquad(self.eq2, freq=self.p3).mix()
        self.out = Mix([self.filt1, self.filt2], voices=2)


class Wave(BaseSynth):
    """
    Bandlimited waveform synthesis.

    Simple waveform synthesis with different waveform shapes. The number of harmonic of the
    waveforms is limited depending on the frequency played on the keyboard and the sampling
    rate to avoid aliasing. Waveform shapes are:
    0 = Ramp (saw up), 1 = Sawtooth, 2 = Square, 3 = Triangle
    4 = Pulse, 5 = Bipolar pulse, 6 = Sample and Hold, 7 = Modulated sine

    Parameters:

        Waveform : Waveform shape.
        Transposition : Transposition, in semitones, of the pitches played on the keyboard.
        Sharpness : The sharpness factor allows more or less harmonics in the waveform.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.change = Change(self.p1)
        self.trigChange = TrigFunc(self.change, function=self.changeWave)
        self.norm_amp = self.amp * 0.15
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.wav1 = LFO(freq=self.pitch, sharp=self.p3, type=0, mul=self.leftamp)
        self.wav2 = LFO(freq=self.pitch*.997, sharp=self.p3, type=0, mul=self.rightamp)
        self.wav3 = LFO(freq=self.pitch*1.002, sharp=self.p3, type=0, mul=self.leftamp)
        self.wav4 = LFO(freq=self.pitch*1.0045, sharp=self.p3, type=0, mul=self.rightamp)
        self.out = Mix([self.wav1.mix(), self.wav2.mix(), self.wav3.mix(), self.wav4.mix()], voices=2)

    def changeWave(self):
        typ = int(self.p1.get())
        self.wav1.type = typ
        self.wav2.type = typ
        self.wav3.type = typ
        self.wav4.type = typ


class PluckedString(BaseSynth):
    """
    Simple plucked string synthesis model.

    A Resonator network is feed with a burst of noise to simulate the behavior of a
    plucked string.

    Parameters:

        Transposition : Transposition, in semitones, of the pitches played on the keyboard.
        Duration : Length, in seconds, of the string resonance.
        Chorus depth : Depth of the frequency deviation between the left and right channels.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.deviation = Randi(min=0.-self.p3, max=self.p3, freq=[random.uniform(2, 4) for i in range(2)], add=1)
        self.table = CosTable([(0, 0), (50, 1), (300, 0), (8191, 0)])
        self.impulse = TrigEnv(self.trig, table=self.table, dur=.1)
        self.noise = Biquad(Noise(self.impulse), freq=2500)
        self.leftamp = self.amp*self.panL
        self.rightamp = self.amp*self.panR
        self.wave1 = Waveguide(self.noise, freq=self.pitch*self.deviation[0],
                               dur=self.p2, minfreq=.5, mul=self.leftamp).mix()
        self.wave2 = Waveguide(self.noise, freq=self.pitch*self.deviation[1],
                               dur=self.p2, minfreq=.5, mul=self.rightamp).mix()
        self.out = Mix([self.wave1, self.wave2], voices=2)


class Reson(BaseSynth):
    """
    Stereo resonators.

    A Resonator network feeded with a white noise.

    Parameters:

        Transposition : Transposition, in semitones, of the pitches played on the keyboard.
        Chorus depth : Depth of the frequency deviation between the left and right channels.
        Lowpass Cutoff : Cutoff frequency of the lowpass filter.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.deviation = Randi(min=0.-self.p2, max=self.p2, freq=[random.uniform(2, 4) for i in range(4)], add=1)
        self.excite = Noise(.02)
        self.leftamp = self.amp*self.panL
        self.rightamp = self.amp*self.panR
        self.wave1 = Waveguide(self.excite, freq=self.pitch*self.deviation[0], dur=30, minfreq=1, mul=self.leftamp)
        self.wave2 = Waveguide(self.excite, freq=self.pitch*self.deviation[1], dur=30, minfreq=1, mul=self.rightamp)
        self.filt1 = Biquad(self.wave1, freq=self.p3).mix()
        self.filt2 = Biquad(self.wave2, freq=self.p3).mix()
        self.out = Mix([self.filt1, self.filt2], voices=2)


class CrossFmSynth(BaseSynth):
    """
    Cross frequency modulation synthesis.

    Frequency modulation synthesis where the output of both oscillators modulates the
    frequency of the other one.

    Parameters:

        FM Ratio : Ratio between carrier frequency and modulation frequency.
        FM Index 1 : This value multiplied by the carrier frequency gives the carrier
                     amplitude for modulating the modulation oscillator frequency.
        FM Index 2 : This value multiplied by the modulation frequency gives the modulation
                     amplitude for modulating the carrier oscillator frequency.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config,  mode=1)
        self.indexLine = self.amp * self.p2
        self.indexrnd = Randi(min=.95, max=1.05, freq=[random.uniform(.5, 2) for i in range(4)])
        self.indexLine2 = self.amp * self.p3
        self.indexrnd2 = Randi(min=.95, max=1.05, freq=[random.uniform(.5, 2) for i in range(4)])
        self.norm_amp = self.amp * 0.1
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.ratio = 1 / self.p1
        self.fm1 = CrossFM(carrier=self.pitch, ratio=self.ratio, ind1=self.indexLine*self.indexrnd[0],
                           ind2=self.indexLine2*self.indexrnd2[0], mul=self.leftamp).mix()
        self.fm2 = CrossFM(carrier=self.pitch*.997, ratio=self.ratio, ind1=self.indexLine*self.indexrnd[1],
                           ind2=self.indexLine2*self.indexrnd2[1], mul=self.rightamp).mix()
        self.fm3 = CrossFM(carrier=self.pitch*.995, ratio=self.ratio, ind1=self.indexLine*self.indexrnd[2],
                           ind2=self.indexLine2*self.indexrnd2[2], mul=self.leftamp).mix()
        self.fm4 = CrossFM(carrier=self.pitch*1.002, ratio=self.ratio, ind1=self.indexLine*self.indexrnd[3],
                           ind2=self.indexLine2*self.indexrnd2[3], mul=self.rightamp).mix()
        self.filt1 = Biquad(self.fm1+self.fm3, freq=5000, q=1, type=0)
        self.filt2 = Biquad(self.fm2+self.fm4, freq=5000, q=1, type=0)
        self.out = Mix([self.filt1, self.filt2], voices=2)


class OTReson(BaseSynth):
    """
    Out of tune waveguide model with a recursive allpass network.

    A waveguide model consisting of a delay-line with a 3-stages recursive allpass filter
    which made the resonances of the waveguide out of tune.

    Parameters:

        Transposition : Transposition, in semitones, of the pitches played on the keyboard.
        Detune : Control the depth of the allpass delay-line filter, i.e. the depth of the detuning.
        Lowpass Cutoff : Cutoff frequency of the lowpass filter.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.excite = Noise(.02)
        self.leftamp = self.amp*self.panL
        self.rightamp = self.amp*self.panR
        self.wave1 = AllpassWG(self.excite, freq=self.pitch, feed=1, detune=self.p2, minfreq=1, mul=self.leftamp)
        self.wave2 = AllpassWG(self.excite, freq=self.pitch*.999, feed=1, detune=self.p2, minfreq=1, mul=self.rightamp)
        self.filt1 = Biquad(self.wave1, freq=self.p3).mix()
        self.filt2 = Biquad(self.wave2, freq=self.p3).mix()
        self.out = Mix([self.filt1, self.filt2], voices=2)


class InfiniteRev(BaseSynth):
    """
    Infinite reverb.

    An infinite reverb feeded by a short impulse of a looped sine. The impulse frequencies
    is controled by the pitches played on the keyboard.

    Parameters:

        Transposition : Transposition, in semitones, applied on the sinusoidal impulse.
        Brightness : Amount of feedback of the looped sine.
        Lowpass Cutoff : Cutoff frequency of the lowpass filter.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.table = CosTable([(0, 0), (4000, 1), (8191, 0)])
        self.feedtrig = Ceil(self.amp)
        self.feedadsr = MidiAdsr(self.feedtrig, .0001, 0.0, 1.0, 4.0)
        self.env = TrigEnv(self.trig, self.table, dur=.25, mul=.2)
        self.src1 = SineLoop(freq=self.pitch, feedback=self.p2*0.0025, mul=self.env)
        self.src2 = SineLoop(freq=self.pitch*1.002, feedback=self.p2*0.0025, mul=self.env)
        self.excite = self.src1+self.src2
        self.leftamp = self.amp*self.panL
        self.rightamp = self.amp*self.panR
        self.rev1 = WGVerb(self.excite, feedback=self.feedadsr, cutoff=15000, mul=self.leftamp)
        self.rev2 = WGVerb(self.excite, feedback=self.feedadsr, cutoff=15000, mul=self.rightamp)
        self.filt1 = Biquad(self.rev1, freq=self.p3).mix()
        self.filt2 = Biquad(self.rev2, freq=self.p3).mix()
        self.out = Mix([self.filt1, self.filt2], voices=2)


class Degradation(BaseSynth):
    """
    Signal quality reducer.

    Reduces the sampling rate and/or bit-depth of a chorused complex waveform oscillator.

    Parameters:

        Bit Depth : Signal quantization in bits.
        SR Scale : Sampling rate multiplier.
        Lowpass Cutoff : Cutoff frequency of the lowpass filter.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        #self.table = HarmTable([1,0,0,.2,0,0,.1,0,0,.07,0,0,0,.05]).normalize()
        self.table = HarmTable()
        self.leftamp = self.amp*self.panL
        self.rightamp = self.amp*self.panR
        self.src1 = Osc(table=self.table, freq=self.pitch, mul=.25)
        self.src2 = Osc(table=self.table, freq=self.pitch*0.997, mul=.25)
        self.src3 = Osc(table=self.table, freq=self.pitch*1.004, mul=.25)
        self.src4 = Osc(table=self.table, freq=self.pitch*1.0021, mul=.25)
        self.deg1 = Degrade(self.src1+self.src3, bitdepth=self.p1, srscale=self.p2, mul=self.leftamp)
        self.deg2 = Degrade(self.src2+self.src4, bitdepth=self.p1, srscale=self.p2, mul=self.rightamp)
        self.filt1 = Biquad(self.deg1, freq=self.p3).mix()
        self.filt2 = Biquad(self.deg2, freq=self.p3).mix()
        self.mix = Mix([self.filt1, self.filt2], voices=2)
        self.out = DCBlock(self.mix)


class PulseWidthModulation(BaseSynth):
    """
    Signal quality reducer.

    Reduces the sampling rate and/or bit-depth of a chorused complex waveform oscillator.

    Parameters:

        Bit Depth : Signal quantization in bits.
        SR Scale : Sampling rate multiplier.
        Lowpass Cutoff : Cutoff frequency of the lowpass filter.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.leftamp = self.amp*self.panL
        self.rightamp = self.amp*self.panR
        self.change = Change(self.p1)
        self.trigChange = TrigFunc(self.change, function=self.changeMode)
        self.fac = SigTo(1, 0.02)
        self.src = PWM(freq=self.pitch, duty=self.p2, damp=4, mul=.1)
        #self.src2 = PWM(freq=self.pitch*self.fac, duty=self.p2, damp=4, mul=.1)
        self.stereo = Stereofy(self.src)
        self.src1 = self.stereo.outL
        self.src2 = self.stereo.outR
        self.filt1 = Biquad(self.src1, freq=self.p3, mul=self.leftamp).mix()
        self.filt2 = Biquad(self.src2, freq=self.p3, mul=self.rightamp).mix()
        self.mix = Mix([self.filt1, self.filt2], voices=2)
        self.out = DCBlock(self.mix)

    def changeMode(self):
        if int(self.p1.get()):
            self.stereo.split()
            #self.fac.value = 1.0025
        else:
            self.stereo.unsplit()
            #self.fac.value = 1.


class VoltageControlledOsc(BaseSynth):
    """
    Signal quality reducer.

    Reduces the sampling rate and/or bit-depth of a chorused complex waveform oscillator.

    Parameters:

        Bit Depth : Signal quantization in bits.
        SR Scale : Sampling rate multiplier.
        Lowpass Cutoff : Cutoff frequency of the lowpass filter.

    ____________________________________________________________________________
    Author : Olivier Bélanger - 2011
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.leftamp = self.amp*self.panL
        self.rightamp = self.amp*self.panR
        self.src = VCO(freq=self.pitch, shape=self.p2, damp=4, mul=.1)
        self.filt1 = Biquad(self.src, freq=self.p3, mul=self.leftamp).mix()
        self.filt2 = Biquad(self.src, freq=self.p3, mul=self.rightamp).mix()
        self.mix = Mix([self.filt1, self.filt2], voices=2)
        self.out = DCBlock(self.mix)


class ZB_Sampler(BaseSynth):
    """
    Sampler and Looper.

    Parameters:

    ____________________________________________________________________________
    Author : Hans-Jörg Bibiko - 2022
    ____________________________________________________________________________
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=3)
        self.isSampler = True
        self.loops = {}
        self.path = ""

        self.loopmode = 0
        self.starttime = 0.
        self.duration = 0.
        self.xfade = 0
        self.samplerpitch = 1.
        self.out = 0.

    def stoploop(self, voice):
        pit = int(self.pitch.get(all=True)[voice])
        if pit in self.loops:
            self.loops[pit].stop()
            if isinstance(self.loops[pit].mul, MidiDelAdsr):
                self.loops[pit].mul.setInput([Sig(0.)] * 2, 0.)

    def playloop(self, voice):
        pit = int(self.pitch.get(all=True)[voice])
        vel = self._trigamp.get(all=True)[voice]
        if vel == 0.:
            self.stoploop(voice)
            return
        if pit in self.loops:
            o = self.loops[pit]
            o.reset()
            o.start = o.table.getDur() * self.starttime
            if self.duration == 0:
                o.dur = o.table.getDur()
            else:
                o.dur = o.table.getDur() * self.duration
            if self.loopmode == 0:
                o.xfade = [0, 0]
            else:
                o.xfade = [self.xfade] * 2
            o.mode = self.loopmode
            o.pitch = [self.samplerpitch] * 2
            if isinstance(o.mul, MidiDelAdsr):
                o.mul.stop()
                o.mul = 1.
            env = MidiDelAdsr([Sig(vel)] * 2, delay=self.amp.delay, attack=self.amp.attack, decay=self.amp.decay,
                           sustain=self.amp.sustain, release=self.amp.release, mul=self._rawamp * 0.5,
                           add=[self._lfo_amp.sig()] * 2)
            env.setExp(self.amp.exp)
            o.mul = env
            o.play(delay=self.amp.delay)
            o.setStopDelay(self.amp.release + .001)

    def set(self, which, x):
        if which == 1:
            self.starttime = x
            for o in self.loops.values():
                o.start = o.table.getDur() * x
        elif which == 2:
            self.duration = x
            for o in self.loops.values():
                if x > 0:
                    o.dur = o.table.getDur() * x
                else:
                    o.dur = o.table.getDur()
        elif which == 3:
            self.samplerpitch = x + self.p3

    def SetLoopmode(self, x):
        self.loopmode = int(x)
        if x > 0:
            for o in self.loops.values():
                o.mode = x
        else:
            for o in self.loops.values():
                o.mode = x
                o.xfade = 0.
                self.xfade = 0.

    def SetXFade(self, x):
        self.xfade = int(x)
        if self.loopmode > 0:
            for o in self.loops.values():
                o.xfade = x
        else:
            for o in self.loops.values():
                o.xfade = 0.
                self.xfade = 0.

    def loadSamples(self, foldername):

        if not os.path.isdir(foldername):
            return False

        self.path = foldername
        self.loops = {}

        for f in [f for f in os.listdir(self.path) if f[-4:].lower() in [".wav", ".aif"]]:
            try:
                key_index = int(f.split('_')[0])
            except Exception:
                continue
            if key_index >= 0 and key_index < 128:
                self.loops[key_index] = Looper(table=SndTable(os.path.join(self.path, f)),
                                               xfadeshape=0, startfromloop=True, autosmooth=True).stop()

        if len(self.loops.keys()) == 0:
            return False

        self.ton = TrigFunc(Change(self._trigamp), self.playloop, arg=list(range(vars.vars["POLY"])))

        self.out = Mix([o for o in self.loops.values()], voices=2,
                       mul=[Sig(self._panner.amp_L), Sig(self._panner.amp_R)]).out()

        return True

    def __del__(self):
        if hasattr(self, 'loops'):
            for o in self.loops.values():
                if isinstance(o.mul, MidiDelAdsr):
                    o.mul.stop()
                    o.mul = 1.
                o.setStopDelay(0.)
                o.stop()
        for key in list(self.__dict__.keys()):
            del self.__dict__[key]


def checkForCustomModules():
    vars.readPreferencesFile()
    path = vars.vars["CUSTOM_MODULES_PATH"]
    if len(path.strip()) > 0:
        if os.path.isdir(path):
            files = [f for f in os.listdir(path) if f.endswith(".py")]
            for file in files:
                try:
                    filepath = os.path.join(path, file)
                    with open(filepath, "r") as f:
                        exec(f.read(), globals())
                    vars.vars["EXTERNAL_MODULES"].update(MODULES)
                except Exception as e:
                    print(f'The following error occurred when loading "{file}":\n{e}')


checkForCustomModules()
