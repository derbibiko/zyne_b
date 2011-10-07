# encoding: utf-8
import random, os, time, math, codecs
import Resources.variables as vars
from types import ListType

if vars.vars["PYO_PRECISION"] == "single":
    from pyo import *
else:
    from pyo64 import *

def get_output_devices():
    return pa_get_output_devices()
def get_default_output():
    return pa_get_default_output()
def get_midi_input_devices():
    return pm_get_input_devices()
def get_midi_default_input():
    return pm_get_default_input()

class FSServer:
    def __init__(self):
        self.eqOn = False
        self.compOn = False
        self.eqFreq = [100, 500, 2000]
        self.eqGain = [1, 1, 1, 1]
        self.server = Server(audio=vars.vars["AUDIO_HOST"].lower())
        self.boot()
    
    def scanning(self, x):
        if vars.vars["LEARNINGSLIDER"] != None:
            vars.vars["LEARNINGSLIDER"].setMidiCtl(x)
            vars.vars["LEARNINGSLIDER"].Enable()
            vars.vars["LEARNINGSLIDER"] = None
    
    def startMidiLearn(self):
        self.server.shutdown()
        self.server.boot()
        self.scan = CtlScan(self.scanning, False)
        self.server.start()
    
    def stopMidiLearn(self):
        del self.scan
        self.server.stop()
        time.sleep(.25)
    
    def start(self):
        self.server.start()
    
    def stop(self):
        self.server.stop()
    
    def shutdown(self):
        self.server.shutdown()
    
    def boot(self):
        self.server.boot()
        self._outSig = Sig([0,0]).out()
        vars.vars["MIDI_ACTIVE"] = self.server.getMidiActive()
        #print "midi is active :", vars.vars["MIDI_ACTIVE"]
        self._outSigMix = self._outSig.mix(1)
        
        self._fbEqAmps = SigTo(self.eqGain, time=.1, init=self.eqGain)
        self._fbEq = FourBand(self._outSig, freq1=self.eqFreq[0], 
                            freq2=self.eqFreq[1], freq3=self.eqFreq[2], mul=self._fbEqAmps).stop()
        self._outEq = Mix(self._fbEq, voices=2).stop()
        self._outEqMix = self._outEq.mix(1)
        
        self._compLevel = Compress(self._outSigMix, thresh=-3, ratio=2, risetime=.01, 
                                    falltime=.1, lookahead=0, knee=0.5, outputAmp=True).stop()
        self._compDelay = Delay(self._outSig, delay=0.005).stop()
        self._outComp = self._compDelay * self._compLevel
        self._outComp.stop()
    
    def reinit(self, audio):
        self.server.reinit(audio=audio.lower())
    
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
            self.server.setInOutDevice(device)
    
    def setMidiInputDevice(self, device):
        self.server.setMidiInputDevice(device)
    
    def setSamplingRate(self, sr):
        self.server.setSamplingRate(sr)
    
    def recordOptions(self, dur, filename, fileformat, sampletype):
        self.server.recordOptions(dur=dur, filename=filename, fileformat=fileformat, sampletype=sampletype)
    
    def onOffEq(self, state):
        if state == 1:
            self.eqOn = True
            self._outSig.play()
            self._fbEq.play()
            if not self.compOn:
                self._outEq.out()
            else:
                self._outEq.play()
                self._compLevel.input = self._outEqMix
                self._compDelay.input = self._outEq
        else:
            self.eqOn = False
            self._fbEq.stop()
            self._outEq.stop()
            if self.compOn:
                self._compLevel.input = self._outSigMix
                self._compDelay.input = self._outSig
                self._outComp.out()
            else:
                self._outSig.out()
    
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
    
    def onOffComp(self, state):
        if state == 1:
            self.compOn = True
            self._outSig.play()
            if self.eqOn:
                self._outEq.play()
                self._compLevel.input = self._outEqMix
                self._compDelay.input = self._outEq
            else:
                self._compLevel.input = self._outSigMix
                self._compDelay.input = self._outSig
            self._compLevel.play()
            self._compDelay.play()
            self._outComp.out()
        else:
            self.compOn = False
            self._compLevel.stop()
            self._compDelay.stop()
            self._outComp.stop()
            if self.eqOn:
                self._outEq.out()
            else:
                self._outSig.out()
    
    def setCompParam(self, param, value):
        if param == "thresh":
            self._compLevel.thresh = value
        elif param == "ratio":
            self._compLevel.ratio = value
        elif param == "risetime":
            self._compLevel.risetime = value
        elif param == "falltime":
            self._compLevel.falltime = value

class CtlBind:
    def __init__(self):
        self.last_midi_val = 0.0
        self.lfo_last_midi_vals = [0.0, 0.0, 0.0, 0.0]
    
    def valToWidget(self):
        val = self.midictl.get()
        if val != self.last_midi_val:
            self.last_midi_val = val
            if self.widget.log:
                val **= 10.0
                val *= (self.widget.getMaxValue() - self.widget.getMinValue()) 
                val += self.widget.getMinValue()
            self.widget.setValue(val)
    
    def valToWidget0(self):
        val = self.lfo_midictl_0.get()
        is_log = self.lfo_widget_0.log
        if val != self.lfo_last_midi_vals[0]:
            self.lfo_last_midi_vals[0] = val
            if is_log:
                val **= 10.0
                val *= (self.lfo_widget_0.getMaxValue() - self.lfo_widget_0.getMinValue())
                val += self.lfo_widget_0.getMinValue()
            self.lfo_widget_0.setValue(val)
            self.lfo_widget_0.outFunction(val)
    
    def valToWidget1(self):
        val = self.lfo_midictl_1.get()
        is_log = self.lfo_widget_1.log
        if val != self.lfo_last_midi_vals[1]:
            self.lfo_last_midi_vals[1] = val
            if is_log:
                val **= 10.0
                val *= (self.lfo_widget_1.getMaxValue() - self.lfo_widget_1.getMinValue())
                val += self.lfo_widget_1.getMinValue()
            self.lfo_widget_1.setValue(val)
            self.lfo_widget_1.outFunction(val)
    
    def valToWidget2(self):
        val = self.lfo_midictl_2.get()
        is_log = self.lfo_widget_2.log
        if val != self.lfo_last_midi_vals[2]:
            self.lfo_last_midi_vals[2] = val
            if is_log:
                val **= 10.0
                val *= (self.lfo_widget_2.getMaxValue() - self.lfo_widget_2.getMinValue())
                val += self.lfo_widget_2.getMinValue()
            self.lfo_widget_2.setValue(val)
            self.lfo_widget_2.outFunction(val)
    
    def valToWidget3(self):
        val = self.lfo_midictl_3.get()
        is_log = self.lfo_widget_3.log
        if val != self.lfo_last_midi_vals[3]:
            self.lfo_last_midi_vals[3] = val
            if is_log:
                val **= 10.0
                val *= (self.lfo_widget_3.getMaxValue() - self.lfo_widget_3.getMinValue())
                val += self.lfo_widget_3.getMinValue()
            self.lfo_widget_3.setValue(val)
            self.lfo_widget_3.outFunction(val)
    
    def assignMidiCtl(self, ctl, widget):
        if not vars.vars["MIDI_ACTIVE"]:
            return
        mini = widget.getMinValue()
        maxi = widget.getMaxValue()
        value = widget.GetValue()
        is_log = widget.log
        self.widget = widget
        if is_log:
            norm_init = pow(float(value - mini) / (maxi - mini), .1)
            self.midictl = Midictl(ctl, 0, 1.01, norm_init)
        else:
            self.midictl = Midictl(ctl, mini, maxi+.1, value)
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
                norm_init = pow(float(value - mini) / (maxi - mini), .1)
                self.lfo_midictl_0 = Midictl(ctl, 0, 1.01, norm_init)
            else:
                self.lfo_midictl_0 = Midictl(ctl, mini, maxi+.1, value)
            self.lfo_trigFunc_0 = TrigFunc(self._midi_metro, self.valToWidget0)
        elif i == 1:
            self.lfo_widget_1 = widget
            if is_log:
                norm_init = pow(float(value - mini) / (maxi - mini), .1)
                self.lfo_midictl_1 = Midictl(ctl, 0, 1.01, norm_init)
            else:
                self.lfo_midictl_1 = Midictl(ctl, mini, maxi+.1, value)
            self.lfo_trigFunc_1 = TrigFunc(self._midi_metro, self.valToWidget1)
        elif i == 2:
            self.lfo_widget_2 = widget
            if is_log:
                norm_init = pow(float(value - mini) / (maxi - mini), .1)
                self.lfo_midictl_2 = Midictl(ctl, 0, 1.01, norm_init)
            else:
                self.lfo_midictl_2 = Midictl(ctl, mini, maxi+.1, value)
            self.lfo_trigFunc_2 = TrigFunc(self._midi_metro, self.valToWidget2)
        elif i == 3:
            self.lfo_widget_3 = widget
            if is_log:
                norm_init = pow(float(value - mini) / (maxi - mini), .1)
                self.lfo_midictl_3 = Midictl(ctl, 0, 1.01, norm_init)
            else:
                self.lfo_midictl_3 = Midictl(ctl, mini, maxi+.1, value)
            self.lfo_trigFunc_3 = TrigFunc(self._midi_metro, self.valToWidget3)

class LFOSynth(CtlBind):
    def __init__(self, rng, trigger, midi_metro, lfo_config=None):
        CtlBind.__init__(self)
        self.trigger = trigger
        self._midi_metro = midi_metro
        self.rawamp = SigTo(.1, vars.vars["SLIDERPORT"], .1, mul=rng)
        self.amp = MidiDelAdsr(self.trigger, delay=0, attack=5, decay=.1, sustain=.5, release=1, mul=self.rawamp)
        self.speed = SigTo(4, vars.vars["SLIDERPORT"], 4)
        self.jitter = SigTo(0, vars.vars["SLIDERPORT"], 0)
        self.freq = Randi(min=1-self.jitter, max=1+self.jitter, freq=1, mul=self.speed)
        self.lfo = LFO(freq=self.freq, sharp=.9, type=3).stop()
        self.sigout = Sig(self.lfo * self.amp).stop()
    
    def play(self):
        self.rawamp.play()
        self.amp.play()
        self.speed.play()
        self.jitter.play()
        self.freq.play()
        self.lfo.play()
        self.sigout.play()
    
    def stop(self):
        self.rawamp.stop()
        self.amp.stop()
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
        self.lfo.type = x
    
    def setJitter(self, x):
        self.jitter.value = x

    def setSharp(self, x):
        self.lfo.sharp = x
    
    def setAmp(self, x):
        self.rawamp.value = x
    
    def __del__(self):
        for key in self.__dict__.keys():
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
            setattr(self.parent, "p%d" % i, self.slider)
        else:
            self.lfo = LFOSynth(rng, lfo_trigger, midi_metro)
            self.slider = SigTo(self.init, vars.vars["SLIDERPORT"], self.init, add=self.lfo.sig())
            self.out = Clip(self.slider, self.mini, self.maxi)
            setattr(self.parent, "p%d" % i, self.out)
    
    def set(self, x):
        self.slider.value = x
    
    def start_lfo(self, x):
        if x == 0:
            self.lfo.stop()
        else:
            self.lfo.play()
    
    def __del__(self):
        for key in self.__dict__.keys():
            del self.__dict__[key]

class Panner(CtlBind):
    def __init__(self, parent, lfo_trigger, midi_metro):
        CtlBind.__init__(self)
        self.parent = parent
        self.lfo_trigger = Ceil(lfo_trigger)
        self._midi_metro = midi_metro
        self.lfo = LFOSynth(0.5, self.lfo_trigger, midi_metro)
        self.slider = SigTo(0.5, vars.vars["SLIDERPORT"], 0.5, add=self.lfo.sig())
        self.clip = Clip(self.slider, 0., 1.)
        self.amp_L = Sqrt(1 - self.clip)
        self.amp_R = Sqrt(self.clip)

    def set(self, x):
        self.slider.value = x

    def start_lfo(self, x):
        if not x:
            self.lfo.stop()
        else:
            self.lfo.play()

    def __del__(self):
        for key in self.__dict__.keys():
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
        self.midictl = Midictl(ctl, -36.5, 36.5, widget.GetValue())
        self.trigFunc = TrigFunc(self._midi_metro, self.valToWidget)
    
    def __del__(self):
        for key in self.__dict__.keys():
            del self.__dict__[key]

class BaseSynth:
    def __init__(self, config,  mode=1):
        self.module_path = vars.vars["CUSTOM_MODULES_PATH"]
        self.export_path = vars.vars["EXPORT_PATH"]
        scaling = {1: 1, 2: 2, 3: 0}[mode]
        with_transpo = False
        for conf in config:
            if conf[0] == "Transposition":
                with_transpo = True
                break
        self._midi_metro = Metro(.1).play()
        self._rawamp = SigTo(1, vars.vars["SLIDERPORT"], 1)
        if vars.vars["MIDIPITCH"] != None:
            if with_transpo:
                self._note = Sig(vars.vars["MIDIPITCH"])
                self._transpo = Sig(value=0)
                self.pitch = Snap(self._note+self._transpo, choice=[0,1,2,3,4,5,6,7,8,9,10,11], scale=scaling)
            elif mode == 1:
                if type(vars.vars["MIDIPITCH"]) == ListType:
                    _tmp_hz = [midiToHz(x) for x in vars.vars["MIDIPITCH"]]
                else:
                    _tmp_hz = midiToHz(vars.vars["MIDIPITCH"])
                self.pitch = Sig(_tmp_hz)
            elif mode == 2:
                if type(vars.vars["MIDIPITCH"]) == ListType:
                    _tmp_tr = [midiToTranspo(x) for x in vars.vars["MIDIPITCH"]]
                else:
                    _tmp_tr = midiToTranspo(vars.vars["MIDIPITCH"])
                self.pitch = Sig(_tmp_tr)
            elif mode == 3:
                self.pitch = Sig(vars.vars["MIDIPITCH"])
            self._firsttrig = Trig().play()
            self._secondtrig = Trig().play(delay=vars.vars["NOTEONDUR"])
            self._trigamp = Counter(Mix([self._firsttrig,self._secondtrig]), min=0, max=2, dir=1)
            self._lfo_amp = LFOSynth(.5, self._trigamp, self._midi_metro)
            self.amp = MidiDelAdsr(self._trigamp, delay=0, attack=.001, decay=.1, sustain=.5, release=1, 
                                mul=self._rawamp*vars.vars["MIDIVELOCITY"], add=self._lfo_amp.sig())
            self.trig = Trig().play()
        elif vars.vars["VIRTUAL"]:
            self._virtualpit = Sig([0.0]*vars.vars["POLY"])
            self._trigamp = Sig([0.0]*vars.vars["POLY"])
            if with_transpo:
                self._transpo = Sig(value=0)
                self.pitch = Snap(self._virtualpit+self._transpo, choice=[0,1,2,3,4,5,6,7,8,9,10,11], scale=scaling)
            else:
                self.pitch = Snap(self._virtualpit, choice=[0,1,2,3,4,5,6,7,8,9,10,11], scale=scaling)
            self._lfo_amp = LFOSynth(.5, self._trigamp, self._midi_metro)
            self.amp = MidiDelAdsr(self._trigamp, delay=0, attack=.001, decay=.1, sustain=.5, release=1, 
                                   mul=self._rawamp, add=self._lfo_amp.sig())
            self.trig = Thresh(self._trigamp)
        else:
            if with_transpo:
                self._note = Notein(poly=vars.vars["POLY"], scale=0)
                self._transpo = Sig(value=0)
                self.pitch = Snap(self._note["pitch"]+self._transpo, choice=[0,1,2,3,4,5,6,7,8,9,10,11], scale=scaling)
            else:
                self._note = Notein(poly=vars.vars["POLY"], scale=scaling)
                self.pitch = self._note["pitch"]
            self._trigamp = self._note["velocity"]
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
    
    def __del__(self):
        for param in self._params:
            if param != None:
                del param
        for key in self.__dict__.keys():
            del self.__dict__[key]

class FmSynth(BaseSynth):
    """
    Simple frequency modulation synthesis.

    Author : Olivier Bélanger - 2011

    Parameters:

        FM Ratio : Ratio between carrier frequency and modulation frequency.
        FM Index : Modulation index.
        Lowpass Cutoff : Cutoff frequency of the lowpass filter.
    
    """
    def __init__(self, config):
        BaseSynth.__init__(self, config,  mode=1)
        self.indexLine = self.amp * self.p2
        self.indexrnd = Randi(min=.95, max=1.05, freq=[random.uniform(.5,2) for i in range(4)])
        self.norm_amp = self.amp * 0.1
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.fm1 = FM(carrier=self.pitch, ratio=self.p1, index=self.indexLine*self.indexrnd[0], mul=self.leftamp)
        self.fm2 = FM(carrier=self.pitch*.997, ratio=self.p1, index=self.indexLine*self.indexrnd[1], mul=self.rightamp)
        self.fm3 = FM(carrier=self.pitch*.995, ratio=self.p1, index=self.indexLine*self.indexrnd[2], mul=self.leftamp)
        self.fm4 = FM(carrier=self.pitch*1.002, ratio=self.p1, index=self.indexLine*self.indexrnd[3], mul=self.rightamp)
        self.filt1 = Biquadx(self.fm1+self.fm3, freq=self.p3, q=1, type=0, stages=2).mix()
        self.filt2 = Biquadx(self.fm2+self.fm4, freq=self.p3, q=1, type=0, stages=2).mix()
        self.out = Mix([self.filt1, self.filt2], voices=2)

class AddSynth(BaseSynth):
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.fac = Pow(range(1,6), self.p2, mul=[random.uniform(.995,1.005) for i in range(4)])
        self.feedrnd = Randi(min=.15, max=.25, freq=[random.uniform(.5,2) for i in range(4)])
        self.norm_amp = self.amp * 0.1
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.sine1 = SineLoop(freq=self.pitch*self.fac[0], feedback=self.p3*self.feedrnd[0], mul=self.leftamp).mix()
        self.sine2 = SineLoop(freq=self.pitch*self.fac[1], feedback=self.p3*self.feedrnd[1], mul=self.rightamp).mix()
        self.sine3 = SineLoop(freq=self.pitch*self.fac[2], feedback=self.p3*self.feedrnd[2], mul=self.leftamp).mix()
        self.sine4 = SineLoop(freq=self.pitch*self.fac[3], feedback=self.p3*self.feedrnd[3], mul=self.rightamp).mix()
        self.out = Mix([self.sine1, self.sine2, self.sine3, self.sine4], voices=2)

class WindSynth(BaseSynth):
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.clpit = Clip(self.pitch, min=40, max=15000)
        self.norm_amp = self.p3 * .2
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.noise = Noise(mul=self.amp*self.norm_amp)
        self.dev = Randi(min=0.-self.p2, max=self.p2, freq=self.p1*[random.uniform(.75,1.25) for i in range(4)], add=1)
        self.filt1 = Biquadx(self.noise, freq=self.clpit*self.dev[0], q=self.p3, type=2, stages=2, mul=self.leftamp).mix()
        self.filt2 = Biquadx(self.noise, freq=self.clpit*self.dev[1], q=self.p3, type=2, stages=2, mul=self.rightamp).mix()
        self.filt3 = Biquadx(self.noise, freq=self.clpit*self.dev[2], q=self.p3, type=2, stages=2, mul=self.leftamp).mix()
        self.filt4 = Biquadx(self.noise, freq=self.clpit*self.dev[3], q=self.p3, type=2, stages=2, mul=self.rightamp).mix()
        self.out = Mix([self.filt1, self.filt2, self.filt3, self.filt4], voices=2)

class SquareMod(BaseSynth):
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
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.rosspit = Clip(self.pitch / 5000. + 0.25, min=0., max=1.)
        self.deviation = Randi(min=0.-self.p2, max=self.p2, freq=[random.uniform(2,4) for i in range(2)], add=1)
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
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.deviation = Randi(min=0.-self.p3, max=self.p3, freq=[random.uniform(2,4) for i in range(2)], add=1)
        self.table = CosTable([(0,0),(50,1),(300,0),(8191,0)])
        self.impulse = TrigEnv(self.trig, table=self.table, dur=.1)
        self.noise = Biquad(Noise(self.impulse), freq=2500)
        self.leftamp = self.amp*self.panL
        self.rightamp = self.amp*self.panR
        self.wave1 = Waveguide(self.noise, freq=self.pitch*self.deviation[0], dur=self.p2, minfreq=.5, mul=self.leftamp).mix()
        self.wave2 = Waveguide(self.noise, freq=self.pitch*self.deviation[1], dur=self.p2, minfreq=.5, mul=self.rightamp).mix()
        self.out = Mix([self.wave1, self.wave2], voices=2)

class Reson(BaseSynth):
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.deviation = Randi(min=0.-self.p2, max=self.p2, freq=[random.uniform(2,4) for i in range(4)], add=1)
        self.excite = Noise(.02)
        self.leftamp = self.amp*self.panL
        self.rightamp = self.amp*self.panR
        self.wave1 = Waveguide(self.excite, freq=self.pitch*self.deviation[0], dur=30, minfreq=1, mul=self.leftamp)
        self.wave2 = Waveguide(self.excite, freq=self.pitch*self.deviation[1], dur=30, minfreq=1, mul=self.rightamp)
        self.filt1 = Biquad(self.wave1, freq=self.p3).mix()
        self.filt2 = Biquad(self.wave2, freq=self.p3).mix()
        self.out = Mix([self.filt1, self.filt2], voices=2)

# class Particle(BaseSynth):
#     def __init__(self, config):
#         BaseSynth.__init__(self, config, mode=1)
#         num = len(self.p1)
#         self.table = CosTable([(0,0), (100,1), (500,.5), (3000,.25), (8191,0)])
#         self.cloud = [Cloud(self.p1[i], poly=4).play() for i in range(num)]
#         self.env = [TrigEnv(self.cloud[i], self.table, self.p2[i]) for i in range(num)]
#         self.src = Noise()
#         self.leftamp = self.amp*self.panL
#         self.rightamp = self.amp*self.panR
#         self.rndfreq1 = [TrigRand(self.cloud[i], min=.85, max=1.25, port=.005, init=1, 
#                         mul=self.pitch[i]*2) for i in range(num)]
#         self.filters1 = [Biquadx(self.src, freq=self.rndfreq1, q=self.p3[i], type=2, 
#                         mul=self.env[i]*self.leftamp[i]).mix() for i in range(num)]
#         self.rndfreq2 = [TrigRand(self.cloud[i], min=.85, max=1.25, port=.005, init=1, 
#                         mul=self.pitch[i]*2) for i in range(num)]
#         self.filters2 = [Biquadx(self.src, freq=self.rndfreq2, q=self.p3[i], type=2, 
#                         mul=self.env[i]*self.rightamp[i]).mix() for i in range(num)]
#         self.mixL = Mix(self.filters1, voices=1)
#         self.mixR = Mix(self.filters2, voices=1)
#         self.out = Mix([self.mixL, self.mixR], voices=2)

class CrossFmSynth(BaseSynth):
    def __init__(self, config):
        BaseSynth.__init__(self, config,  mode=1)
        self.indexLine = self.amp * self.p2
        self.indexrnd = Randi(min=.95, max=1.05, freq=[random.uniform(.5,2) for i in range(4)])
        self.indexLine2 = self.amp * self.p3
        self.indexrnd2 = Randi(min=.95, max=1.05, freq=[random.uniform(.5,2) for i in range(4)])
        self.norm_amp = self.amp * 0.1
        self.leftamp = self.norm_amp*self.panL
        self.rightamp = self.norm_amp*self.panR
        self.fm1 = CrossFM(carrier=self.pitch, ratio=self.p1, ind1=self.indexLine*self.indexrnd[0], 
                            ind2=self.indexLine2*self.indexrnd2[0], mul=self.leftamp).mix()
        self.fm2 = CrossFM(carrier=self.pitch*.997, ratio=self.p1, ind1=self.indexLine*self.indexrnd[1], 
                            ind2=self.indexLine2*self.indexrnd2[1], mul=self.rightamp).mix()
        self.fm3 = CrossFM(carrier=self.pitch*.995, ratio=self.p1, ind1=self.indexLine*self.indexrnd[2], 
                            ind2=self.indexLine2*self.indexrnd2[2], mul=self.leftamp).mix()
        self.fm4 = CrossFM(carrier=self.pitch*1.002, ratio=self.p1, ind1=self.indexLine*self.indexrnd[3], 
                            ind2=self.indexLine2*self.indexrnd2[3], mul=self.rightamp).mix()
        self.filt1 = Biquad(self.fm1+self.fm3, freq=5000, q=1, type=0)
        self.filt2 = Biquad(self.fm2+self.fm4, freq=5000, q=1, type=0)
        self.out = Mix([self.filt1, self.filt2], voices=2)

class OTReson(BaseSynth):
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
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.table = CosTable([(0,0), (4000,1), (8191,0)])
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
    def __init__(self, config):
        BaseSynth.__init__(self, config, mode=1)
        self.table = HarmTable([1,0,0,.2,0,0,.1,0,0,.07,0,0,0,.05]).normalize()
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

def checkForCustomModules():
    path = ""
    preffile = os.path.join(os.path.expanduser("~"), ".zynerc")
    if os.path.isfile(preffile):
        with codecs.open(preffile, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines[0].startswith("### Zyne") or not vars.constants["VERSION"] in lines[0]:
                pass
            else:
                for line in lines:
                    if "CUSTOM_MODULES_PATH" in line:
                        line = line.strip()
                        if line:
                            sline = line.split("=")
                            path = vars.vars["ensureNFD"](sline[1].strip())
    
    if path != "":
        if os.path.isdir(path):
            files = [f for f in os.listdir(path) if f.endswith(".py")]
            for file in files:
                try:
                    filepath = os.path.join(path, file)
                    execfile(vars.vars["toSysEncoding"](filepath), globals())
                    vars.vars["EXTERNAL_MODULES"].update(MODULES)
                except:
                    pass

checkForCustomModules()
