"""
Copyright 2009-2015 Olivier Belanger - modifications by Hans-Jörg Bibiko 2022

Some classes of this file were parts of pyo's _wxwidgets.py,
a python module to help digital signal processing script creation.
"""

import copy
import wx
import Resources.variables as vars
from Resources.utils import *


if "phoenix" in wx.version():
    wx.GraphicsContext_Create = wx.GraphicsContext.Create
    wx.EmptyBitmap = wx.Bitmap
    wx.EmptyImage = wx.Image
    wx.BitmapFromImage = wx.Bitmap
    wx.Image_HSVValue = wx.Image.HSVValue
    wx.Image_HSVtoRGB = wx.Image.HSVtoRGB


HEADTITLE_BACK_COLOUR = "#9999A0"
BACKGROUND_COLOUR = "#EBEBEB"
CHAR_SET = set("0123456789.-")


class ZB_HeadTitle(wx.Panel):
    def __init__(self, parent, title, font=None, togcall=None):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.SetBackgroundColour(HEADTITLE_BACK_COLOUR)
        mainsizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        if togcall is not None:
            self.toggle = wx.CheckBox(self, id=-1)
            mainsizer.Add(self.toggle, 0, wx.LEFT | wx.ALL, 2)
            self.toggle.Bind(wx.EVT_CHECKBOX, togcall)
        self.label = wx.StaticText(self, -1, title)
        if font is not None:
            self.label.SetFont(font)
        self.label.SetForegroundColour(wx.WHITE)
        sizer.Add(self.label, 0, wx.CENTER | wx.ALL, 2)
        mainsizer.Add(sizer, 1)
        self.SetSizerAndFit(mainsizer)

    def setLabel(self, s):
        if len(s) > 27:
            self.label.SetLabel(s[:27].strip() + '..')
            self.label.SetToolTip(wx.ToolTip(s))
        else:
            self.label.SetLabel(s)


class ZB_Base_Control(wx.Panel):
    def __init__(self, parent, minvalue, maxvalue, init=None,
                 pos=(0, 0), size=(200, 16),
                 log=False, powoftwo=False, integer=False,
                 outFunction=None, label=""):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, pos=pos, size=size,
                          style=wx.NO_BORDER | wx.WANTS_CHARS | wx.EXPAND)

        self.parent = parent
        self.pos = self.FromDIP(wx.Point(pos))
        self.size = self.FromDIP(wx.Size(size))
        self.SetSize(self.size)
        self.SetPosition(self.pos)
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.backgroundColour = vars.constants["BACKCOLOUR"]
        self.foregroundColour = vars.constants["FORECOLOUR"]
        self.SetBackgroundColour(self.backgroundColour)
        self.SetForegroundColour(self.foregroundColour)
        self.outFunction = outFunction
        self.integer = integer
        self.log = log
        self.powoftwo = powoftwo
        if self.powoftwo:
            self.integer = True
            self.log = False
        self.borderWidth = 1
        self.selected = False
        self._enable = True
        self.midictl = None
        self.midictlnumber = None
        self.last_midi_val = 0
        self.label = label
        self.new = ""
        self.value = 0
        self.display_value = 0
        self.SetRange(minvalue, maxvalue)

        if log:
            self.toexp_c0 = p_mathlog10(minvalue)
            self.toexp_c1 = p_mathlog10(maxvalue) - self.toexp_c0

        if init is not None:
            self.SetValue(init)
            self.init = init
        else:
            self.SetValue(minvalue)
            self.init = minvalue

        self.clampPos()

        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.MouseUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.DoubleClick)
        self.Bind(wx.EVT_MOTION, self.MouseMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_CHAR, self.onChar)
        self.Bind(wx.EVT_KILL_FOCUS, self.LooseFocus)

        self.handleNewValue()

    def onChar(self, event):
        if self.selected:
            old_val = self.GetValue()
            char = ""
            if event.GetKeyCode() in range(wx.WXK_NUMPAD0, wx.WXK_NUMPAD9 + 1):
                char = str(event.GetKeyCode() - wx.WXK_NUMPAD0)

            elif event.GetKeyCode() in [wx.WXK_SUBTRACT, wx.WXK_NUMPAD_SUBTRACT]:
                char = "-"

            elif event.GetKeyCode() in [wx.WXK_DECIMAL, wx.WXK_NUMPAD_DECIMAL]:
                char = "."

            elif event.GetKeyCode() == wx.WXK_BACK:
                if self.new != "":
                    self.new = self.new[0:-1]

            elif event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
                try:
                    self.SetValue(float(self.new))
                except Exception:
                    self.SetValue(float(old_val))
                evt = wx.FocusEvent(wx.EVT_KILL_FOCUS.evtType[0], self.GetId())
                wx.PostEvent(self.GetEventHandler(), evt)

            elif event.GetKeyCode() == wx.WXK_ESCAPE:
                self.SetValue(float(old_val))
                evt = wx.FocusEvent(wx.EVT_KILL_FOCUS.evtType[0], self.GetId())
                wx.PostEvent(self.GetEventHandler(), evt)

            elif event.GetKeyCode() in [wx.WXK_LEFT, wx.WXK_DOWN]:
                if event.GetKeyCode() == wx.WXK_DOWN and not self.integer:
                    new_val = old_val - 0.01
                else:
                    if self.integer:
                        new_val = old_val - 1
                    else:
                        new_val = old_val - 0.001
                try:
                    self.SetValue(float(new_val), True)
                    self.SetFocus()
                except Exception:
                    self.SetValue(float(old_val))
                    self.selected = False

            elif event.GetKeyCode() in [wx.WXK_RIGHT, wx.WXK_UP]:
                if event.GetKeyCode() == wx.WXK_UP and not self.integer:
                    new_val = old_val + 0.01
                else:
                    if self.integer:
                        new_val = old_val + 1
                    else:
                        new_val = old_val + 0.001
                try:
                    self.SetValue(float(new_val), True)
                    self.SetFocus()
                except Exception:
                    self.SetValue(float(old_val))
                    self.selected = False

            elif event.GetKeyCode() < 256:
                char = chr(event.GetKeyCode())

            if char in CHAR_SET:
                self.new += char
            if not self.selected:
                wx.GetTopLevelWindows()[0].Raise()
            wx.CallAfter(self.Refresh)
            event.StopPropagation()

    def getLabel(self):
        return self.label

    def setMidiCtlNumber(self, x):
        self.midictlnumber = x
        self.Refresh()

    def getMidiCtlNumber(self):
        return self.midictlnumber

    def getMinValue(self):
        return self.minvalue

    def getMaxValue(self):
        return self.maxvalue

    def Enable(self):
        self._enable = True
        wx.CallAfter(self.Refresh)

    def Disable(self):
        self._enable = False
        wx.CallAfter(self.Refresh)

    def getInit(self):
        return self.init

    def SetRange(self, minvalue, maxvalue):
        self.minvalue = minvalue
        self.maxvalue = maxvalue

    def getRange(self):
        return [self.minvalue, self.maxvalue]

    def handleNewValue(self):
        if self.outFunction:
            self.outFunction(self.GetValue())

        if self.integer:
            self.display_value = str(self.GetValue())
        else:
            val = self.GetValue()
            absval = abs(val)
            if absval >= 1000:
                self.display_value = "%.0f" % val
            elif absval >= 100:
                self.display_value = "%.1f" % val
            elif absval >= 10:
                self.display_value = "%.2f" % val
            elif absval < 10:
                self.display_value = "%.3f" % val
        self.setFocusToKeyboard()

    def setFocusToKeyboard(self):
        if not vars.vars["VIRTUAL"] or self.selected:
            return
        try:
            wx.GetTopLevelWindows()[0].Raise()
            wx.GetTopLevelWindows()[0].keyboard.SetFocus()
        except Exception as e:
            pass

    def SetValue(self, value, keepSelected=False):
        self.selected = keepSelected
        if self.HasCapture():
            self.ReleaseMouse()
        if self.powoftwo:
            value = powOfTwoToInt(value)
        value = clamp(value, self.minvalue, self.maxvalue)
        if self.log:
            t = toLog(value, self.minvalue, self.maxvalue)
            self.value = interpFloat(t, self.minvalue, self.maxvalue)
        else:
            t = tFromValue(value, self.minvalue, self.maxvalue)
            self.value = interpFloat(t, self.minvalue, self.maxvalue)
        if self.integer:
            self.value = int(self.value)
        if self.powoftwo:
            self.value = powOfTwo(self.value)
        self.handleNewValue()
        self.clampPos()
        wx.CallAfter(self.setFocusToKeyboard)
        wx.CallAfter(self.Refresh)

    def GetValue(self):
        if self.log:
            t = tFromValue(self.value, self.minvalue, self.maxvalue)
            # := val = toExp(t, self.minvalue, self.maxvalue)
            val = 10**(t * self.toexp_c1 + self.toexp_c0)
        else:
            val = self.value
        if self.integer:
            val = int(val)
        return val

    def valToWidget(self):
        if self.midictl is not None:
            val = self.midictl.get()
            if val != self.last_midi_val:
                self.last_midi_val = val
                if self.log:
                    # := val = toExp(val, self.minvalue, self.maxvalue)
                    val = 10**(val * self.toexp_c1 + self.toexp_c0)
                self.SetValue(val)

    def clampPos(self):
        pass

    def LooseFocus(self, event):
        self.new = ""
        self.selected = False
        wx.CallAfter(self.Refresh)
        event.Skip()

    def getLabel(self):
        return self.label

    def getLog(self):
        return self.log

    def setBackgroundColour(self, col):
        self.SetBackgroundColour(col)
        self.backgroundColour = col
        self.Refresh()

    def OnResize(self, evt):
        self.clampPos()
        self.Refresh()

    def SetLabel(self, label):
        self.label = label


class ZB_ControlSlider(ZB_Base_Control):
    def __init__(self, parent, minvalue, maxvalue, init=None,
                 pos=(0, 0), size=(-1, -1),
                 log=False, integer=False, powoftwo=False,
                 outFunction=None, label="", orient=wx.HORIZONTAL):

        self.orient = orient

        if self.orient == wx.VERTICAL:
            size = (40, -1)
        else:
            size = (-1, 16)
        if self.orient == wx.VERTICAL:
            self.knobSize = 17
            self.knobHalfSize = 8
            self.sliderWidth = size[0] - 29
        else:
            self.knobSize = 40
            self.knobHalfSize = 20
            self.sliderHeight = size[1] - 5

        super().__init__(parent, minvalue, maxvalue, init,
                         pos=pos, size=size,
                         log=log, integer=integer, powoftwo=powoftwo,
                         outFunction=outFunction, label=label)

        self.parent = parent
        self.SetMinSize(self.GetSize())
        self.fromdip1 = self.FromDIP(1)
        self.fromdip2 = self.FromDIP(2)
        self.fromdip3 = self.FromDIP(3)
        self.fromdip12 = self.FromDIP(12)
        self.clampPos()
        self.pos_offset = 0

        self.knobSize = self.FromDIP(self.knobSize)
        self.knobHalfSize = self.FromDIP(self.knobHalfSize)
        if self.orient == wx.VERTICAL:
            self.sliderWidth = self.FromDIP(self.sliderWidth)
        else:
            self.sliderHeight = self.FromDIP(self.sliderHeight)

        if vars.constants["IS_WIN"] or vars.constants["IS_LINUX"]:
            self.dcref = wx.BufferedPaintDC
            self.font = wx.Font(7, wx.FONTFAMILY_TELETYPE,
                                wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        else:
            self.dcref = wx.PaintDC
            self.font = wx.Font(10, wx.FONTFAMILY_TELETYPE,
                                wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

    def scale(self):
        if self.orient == wx.VERTICAL:
            h = self.GetSize()[1]
            inter = tFromValue(
                h - self.pos, self.knobHalfSize, self.GetSize()[1] - self.knobHalfSize)
        else:
            inter = tFromValue(
                self.pos, self.knobHalfSize, self.GetSize()[0] - self.knobHalfSize)
        if not self.integer:
            return interpFloat(inter, self.minvalue, self.maxvalue)
        elif self.powoftwo:
            return powOfTwo(int(interpFloat(inter, self.minvalue, self.maxvalue)))
        else:
            return int(interpFloat(inter, self.minvalue, self.maxvalue))

    def MouseDown(self, evt):
        if evt.ShiftDown():
            self.DoubleClick(evt)
            return
        if self._enable:
            w, h = self.GetSize()
            pos = evt.GetPosition()
            if self.orient == wx.VERTICAL:
                if not wx.Rect(0, self.pos - self.knobHalfSize, w, self.knobSize).Contains(pos):
                    self.pos = clamp(evt.GetPosition()[1], self.knobHalfSize, h - self.knobHalfSize)
                    self.value = self.scale()
                    self.handleNewValue()
                    self.pos_offset = 0
                else:
                    self.pos_offset = pos[1] - self.pos
            else:
                if not wx.Rect(self.pos - self.knobHalfSize, 0, self.knobSize, h).Contains(pos):
                    self.pos = clamp(evt.GetPosition()[0], self.knobHalfSize, w - self.knobHalfSize)
                    self.value = self.scale()
                    self.handleNewValue()
                    self.pos_offset = 0
                else:
                    self.pos_offset = pos[0] - self.pos
            self.CaptureMouse()
            self.selected = False
            self.Refresh()
        evt.Skip()

    def MouseUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()

    def DoubleClick(self, event):
        if self._enable:
            self.SetFocus()
            w, h = self.GetSize()
            pos = event.GetPosition()
            if self.orient == wx.VERTICAL:
                if wx.Rect(0, self.pos - self.knobHalfSize, w, self.knobSize).Contains(pos):
                    self.selected = True
            else:
                if wx.Rect(self.pos - self.knobHalfSize, 0, self.knobSize, h).Contains(pos):
                    self.selected = True
            self.Refresh()
        event.Skip()

    def MouseMotion(self, evt):
        if self._enable:
            size = self.GetSize()
            if self.HasCapture():
                if self.orient == wx.VERTICAL:
                    self.pos = clamp(evt.GetPosition()[1] - self.pos_offset, self.knobHalfSize, size[1] - self.knobHalfSize)
                else:
                    self.pos = clamp(evt.GetPosition()[0] - self.pos_offset, self.knobHalfSize, size[0] - self.knobHalfSize)
                self.value = self.scale()
                self.handleNewValue()
                self.selected = False
                self.Refresh()

    def OnResize(self, evt):
        self.clampPos()
        self.Refresh()

    def clampPos(self):
        size = self.GetSize()
        if self.powoftwo:
            val = powOfTwoToInt(self.value)
        else:
            val = self.value
        if self.orient == wx.VERTICAL:
            self.pos = tFromValue(
                val, self.minvalue, self.maxvalue) * (size[1] - self.knobSize) + self.knobHalfSize
            self.pos = clamp(size[1] - self.pos, self.knobHalfSize, size[1] - self.knobHalfSize)
        else:
            self.pos = tFromValue(
                val, self.minvalue, self.maxvalue) * (size[0] - self.knobSize) + self.knobHalfSize
            self.pos = clamp(self.pos, self.knobHalfSize, size[0] - self.knobHalfSize)

    def OnPaint(self, evt):
        w, h = self.GetSize()

        if w <= 0 or h <= 0:
            evt.Skip()
            return

        dc = self.dcref(self)
        gc = wx.GraphicsContext_Create(dc)

        dc.SetBrush(wx.Brush(self.backgroundColour, wx.SOLID))
        dc.Clear()

        # Draw background
        dc.SetPen(wx.Pen(self.backgroundColour, width=self.borderWidth, style=wx.SOLID))
        dc.DrawRectangle(0, 0, w, h)

        # Draw inner part
        if self._enable:
            sliderColour = "#999999"
        else:
            sliderColour = "#BBBBBB"
        if self.orient == wx.VERTICAL:
            w2 = (w - self.sliderWidth) // 2
            rec = wx.Rect(w2, 0, self.sliderWidth, h)
            brush = gc.CreateLinearGradientBrush(w2, 0, w2 + self.sliderWidth, 0, "#666666", sliderColour)
        else:
            h2 = self.sliderHeight // 4
            rec = wx.Rect(0, h2, w, self.sliderHeight)
            brush = gc.CreateLinearGradientBrush(0, h2, 0, h2 + self.sliderHeight, "#666666", sliderColour)
        gc.SetBrush(brush)
        gc.DrawRoundedRectangle(rec[0], rec[1], rec[2], rec[3], self.fromdip2)

        if self.midictlnumber is not None:
            if vars.constants["IS_WIN"] or vars.constants["IS_LINUX"]:
                dc.SetFont(wx.Font(6, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            else:
                dc.SetFont(wx.Font(9, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            dc.SetTextForeground("#FFFFFF")
            ctl = str(self.midictlnumber)
            if self.orient == wx.VERTICAL:
                dc.DrawLabel(ctl, wx.Rect(w2, self.fromdip2, self.sliderWidth, self.fromdip12), wx.ALIGN_CENTER)
                dc.DrawLabel(ctl, wx.Rect(w2, h - self.fromdip12, self.sliderWidth, self.fromdip12), wx.ALIGN_CENTER)
            else:
                dc.DrawLabel(ctl, wx.Rect(self.fromdip2, self.fromdip1, h, h), wx.ALIGN_CENTER)
                dc.DrawLabel(ctl, wx.Rect(w - h, self.fromdip1, h, h), wx.ALIGN_CENTER)

        # Draw knob
        if self._enable:
            knobColour = "#888888"
        else:
            knobColour = "#DDDDDD"
        if self.orient == wx.VERTICAL:
            rec = wx.Rect(0, self.pos - self.knobHalfSize, w, self.knobSize - self.FromDIP(1))
            if self.selected:
                brush = wx.Brush("#333333", wx.SOLID)
            else:
                brush = gc.CreateLinearGradientBrush(0, 0, w, 0, "#323232", knobColour)
            gc.SetBrush(brush)
            gc.DrawRoundedRectangle(rec[0], rec[1], rec[2], rec[3], self.FromDIP(3))
        else:
            rec = wx.Rect(int(self.pos) - self.knobHalfSize, 0, self.knobSize - self.FromDIP(1), h)
            if self.selected:
                brush = wx.Brush("#333333", wx.SOLID)
            else:
                brush = gc.CreateLinearGradientBrush(
                    self.pos - self.knobHalfSize, 0, self.pos + self.knobHalfSize, 0, "#323232", knobColour
                )
            gc.SetBrush(brush)
            gc.DrawRoundedRectangle(rec[0], rec[1], rec[2], rec[3], self.fromdip3)

        dc.SetFont(self.font)

        # Draw text
        if self.selected and self.new:
            val = self.new
        else:
            val = self.display_value
        if vars.constants["IS_LINUX"]:
            width = len(val) * (dc.GetCharWidth() - 3)
        else:
            width = len(val) * dc.GetCharWidth()
        dc.SetTextForeground(wx.WHITE)
        dc.DrawLabel(val, rec, wx.ALIGN_CENTER)

        evt.Skip()


class ZyneB_ControlSlider(ZB_ControlSlider):
    def __init__(self, parent, minvalue, maxvalue, init=None,
                 pos=(0, 0), size=(200, 16),
                 log=False, integer=False, powoftwo=False,
                 outFunction=None, label="", orient=wx.HORIZONTAL):
        super().__init__(parent, minvalue, maxvalue, init,
                         pos, size,
                         log, integer, powoftwo,
                         outFunction, label=label, orient=orient)
        self.parent = parent

    def setValue(self, x):
        wx.CallAfter(self.SetValue, x)

    def MouseDown(self, evt):
        if vars.vars["MIDILEARN"]:
            if vars.vars["LEARNINGSLIDER"] is None:
                vars.vars["LEARNINGSLIDER"] = self
                self.Disable()
            elif vars.vars["LEARNINGSLIDER"] == self:
                vars.vars["LEARNINGSLIDER"].setMidiCtlNumber(None)
                vars.vars["LEARNINGSLIDER"] is None
                self.Enable()
            else:
                vars.vars["LEARNINGSLIDER"].Enable()
                vars.vars["LEARNINGSLIDER"] = self
                self.Disable()
            evt.StopPropagation()
        else:
            ZB_ControlSlider.MouseDown(self, evt)


class ZB_ControlKnob(ZB_Base_Control):
    def __init__(self, parent, minvalue, maxvalue, init=None,
                 pos=(0, 0), size=(44, 74),
                 log=False, integer=False,
                 outFunction=None, label=''):

        self.knobCenterPosX = int(size[0] / 2)
        self.knobRadius = 14
        self.knobCenterPosY = self.knobRadius + 18
        self.knobStartAngle = 18 * p_math_pi / 180  # 18° := start angle
        self.knobEndAngle = 2 * p_math_pi - self.knobStartAngle

        if vars.constants["IS_MAC"]:
            self.font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        else:
            self.font = wx.Font(7, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        super().__init__(parent, minvalue, maxvalue, init,
                         pos=pos, size=size,
                         log=log, integer=integer,
                         outFunction=outFunction, label=label)
        self.parent = parent
        self.SetMinSize(self.GetSize())
        self.knobRadius = self.FromDIP(self.knobRadius)
        self.knobCenterPosX = self.FromDIP(self.knobCenterPosX)
        self.knobCenterPosY = self.FromDIP(self.knobCenterPosY)
        self.knobRec = wx.Rect(self.knobCenterPosX - self.knobRadius - self.FromDIP(5),
                               self.knobCenterPosY - self.knobRadius - self.FromDIP(5),
                               2 * self.knobRadius + self.FromDIP(10), 2 * self.knobRadius + self.FromDIP(10))

        self.knobInnerColour = wx.Colour("#bebebe")
        self.knobColour = wx.Colour(self.foregroundColour.red, self.foregroundColour.green, self.foregroundColour.blue)
        self.fromdip1 = self.FromDIP(1)
        self.fromdip2 = self.FromDIP(2)
        self.fromdip3 = self.FromDIP(3)
        self.fromdip4 = self.FromDIP(4)
        self.fromdip5 = self.FromDIP(5)
        self.fromdip9 = self.FromDIP(9)
        self.fromdip11 = self.FromDIP(11)

    def MouseDown(self, evt):
        if evt.ShiftDown() and not evt.Dragging():
            self.DoubleClick(evt)
            return
        if self._enable:
            pos = evt.GetPosition()
            if self.knobRec.Contains(pos):
                self.clickPos = wx.GetMousePosition()
                self.oldValue = self.value
                self.CaptureMouse()
                self.selected = False
            self.Refresh()
        evt.Skip()

    def MouseUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()

    def DoubleClick(self, event):
        if self._enable:
            self.SetFocus()
            w, h = self.GetSize()
            pos = event.GetPosition()

            # check for number field is pressed
            reclab = wx.Rect(self.FromDIP(5), self.FromDIP(55), w-self.FromDIP(10), self.FromDIP(13))
            if reclab.Contains(pos):
                self.selected = True

            # check for knob area was pressed
            if not self.selected and self.knobRec.Contains(pos):
                try:
                    _rad = None
                    _x = self.knobCenterPosX - pos[0]
                    _y = self.knobCenterPosY - pos[1]
                    if _x == 0 and _y <= 0:
                        pass
                    elif _x == 0 and _y > 0:
                        _rad = p_math_pi
                    elif _y == 0:
                        _rad = p_math_pi / 2
                        if _x < 0:
                            _rad *= 3
                    else:
                        _rad = p_mathatan(_x / _y)
                        if _x > 0 and _y < 0:
                            _rad = 0 - _rad
                        elif _x < 0 and _y < 0:
                            _rad = 2 * p_math_pi - _rad
                        elif _x > 0 and _y > 0:
                            _rad = p_math_pi - _rad
                        elif _x < 0 and _y > 0:
                            _rad = p_math_pi - _rad
                    if _rad is not None:
                        _v = (_rad - self.knobStartAngle) / (self.knobEndAngle - self.knobStartAngle) * \
                             (self.maxvalue - self.minvalue) + self.minvalue
                        if self.log:
                            _v = toExp(tFromValue(_v, self.minvalue, self.maxvalue),
                                       self.minvalue, self.maxvalue)
                        self.SetValue(_v)
                except Exception as e:
                    pass

            self.Refresh()
        event.Skip()

    def MouseMotion(self, evt):
        if self._enable:
            if evt.Dragging() and evt.LeftIsDown() and self.HasCapture():
                pos = wx.GetMousePosition()
                offY = self.clickPos[1] - pos[1]  # fast changes, up +, down -
                offX = self.clickPos[0] - pos[0]  # slow changes, right +, left -
                off = 0.005 * offY * (self.maxvalue - self.minvalue) - \
                    0.001 * offX * (self.maxvalue - self.minvalue)
                self.value = clamp(self.oldValue + off, self.minvalue, self.maxvalue)
                self.handleNewValue()
                self.selected = False
                self.Refresh()

    def OnPaint(self, evt):
        w, h = self.GetSize()

        if vars.constants["IS_WIN"]:
            dc = wx.GCDC(wx.BufferedPaintDC(self))
            dc.GetGraphicsContext().SetAntialiasMode(True)
        else:
            dc = wx.BufferedPaintDC(self)

        dc.SetBrush(wx.Brush(self.backgroundColour, wx.SOLID))
        dc.SetTextForeground(self.foregroundColour)
        dc.Clear()

        # Draw background
        if self._enable:
            dc.SetBrush(wx.Brush(self.backgroundColour, wx.SOLID))
            dc.SetPen(wx.Pen(self.backgroundColour, width=0, style=wx.SOLID))
        else:
            dc.SetBrush(wx.Brush("#DDDDDD99", wx.SOLID))
            dc.SetPen(wx.Pen("#DDDDDD", width=0, style=wx.SOLID))
        dc.DrawRectangle(0, 0, w, h)

        dc.SetFont(self.font)

        # Draw text label
        reclab = wx.Rect(0, self.fromdip1, w, self.fromdip9)
        dc.DrawLabel(self.label, reclab, wx.ALIGN_CENTER_HORIZONTAL)

        recval = wx.Rect(self.fromdip1, self.knobCenterPosY + self.knobRadius + self.fromdip9, w - self.fromdip1, self.fromdip11)

        if self.selected:
            dc.SetPen(wx.Pen('#AAAAAA'))
            dc.SetBrush(wx.Brush(wx.WHITE, wx.TRANSPARENT))
            dc.DrawRoundedRectangle(recval, self.fromdip4)

        # Draw knob
        ph = interpFloat(tFromValue(self.value, self.minvalue, self.maxvalue),
                         self.knobStartAngle, self.knobEndAngle)
        lendx = self.knobCenterPosX - self.knobRadius * p_mathsin(ph)
        lendy = self.knobCenterPosY + self.knobRadius * p_mathcos(ph)

        if vars.constants["IS_WIN"]:
            dc.SetPen(wx.Pen(self.knobInnerColour, width=2, style=wx.SOLID))
        else:
            dc.SetPen(wx.Pen(self.knobInnerColour, width=0, style=wx.SOLID))
        dc.SetBrush(wx.Brush(self.knobInnerColour, wx.SOLID))
        dc.DrawCircle(self.knobCenterPosX, self.knobCenterPosY, self.knobRadius - self.fromdip3)

        dc.SetPen(wx.Pen(self.knobColour, width=self.fromdip4, style=wx.SOLID))
        dc.DrawLine(self.knobCenterPosX, self.knobCenterPosY, lendx, lendy)

        dc.SetPen(wx.Pen(self.backgroundColour, width=self.fromdip2, style=wx.SOLID))
        dc.DrawLine(self.knobCenterPosX, self.knobCenterPosY, lendx, lendy)

        dc.SetPen(wx.Pen(self.foregroundColour, width=self.fromdip1, style=wx.SOLID))
        dc.SetBrush(wx.Brush(self.knobColour, wx.TRANSPARENT))
        dc.DrawCircle(self.knobCenterPosX, self.knobCenterPosY, self.knobRadius)

        dc.SetPen(wx.Pen(self.backgroundColour, width=self.fromdip5, style=wx.SOLID))
        dc.DrawCircle(self.knobCenterPosX, self.knobCenterPosY, self.knobRadius + self.fromdip3)

        # Draw text value
        if self.selected and self.new:
            val = self.new
        else:
            val = self.display_value
        if vars.constants["IS_LINUX"]:
            width = len(val) * (dc.GetCharWidth() - 3)
        else:
            width = len(val) * dc.GetCharWidth()

        dc.DrawLabel(val, recval, wx.ALIGN_CENTER)

        if self.midictlnumber is not None:
            if vars.constants["IS_WIN"] or vars.constants["IS_LINUX"]:
                dc.SetFont(wx.Font(6, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            else:
                dc.SetFont(wx.Font(9, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            if vars.constants["IS_WIN"]:
                dc.DrawLabel(str(self.midictlnumber), wx.Rect(4, recval[1] - 27, recval[2], 15), wx.ALIGN_LEFT)
            else:
                dc.DrawLabel(str(self.midictlnumber), wx.Rect(4, recval[1] - 11, recval[2], 15), wx.ALIGN_LEFT)

        evt.Skip()


class ZyneB_ControlKnob(ZB_ControlKnob):
    def __init__(self, parent, minvalue, maxvalue, init=None,
                 pos=(0, 0), size=(44, 74),
                 log=False, integer=False,
                 outFunction=None, label=''):
        super().__init__(parent, minvalue, maxvalue, init,
                         pos=pos, size=size,
                         log=log, integer=integer,
                         outFunction=outFunction, label=label)
        self.parent = parent

    def setValue(self, x):
        wx.CallAfter(self.SetValue, x)

    def MouseDown(self, evt):
        if vars.vars["MIDILEARN"]:
            if vars.vars["LEARNINGSLIDER"] is None:
                vars.vars["LEARNINGSLIDER"] = self
                self.Disable()
            elif vars.vars["LEARNINGSLIDER"] == self:
                vars.vars["LEARNINGSLIDER"].setMidiCtlNumber(None)
                vars.vars["LEARNINGSLIDER"] is None
                self.Enable()
            else:
                vars.vars["LEARNINGSLIDER"].Enable()
                vars.vars["LEARNINGSLIDER"] = self
                self.Disable()
            evt.StopPropagation()
        else:
            ZB_ControlKnob.MouseDown(self, evt)


class ZB_VuMeter(wx.Panel):
    def __init__(self, parent, size=(200, 11), numSliders=2,
                 orient=wx.HORIZONTAL, pos=wx.DefaultPosition, style=0):
        wx.Panel.__init__(self, parent, -1, pos=pos, size=size, style=style)
        self.SetSize(self.FromDIP(wx.Size(size)))
        _b = self.FromDIP(1)
        _b = 0 if _b == 1 else 1
        if orient == wx.HORIZONTAL:
            size = (self.GetSize()[0], numSliders * self.FromDIP(5) + self.FromDIP(1) + _b)
        else:
            size = (numSliders * self.FromDIP(5) + self.FromDIP(1) + _b, self.GetSize()[1])
        self.SetSize(size)
        self.SetMinSize(size)
        self.parent = parent
        self.orient = orient
        self.SetBackgroundColour(wx.BLACK)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.old_nchnls = numSliders
        self.numSliders = numSliders
        self.amplitude = [0] * self.numSliders
        self.createBitmaps()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.fromdip6 = self.FromDIP(6)

    def OnSize(self, evt):
        self.createBitmaps()
        wx.CallAfter(self.Refresh)

    def createBitmaps(self):
        w, h = self.GetSize()
        if w == 0 or h == 0:
            return

        b = wx.Bitmap(w, h)
        f = wx.Bitmap(w, h)
        dcb = wx.MemoryDC(b)
        dcf = wx.MemoryDC(f)
        _scale = self.FromDIP(1)
        dcb.SetPen(wx.Pen(wx.BLACK, width=1))
        dcf.SetPen(wx.Pen(wx.BLACK, width=1))
        if self.orient == wx.HORIZONTAL:
            height = self.FromDIP(6)
            steps = int(w / (10.0 * _scale) + 0.5)
        else:
            width = self.FromDIP(6)
            steps = int(h / (10.0 * _scale) + 0.5)
        bounds = int(steps / 6.0)
        for i in range(steps):
            if i == (steps - 1):
                dcb.SetBrush(wx.Brush("#770000"))
                dcf.SetBrush(wx.Brush("#FF0000"))
            elif i >= (steps - bounds):
                dcb.SetBrush(wx.Brush("#440000"))
                dcf.SetBrush(wx.Brush("#CC0000"))
            elif i >= (steps - (bounds * 2)):
                dcb.SetBrush(wx.Brush("#444400"))
                dcf.SetBrush(wx.Brush("#CCCC00"))
            else:
                dcb.SetBrush(wx.Brush("#004400"))
                dcf.SetBrush(wx.Brush("#00CC00"))
            if self.orient == wx.HORIZONTAL:
                dcb.DrawRectangle(i * 10 * _scale, 0, 11 * _scale, height)
                dcf.DrawRectangle(i * 10 * _scale, 0, 11 * _scale, height)
            else:
                ii = steps - 1 - i
                dcb.DrawRectangle(0, ii * 10 * _scale, width, 11 * _scale)
                dcf.DrawRectangle(0, ii * 10 * _scale, width, 11 * _scale)
        if self.orient == wx.HORIZONTAL:
            dcb.DrawLine(w - 1, 0, w - 1, height)
            dcf.DrawLine(w - 1, 0, w - 1, height)
        else:
            dcb.DrawLine(0, 0, width, 0)
            dcf.DrawLine(0, 0, width, 0)
        dcb.SelectObject(wx.NullBitmap)
        dcf.SelectObject(wx.NullBitmap)
        self.backBitmap = b
        self.bitmap = f

    def setNumSliders(self, numSliders):
        w, h = self.GetSize()
        oldChnls = self.old_nchnls
        self.numSliders = numSliders
        self.amplitude = [0] * self.numSliders
        gap = (self.numSliders - oldChnls) * 5
        parentSize = self.parent.GetSize()
        if self.orient == wx.HORIZONTAL:
            self.SetSize((w, self.numSliders * 5 + 1))
            self.SetMinSize((w, 5 * self.numSliders + 1))
            self.parent.SetSize((parentSize[0], parentSize[1] + gap))
            self.parent.SetMinSize((parentSize[0], parentSize[1] + gap))
        else:
            self.SetSize((self.numSliders * 5 + 1, h))
            self.SetMinSize((5 * self.numSliders + 1, h))
            self.parent.SetSize((parentSize[0] + gap, parentSize[1]))
            self.parent.SetMinSize((parentSize[0] + gap, parentSize[1]))
        wx.CallAfter(self.Refresh)
        wx.CallAfter(self.parent.Layout)
        wx.CallAfter(self.parent.Refresh)

    def setRms(self, *args):
        if args[0] < 0:
            return
        if not args:
            self.amplitude = [0] * self.numSliders
        else:
            self.amplitude = args
        wx.CallAfter(self.Refresh)

    def OnPaint(self, event):
        w, h = self.GetSize()
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBrush(wx.Brush(wx.BLACK))
        dc.Clear()
        dc.DrawRectangle(0, 0, w, h)
        if self.orient == wx.HORIZONTAL:
            height = self.fromdip6
            for i in range(self.numSliders):
                y = i * (height - 1)
                if i < len(self.amplitude):
                    db = p_mathlog10(self.amplitude[i] + 0.00001) * 0.2 + 1.0
                    try:
                        width = int(db * w)
                    except OverflowError:
                        width = w
                else:
                    width = 0
                dc.DrawBitmap(self.backBitmap, 0, y)
                if width > 0:
                    dc.SetClippingRegion(0, y, width, height)
                    dc.DrawBitmap(self.bitmap, 0, y)
                    dc.DestroyClippingRegion()
        else:
            width = self.fromdip6
            for i in range(self.numSliders):
                y = i * (width - 1)
                if i < len(self.amplitude):
                    db = p_mathlog10(self.amplitude[i] + 0.00001) * 0.2 + 1.0
                    try:
                        height = int(db * h)
                    except OverflowError:
                        height = h
                else:
                    height = 0
                dc.DrawBitmap(self.backBitmap, y, 0)
                if height > 0:
                    dc.SetClippingRegion(y, h - height, width, height)
                    dc.DrawBitmap(self.bitmap, y, 0)
                    dc.DestroyClippingRegion()
        event.Skip()

    def OnClose(self, evt):
        self.Destroy()


class ZB_Keyboard_Control(wx.Panel):
    def __init__(self, parent, keyboard, id=-1):
        wx.Panel.__init__(self, parent, id=id, style=wx.SIMPLE_BORDER)

        self.keyboard = keyboard
        self.parent = parent

        self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        self.SetForegroundColour(vars.constants["FORECOLOUR"])

        sizer = wx.BoxSizer(wx.VERTICAL)

        row1Box = wx.BoxSizer(wx.HORIZONTAL)

        chBox = wx.BoxSizer(wx.VERTICAL)
        self.channelText = wx.StaticText(self, id=-1, label="Channel")

        font, psize = self.channelText.GetFont(), self.channelText.GetFont().GetPointSize()
        font.SetPointSize(psize - 2)
        w, h = font.GetPixelSize()
        popsize = self.FromDIP(wx.Size(-1, h + 12))
        self.channelText.SetFont(font)

        chBox.Add(self.channelText, 0, wx.LEFT, 4)
        self.cbChannel = wx.ComboBox(self, value="1", size=popsize,
                                     choices=vars.constants["VAR_CHOICES"]["CHANNEL_KEYBOARD"],
                                     style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.cbChannel.SetFont(font)
        self.cbChannel.Bind(wx.EVT_COMBOBOX, self.changeChannel)
        chBox.Add(self.cbChannel, 0, wx.EXPAND | wx.ALL, 2)

        scBox = wx.BoxSizer(wx.VERTICAL)
        self.octaveText = wx.StaticText(self, id=-1, label="Octave")
        self.octaveText.SetFont(font)
        scBox.Add(self.octaveText, 0, wx.LEFT, 4)
        self.cbOctave = wx.ComboBox(self, value="0", size=popsize,
                                    choices=list(map(str, range(-3, 5))),
                                    style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.cbOctave.SetFont(font)
        self.cbOctave.Bind(wx.EVT_COMBOBOX, self.changeOctave)
        scBox.Add(self.cbOctave, 0, wx.EXPAND | wx.ALL, 2)

        row1Box.Add(chBox, 1)
        row1Box.Add(scBox, 1)
        sizer.Add(row1Box, 0, wx.EXPAND | wx.TOP, 2)

        self.modeText = wx.StaticText(self, id=-1, label="Key Mode")
        self.modeText.SetFont(font)
        sizer.Add(self.modeText, 0, wx.LEFT, 4)
        self.cbKeymode = wx.ComboBox(self, value="Hold", size=popsize,
                                     choices=["Normal", "Hold", "Single Key Hold"],
                                     style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.cbKeymode.Bind(wx.EVT_COMBOBOX, self.changeKeymode)
        self.cbKeymode.SetFont(font)
        sizer.Add(self.cbKeymode, 0, wx.EXPAND | wx.ALL, 2)

        self.SetSizerAndFit(sizer)

    def changeChannel(self, evt):
        self.keyboard.reset()
        self.keyboard.channel = int(self.cbChannel.GetValue())
        self.keyboard.SetFocus()

    def changeOctave(self, evt):
        self.keyboard.reset()
        self.keyboard.octave = int(self.cbOctave.GetValue()) * 12
        self.keyboard.c_key_idx = (35 - (7 * int(self.keyboard.octave / 12)))
        wx.CallAfter(self.keyboard.Refresh)
        self.keyboard.SetFocus()

    def changeKeymode(self, evt):
        self.keyboard.reset()
        mode = self.cbKeymode.GetSelection()
        if mode == 0:
            self.keyboard.hold = 0
        elif mode == 1:
            self.keyboard.hold = 1
        self.keyboard.SetFocus()


class ZB_Keyboard(wx.Panel):
    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        pos=wx.DefaultPosition,
        size=(-1, 100),
        poly=64,
        outFunction=None,
        style=wx.TAB_TRAVERSAL,
    ):
        wx.Panel.__init__(self, parent, id, pos, size, style)
        self.SetSize(self.FromDIP(self.GetSize()))
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour(vars.constants["BACKCOLOUR"])
        self.parent = parent
        self.outFunction = outFunction

        self.poly = poly
        self.gap = 0
        self.octave = 0
        self.w1 = self.FromDIP(15)
        self.w2 = int(self.w1 / 2) + 1
        self.hold = 1
        self.keyPressed = None
        self.channel = 0
        self.c_key_idx = 35

        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.MouseUp)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        self.white = (0, 2, 4, 5, 7, 9, 11)
        self.black = (1, 3, 6, 8, 10)
        self.whiteSelected = set()
        self.blackSelected = set()
        self.whiteVelocities = {}
        self.blackVelocities = {}
        self.whiteKeys = []
        self.blackKeys = []

        if vars.constants["IS_MAC"]:
            self.key_font = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        else:
            self.key_font = wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        self.brush_444444 = wx.Brush("#444444", wx.SOLID)
        self.brush_black = wx.Brush(wx.BLACK, wx.SOLID)
        self.brush_cccccc = wx.Brush("#CCCCCC", wx.SOLID)
        self.brush_white = wx.Brush(wx.WHITE, wx.SOLID)
        self.gradient_start_col = (250, 250, 250)
        self.pen_black = wx.Pen(wx.BLACK, width=1, style=wx.SOLID)
        self.pen_cccccc = wx.Pen("#CCCCCC", width=1, style=wx.SOLID)

        self.keydown = set()
        self.keymap = {
            90: 36,
            83: 37,
            88: 38,  # X
            68: 39,
            67: 40,
            86: 41,
            71: 42,
            66: 43,
            72: 44,
            78: 45,
            74: 46,
            77: 47,
            44: 48,
            76: 49,
            46: 50,
            59: 51,
            47: 52,
            81: 60,  # Q
            50: 61,
            87: 62,
            51: 63,
            69: 64,
            82: 65,
            53: 66,
            84: 67,
            54: 68,
            89: 69,
            55: 70,
            85: 71,
            73: 72,
            57: 73,
            79: 74,
            48: 75,
            80: 76,
        }

        wx.CallAfter(self._setRects)

    def getCurrentNotes(self):
        "Returns a list of the current notes."
        notes = []
        for key in self.whiteSelected:
            notes.append((self.white[key % 7] + int(key / 7) * 12 + self.octave,
                          127 - self.whiteVelocities[key], self.channel))
        for key in self.blackSelected:
            notes.append((self.black[key % 5] + int(key / 5) * 12 + self.octave,
                          127 - self.blackVelocities[key], self.channel))
        notes.sort()
        return notes

    def reset(self):
        "Resets the keyboard state."
        for key in self.blackSelected:
            pit = self.black[key % 5] + int(key / 5) * 12
            note = (pit + self.octave, 0, 0)
            if self.outFunction:
                self.outFunction(note)
        for key in self.whiteSelected:
            pit = self.white[key % 7] + int(key / 7) * 12
            note = (pit + self.octave, 0, 0)
            if self.outFunction:
                self.outFunction(note)
        self.whiteSelected = set()
        self.blackSelected = set()
        self.whiteVelocities = {}
        self.blackVelocities = {}
        wx.CallAfter(self.Refresh)

    def setPoly(self, poly):
        "Sets the maximum number of notes that can be held at the same time."
        self.poly = poly

    def _setRects(self):
        w, h = self.GetSize()
        height2 = int(h * 4 / 7)
        h1 = h - 1
        w1 = self.w1
        w11 = w1 - 1
        w2 = self.w2
        num = int(w / w1)
        off_start = w2 + 1
        self.gap = w - num * w1
        self.whiteKeys = [wx.Rect(i * w1, 0, w11, h1) for i in range(num)]
        self.blackKeys = []
        for i in range(int(num / 7) + 1):
            off = off_start + w1 * 7 * i
            self.blackKeys.append(wx.Rect(off, 0, w2, height2))
            off += w1
            self.blackKeys.append(wx.Rect(off, 0, w2, height2))
            off += w1 * 2
            self.blackKeys.append(wx.Rect(off, 0, w2, height2))
            off += w1
            self.blackKeys.append(wx.Rect(off, 0, w2, height2))
            off += w1
            self.blackKeys.append(wx.Rect(off, 0, w2, height2))
        self.Refresh()

    def OnSize(self, evt):
        self._setRects()
        wx.CallAfter(self.Refresh)
        evt.Skip()

    def OnKeyDown(self, evt):
        if evt.HasAnyModifiers():
            evt.Skip()
            return

        key_code = evt.GetKeyCode()
        if key_code in self.keymap and key_code not in self.keydown:
            self.keydown.add(key_code)
            pit = self.keymap[key_code]
            deg = pit % 12

            total = len(self.blackSelected) + len(self.whiteSelected)
            note = None
            if self.hold:
                if deg in self.black:
                    which = self.black.index(deg) + int(pit / 12) * 5
                    if which in self.blackSelected:
                        self.blackSelected.remove(which)
                        del self.blackVelocities[which]
                        total -= 1
                        note = (pit + self.octave, 0, self.channel)
                    else:
                        if total < self.poly:
                            self.blackSelected.add(which)
                            self.blackVelocities[which] = 100
                            note = (pit + self.octave, 100, self.channel)

                elif deg in self.white:
                    which = self.white.index(deg) + int(pit / 12) * 7
                    if which in self.whiteSelected:
                        self.whiteSelected.remove(which)
                        del self.whiteVelocities[which]
                        total -= 1
                        note = (pit + self.octave, 0, self.channel)
                    else:
                        if total < self.poly:
                            self.whiteSelected.add(which)
                            self.whiteVelocities[which] = 100
                            note = (pit + self.octave, 100, self.channel)
            else:
                if deg in self.black:
                    which = self.black.index(deg) + int(pit / 12) * 5
                    if which not in self.blackSelected and total < self.poly:
                        self.blackSelected.add(which)
                        self.blackVelocities[which] = 100
                        note = (pit + self.octave, 100, self.channel)
                elif deg in self.white:
                    which = self.white.index(deg) + int(pit / 12) * 7
                    if which not in self.whiteSelected and total < self.poly:
                        self.whiteSelected.add(which)
                        self.whiteVelocities[which] = 100
                        note = (pit + self.octave, 100, self.channel)

            if note and self.outFunction and total < self.poly:
                self.outFunction(note)

            wx.CallAfter(self.Refresh)
        evt.StopPropagation()

    def OnKeyUp(self, evt):
        if evt.HasAnyModifiers():
            evt.Skip()
            return

        key_code = evt.GetKeyCode()
        if key_code in self.keydown:
            self.keydown.remove(key_code)

        if not self.hold and key_code in self.keymap:
            pit = self.keymap[key_code]
            deg = pit % 12

            note = None
            if deg in self.black:
                which = self.black.index(deg) + int(pit / 12) * 5
                if which in self.blackSelected:
                    self.blackSelected.remove(which)
                    del self.blackVelocities[which]
                    note = (pit + self.octave, 0, self.channel)
            elif deg in self.white:
                which = self.white.index(deg) + int(pit / 12) * 7
                if which in self.whiteSelected:
                    self.whiteSelected.remove(which)
                    del self.whiteVelocities[which]
                    note = (pit + self.octave, 0, self.channel)

            if note and self.outFunction:
                self.outFunction(note)

            wx.CallAfter(self.Refresh)

        evt.StopPropagation()

    def MouseUp(self, evt):
        if not self.hold and self.keyPressed is not None:
            key = self.keyPressed[0]
            pit = self.keyPressed[1]
            if key in self.blackSelected:
                self.blackSelected.remove(key)
                del self.blackVelocities[key]
            if key in self.whiteSelected:
                self.whiteSelected.remove(key)
                del self.whiteVelocities[key]
            note = (pit, 0, self.channel)
            if self.outFunction:
                self.outFunction(note)
            self.keyPressed = None
            wx.CallAfter(self.Refresh)
        evt.Skip()

    def MouseDown(self, evt):
        w, h = self.GetSize()
        pos = evt.GetPosition()

        total = len(self.blackSelected) + len(self.whiteSelected)
        note = None
        if self.hold:
            for i, rec in enumerate(self.blackKeys):
                if rec.Contains(pos):
                    pit = self.black[i % 5] + int(i / 5) * 12 + self.octave
                    if pit < 0 or pit > 127:
                        return
                    if i in self.blackSelected:
                        self.blackSelected.remove(i)
                        del self.blackVelocities[i]
                        total -= 1
                        vel = 0
                    else:
                        hb = int(h * 4 / 7)
                        vel = int((hb - pos[1]) * 127 / hb)
                        if total < self.poly:
                            self.blackSelected.add(i)
                            self.blackVelocities[i] = int(127 - vel)
                    note = (pit, vel, self.channel)
                    break
            else:
                for i, rec in enumerate(self.whiteKeys):
                    if rec.Contains(pos):
                        pit = self.white[i % 7] + int(i / 7) * 12 + self.octave
                        if pit < 0 or pit > 127:
                            return
                        if i in self.whiteSelected:
                            self.whiteSelected.remove(i)
                            del self.whiteVelocities[i]
                            total -= 1
                            vel = 0
                        else:
                            vel = int((h - pos[1]) * 127 / h)
                            if total < self.poly:
                                self.whiteSelected.add(i)
                                self.whiteVelocities[i] = int(127 - vel)
                        note = (pit, vel, self.channel)
                        break
        else:
            self.keyPressed = None
            for i, rec in enumerate(self.blackKeys):
                if rec.Contains(pos):
                    pit = self.black[i % 5] + int(i / 5) * 12 + self.octave
                    if pit < 0 or pit > 127:
                        return
                    vel = 0
                    if i not in self.blackSelected:
                        hb = int(h * 4 / 7)
                        vel = int((hb - pos[1]) * 127 / hb)
                        if total < self.poly:
                            self.blackSelected.add(i)
                            self.blackVelocities[i] = int(127 - vel)
                    note = (pit, vel, self.channel)
                    self.keyPressed = (i, pit)
                    break
            else:
                for i, rec in enumerate(self.whiteKeys):
                    if rec.Contains(pos):
                        pit = self.white[i % 7] + int(i / 7) * 12 + self.octave
                        if pit < 0 or pit > 127:
                            return
                        vel = 0
                        if i not in self.whiteSelected:
                            vel = int((h - pos[1]) * 127 / h)
                            if total < self.poly:
                                self.whiteSelected.add(i)
                                self.whiteVelocities[i] = int(127 - vel)
                        note = (pit, vel, self.channel)
                        self.keyPressed = (i, pit)
                        break
        if note and self.outFunction and total < self.poly:
            self.outFunction(note)
        wx.CallAfter(self.Refresh)
        evt.Skip()

    def OnPaint(self, evt):
        w, h = self.GetSize()
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBrush(self.brush_black)
        dc.Clear()
        dc.SetPen(self.pen_black)
        dc.DrawRectangle(0, 0, w, h)
        dc.SetFont(self.key_font)
        gradient_start_col = self.gradient_start_col
        for i, rec in enumerate(self.whiteKeys):
            if i in self.whiteSelected:
                amp = int(self.whiteVelocities[i] * 1.5)
                dc.SetBrush(self.brush_cccccc)
                dc.SetPen(self.pen_cccccc)
                dc.GradientFillLinear(rec, gradient_start_col, (amp, amp, amp), wx.SOUTH)
            else:
                if self.c_key_idx - 35 > i or self.c_key_idx + 39 < i:
                    dc.SetBrush(self.brush_444444)
                else:
                    dc.SetBrush(self.brush_white)
                dc.SetPen(self.pen_cccccc)
                dc.DrawRectangle(rec)
            if i == self.c_key_idx:
                if i in self.whiteSelected:
                    dc.SetTextForeground(wx.WHITE)
                else:
                    dc.SetTextForeground(wx.BLACK)
                dc.DrawText("C", rec[0] + self.FromDIP(3), rec[3] - 25)

        dc.SetPen(self.pen_black)
        for i, rec in enumerate(self.blackKeys):
            if i in self.blackSelected:
                amp = int(self.blackVelocities[i] * 1.5)
                dc.GradientFillLinear(rec, gradient_start_col, (amp, amp, amp), wx.SOUTH)
                dc.DrawLine(rec[0], 0, rec[0], rec[3])
                dc.DrawLine(rec[0] + rec[2], 0, rec[0] + rec[2], rec[3])
                dc.DrawLine(rec[0], rec[3], rec[0] + rec[2], rec[3])
            else:
                dc.SetBrush(self.brush_black)
                dc.DrawRectangle(rec)

        dc.SetBrush(wx.Brush(BACKGROUND_COLOUR, wx.SOLID))
        dc.SetPen(self.pen_cccccc)
        dc.DrawRectangle(wx.Rect(w - self.w1, 0, self.w1, h))

        evt.Skip()
