import wx
from Resources.audio import *
from Resources.widgets import *
from Resources.utils import p_mathpow
import Resources.variables as vars


class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filename):
        self.window.GetTopLevelParent().openfile(filename[0])
        return True


class ServerPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE)
        self.parent = parent
        self.mainFrame = self.GetTopLevelParent()
        self.SetSize(self.FromDIP(wx.Size(230, 500)))
        self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        self.SetForegroundColour(vars.constants["FORECOLOUR"])
        self.fileformat = vars.vars["FORMAT"]
        self.sampletype = vars.vars["BITS"]
        self.virtualNotePressed = {}
        self.virtualNotePressedHold = {}
        self.virtualNotePressedHold = {}
        self.virtualNoteActiveHold = {}
        self.keyboardShown = 0
        self.serverSettings = []
        self.selected_output_driver_name = None
        self.selected_midi_interface_name = None

        self.mainBox = wx.BoxSizer(wx.VERTICAL)

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
            elif self.defaultDriver >= 0:
                drivename = self.driverList[self.driverIndexes.index(self.defaultDriver)]
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
                        vars.constants["ID"]["UpdateModules"], vars.constants["ID"]["CheckoutModules"],
                        vars.constants["ID"]["Select"], vars.constants["ID"]["DeSelect"]]

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
            modules = self.mainFrame.modules
            for pit, voice in self.virtualNotePressed.items():
                for module in modules:
                    synth = module.synth
                    if synth.keymode == 0:
                        synth._virtualpit[voice].setValue(pit)
                        synth._trigamp[voice].setValue(0)
            for pit, voice in self.virtualNotePressedHold.items():
                for module in modules:
                    synth = module.synth
                    if synth.keymode > 0:
                        synth._virtualpit[voice].setValue(pit)
                        synth._trigamp[voice].setValue(0)
            self.virtualNotePressed = {}
            self.virtualNotePressedHold = {}
            self.virtualNoteActiveHold = {}

    def retrigVirtualNotes(self):
        notes = self.keyboard.getCurrentNotes()
        self.resetVirtualKeyboard(resetDisplay=False)
        for note in notes:
            wx.CallLater(50, self.onKeyboard, note)

    def onKeyboard(self, note):
        try:
            pit = note[0]
            vel = note[1] / 127.
            velHold = vel
            voice = None
            voiceHold = None

            if vel > 0 and pit not in self.virtualNotePressed.keys():
                vals = self.virtualNotePressed.values()
                for i in range(vars.vars["POLY"]):
                    if i not in vals:
                        break
                voice = self.virtualNotePressed[pit] = i
            elif vel == 0 and pit in self.virtualNotePressed.keys():
                voice = self.virtualNotePressed[pit]
                del self.virtualNotePressed[pit]

            if vel > 0 and pit not in self.virtualNotePressedHold.keys():
                vals = self.virtualNotePressedHold.values()
                for j in range(vars.vars["POLY"]):
                    if j not in vals:
                        break
                voiceHold = self.virtualNotePressedHold[pit] = j
            elif vel > 0 and pit in self.virtualNotePressedHold.keys():
                voiceHold = self.virtualNotePressedHold[pit]
                velHold = 0.0
                del self.virtualNotePressedHold[pit]

            for module in self.mainFrame.modules:
                synth = module.synth
                if (synth.channel == 0 or synth.channel == note[2]) \
                        and pit >= synth.first \
                        and pit <= synth.last \
                        and (note[1] == 0 or (note[1] >= synth.firstVel and note[1] <= synth.lastVel)):
                    if voice is not None and synth.keymode == 0:  # no Hold
                        synth._virtualpit[voice].setValue(pit)
                        synth._trigamp[voice].setValue(vel)

                    elif voiceHold is not None and synth.keymode == 1:  # Hold
                        synth._virtualpit[voiceHold].setValue(pit)
                        synth._trigamp[voiceHold].setValue(velHold)
                        if velHold > 0:
                            self.virtualNoteActiveHold[pit] = note[1]
                        else:
                            if pit in self.virtualNoteActiveHold:
                                del self.virtualNoteActiveHold[pit]

                    elif voiceHold is not None and synth.keymode == 2:  # OnOff Hold
                        v = 1.0 if velHold > 0 else velHold
                        synth._virtualpit[voiceHold].setValue(pit)
                        synth._trigamp[voiceHold].setValue(v)
                        if velHold > 0:
                            self.virtualNoteActiveHold[pit] = 127
                        else:
                            if pit in self.virtualNoteActiveHold:
                                del self.virtualNoteActiveHold[pit]

                    elif voiceHold is not None and synth.keymode == 3:  # 1 Key Hold
                        del_keys = set()
                        for k in self.virtualNoteActiveHold.keys():
                            if k == pit:
                                continue
                            for akey, avoice in self.virtualNotePressedHold.items():
                                if akey == k:
                                    synth._virtualpit[avoice].setValue(akey)
                                    synth._trigamp[avoice].setValue(0.0)
                                    del_keys.add(akey)
                        for k in del_keys:
                            del self.virtualNoteActiveHold[k]
                            del self.virtualNotePressedHold[k]

                        synth._virtualpit[voiceHold].setValue(pit)
                        synth._trigamp[voiceHold].setValue(velHold)
                        if velHold > 0:
                            self.virtualNoteActiveHold[pit] = note[1]
                        else:
                            if pit in self.virtualNoteActiveHold:
                                del self.virtualNoteActiveHold[pit]

                    elif voiceHold is not None and synth.keymode == 4:  # 1 Key OnOff Hold
                        v = 1.0 if velHold > 0 else velHold
                        del_keys = set()
                        for k in self.virtualNoteActiveHold.keys():
                            if k == pit:
                                continue
                            for akey, avoice in self.virtualNotePressedHold.items():
                                if akey == k:
                                    synth._virtualpit[avoice].setValue(akey)
                                    synth._trigamp[avoice].setValue(0.0)
                                    del_keys.add(akey)
                        for k in del_keys:
                            del self.virtualNoteActiveHold[k]
                            del self.virtualNotePressedHold[k]

                        synth._virtualpit[voiceHold].setValue(pit)
                        synth._trigamp[voiceHold].setValue(v)
                        if velHold > 0:
                            self.virtualNoteActiveHold[pit] = 127
                        else:
                            if pit in self.virtualNoteActiveHold:
                                del self.virtualNoteActiveHold[pit]

            self.keyboard.redrawActiveKeys()

        except Exception as e:
            print('keyboard reset due to error', e)
            self.keyboard.reset()

    def handleAudio(self, evt):
        modules = self.mainFrame.modules
        if evt.GetInt() == 1:
            hasModule = False
            for popup in self.popups:
                popup.Disable()
            for menuId in self.menuIds:
                menuItem = self.mainFrame.menubar.FindItemById(menuId)
                if menuItem is not None:
                    menuItem.Enable(False)
            for menuId in range(vars.constants["ID"]["Modules"],
                                vars.constants["ID"]["Modules"] + self.mainFrame.addMenu.GetMenuItemCount() - 1):
                menuItem = self.mainFrame.menubar.FindItemById(menuId)
                if menuItem is not None:
                    menuItem.Enable(False)
            for module in self.mainFrame.modules:
                for kt in module.keytriggers:
                    kt._enable = False
                    kt.Refresh()
                    hasModule = True
            self.start()
            if hasModule and self.mainFrame.serverPanel.sliderAmp.midictlnumber is not None:
                slider = self.mainFrame.serverPanel.sliderAmp
                slider.midictl = Midictl(slider.midictlnumber, -60, 18, slider.GetValue())
                slider.trigFunc = TrigFunc(self.mainFrame.modules[0].synth._midi_metro, slider.valToWidget)
            if self.keyboardShown:
                self.mainFrame.keyboard.SetFocus()
        else:
            self.fsserver._stRev.reset()
            for popup in self.popups:
                if popup != self.popupDriver or vars.vars["AUDIO_HOST"] != "Jack":
                    popup.Enable()
            for menuId in self.menuIds:
                menuItem = self.mainFrame.menubar.FindItemById(menuId)
                if menuItem is not None:
                    menuItem.Enable(True)
            for menuId in range(vars.constants["ID"]["Modules"],
                                vars.constants["ID"]["Modules"] + self.mainFrame.addMenu.GetMenuItemCount() - 1):
                menuItem = self.mainFrame.menubar.FindItemById(menuId)
                if menuItem is not None:
                    menuItem.Enable(True)
            for module in self.mainFrame.modules:
                if module.gdadsron is not None:
                    module.gdadsron = None
                for kt in module.keytriggers:
                    kt._enable = True
                    # kt.Refresh()
            wx.CallAfter(self.meter.setRms, *[0 for i in range(self.meter.numSliders)])
            if self.mainFrame.serverPanel.sliderAmp.midictl is not None:
                self.mainFrame.serverPanel.sliderAmp.midictl = None
                self.mainFrame.serverPanel.sliderAmp.trigFunc = None
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
        self.fsserver.setAmp(p_mathpow(10.0, float(value) * 0.05))

    def getServerSettings(self):
        return [self.popupSr.GetSelection(), self.popupPoly.GetSelection(),
                self.popupBit.GetSelection(), self.popupFormat.GetSelection(),
                self.sliderAmp.GetValue(), self.sliderAmp.midictlnumber]

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
        if len(serverSettings) > 5 and serverSettings[5] is not None:
            self.sliderAmp.setMidiCtlNumber(serverSettings[5])
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
        self.mainFrame.panel.Freeze()
        if vars.vars["VIRTUAL"]:
            self.resetVirtualKeyboard()
        modules, params, lfo_params, ctl_params = self.mainFrame.getModulesAndParams()
        postProcSettings = self.getPostProcSettings()
        self.mainFrame.deleteAllModules()
        self.shutdown()
        if func is not None:
            func(val)
        self.boot()
        self.mainFrame.setModulesAndParams(modules, params, lfo_params, ctl_params)
        self.setPostProcSettings(postProcSettings)
        self.mainFrame.panel.Thaw()
        if self.keyboardShown:
            self.mainFrame.keyboard.SetFocus()
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
                self.mainFrame.showKeyboard(False)
        except IndexError:
            vars.vars["VIRTUAL"] = True
            if not self.keyboardShown:
                self.keyboardShown = 1
                self.setDriverSetting()
                self.mainFrame.showKeyboard()

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
        self.fsserver.setEqGain(0, p_mathpow(10.0, x * 0.05))

    def changeEqA2(self, x):
        self.fsserver.setEqGain(1, p_mathpow(10.0, x * 0.05))

    def changeEqA3(self, x):
        self.fsserver.setEqGain(2, p_mathpow(10.0, x * 0.05))

    def changeEqA4(self, x):
        self.fsserver.setEqGain(3, p_mathpow(10.0, x * 0.05))

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
        learnColour = wx.Colour("#DEDEDE")
        gbcolour = vars.constants["BACKCOLOUR"]
        if state:
            self.SetBackgroundColour(learnColour)
            for module in self.mainFrame.modules:
                for kt in module.keytriggers:
                    kt._enable = False
                    kt.Refresh()
            for widget in self.widgets:
                widget.setBackgroundColour(learnColour)
            for popup in self.popupsLearn:
                popup.Disable()
            self.mainFrame.menubar.FindItemById(vars.constants["ID"]["Run"]).Enable(False)
            self.fsserver.startMidiLearn()
        else:
            self.SetBackgroundColour(gbcolour)
            for module in self.mainFrame.modules:
                for kt in module.keytriggers:
                    kt._enable = True
                    kt.Refresh()
            for widget in self.widgets:
                widget.setBackgroundColour(gbcolour)
            for popup in self.popupsLearn:
                popup.Enable()
            self.mainFrame.menubar.FindItemById(vars.constants["ID"]["Run"]).Enable(True)
            self.fsserver.stopMidiLearn()
            wx.CallAfter(self.setDriverSetting)
        wx.CallAfter(self.Refresh)
        if self.keyboardShown:
            self.mainFrame.keyboard.SetFocus()
        else:
            self.SetFocus()
