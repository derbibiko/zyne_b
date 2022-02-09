import wx
import os
import Resources.variables as vars
from Resources.audio import get_output_devices, get_midi_input_devices


class PreferencesDialog(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, wx.ID_ANY, 'Zyne_B Preferences')

        self.paths = ["CUSTOM_MODULES_PATH", "EXPORT_PATH"]
        self.drivers = ["OUTPUT_DRIVER", "MIDI_INTERFACE"]
        self.ids = {"CUSTOM_MODULES_PATH": 10001, "EXPORT_PATH": 10002,
                    "OUTPUT_DRIVER": 20001, "MIDI_INTERFACE": 20002}

        self.prefs = dict()
        for key in vars.constants["VAR_PREF_LABELS"].keys():
            val = str(vars.vars["PREF_FILE_SETTINGS"].get(key, vars.vars[key]))
            if key == "AUDIO_HOST" and \
                    vars.constants["IS_MAC"] \
                    and not vars.constants["OSX_BUILD_WITH_JACK_SUPPORT"] \
                    and val in ["Jack", "Coreaudio"]:
                self.prefs[key] = "Portaudio"
            else:
                self.prefs[key] = val

        self.preffilename = vars.constants["PREF_FILE_NAME"]
        self.createWidgets()

    def createWidgets(self):
        btnSizer = wx.StdDialogButtonSizer()
        itemSizer = wx.FlexGridSizer(0, 2, 10, 5)
        itemSizer.AddGrowableCol(0)
        driverSizer = wx.BoxSizer(wx.VERTICAL)
        pathSizer = wx.BoxSizer(wx.VERTICAL)
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        message = wx.StaticText(self, label="– Changes will be applied on next launch –")
        mainSizer.Add(message, 0, wx.TOP | wx.LEFT | wx.ALIGN_CENTER_HORIZONTAL, 10)
        font, entryfont = message.GetFont(), message.GetFont()
        pointsize = font.GetPointSize()
        font.SetWeight(wx.BOLD)
        if vars.constants["IS_WIN"] or vars.constants["IS_LINUX"]:
            entryfont.SetPointSize(pointsize-1)
        else:
            font.SetPointSize(pointsize-1)
            entryfont.SetPointSize(pointsize-2)

        if vars.constants["IS_LINUX"]:
            host_choices = ["Portaudio", "Jack"]
        elif vars.constants["IS_MAC"]:
            if vars.constants["OSX_BUILD_WITH_JACK_SUPPORT"]:
                host_choices = ["Portaudio", "Jack"]
            else:
                host_choices = ["Portaudio"]
        else:
            host_choices = ["Portaudio"]
        host = self.prefs["AUDIO_HOST"]
        lbl = wx.StaticText(self, label=vars.constants["VAR_PREF_LABELS"]["AUDIO_HOST"])
        lbl.SetFont(font)
        driverSizer.Add(lbl, 0, wx.LEFT | wx.RIGHT, 10)
        cbo = wx.ComboBox(self, value=host, size=(100, -1), choices=host_choices,
                          style=wx.CB_DROPDOWN | wx.CB_READONLY, name="AUDIO_HOST")
        driverSizer.AddSpacer(5)
        driverSizer.Add(cbo, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        for key in self.drivers:
            lbl = wx.StaticText(self, label=vars.constants["VAR_PREF_LABELS"][key])
            lbl.SetFont(font)
            driverSizer.Add(lbl, 0, wx.LEFT, 10)
            ctrlSizer = wx.BoxSizer(wx.HORIZONTAL)
            txt = wx.TextCtrl(self, value=self.prefs[key], name=key)
            ctrlSizer.Add(txt, 4, wx.ALL | wx.EXPAND, 5)
            but = wx.Button(self, id=self.ids[key], label="Choose...")
            but.Bind(wx.EVT_BUTTON, self.getDriver, id=self.ids[key])
            ctrlSizer.Add(but, 1, wx.ALL, 5)
            driverSizer.Add(ctrlSizer, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

        for key in vars.constants["VAR_PREF_LABELS"].keys():
            val = self.prefs[key]
            if key not in self.paths and key not in self.drivers and key != "AUDIO_HOST":
                lbl = wx.StaticText(self, label=vars.constants["VAR_PREF_LABELS"][key])
                lbl.SetFont(font)
                itemSizer.Add(lbl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
                if key in vars.constants["VAR_CHOICES"]:
                    default = val
                    choices = vars.constants["VAR_CHOICES"][key]
                    cbo = wx.ComboBox(self, value=val, size=(200, -1), choices=choices,
                                      style=wx.CB_DROPDOWN | wx.CB_READONLY, name=key)
                    itemSizer.Add(cbo, 0, wx.LEFT | wx.RIGHT, 5)
                else:
                    txt = wx.TextCtrl(self, size=(200, -1), value=val, name=key)
                    itemSizer.Add(txt, 0, wx.LEFT | wx.RIGHT, 5)

        for key in self.paths:
            if key == "CUSTOM_MODULES_PATH":
                func = self.getPath
            elif key == "EXPORT_PATH":
                func = self.getPath
            lbl = wx.StaticText(self, label=vars.constants["VAR_PREF_LABELS"][key])
            lbl.SetFont(font)
            pathSizer.Add(lbl, 0, wx.LEFT | wx.RIGHT, 10)
            ctrlSizer = wx.BoxSizer(wx.HORIZONTAL)
            txt = wx.TextCtrl(self, value=self.prefs[key], name=key)
            txt.SetFont(entryfont)
            ctrlSizer.Add(txt, 1, wx.ALL | wx.EXPAND, 5)
            but = wx.Button(self, id=self.ids[key], label="Choose...")
            but.Bind(wx.EVT_BUTTON, self.getPath, id=self.ids[key])
            ctrlSizer.Add(but, 0, wx.ALL, 5)
            pathSizer.Add(ctrlSizer, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

        saveBtn = wx.Button(self, wx.ID_OK, label="Save")
        saveBtn.SetDefault()
        saveBtn.Bind(wx.EVT_BUTTON, self.onSave)
        btnSizer.AddButton(saveBtn)

        cancelBtn = wx.Button(self, wx.ID_CANCEL)
        btnSizer.AddButton(cancelBtn)
        btnSizer.Realize()

        mainSizer.AddSpacer(5)
        mainSizer.Add(driverSizer, 0, wx.EXPAND)
        mainSizer.Add(itemSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        mainSizer.AddSpacer(5)
        mainSizer.Add(pathSizer, 0, wx.EXPAND)
        mainSizer.Add(wx.StaticLine(self, size=(-1, 1)), 0, wx.ALL | wx.EXPAND, 2)
        mainSizer.Add(btnSizer, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_RIGHT, 5)
        self.SetSizerAndFit(mainSizer)

    def getDriver(self, evt):
        id = evt.GetId()
        for name in self.ids.keys():
            if self.ids[name] == id:
                break
        if name == "OUTPUT_DRIVER":
            driverList, driverIndexes = get_output_devices()
            msg = "Choose an output driver..."
        elif name == "MIDI_INTERFACE":
            driverList, driverIndexes = get_midi_input_devices()
            driverList.append("Virtual Keyboard")
            msg = "Choose a Midi interface..."
        widget = wx.FindWindowByName(name)
        dlg = wx.SingleChoiceDialog(self, message=msg, caption="Driver Selector",
                                    choices=driverList, style=wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            selection = dlg.GetStringSelection()
            widget.SetValue(selection)
        dlg.Destroy()

    def getPath(self, evt):
        id = evt.GetId()
        for name in self.ids.keys():
            if self.ids[name] == id:
                break
        if name == "EXPORT_PATH":
            title = "Choose the directory where to save the exported samples"
        else:
            title = "Choose the directory where you saved your custom module files"
        widget = wx.FindWindowByName(name)
        dlg = wx.DirDialog(self, title, os.path.expanduser("~"), style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            widget.SetValue(path)
        dlg.Destroy()

    def onSave(self, event):
        preffile = os.path.join(os.path.expanduser("~"), self.preffilename)
        with open(preffile, "w", encoding="utf-8") as f:
            f.write(f"### Zyne_B version {vars.constants['VERSION']} preferences ###\n")
            for name in vars.constants["VAR_PREF_LABELS"].keys():
                widget = wx.FindWindowByName(name)
                if isinstance(widget, wx.ComboBox):
                    value = widget.GetValue()
                    choices = widget.GetItems()
                else:
                    value = widget.GetValue()
                try:
                    f.write(f"{name} = {value}\n")
                except UnicodeEncodeError:
                    try:
                        f.write(f"{name} = " + value + "\n")
                    except Exception:
                        f.write(f'{name} = ""\n')
            f.write(f"LAST_SAVED = {vars.vars['LAST_SAVED']}\n")
        self.EndModal(0)
