#!/usr/bin/env python3
# encoding: utf-8

import json
import os
import psutil
import sys
import time
import wx
import Resources.audio as audio
import Resources.tutorial as tutorial
import Resources.variables as vars
import wx.richtext as rt
import wx.lib.scrolledpanel as scrolled
from Resources.Panels.ServerPanel import ServerPanel, MyFileDropTarget
from Resources.panels import *
from Resources.preferences import PreferencesDialog
from Resources.splash import ZyneSplashScreen
from Resources.widgets import ZB_Keyboard
from Resources.utils import toLog


if vars.constants["IS_WIN"]:
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except Exception as e:
        pass

try:
    from wx.adv import AboutDialogInfo, AboutBox
except Exception as e:
    from wx import AboutDialogInfo, AboutBox


class TutorialFrame(wx.Frame):
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        self.menubar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        self.fileMenu.Append(vars.constants["ID"]["CloseTut"], 'Close...\tCtrl+W')
        self.Bind(wx.EVT_MENU, self.onClose, id=vars.constants["ID"]["CloseTut"])
        self.menubar.Append(self.fileMenu, "&File")
        self.SetMenuBar(self.menubar)

        self.code = False

        self.rtc = rt.RichTextCtrl(self, style=wx.VSCROLL | wx.HSCROLL | wx.NO_BORDER)
        self.rtc.SetEditable(False)
        wx.CallAfter(self.rtc.SetFocus)

        font = self.rtc.GetFont()
        newfont = wx.Font(font.GetPointSize(), wx.FONTFAMILY_TELETYPE,
                          wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
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
        self.rtc.WriteText("Welcome to the tutorial on how to create a custom zyne module.")
        self.rtc.EndFontSize()
        self.rtc.EndBold()
        self.rtc.Newline()
        lines = tutorial.__doc__.splitlines(True)
        section_count = 1
        for line in lines:
            if line.count("----") == 2:
                self.rtc.BeginBold()
                if vars.constants["IS_WIN"] or vars.constants["IS_LINUX"]:
                    self.rtc.BeginFontSize(12)
                else:
                    self.rtc.BeginFontSize(16)
                self.rtc.WriteText("%i.%s" % (section_count, line.replace("----", "")))
                self.rtc.EndFontSize()
                self.rtc.EndBold()
                section_count += 1
            elif not self.code and line.startswith("~~~"):
                self.code = True
                if vars.constants["IS_WIN"]:
                    self.rtc.BeginFontSize(10)
                else:
                    self.rtc.BeginFontSize(12)
                self.rtc.BeginItalic()
            elif self.code and line.startswith("~~~"):
                self.code = False
                self.rtc.EndItalic()
                self.rtc.EndFontSize()
            else:
                self.rtc.WriteText(line)
        self.rtc.Newline()
        self.rtc.EndParagraphSpacing()
        self.rtc.EndSuppressUndo()
        self.rtc.Thaw()

    def onClose(self, evt):
        self.Destroy()


class SamplingDialog(wx.Dialog):
    def __init__(self, parent, title="Export Samples...", pos=wx.DefaultPosition, size=wx.DefaultSize, chords=False):
        wx.Dialog.__init__(self, parent, id=1, title=title, pos=pos, size=size)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, "Export settings for sampled sounds."), 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, -1, "Common file name:"), 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.filename = wx.TextCtrl(self, -1, "zyne", size=(80, -1))
        box.Add(self.filename, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, -1, "First:"), 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.first = wx.TextCtrl(self, -1, "60", size=(40, -1))
        box.Add(self.first, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        box.Add(wx.StaticText(self, -1, "Last:"), 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.last = wx.TextCtrl(self, -1, "72", size=(40, -1))
        box.Add(self.last, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        box.Add(wx.StaticText(self, -1, "Step:"), 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.step = wx.TextCtrl(self, -1, "1", size=(40, -1))
        box.Add(self.step, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALL, 5)

        if chords:
            box = wx.BoxSizer(wx.VERTICAL)
            box.Add(wx.StaticText(self, -1, "Chords as 'relative cent/velocity' (default velocity is 100):"), 0, wx.ALIGN_LEFT | wx.ALL, 5)
            self.notechords = wx.TextCtrl(self, -1, "+4/120,-1/40,12", size=(350, -1))
            box.Add(self.notechords, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
            sizer.Add(box, 0, wx.GROW | wx.ALL, 5)
        else:
            box = wx.BoxSizer(wx.HORIZONTAL)
            box.Add(wx.StaticText(self, -1, "MIDI velocity (1-127):"), 0, wx.ALIGN_LEFT | wx.ALL, 5)
            self.velocity = wx.TextCtrl(self, -1, "90", size=(350, -1))
            box.Add(self.velocity, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
            sizer.Add(box, 0, wx.GROW | wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, -1, "Noteon dur:"), 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.noteon = wx.TextCtrl(self, -1, "1", size=(50, -1))
        box.Add(self.noteon, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        box.Add(wx.StaticText(self, -1, "Release dur:"), 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.release = wx.TextCtrl(self, -1, "1", size=(50, -1))
        box.Add(self.release, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.RIGHT | wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.SetSizer(sizer)
        self.filename.SetFocus()


class ZyneFrame(wx.Frame):
    def __init__(self, parent=None, title=f"{vars.constants['WIN_TITLE']} - Untitled", size=(966, 800)):
        wx.Frame.__init__(self, parent, id=-1, title=title, size=size)

        self.number_of_instances = int(len([p.name() for p in psutil.process_iter() if p.name().startswith('Zyne_B')])/2)
        self.SetSize(self.FromDIP(self.GetSize()))

        # self.Bind(wx.EVT_SYS_COLOUR_CHANGED, self.OnColourChanged)
        # print(wx.SystemSettings.GetAppearance().IsDark())

        vars.constants["FORECOLOUR"] = wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENUTEXT)
        vars.constants["BACKCOLOUR"] = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        self.SetForegroundColour(vars.constants["FORECOLOUR"])
        self.selectionBackgroundColour = wx.Colour("#999999")

        self.menubar = wx.MenuBar()

        self.fileMenu = wx.Menu()
        self.fileMenu.Append(vars.constants["ID"]["New"], 'New...\tCtrl+N', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onNew, id=vars.constants["ID"]["New"])
        self.fileMenu.Append(vars.constants["ID"]["Open"], 'Open...\tCtrl+O', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onOpen, id=vars.constants["ID"]["Open"])
        self.fileMenu.Append(vars.constants["ID"]["Save"], 'Save\tCtrl+S', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onSave, id=vars.constants["ID"]["Save"])
        self.fileMenu.Append(vars.constants["ID"]["SaveAs"], 'Save as...\tShift+Ctrl+S', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onSaveAs, id=vars.constants["ID"]["SaveAs"])
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(vars.constants["ID"]["Export"], 'Export as samples...\tCtrl+E', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onExport, id=vars.constants["ID"]["Export"])
        self.fileMenu.Append(vars.constants["ID"]["ExportChord"], 'Export as chords...\tShift+Ctrl+E', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onExport, id=vars.constants["ID"]["ExportChord"])
        self.fileMenu.Append(vars.constants["ID"]["ExportTracks"], 'Export samples as separated tracks...\tCtrl+F', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onExport, id=vars.constants["ID"]["ExportTracks"])
        self.fileMenu.Append(vars.constants["ID"]["ExportChordTracks"], 'Export chords as separated tracks...\tShift+Ctrl+F', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onExport, id=vars.constants["ID"]["ExportChordTracks"])
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(vars.constants["ID"]["MidiLearn"], 'Midi learn mode\tShift+Ctrl+M', kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.onMidiLearnMode, id=vars.constants["ID"]["MidiLearn"])
        self.fileMenu.Append(vars.constants["ID"]["ActivateKeyboard"], 'Activate virtual keyboard\tCtrl+P', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onKeyboardFocus, id=vars.constants["ID"]["ActivateKeyboard"])
        self.fileMenu.Append(vars.constants["ID"]["ResetKeyboard"], 'Reset virtual keyboard\tCtrl+Y', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onResetKeyboard, id=vars.constants["ID"]["ResetKeyboard"])
        self.fileMenu.Append(vars.constants["ID"]["Retrig"], 'Retrig virtual notes\tCtrl+T', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onRetrig, id=vars.constants["ID"]["Retrig"])
        if wx.Platform != "__WXMAC__":
            self.fileMenu.AppendSeparator()
        self.fileMenu.Append(vars.constants["ID"]["Prefs"], 'Preferences...\tCtrl+,', 'Open Zyne_B preferences pane', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onPreferences, id=vars.constants["ID"]["Prefs"])
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(vars.constants["ID"]["Run"], 'Run\tCtrl+R', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onRun, id=vars.constants["ID"]["Run"])
        self.fileMenu.AppendSeparator()
        if (sys.platform == "darwin" and "/Zyne_B.app" in sys.executable) \
                or (sys.platform == "win32" and 'Zyne_B.exe' in sys.executable):
            if sys.platform == "darwin":
                self.fileMenu.AppendSeparator()
            self.fileMenu.Append(vars.constants["ID"]["NewInstance"], 'Open new Zyne_B Instance\tCtrl+Shift+N', kind=wx.ITEM_NORMAL)
            self.Bind(wx.EVT_MENU, self.onNewInstance, id=vars.constants["ID"]["NewInstance"])
            if sys.platform != "darwin":
                self.fileMenu.AppendSeparator()
        self.fileMenu.Append(vars.constants["ID"]["Quit"], 'Quit\tCtrl+Q', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onQuit, id=vars.constants["ID"]["Quit"])
        self.addMenu = wx.Menu()

        self.buildAddModuleMenu()

        self.genMenu = wx.Menu()
        self.genMenu.Append(vars.constants["ID"]["Uniform"], 'Generate uniform random values\tCtrl+G', kind=wx.ITEM_NORMAL)
        self.genMenu.Append(vars.constants["ID"]["Triangular"], 'Generate triangular random values\tCtrl+K', kind=wx.ITEM_NORMAL)
        self.genMenu.Append(vars.constants["ID"]["Minimum"], 'Generate minimum random values\tCtrl+L', kind=wx.ITEM_NORMAL)
        self.genMenu.Append(vars.constants["ID"]["Jitter"], 'Jitterize current values\tCtrl+J', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onGenerateValues, id=vars.constants["ID"]["Uniform"], id2=vars.constants["ID"]["Jitter"])
        self.genMenu.AppendSeparator()
        self.genMenu.Append(vars.constants["ID"]["Select"], 'Select next module\tCtrl+B', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.selectNextModule, id=vars.constants["ID"]["Select"])
        self.genMenu.Append(vars.constants["ID"]["DeSelect"], 'Clear module selection\tShift+Ctrl+B', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.clearSelection, id=vars.constants["ID"]["DeSelect"])
        self.genMenu.AppendSeparator()
        self.genMenu.Append(vars.constants["ID"]["Duplicate"], 'Duplicate selected module\tCtrl+D', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.duplicateSelection, id=vars.constants["ID"]["Duplicate"])
        item = self.genMenu.FindItemById(vars.constants["ID"]["Duplicate"])
        item.Enable(False)

        helpMenu = wx.Menu()
        helpItem = helpMenu.Append(vars.constants["ID"]["About"], f'&About Zyne_B {vars.constants["VERSION"]}', 'wxPython RULES!!!')
        self.Bind(wx.EVT_MENU, self.showAbout, helpItem)
        tuturialCreateModuleItem = helpMenu.Append(vars.constants["ID"]["Tutorial"], "How to create a custom module")
        self.Bind(wx.EVT_MENU, self.openTutorialCreateModule, tuturialCreateModuleItem)
        midiLearnHelpItem = helpMenu.Append(vars.constants["ID"]["MidiLearnHelp"], "How to use the midi learn mode")
        self.Bind(wx.EVT_MENU, self.openMidiLearnHelp, midiLearnHelpItem)
        exportHelpItem = helpMenu.Append(vars.constants["ID"]["ExportHelp"], "How to use the export samples window")
        self.Bind(wx.EVT_MENU, self.openExportHelp, exportHelpItem)

        self.Bind(wx.EVT_CLOSE, self.onQuit)

        self.menubar.Append(self.fileMenu, "&File")
        self.menubar.Append(self.addMenu, "&Modules")
        self.menubar.Append(self.genMenu, "&Generate")
        self.menubar.Append(helpMenu, "&Help")
        self.SetMenuBar(self.menubar)

        self.openedFile = ""
        self.modules = []
        self.selected = None

        self.splitWindow = wx.SplitterWindow(self, -1, style=wx.SP_LIVE_UPDATE)
        self.splitWindow.SetMinimumPaneSize(1)

        self.upperSplitWindow = wx.SplitterWindow(self.splitWindow, -1, style=wx.SP_LIVE_UPDATE)
        self.upperSplitWindow.SetMinimumPaneSize(1)
        self.upperSplitWindow.SetSashInvisible()

        self.panel = scrolled.ScrolledPanel(self.upperSplitWindow, size=self.GetSize(),
                                            pos=self.FromDIP(wx.Point(0, 28)), style=wx.BORDER_NONE)
        self.panel.sizer = wx.WrapSizer()
        self.panel.SetupScrolling(scroll_x=False, scroll_y=True)

        self.serverPanel = ServerPanel(self.upperSplitWindow)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(self.panel.sizer, 1, wx.EXPAND)
        self.panel.SetSizerAndFit(mainSizer)

        self.lowerSplitWindow = wx.SplitterWindow(self.splitWindow, -1, style=wx.SP_LIVE_UPDATE)
        self.lowerSplitWindow.SetMinimumPaneSize(1)
        self.lowerSplitWindow.SetSashInvisible()

        self.keyboard = ZB_Keyboard(self.lowerSplitWindow, outFunction=self.serverPanel.onKeyboard)
        self.keyboard_height = self.keyboard.GetSize()[1]
        self.keyboard.SetMinSize((-1, self.keyboard_height))

        self.serverPanel.keyboard = self.keyboard
        self.serverPanel.setServerSettings(self.serverPanel.serverSettings)

        self.control_keyboard = ZB_Keyboard_Control(self.lowerSplitWindow, self.keyboard)
        self.control_keyboard.SetMinSize((self.FromDIP(60), self.keyboard_height))

        self.lowerSplitWindow.SplitVertically(self.control_keyboard, self.keyboard, -1)
        self.upperSplitWindow.SplitVertically(self.serverPanel, self.panel, -1)

        self.splitWindow.SplitHorizontally(self.upperSplitWindow, self.lowerSplitWindow, -1 * self.keyboard_height)
        self.splitWindow.SetSashInvisible()
        self.splitWindow.Unsplit(None)

        self.Bind(wx.EVT_SIZE, self.OnSize)

        if vars.constants["IS_WIN"]:
            self.SetMinSize(wx.Size(self.FromDIP(530), self.keyboard_height + self.FromDIP(50)))
        else:
            self.SetMinSize(wx.Size(self.FromDIP(530), self.keyboard_height + self.FromDIP(10)))

        self.backup_timer = wx.Timer(self, 1001)
        self.Bind(wx.EVT_TIMER, self.save_bkp_file, self.backup_timer)

        dropTarget = MyFileDropTarget(self.panel)
        self.panel.SetDropTarget(dropTarget)

        self.bkp_file = os.path.join(os.path.expanduser("~"), vars.constants["BACKUP_ZY_NAME"])

        self.loaded_restore = False
        if self.number_of_instances < 2:
            if os.path.exists(self.bkp_file):
                dlg = wx.MessageDialog(None, "Do you want to load the last backup file?", "Zyne_B quit unexpectedly", wx.YES_NO | wx.ICON_QUESTION)
                r = dlg.ShowModal()
                if r == wx.ID_YES:
                    try:
                        self.openfile(self.bkp_file)
                        self.loaded_restore = True
                    except Exception as e:
                        pass
                dlg.Destroy()

        if not self.loaded_restore:
            if vars.vars["AUTO_OPEN"] == 'Default':
                self.openfile(os.path.join(vars.constants["RESOURCES_PATH"], vars.constants["DEFAULT_ZY_NAME"]))
            elif vars.vars["AUTO_OPEN"] == 'Last Saved':
                path = vars.vars["LAST_SAVED"]
                try:
                    self.openfile(path)
                except Exception as e:
                    pass

        self.backup_timer.Start(5000)

    def selectNextModule(self, evt):
        idx = evt.GetInt()
        num = len(self.modules)
        old = self.selected

        if num == 0:
            return

        if idx >= 0:
            self.selected = idx
        else:
            self.selected = 0 if self.selected is None else (self.selected + 1) % num

        if old is not None:
            self.modules[old].headPanel.SetBackgroundColour(vars.constants["HEADTITLE_BACKGROUND_COLOUR"])
            wx.CallAfter(self.modules[old].Refresh)

        self.modules[self.selected].headPanel.SetBackgroundColour(vars.constants["HIGHLIGHT_COLOUR"])
        wx.CallAfter(self.modules[self.selected].Refresh)
        item = self.genMenu.FindItemById(vars.constants["ID"]["Duplicate"])
        item.Enable(True)

    def clearSelection(self, evt):
        if self.selected is not None:
            self.modules[self.selected].headPanel.SetBackgroundColour(vars.constants["HEADTITLE_BACKGROUND_COLOUR"])
            wx.CallAfter(self.modules[self.selected].Refresh)
        self.selected = None
        item = self.genMenu.FindItemById(vars.constants["ID"]["Duplicate"])
        item.Enable(False)

    def duplicateSelection(self, evt):
        if self.selected is not None:
            module = self.modules[self.selected]
            name = module.name
            mute = module.mute
            channel = module.channel
            firstVel = module.firstVel
            lastVel = module.lastVel
            first = module.first
            last = module.last
            firstkey_pitch = module.firstkey_pitch
            loopmode = module.loopmode
            xfade = module.xfade
            if self.modules[-1].synth.isSampler:
                samplerpath = module.synth.path
            else:
                samplerpath = ""
            keymode = module.keymode
            params = [slider.GetValue() for slider in module.sliders]
            lfo_params = module.getLFOParams()
            dic = MODULES[name]
            titleDic = dic.get("slider_title_dicts", None)
            self.modules.append(GenericPanel(self.panel, name, dic["title"], dic["synth"],
                                             dic["p1"], dic["p2"], dic["p3"], titleDic))
            newmod = self.modules[-1]
            self.addModule(newmod)
            newmod.setMute(mute)
            newmod.trigChannel.SetValue(channel)
            newmod.trigVelRange.SetValue((firstVel, lastVel))
            newmod.trigKeyRange.SetValue((first, last))
            newmod.trigFirstKey.SetValue(firstkey_pitch)
            newmod.SetLoopmode(loopmode)
            newmod.SetXFade(xfade)
            newmod.SetSamples(samplerpath)
            newmod.SetKeyMode(keymode)

            for j, param in enumerate(params):
                wx.CallAfter(self.modules[-1].sliders[j].SetValue, param)
            newmod.reinitLFOS(lfo_params, ctl_binding=False)
            self.refresh()

            old = self.selected
            self.selected = len(self.modules) - 1
            self.modules[old].headPanel.SetBackgroundColour(vars.constants["HEADTITLE_BACKGROUND_COLOUR"])
            self.modules[old].headPanel.Refresh()
            self.modules[self.selected].headPanel.SetBackgroundColour(vars.constants["HIGHLIGHT_COLOUR"])
            self.modules[self.selected].headPanel.Refresh()

            wx.CallAfter(self.SetFocus)

    def onNewInstance(self, evt):
        if sys.platform == "darwin":
            p = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            if p.endswith('/Zyne_B.app'):
                os.system(f"open -n {p}")
        elif sys.platform == "win32":
            os.system(f"start {sys.executable}")

    def onRun(self, evt):
        state = self.serverPanel.onOff.GetValue()
        evt = wx.CommandEvent(wx.EVT_TOGGLEBUTTON.typeId, self.serverPanel.onOff.GetId())
        if state:
            evt.SetInt(0)
            self.serverPanel.onOff.SetValue(False)
        else:
            if self.selected is not None:
                self.clearSelection(evt)
            evt.SetInt(1)
            self.serverPanel.onOff.SetValue(True)
        self.serverPanel.onOff.ProcessWindowEvent(evt)
        wx.GetTopLevelWindows()[0].Raise()
        if vars.vars["VIRTUAL"]:
            wx.CallAfter(self.keyboard.SetFocus)

    def onGenerateValues(self, evt):
        id = evt.GetId() - 10000
        if self.selected is None:
            modules = self.modules
        else:
            modules = [self.modules[self.selected]]
        for module in modules:
            if id == 0:
                module.generateUniform()
            elif id == 1:
                module.generateTriangular()
            elif id == 2:
                module.generateMinimum()
            elif id == 3:
                module.jitterize()

    def updateAddModuleMenu(self, evt):
        for mod in list(MODULES.keys()):
            if mod in vars.vars["EXTERNAL_MODULES"]:
                del MODULES[mod]["synth"]
                del MODULES[mod]
        items = self.addMenu.GetMenuItems()
        for item in items:
            self.addMenu.Delete(item)
        audio.checkForCustomModules()
        self.buildAddModuleMenu()
        modules, params, lfo_params, ctl_params = self.getModulesAndParams()
        postProcSettings = self.serverPanel.getPostProcSettings()
        self.deleteAllModules()
        self.serverPanel.shutdown()
        self.serverPanel.boot()
        self.setModulesAndParams(modules, params, lfo_params, ctl_params)
        self.serverPanel.setPostProcSettings(postProcSettings)

    def buildAddModuleMenu(self):
        audio.checkForCustomModules()
        self.moduleNames = sorted(MODULES.keys())
        id = vars.constants["ID"]["Modules"]
        for i, name in enumerate(self.moduleNames):
            if i < 10:
                self.addMenu.Append(id, f'Add {name} module\tCtrl+{((i + 1) % 10)}', kind=wx.ITEM_NORMAL)
                self.Bind(wx.EVT_MENU, self.onAddModule, id=id)
            else:
                self.addMenu.Append(id, f'Add {name} module\tShift+Ctrl+{((i + 1) % 10)}', kind=wx.ITEM_NORMAL)
                self.Bind(wx.EVT_MENU, self.onAddModule, id=id)
            id += 1
        self.addMenu.AppendSeparator()
        if vars.vars["EXTERNAL_MODULES"] != {}:
            moduleNames = sorted(vars.vars["EXTERNAL_MODULES"].keys())
            for i, name in enumerate(moduleNames):
                self.addMenu.Append(id, f'Add {name} module', kind=wx.ITEM_NORMAL)
                self.Bind(wx.EVT_MENU, self.onAddModule, id=id)
                self.moduleNames.append(name)
                MODULES.update(vars.vars["EXTERNAL_MODULES"].items())
                id += 1
            self.addMenu.AppendSeparator()
            self.addMenu.Append(vars.constants["ID"]["UpdateModules"], "Update Modules\tCtrl+U", kind=wx.ITEM_NORMAL)
            self.Bind(wx.EVT_MENU, self.updateAddModuleMenu, id=vars.constants["ID"]["UpdateModules"])

    def openMidiLearnHelp(self, evt):
        size = (750, 500)
        lines = []
        lines.append("To assign midi controllers to module's sliders, user can use the midi learn mode.\n")
        lines.append("First, hit Shift+Ctrl+M (Shift+Cmd+M on Mac) to start midi learn mode, the server panel will change its background colour.\n")
        lines.append("When in midi learn mode, click on a slider and play with the midi controller you want to assign, the controller number will appear at both end of the slider.\n")
        lines.append("To remove a midi assignation, click a second time on the selected slider without playing with a midi controller.\n")
        lines.append("Finally, hit Shift+Ctrl+M (Shift+Cmd+M on Mac) again to leave midi learn mode. Next time you start the server, you will be able to control the sliders with your midi controller.\n\n")
        lines.append(f"Midi assignations are saved within the {vars.constants['ZYNE_B_FILE_EXT']} file and will be automatically assigned at future launches of the synth.\n")
        win = HelpFrame(self, -1, title="Midi Learn Help", size=size, subtitle="How to use the midi learn mode.", lines=lines, from_module=False)
        win.CenterOnParent()
        win.Show(True)

    def openExportHelp(self, evt):
        if vars.constants["IS_LINUX"]:
            size = (750, 500)
        else:
            size = (750, 500)
        lines = []
        lines.append("The export samples window allows the user to create a bank of samples, mapped on a range of midi keys, from the actual state of the current synth.\n")
        lines.append("The path where the exported samples will be saved can be defined in the preferences panel. If not, a folder named 'zyne_export' will be created on the Desktop. Inside this folder, a subfolder will be created according to the string given in the field 'Common file name'. Samples will be saved inside this subfolder with automatic name incrementation.\n")
        lines.append("The fields 'First', 'Last' and 'Step' define which notes, in midi keys, will be sampled and exported. From 'First' to 'Last' in steps of 'Step'.\n")
        lines.append("The fields 'Noteon dur' and 'Release dur' define the duration, in seconds, of the note part and the release part, respectively. The value in 'Noteon dur' should be equal or higher than the addition of the attack and the decay of the longest module. The value in the 'Release part' should be equal or higher than the longest release.\n")
        win = HelpFrame(self, -1, title="Export Samples Help", size=size, subtitle="How to use the export samples window.", lines=lines, from_module=False)
        win.CenterOnParent()
        win.Show(True)

    def openTutorialCreateModule(self, evt):
        win = TutorialFrame(self, -1, "Zyne tutorial", size=(1020, 650), style=wx.DEFAULT_FRAME_STYLE)
        win.CenterOnParent()
        win.Show(True)

    def showKeyboard(self, state=True):
        display_h = wx.Display(0).GetGeometry()[2:][1]
        for itemid in ["ActivateKeyboard", "Retrig", "ResetKeyboard"]:
            item = self.fileMenu.FindItemById(vars.constants["ID"][itemid])
            item.Enable(state)
        if state:
            self.splitWindow.SplitHorizontally(self.upperSplitWindow, self.lowerSplitWindow, self.keyboard_height * -1)
            h = self.GetSize()[1]
            if h >= display_h:
                self.SetSize(wx.Size(-1, display_h - self.FromDIP(20)))
        else:
            self.splitWindow.Unsplit()

    def onResetKeyboard(self, evt):
        self.serverPanel.resetVirtualKeyboard()

    def onKeyboardFocus(self, evt):
        if vars.vars["VIRTUAL"] and self.splitWindow.IsSplit():
            wx.GetTopLevelWindows()[0].Raise()
            self.serverPanel.keyboard.SetFocus()

    def onRetrig(self, evt):
        self.serverPanel.retrigVirtualNotes()

    def OnSize(self, evt):
        self.panel.SetVirtualSize(
            wx.Size(self.panel.GetSize()[0], self.panel.GetVirtualSize()[1]))
        self.panel.SetupScrolling(scroll_x=False, scroll_y=True)
        self.splitWindow.SetSashPosition(self.keyboard_height * -1, False)
        evt.Skip()

    def onMidiLearnModeFromLfoFrame(self):
        if self.serverPanel.onOff.GetValue():
            return
        item = self.fileMenu.FindItemById(vars.constants["ID"]["MidiLearn"])
        if item.IsChecked():
            self.serverPanel.midiLearn(False)
            vars.vars["MIDILEARN"] = False
            item.Check(False)
        else:
            self.serverPanel.midiLearn(True)
            vars.vars["MIDILEARN"] = True
            item.Check(True)
        wx.GetTopLevelWindows()[0].Raise()

    def onMidiLearnMode(self, evt):
        if self.serverPanel.onOff.GetValue():
            return
        if evt.GetInt():
            self.serverPanel.midiLearn(True)
            vars.vars["MIDILEARN"] = True
        else:
            self.serverPanel.midiLearn(False)
            vars.vars["MIDILEARN"] = False
        wx.GetTopLevelWindows()[0].Raise()

    def onPreferences(self, evt):
        dlg = PreferencesDialog()
        dlg.ShowModal()
        dlg.Destroy()
        wx.GetTopLevelWindows()[0].Raise()

    def updateLastSavedInPreferencesFile(self, path):
        preffile = os.path.join(os.path.expanduser("~"), vars.constants["PREF_FILE_NAME"])
        if os.path.isfile(preffile):
            with open(preffile, "r") as f:
                lines = f.readlines()
                if not lines[0].startswith("### Zyne") or not vars.constants["VERSION"] in lines[0]:
                    return
            with open(preffile, "w") as f:
                for line in lines:
                    if "LAST_SAVED" in line:
                        f.write(f"LAST_SAVED = {path}\n")
                    else:
                        f.write(line)

    def onQuit(self, evt):
        self.backup_timer.Stop()
        vars.vars["MIDIPITCH"] = None
        self.serverPanel.shutdown()
        try:
            self.serverPanel.keyboard.Destroy()
        except Exception as e:
            pass
        try:
            if os.path.exists(self.bkp_file):
                os.remove(self.bkp_file)
        except Exception as e:
            pass
        for win in wx.GetTopLevelWindows():
            win.Destroy()
        self.Destroy()
        sys.exit()

    def onNew(self, evt):
        if self.serverPanel.onOff.GetValue():
            return
        self.deleteAllModules()
        self.openedFile = ""
        self.setServerPanelFooter("")
        self.SetTitle(f"{vars.constants['WIN_TITLE']} Synth")
        self.selected = None
        wx.GetTopLevelWindows()[0].Raise()

    def onSave(self, evt):
        if self.openedFile != "":
            self.savefile(self.openedFile)
        else:
            self.onSaveAs(evt)
        wx.GetTopLevelWindows()[0].Raise()
        if vars.vars["VIRTUAL"]:
            wx.CallAfter(self.keyboard.SetFocus)

    def onSaveAs(self, evt):
        if self.openedFile != "":
            filename = os.path.split(self.openedFile)[1]
        else:
            filename = f"zynesynth{vars.constants['ZYNE_B_FILE_EXT']}"
        dlg = wx.FileDialog(self, "Save file as...", defaultFile=filename, style=wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path != "":
                self.savefile(path)
        dlg.Destroy()
        wx.GetTopLevelWindows()[0].Raise()
        if vars.vars["VIRTUAL"]:
            wx.CallAfter(self.keyboard.SetFocus)

    def onOpen(self, evt):
        if self.serverPanel.onOff.GetValue():
            return
        wildcard = f"Zyne files (*{vars.constants['ZYNE_B_FILE_EXT']})|*{vars.constants['ZYNE_B_FILE_EXT']}"
        dlg = wx.FileDialog(self, "Choose Zyne Synth file...", wildcard=wildcard, style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path != "":
                self.openfile(path)
        dlg.Destroy()
        wx.GetTopLevelWindows()[0].Raise()
        if vars.vars["VIRTUAL"]:
            wx.CallAfter(self.keyboard.SetFocus)

    def onExport(self, evt):
        if self.serverPanel.onOff.GetValue():
            return
        chords = False
        if evt.GetId() == vars.constants["ID"]["Export"]:
            mode = "Samples"
            title = "Export samples..."
            title2 = "Exporting samples..."
            num_modules = 1
        elif evt.GetId() in [vars.constants["ID"]["ExportChord"], vars.constants["ID"]["ExportChordTracks"]]:
            chords = True
            if evt.GetId() == vars.constants["ID"]["ExportChord"]:
                mode = "Chords"
                title = "Export chords..."
                title2 = "Exporting chords..."
                num_modules = 1
            else:
                mode = "ChordsTracks"
                title = "Export chords as separated tracks..."
                title2 = "Exporting chords as separated tracks..."
                num_modules = len(self.modules)
        elif evt.GetId() == vars.constants["ID"]["ExportTracks"]:
            mode = "Tracks"
            title = "Export samples as separated tracks..."
            title2 = "Exporting samples as separated tracks..."
            num_modules = len(self.modules)
        dlg = SamplingDialog(self, title=title, size=(450, 310), chords=chords)
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:

            if chords:
                try:
                    chrds = dlg.notechords.GetValue().split(',')
                    notes = []
                    for c in chrds:
                        s = c.split('/')
                        if len(s) == 1:
                            s.append(100)
                        notes.append((int(s[0]), abs(int(s[1]))))
                except Exception as e:
                    wx.LogMessage("Please check input of chords. It may only contain positive and negative integers separated"
                                  "by a comma or a slash.")
                    return

                pitch_factors = [n[0] for n in notes]
                amp_factors_ = [n / 127 for n in [127 if n[1] > 127 else n[1] for n in notes]]
                m_amp = sum(amp_factors_)
                if m_amp < 1.:
                    m_map = 1.
                amp_factors = [a / m_amp for a in amp_factors_]
            else:
                try:
                    velocity = abs(int(dlg.velocity.GetValue()))
                    if velocity > 127:
                        velocity = 1.
                    elif velocity < 1:
                        velocity = 1 / 127
                    else:
                        velocity /= 127
                    velocity *= .33
                except Exception as e:
                    wx.LogMessage("Please check input for velocity. It may only contain a positive integer between 1 and 127.")
                    return

            keyboard_visible = self.serverPanel.keyboardShown
            if keyboard_visible:
                self.showKeyboard(False)

            if vars.vars["EXPORT_PATH"] and os.path.isdir(vars.vars["EXPORT_PATH"]):
                rootpath = vars.vars["EXPORT_PATH"]
            else:
                rootpath = os.path.join(os.path.expanduser("~"), "Desktop", "zyne_export")
                if not os.path.isdir(rootpath):
                    os.mkdir(rootpath)
            filename = dlg.filename.GetValue()
            subrootpath = os.path.join(rootpath, filename)
            if not os.path.isdir(subrootpath):
                os.mkdir(subrootpath)
            first = int(dlg.first.GetValue())
            last = int(dlg.last.GetValue())
            step = int(dlg.step.GetValue())
            num_iter = len(range(first, last, step)) * num_modules
            vars.vars["NOTEONDUR"] = float(dlg.noteon.GetValue())
            duration = float(dlg.release.GetValue()) + vars.vars["NOTEONDUR"]
            ext = self.serverPanel.getExtensionFromFileFormat()
            modules, params, lfo_params, ctl_params = self.getModulesAndParams()
            serverSettings = self.serverPanel.getServerSettings()
            postProcSettings = self.serverPanel.getPostProcSettings()
            self.deleteAllModules()
            self.serverPanel.reinitServer(0.001, "offline", serverSettings, postProcSettings)
            dlg2 = wx.ProgressDialog(title2, "", maximum=num_iter, parent=self,
                                     style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_SMOOTH)
            if vars.constants["IS_WIN"]:
                dlg2.SetSize((500, 125))
            else:
                dlg2.SetSize((500, 100))
            count = 0
            for i in range(first, last, step):
                if mode == "Samples":
                    vars.vars["MIDIPITCH"] = i
                    vars.vars["MIDIVELOCITY"] = velocity
                elif mode == "Chords":
                    vars.vars["MIDIPITCH"] = [i + fac for fac in pitch_factors]
                    vars.vars["MIDIVELOCITY"] = amp_factors
                elif mode == "Tracks":
                    vars.vars["MIDIPITCH"] = i
                    vars.vars["MIDIVELOCITY"] = velocity
                elif mode == "ChordsTracks":
                    vars.vars["MIDIPITCH"] = [i + fac for fac in pitch_factors]
                    vars.vars["MIDIVELOCITY"] = amp_factors
                if mode in ["Samples", "Chords"]:
                    self.setModulesAndParams(modules, params, lfo_params, ctl_params, True)
                    self.serverPanel.setPostProcSettings(postProcSettings)
                    name = "%03d_%s.%s" % (i, filename, ext)
                    path = os.path.join(subrootpath, name)
                    count += 1
                    (keepGoing, skip) = dlg2.Update(count, "Exporting %s" % name)
                    self.serverPanel.setRecordOptions(dur=duration, filename=path)
                    self.serverPanel.start()
                    time.sleep(0.25)
                    self.deleteAllModules()
                    self.serverPanel.shutdown()
                    self.serverPanel.boot()
                    time.sleep(0.25)
                else:
                    for j in range(num_modules):
                        self.setModulesAndParams(modules, params, lfo_params, ctl_params, True)
                        self.serverPanel.setPostProcSettings(postProcSettings)
                        self.modules[j].setMute(2)
                        name = "%03d_%s_track_%02d_%s.%s" % (i, filename, j, self.modules[j].name, ext)
                        path = os.path.join(subrootpath, name)
                        count += 1
                        (keepGoing, skip) = dlg2.Update(count, "Exporting %s" % name)
                        self.serverPanel.setRecordOptions(dur=duration, filename=path)
                        self.serverPanel.start()
                        time.sleep(0.25)
                        self.deleteAllModules()
                        self.serverPanel.shutdown()
                        self.serverPanel.boot()
                        time.sleep(0.25)
            dlg2.Destroy()
            self.serverPanel.reinitServer(vars.vars["SLIDERPORT"], vars.vars["AUDIO_HOST"], serverSettings, postProcSettings)
            vars.vars["MIDIPITCH"] = None
            vars.vars["MIDIVELOCITY"] = 0.707
            self.serverPanel.setAmpCallable()
            self.setModulesAndParams(modules, params, lfo_params, ctl_params)
            if keyboard_visible:
                self.showKeyboard(True)
            self.serverPanel.meter.setRms(*[0., 0.])
        dlg.Destroy()

    def getModulesAndParams(self):
        modules = [module.getModuleParams() for module in self.modules]
        params = [[slider.GetValue() for slider in module.sliders] for module in self.modules]
        lfo_params = [module.getLFOParams() for module in self.modules]
        ctl_params = [[slider.midictlnumber for slider in module.sliders] for module in self.modules]
        return modules, params, lfo_params, ctl_params

    def setModulesAndParams(self, modules, params, lfo_params, ctl_params, from_export=False):
        for modparams in modules:
            name = modparams[0]
            dic = MODULES[name]
            titleDic = dic.get("slider_title_dicts", None)
            lastModule = GenericPanel(self.panel, name, dic["title"], dic["synth"],
                                      dic["p1"], dic["p2"], dic["p3"], titleDic)
            self.modules.append(lastModule)
            self.addModule(lastModule)

            mute, channel, firstVel, lastVel, first, last, firstkey_pitch, loopmode, xfade, samplerpath, keymode = modparams[1:12]
            lastModule.setMute(mute)
            lastModule.trigChannel.SetValue(channel)
            lastModule.trigVelRange.SetValue((firstVel, lastVel))
            lastModule.trigKeyRange.SetValue((first, last))
            lastModule.trigFirstKey.SetValue(firstkey_pitch)
            lastModule.trigKeyMode.SetValue(keymode)
            if lastModule.synth.isSampler:
                lastModule.trigLoopmode.SetValue(loopmode)
                lastModule.trigXfade.SetValue(xfade)
                lastModule.SetSamples(samplerpath)

            if len(modparams) == 13 and modparams[12] is not None:
                envmode, graphAtt_pts, graphRel_pts, graphAtt_exp, graphRel_exp, \
                    graphAtt_dur, graphRel_dur, graphAtt_mode, graphRel_mode = modparams[12]
                lastModule.synth.graphAttAmp.SetList(graphAtt_pts)
                lastModule.synth.graphRelAmp.SetList(graphRel_pts)
                lastModule.knobGAttExp.SetValue(graphAtt_exp)
                lastModule.knobGRelExp.SetValue(graphRel_exp)
                lastModule.knobAttDur.SetValue(graphAtt_dur)
                lastModule.knobRelDur.SetValue(graphRel_dur)
                lastModule.knobGAttMode.SetValue(graphAtt_mode)
                lastModule.knobGRelMode.SetValue(graphRel_mode)
                lastModule.setEnvMode(envmode)

        slider_idx = 0
        for i, ctl_paramset in enumerate(ctl_params):
            for j, ctl_param in enumerate(ctl_paramset):
                slider = self.modules[i].sliders[j]
                slider.setMidiCtlNumber(ctl_param)
                if ctl_param is not None and not from_export and vars.vars["MIDI_ACTIVE"]:
                    if 'knobRadius' in slider.__dict__:
                        mini = slider.getMinValue()
                        maxi = slider.getMaxValue()
                        value = slider.GetValue()
                        if slider.log:
                            norm_init = toLog(value, mini, maxi)
                            slider.midictl = Midictl(ctl_param, 0, 1.0, norm_init)
                        else:
                            slider.midictl = Midictl(ctl_param, mini, maxi, value)
                        slider.trigFunc = TrigFunc(self.modules[i].synth._midi_metro, slider.valToWidget)
                    else:
                        if self.modules[i].synth._params[slider_idx] is not None:
                            self.modules[i].synth._params[slider_idx].assignMidiCtl(ctl_param, slider)
                        slider_idx += 1

        for i, lfo_param in enumerate(lfo_params):
            self.modules[i].reinitLFOS(lfo_param)

        for i, paramset in enumerate(params):
            if len(paramset) == 10:  # old zy
                paramset = paramset[:5] + [1.] + paramset[5:]
            for j, param in enumerate(paramset):
                self.modules[i].sliders[j].SetValue(param)

        self.refresh()

    def setServerPanelFooter(self, s=None):
        if s is None:
            if self.openedFile:
                s = os.path.split(self.openedFile)[1]
                s = ".".join(s.split('.')[:-1]).replace('_', ' ')
            else:
                s = ""
        self.serverPanel.footer.setLabel(s)
        self.serverPanel.Layout()

    def save_bkp_file(self, evt):
        if app.IsActive():
            try:
                self.savefile(self.bkp_file, True)
            except Exception as e:
                pass

    def savefile(self, filename, from_backup=False):

        def _f(x):
            if isinstance(x, dict):
                r = {}
                for k, v in x.items():
                    r[k] = _f(v)
                return r
            elif not isinstance(x, (tuple, list)):
                return x
            else:
                r = []
                for i in x:
                    if i is None:
                        r.append(None)
                    elif isinstance(i, bool):
                        r.append(i)
                    elif isinstance(i, str):
                        r.append(i)
                    elif isinstance(i, (list, tuple)):
                        r.append(_f(i))
                    elif isinstance(i, dict):
                        r.append(_f(i))
                    else:
                        r.append(round(i, 6))
                return r

        modules, params, lfo_params, ctl_params = self.getModulesAndParams()
        serverSettings = self.serverPanel.getServerSettings()
        postProcSettings = self.serverPanel.getPostProcSettings()
        out_drv = self.serverPanel.getSelectedOutputDriverName()
        midi_itf = self.serverPanel.getSelectedMidiInterfaceName()

        dic = _f({
            "server": serverSettings, "postproc": postProcSettings,
            "modules": modules, "params": params, "lfo_params": lfo_params,
            "ctl_params": ctl_params,
            "output_driver": out_drv, "midi_interface": midi_itf
        })
        if not filename.endswith(vars.constants["ZYNE_B_FILE_EXT"]):
            filename = f"{filename}{vars.constants['ZYNE_B_FILE_EXT']}"
        with open(filename, "w") as f:
            f.write(json.dumps(dic))
        if not from_backup:
            self.openedFile = filename
            self.SetTitle(f"{vars.constants['WIN_TITLE']} Synth - " + os.path.split(filename)[1])
            self.setServerPanelFooter()
            self.updateLastSavedInPreferencesFile(filename)

    def openfile(self, filename):
        try:
            with open(filename, "r") as json_file:
                dic = json.load(json_file)
        except Exception as e:
            # try to read original zy file notation via eval
            with open(filename, "r") as f:
                text = f.read()
            try:
                dic = eval(text)
            except Exception as e:
                wx.MessageBox(
                    f'The following error occurred when loading {filename}:\n"{e}"', 'Warning',
                    wx.OK | wx.ICON_WARNING)
        self.deleteAllModules()
        self.serverPanel.shutdown()
        self.serverPanel.boot()
        self.openedFile = ""
        if not filename.endswith(vars.constants["DEFAULT_ZY_NAME"]) and not filename.endswith(vars.constants["BACKUP_ZY_NAME"]):
            self.openedFile = filename
        self.serverPanel.setServerSettings(dic["server"])
        if "postproc" in dic:
            self.serverPanel.setPostProcSettings(dic["postproc"])
        if "output_driver" in dic:
            self.serverPanel.setDriverByString(dic["output_driver"])
        if "midi_interface" in dic:
            self.serverPanel.setInterfaceByString(dic["midi_interface"])
        fn = os.path.split(filename)[1]
        if self.openedFile == "":
            self.SetTitle(f"{vars.constants['WIN_TITLE']} Synth")
            self.setServerPanelFooter("")
        else:
            self.SetTitle(f"{vars.constants['WIN_TITLE']} Synth - {fn}")
            self.setServerPanelFooter()
        if len(dic["modules"]) and len(dic["modules"][0]) == 2:  # update old set
            for m in dic["modules"]:
                m.extend([0, 1, 127, 0, 127, 0, 0, 0, ""])
        self.setModulesAndParams(dic["modules"], dic["params"], dic["lfo_params"], dic["ctl_params"])

    def onAddModule(self, evt):
        name = self.moduleNames[evt.GetId()-vars.constants["ID"]["Modules"]]
        dic = MODULES[name]
        titleDic = dic.get("slider_title_dicts", None)
        self.modules.append(GenericPanel(self.panel, name, dic["title"], dic["synth"],
                                         dic["p1"], dic["p2"], dic["p3"], titleDic))
        self.addModule(self.modules[-1])
        wx.CallAfter(self.SetFocus)

    def addModule(self, mod):
        self.refreshOutputSignal()
        self.panel.sizer.Add(mod, 0, wx.ALL, 1)
        wx.CallAfter(self.OnSize, wx.CommandEvent())

    def deleteModule(self, module):
        if self.selected == self.modules.index(module):
            self.selected = None
        for frame in module.lfo_frames:
            if frame is not None:
                del frame.panel.synth
                frame.Destroy()
        module.synth.__del__()
        wx.CallAfter(module.Destroy)
        self.modules.remove(module)
        self.refreshOutputSignal()
        wx.CallAfter(self.OnSize, wx.CommandEvent())

    def deleteAllModules(self):
        for module in self.modules:
            for frame in module.lfo_frames:
                if frame is not None:
                    del frame.panel.synth
                    frame.Destroy()
            module.synth.__del__()
            wx.CallAfter(module.Destroy)
        self.modules = []
        self.refreshOutputSignal()
        self.serverPanel.resetVirtualKeyboard()
        wx.CallAfter(self.OnSize, wx.CommandEvent())

    def refreshOutputSignal(self):
        if len(self.modules) == 0:
            out = Sig(0.0)
        else:
            for i, mod in enumerate(self.modules):
                if i == 0:
                    out = Sig(mod.synth.out)
                else:
                    out = out + Sig(mod.synth.out)
        self.serverPanel.fsserver._modMix.value = out
        self.serverPanel.fsserver._outSig.value = self.serverPanel.fsserver._modMix

    def refresh(self):
        self.panel.sizer.Layout()
        self.Refresh()

    def showAbout(self, evt):
        info = AboutDialogInfo()

        info.SetDescription(
            f"{vars.constants['WIN_TITLE']} is a simple soft synthesizer allowing the "
            "user to create original sounds and export bank of samples.\n\n"
            "Zyne_B is written with Python and WxPython and uses pyo as its audio engine.\n\n"
            "A special thank to Jean-Michel Dumas for beta testing and a lots of ideas!")

        info.SetName(vars.constants["WIN_TITLE"])
        info.SetVersion(f'{vars.constants["VERSION"]}')
        info.SetCopyright(f'© {vars.constants["YEAR"]} Olivier Bélanger – Hans-Jörg Bibiko')
        AboutBox(info)


class ZyneApp(wx.App):
    def OnInit(self):
        self.frame = ZyneFrame(None)
        self.frame.SetPosition((45 + 10 * self.frame.number_of_instances, 90 + 10 * self.frame.number_of_instances))
        return True

    def MacOpenFile(self, filename):
        self.frame.openfile(filename)


if __name__ == '__main__':
    file = None
    if len(sys.argv) >= 2:
        file = sys.argv[1]
    vars.readPreferencesFile()
    app = ZyneApp(0)
    app.SetAppName(vars.constants["WIN_TITLE"])
    app.SetAppDisplayName(vars.constants["WIN_TITLE"])
    splash = ZyneSplashScreen(
        None, os.path.join(vars.constants["RESOURCES_PATH"], "ZyneSplash.png"), app.frame)
    if file:
        app.frame.openfile(file)
    app.MainLoop()
