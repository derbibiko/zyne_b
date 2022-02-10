#!/usr/bin/env python3
# encoding: utf-8

import json
import os
import sys
import wx
import Resources.audio as audio
import Resources.tutorial as tutorial
import Resources.variables as vars
import wx.richtext as rt
import wx.lib.scrolledpanel as scrolled
from Resources.audio import get_output_devices, get_midi_input_devices
from Resources.panels import *
from Resources.preferences import PreferencesDialog
from Resources.splash import ZyneSplashScreen
from Resources.widgets import ZB_Keyboard
from Resources.utils import toLog


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

        self.rtc = rt.RichTextCtrl(self, style=wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER)
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
    def __init__(self, parent, title="Export Samples...", pos=wx.DefaultPosition, size=wx.DefaultSize):
        wx.Dialog.__init__(self, parent, id=1, title=title, pos=pos, size=size)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, "Export settings for sampled sounds."), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
    
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, -1, "Common file name:"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.filename = wx.TextCtrl(self, -1, "zyne", size=(80,-1))
        box.Add(self.filename, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALL, 5)
    
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, -1, "First:"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.first = wx.TextCtrl(self, -1, "0", size=(40,-1))
        box.Add(self.first, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        box.Add(wx.StaticText(self, -1, "Last:"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.last = wx.TextCtrl(self, -1, "128", size=(40,-1))
        box.Add(self.last, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        box.Add(wx.StaticText(self, -1, "Step:"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.step = wx.TextCtrl(self, -1, "1", size=(40,-1))
        box.Add(self.step, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALL, 5)
    
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, -1, "Noteon dur:"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.noteon = wx.TextCtrl(self, -1, "1", size=(50,-1))
        box.Add(self.noteon, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        box.Add(wx.StaticText(self, -1, "Release dur:"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.release = wx.TextCtrl(self, -1, "1", size=(50,-1))
        box.Add(self.release, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALL, 5)
    
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.RIGHT|wx.TOP, 5)
    
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.SetSizer(sizer)
        self.filename.SetFocus()

class ZyneFrame(wx.Frame):
    def __init__(self, parent=None, title=f"{vars.constants['WIN_TITLE']} - Untitled", size=(966, 660)):
        wx.Frame.__init__(self, parent, id=-1, title=title, size=size)

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
        self.fileMenu.Append(vars.constants["ID"]["ResetKeyboard"], 'Reset virtual keyboard\tCtrl+Y', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onResetKeyboard, id=vars.constants["ID"]["ResetKeyboard"])
        self.fileMenu.Append(vars.constants["ID"]["Retrig"], 'Retrig virtual notes\tCtrl+T', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onRetrig, id=vars.constants["ID"]["Retrig"])
        if wx.Platform != "__WXMAC__":
            self.fileMenu.AppendSeparator()
        self.fileMenu.Append(vars.constants["ID"]["Prefs"], 'Preferences...\tCtrl+,', 'Open Cecilia preferences pane', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onPreferences, id=vars.constants["ID"]["Prefs"])
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(vars.constants["ID"]["Run"], 'Run\tCtrl+R', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onRun, id=vars.constants["ID"]["Run"])
        self.fileMenu.AppendSeparator()
        if wx.Platform == "__WXMAC__" and '/Zyne_B.app' in sys.executable:
            self.fileMenu.AppendSeparator()
            self.fileMenu.Append(vars.constants["ID"]["NewInstance"], 'Open new Zyne_B Instance\tCtrl+Shift+N', kind=wx.ITEM_NORMAL)
            self.Bind(wx.EVT_MENU, self.onNewInstance, id=vars.constants["ID"]["NewInstance"])
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
        self.genMenu.Append(vars.constants["ID"]["Select"], 'Select first module\tCtrl+B', kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.tabulate, id=vars.constants["ID"]["Select"])
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

        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.openedFile = ""
        self.modules = []
        self.selected = None

        self.splitWindow = wx.SplitterWindow(self, -1, style = wx.SP_LIVE_UPDATE)
        self.splitWindow.SetMinimumPaneSize(1)

        self.upperSplitWindow = wx.SplitterWindow(self.splitWindow, -1, style = wx.SP_LIVE_UPDATE)
        self.upperSplitWindow.SetMinimumPaneSize(1)
        self.upperSplitWindow.SetSashInvisible()

        self.panel = scrolled.ScrolledPanel(self.upperSplitWindow, size=size, pos=(0,28), style=wx.BORDER_NONE)
        self.panel.sizer = wx.WrapSizer()
        self.panel.SetupScrolling(scroll_x=False, scroll_y=True)

        self.serverPanel = ServerPanel(self.upperSplitWindow)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(self.panel.sizer, 1, wx.EXPAND)
        self.panel.SetSizerAndFit(mainSizer)

        self.upperSplitWindow.SplitVertically(self.serverPanel, self.panel, 80)

        self.keyboard = ZB_Keyboard(self.splitWindow, outFunction=self.serverPanel.onKeyboard)
        self.keyboard.SetMinSize((-1, 86))
        self.serverPanel.keyboard = self.keyboard
        self.serverPanel.setServerSettings(self.serverPanel.serverSettings)

        self.splitWindow.SplitHorizontally(self.upperSplitWindow, self.keyboard, 80)
        self.splitWindow.SetSashInvisible()
        self.splitWindow.Unsplit(None)

        dropTarget = MyFileDropTarget(self.panel)
        self.panel.SetDropTarget(dropTarget)
        if vars.vars["AUTO_OPEN"] == 'Default':
            self.openfile(os.path.join(vars.constants["RESOURCES_PATH"], vars.constants["DEFAULT_ZY_NAME"]))
        elif vars.vars["AUTO_OPEN"] == 'Last Saved':
            path = vars.vars["LAST_SAVED"]
            try:
                self.openfile(path)
            except:
                pass

    def tabulate(self, evt):
        num = len(self.modules)
        old = self.selected
        if num == 0:
            return
        if self.selected is None:
            self.selected = 0
        else:
            self.selected = (self.selected + 1) % num
        if old is not None:
            self.modules[old].setBackgroundColour(self.GetBackgroundColour())
        self.modules[self.selected].setBackgroundColour("#9999A7")
        item = self.genMenu.FindItemById(vars.constants["ID"]["Duplicate"])
        item.Enable(True)

    def clearSelection(self, evt):
        if self.selected is not None:
            self.modules[self.selected].setBackgroundColour(self.GetBackgroundColour())
        self.selected = None
        item = self.genMenu.FindItemById(vars.constants["ID"]["Duplicate"])
        item.Enable(False)

    def duplicateSelection(self, evt):
        if self.selected != None:
            module = self.modules[self.selected]
            name = module.name
            mute = module.mute
            params = [slider.GetValue() for slider in module.sliders]
            lfo_params = module.getLFOParams()
            dic = MODULES[name]
            self.modules.append(GenericPanel(self.panel, name, dic["title"], dic["synth"], dic["p1"], dic["p2"], dic["p3"]))
            self.addModule(self.modules[-1])
            self.modules[-1].setMute(mute)
            for j, param in enumerate(params):
                slider = self.modules[-1].sliders[j]
                slider.SetValue(param)
                slider.outFunction(param)
            self.modules[-1].reinitLFOS(lfo_params, ctl_binding=False)
            self.refresh()
            
            old = self.selected
            self.selected = len(self.modules) - 1
            self.modules[old].setBackgroundColour(self.GetBackgroundColour())
            self.modules[self.selected].setBackgroundColour("#9999A7")
            
            wx.CallAfter(self.SetFocus)

    def onNewInstance(self, evt):
        if wx.Platform == "__WXMAC__":
            p = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            if p.endswith('/Zyne_B.app'):
                os.system(f"open -n {p}")

    def onRun(self, evt):
        state = self.serverPanel.onOff.GetValue()
        evt = wx.CommandEvent(wx.EVT_TOGGLEBUTTON.typeId, self.serverPanel.onOff.GetId())
        if state:
            evt.SetInt(0)
            self.serverPanel.onOff.SetValue(False)
        else:
            evt.SetInt(1)
            self.serverPanel.onOff.SetValue(True)
        self.serverPanel.onOff.ProcessWindowEvent(evt)

    def onGenerateValues(self, evt):
        id = evt.GetId() - 10000
        if self.selected == None:
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
            self.addMenu.DeleteItem(item)
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
                self.addMenu.Append(id, 'Add %s module\tCtrl+%d' % (name, ((i+1)%10)), kind=wx.ITEM_NORMAL)
                self.Bind(wx.EVT_MENU, self.onAddModule, id=id)
            else:
                self.addMenu.Append(id, 'Add %s module\tShift+Ctrl+%d' % (name, ((i+1)%10)), kind=wx.ITEM_NORMAL)
                self.Bind(wx.EVT_MENU, self.onAddModule, id=id)
            id += 1
        self.addMenu.AppendSeparator()
        if vars.vars["EXTERNAL_MODULES"] != {}:
            moduleNames = sorted(vars.vars["EXTERNAL_MODULES"].keys())
            for i, name in enumerate(moduleNames):
                self.addMenu.Append(id, 'Add %s module' % name, kind=wx.ITEM_NORMAL)
                self.Bind(wx.EVT_MENU, self.onAddModule, id=id)
                self.moduleNames.append(name)
                MODULES.update(vars.vars["EXTERNAL_MODULES"].items())
                id += 1
            self.addMenu.AppendSeparator()
            self.addMenu.Append(vars.constants["ID"]["UpdateModules"], "Update Modules\tCtrl+U", kind=wx.ITEM_NORMAL)
            self.Bind(wx.EVT_MENU, self.updateAddModuleMenu, id=vars.constants["ID"]["UpdateModules"])

    def openMidiLearnHelp(self, evt):
        if vars.constants["IS_LINUX"]:
            size = (750, 500)
        else:
            size = (750, 500)
        lines = []
        lines.append("To assign midi controllers to module's sliders, user can use the midi learn mode.\n")
        lines.append("First, hit Shift+Ctrl+M (Shift+Cmd+M on Mac) to start midi learn mode, the server panel will change its background colour.\n")
        lines.append("When in midi learn mode, click on a slider and play with the midi controller you want to assign, the controller number will appear at both end of the slider.\n")
        lines.append("To remove a midi assignation, click a second time on the selected slider without playing with a midi controller.\n")
        lines.append("Finally, hit Shift+Ctrl+M (Shift+Cmd+M on Mac) again to leave midi learn mode. Next time you start the server, you will be able to control the sliders with your midi controller.\n\n")
        lines.append("Midi assignations are saved within the .zy file and will be automatically assigned at future launches of the synth.\n")
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
        if state:
            self.splitWindow.SplitHorizontally(self.upperSplitWindow, self.keyboard, -80)
            self.SetMinSize((460, 660))
            self.SetSize((-1, 755))
        else:
            self.splitWindow.Unsplit()
            w, h = self.serverPanel.mainBox.GetSize()
            self.SetMinSize((460, h + 30))
            self.SetSize((-1, h + 30))

    def onResetKeyboard(self, evt):
        self.serverPanel.resetVirtualKeyboard()

    def onRetrig(self, evt):
        self.serverPanel.retrigVirtualNotes()

    def OnSize(self, evt):
        self.panel.SetVirtualSize(
            (self.panel.GetSize()[0], self.panel.GetVirtualSize()[1]))
        self.panel.SetupScrolling(scroll_x=False, scroll_y=True)
        self.splitWindow.SetSashPosition(-80)
        evt.Skip()

    def onMidiLearnModeFromLfoFrame(self):
        item = self.fileMenu.FindItemById(vars.constants["ID"]["MidiLearn"])
        if item.IsChecked():
            self.serverPanel.midiLearn(False)
            vars.vars["MIDILEARN"] = False
            item.Check(False)
        else:
            self.serverPanel.midiLearn(True)
            vars.vars["MIDILEARN"] = True
            item.Check(True)

    def onMidiLearnMode(self, evt):
        if evt.GetInt():
            self.serverPanel.midiLearn(True)
            vars.vars["MIDILEARN"] = True
        else:
            self.serverPanel.midiLearn(False)
            vars.vars["MIDILEARN"] = False

    def onPreferences(self, evt):
        dlg = PreferencesDialog()
        dlg.ShowModal()
        dlg.Destroy()
    
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
        try:
            self.serverPanel.keyboardFrame.Destroy()
        except:
            pass
        for win in wx.GetTopLevelWindows():
            win.Destroy()
        self.serverPanel.shutdown()
        self.Destroy()
        sys.exit()

    def onNew(self, evt):
        self.deleteAllModules()
        self.openedFile = ""
        self.setServerPanelFooter("")
        self.SetTitle(f"{vars.constants['WIN_TITLE']} Synth - Untitled")
    
    def onSave(self, evt):
        if self.openedFile != "":
            self.savefile(self.openedFile)
        else:
            self.onSaveAs(evt)
    
    def onSaveAs(self, evt):
        if self.openedFile != "":
            filename = os.path.split(self.openedFile)[1]
        else:
            filename = "zynesynth.zy"    
        dlg = wx.FileDialog(self, "Save file as...", defaultFile=filename, style=wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path != "":
                self.savefile(path)
        dlg.Destroy()
    
    def onOpen(self, evt):
        wildcard = "Zyne files (*.zy)|*.zy"
        dlg = wx.FileDialog(self, "Choose Zyne Synth file...", wildcard=wildcard, style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if path != "":
                self.openfile(path)
        dlg.Destroy()
    
    def onExport(self, evt):
        if evt.GetId() == vars.constants["ID"]["Export"]:
            mode = "Samples"
            title = "Export samples..."
            title2 = "Exporting samples..."
            num_modules = 1
        elif evt.GetId() in [vars.constants["ID"]["ExportChord"], vars.constants["ID"]["ExportChordTracks"]]:
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
            notes = self.keyboard.getCurrentNotes()
            if len(notes) == 0:
                wx.LogMessage("Play some notes on the virtual keyboard before calling the export chords function!.")
                return
            midi_pitches = [tup[0] for tup in notes]
            midi_velocities = [tup[1] for tup in notes]
            min_pitch = min(midi_pitches)
            pitch_factors = [pit - min_pitch for pit in midi_pitches]
            amp_factors = [amp / 127.0 for amp in midi_velocities]
        elif evt.GetId() == vars.constants["ID"]["ExportTracks"]:
            mode = "Tracks"
            title = "Export samples as separated tracks..."
            title2 = "Exporting samples as separated tracks..."
            num_modules = len(self.modules)
        dlg = SamplingDialog(self, title=title, size=(450,270))
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
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
            num_iter = len(range(first,last,step)) * num_modules
            vars.vars["NOTEONDUR"] = float(dlg.noteon.GetValue())
            duration = float(dlg.release.GetValue()) + vars.vars["NOTEONDUR"]
            ext = self.serverPanel.getExtensionFromFileFormat()
            modules, params, lfo_params, ctl_params = self.getModulesAndParams()
            serverSettings = self.serverPanel.getServerSettings()
            postProcSettings = self.serverPanel.getPostProcSettings()
            self.deleteAllModules()
            self.serverPanel.reinitServer(0.001, "offline", serverSettings, postProcSettings)
            dlg2 = wx.ProgressDialog(title2, "", maximum = num_iter, parent=self,
                                   style = wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_SMOOTH)
            if vars.constants["IS_WIN"]:
                dlg2.SetSize((500, 125))
            else:
                dlg2.SetSize((500,100))
            count = 0
            for i in range(first,last,step):
                if mode == "Samples":
                    vars.vars["MIDIPITCH"] = i
                    vars.vars["MIDIVELOCITY"] = 0.707
                elif mode == "Chords":
                    vars.vars["MIDIPITCH"] = [i + fac for fac in pitch_factors]
                    vars.vars["MIDIVELOCITY"] = amp_factors
                elif mode == "Tracks":
                    vars.vars["MIDIPITCH"] = i
                    vars.vars["MIDIVELOCITY"] = 0.707
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
                    self.deleteAllModules()
                    self.serverPanel.shutdown()
                    self.serverPanel.boot()
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
                        self.deleteAllModules()
                        self.serverPanel.shutdown()
                        self.serverPanel.boot()
            dlg2.Destroy()
            self.serverPanel.reinitServer(0.05, vars.vars["AUDIO_HOST"], serverSettings, postProcSettings)
            vars.vars["MIDIPITCH"] = None
            vars.vars["MIDIVELOCITY"] = 0.707
            self.serverPanel.setAmpCallable()
            self.setModulesAndParams(modules, params, lfo_params, ctl_params)
        dlg.Destroy()
    
    def getModulesAndParams(self):
        modules = [(module.name, module.mute) for module in self.modules]
        params = [[slider.GetValue() for slider in module.sliders] for module in self.modules]
        lfo_params = [module.getLFOParams() for module in self.modules]
        ctl_params = [[slider.midictlnumber for slider in module.sliders] for module in self.modules]
        return modules, params, lfo_params, ctl_params
    
    def setModulesAndParams(self, modules, params, lfo_params, ctl_params, from_export=False):
        for name, mute in modules:
            dic = MODULES[name]
            self.modules.append(GenericPanel(self.panel, name, dic["title"], dic["synth"], dic["p1"], dic["p2"], dic["p3"]))
            self.addModule(self.modules[-1])
            self.modules[-1].setMute(mute)
        for i, paramset in enumerate(params):
            for j, param in enumerate(paramset):
                slider = self.modules[i].sliders[j]
                slider.SetValue(param)
                slider.outFunction(param)

        slider_idx = 0
        for i, ctl_paramset in enumerate(ctl_params):
            for j, ctl_param in enumerate(ctl_paramset):
                slider = self.modules[i].sliders[j]
                slider.setMidiCtlNumber(ctl_param, False)
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

    def savefile(self, filename):
        modules, params, lfo_params, ctl_params = self.getModulesAndParams()
        serverSettings = self.serverPanel.getServerSettings()
        postProcSettings = self.serverPanel.getPostProcSettings()
        out_drv = self.serverPanel.getSelectedOutputDriverName()
        midi_itf = self.serverPanel.getSelectedMidiInterfaceName()
        dic = {
            "server": serverSettings, "postproc": postProcSettings,
            "modules": modules, "params": params, "lfo_params": lfo_params,
            "ctl_params": ctl_params,
            "output_driver": out_drv, "midi_interface": midi_itf
        }
        with open(filename, "w") as f:
            f.write(json.dumps(dic))
        self.openedFile = filename
        self.SetTitle(f"{vars.constants['WIN_TITLE']} - " + os.path.split(filename)[1])
        self.setServerPanelFooter()
        self.updateLastSavedInPreferencesFile(filename)

    def openfile(self, filename):
        try:
            try:
                with open(filename, "r") as json_file:
                    dic = json.load(json_file)
            except Exception as e:
                # try to read original zy file notation via eval
                with open(filename, "r") as f:
                    text = f.read()
                dic = eval(text)
            self.deleteAllModules()
            self.serverPanel.shutdown()
            self.serverPanel.boot()
            if filename.endswith(vars.constants["DEFAULT_ZY_NAME"]):
                self.openedFile = ""
            else:
                self.serverPanel.setServerSettings(dic["server"])
                self.openedFile = filename
            if "postproc" in dic:
                self.serverPanel.setPostProcSettings(dic["postproc"])
            if "output_driver" in dic:
                self.serverPanel.setDriverByString(dic["output_driver"])
            if "midi_interface" in dic:
                self.serverPanel.setInterfaceByString(dic["midi_interface"])
            fn = os.path.split(filename)[1]
            self.SetTitle(f"{vars.constants['WIN_TITLE']} Synth - {fn}")
            if not fn.endswith(vars.constants["DEFAULT_ZY_NAME"]):
                self.setServerPanelFooter()
            wx.CallAfter(self.setModulesAndParams,
                         dic["modules"], dic["params"], dic["lfo_params"], dic["ctl_params"])
        except Exception as e:
            wx.MessageBox(
                f'The following error occurred when loading {filename}:\n"{e}"', 'Warning',
                wx.OK | wx.ICON_WARNING)

    def onAddModule(self, evt):
        name = self.moduleNames[evt.GetId()-vars.constants["ID"]["Modules"]]
        dic = MODULES[name]
        self.modules.append(GenericPanel(self.panel, name, dic["title"], dic["synth"], dic["p1"], dic["p2"], dic["p3"]))
        self.addModule(self.modules[-1])
        wx.CallAfter(self.SetFocus)
    
    def addModule(self, mod):
        mod.cbChannel.Enable(not self.serverPanel.onOff.GetValue())
        self.refreshOutputSignal()
        self.panel.sizer.Add(mod, 0, wx.ALL, 1)
        self.panel.sizer.Layout()
        wx.CallAfter(self.refresh)
        wx.CallAfter(self.OnSize, wx.CommandEvent())

    def deleteModule(self, module):
        if self.selected == self.modules.index(module):
            self.selected = None
        for frame in module.lfo_frames:
            if frame is not None:
                del frame.panel.synth
                frame.Destroy()
        module.synth.__del__()
        module.Destroy()
        self.modules.remove(module)
        self.refreshOutputSignal()
        self.OnSize(wx.CommandEvent())
        self.refresh()

    def deleteAllModules(self):
        for module in self.modules:
            for frame in module.lfo_frames:
                if frame is not None:
                    del frame.panel.synth
                    frame.Destroy()
            module.synth.__del__()
            module.Destroy()
        self.modules = []
        self.refreshOutputSignal()
        self.serverPanel.resetVirtualKeyboard()
        self.OnSize(wx.CommandEvent())
        self.refresh()
    
    def refreshOutputSignal(self):
        if len(self.modules) == 0:
            out = Sig(0.0)
        else:
            for i,mod in enumerate(self.modules):
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
        self.frame.SetPosition((50,50))
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

