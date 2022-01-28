"""
Copyright 2009-2015 Olivier Belanger - modifications by Hans-Jörg Bibiko 2022

Some classes of this file were parts of pyo's _wxwidgets.py,
a python module to help digital signal processing script creation.
"""

import copy
import math
import sys
import wx
import Resources.variables as vars
from wx.lib.embeddedimage import PyEmbeddedImage


p_mathlog10 = math.log10
p_mathpow = math.pow
p_mathsin = math.sin
p_mathcos = math.cos
p_math_pi = math.pi


if "phoenix" in wx.version():
    wx.GraphicsContext_Create = wx.GraphicsContext.Create
    wx.EmptyBitmap = wx.Bitmap
    wx.EmptyImage = wx.Image
    wx.BitmapFromImage = wx.Bitmap
    wx.Image_HSVValue = wx.Image.HSVValue
    wx.Image_HSVtoRGB = wx.Image.HSVtoRGB


def interpFloat(t, v1, v2):
    "interpolator for a single value; interprets t in [0-1] between v1 and v2"
    return (v2 - v1) * t + v1


def tFromValue(value, v1, v2):
    "returns a t (in range 0-1) given a value in the range v1 to v2"
    return (value - v1) / (v2 - v1)


def clamp(v, vmin, vmax):
    "clamps a value within a range"
    return vmin if v < vmin else vmax if v > vmax else v


def toLog(t, v1, v2):
    return p_mathlog10(t/v1) / p_mathlog10(v2/v1)


def toExp(t, v1, v2):
    v1log = p_mathlog10(v1)
    return p_mathpow(10, t * (p_mathlog10(v2) - v1log) + v1log)


POWOFTWO = {
    2: 1,
    4: 2,
    8: 3,
    16: 4,
    32: 5,
    64: 6,
    128: 7,
    256: 8,
    512: 9,
    1024: 10,
    2048: 11,
    4096: 12,
    8192: 13,
    16384: 14,
    32768: 15,
    65536: 16,
}


def powOfTwo(x):
    "Return 2 raised to the power of x."
    return 2 ** x


def powOfTwoToInt(x):
    "Return the exponent of 2 correponding to the value x."
    return POWOFTWO[x]


HEADTITLE_BACK_COLOUR = "#9999A0"
BACKGROUND_COLOUR = "#EBEBEB"


class ZB_HeadTitle(wx.Panel):
    def __init__(self, parent, title, font=None, togcall=None):
        wx.Panel.__init__(self, parent, -1)
        self.SetBackgroundColour(HEADTITLE_BACK_COLOUR)
        mainsizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        if togcall is not None:
            self.toggle = wx.CheckBox(self, id=-1)
            mainsizer.Add(self.toggle, 0, wx.LEFT | wx.RIGHT | wx.CENTER, 2)
            self.toggle.Bind(wx.EVT_CHECKBOX, togcall)
        self.label = wx.StaticText(self, -1, title)
        if font is not None:
            label.SetFont(font)
        self.label.SetForegroundColour(wx.WHITE)
        sizer.Add(self.label, 0, wx.CENTER | wx.ALL, 2)
        mainsizer.Add(sizer, 1)
        self.SetSizerAndFit(mainsizer)

    def setLabel(self, s):
        self.label.SetLabel(s)


class ZB_ControlSlider(wx.Panel):
    def __init__(
        self,
        parent,
        minvalue,
        maxvalue,
        init=None,
        pos=(0, 0),
        size=(200, 16),
        log=False,
        outFunction=None,
        integer=False,
        powoftwo=False,
        backColour=None,
        orient=wx.HORIZONTAL,
        ctrllabel="",
    ):
        if size == (200, 16) and orient == wx.VERTICAL:
            size = (40, 200)
        wx.Panel.__init__(
            self, parent=parent, id=wx.ID_ANY, pos=pos, size=size,
            style=wx.NO_BORDER | wx.WANTS_CHARS | wx.EXPAND
        )
        self.parent = parent
        if backColour:
            self.backgroundColour = backColour
        else:
            self.backgroundColour = BACKGROUND_COLOUR
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour(self.backgroundColour)
        self.orient = orient
        # self.SetMinSize(self.GetSize())
        if self.orient == wx.VERTICAL:
            self.knobSize = 17
            self.knobHalfSize = 8
            self.sliderWidth = size[0] - 29
        else:
            self.knobSize = 40
            self.knobHalfSize = 20
            self.sliderHeight = size[1] - 5
        self.outFunction = outFunction
        self.integer = integer
        self.log = log
        self.powoftwo = powoftwo
        if self.powoftwo:
            self.integer = True
            self.log = False
        self.ctrllabel = ctrllabel
        self.SetRange(minvalue, maxvalue)
        self.borderWidth = 1
        self.selected = False
        self._enable = True
        self.propagate = True
        self.midictl = None
        self.new = ""
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

        if sys.platform == "win32" or sys.platform.startswith("linux"):
            self.dcref = wx.BufferedPaintDC
            self.font = wx.Font(7, wx.FONTFAMILY_TELETYPE,
                                wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        else:
            self.dcref = wx.PaintDC
            self.font = wx.Font(10, wx.FONTFAMILY_TELETYPE,
                                wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

    def getCtrlLabel(self):
        return self.ctrllabel

    def setMidiCtl(self, x, propagate=True):
        self.propagate = propagate
        self.midictl = x
        self.Refresh()

    def getMidiCtl(self):
        return self.midictl

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

    def setSliderHeight(self, height):
        self.sliderHeight = height
        self.Refresh()

    def setSliderWidth(self, width):
        self.sliderWidth = width

    def getInit(self):
        return self.init

    def SetRange(self, minvalue, maxvalue):
        self.minvalue = minvalue
        self.maxvalue = maxvalue

    def getRange(self):
        return [self.minvalue, self.maxvalue]

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

    def SetValue(self, value, propagate=True):
        self.propagate = propagate
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
        self.clampPos()
        self.selected = False
        wx.CallAfter(self.Refresh)

    def GetValue(self):
        if self.log:
            t = tFromValue(self.value, self.minvalue, self.maxvalue)
            val = toExp(t, self.minvalue, self.maxvalue)
        else:
            val = self.value
        if self.integer:
            val = int(val)
        return val

    def LooseFocus(self, event):
        self.new = ""
        self.selected = False
        self.Refresh()
        event.Skip()

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
            elif event.GetKeyCode() < 256:
                char = chr(event.GetKeyCode())

            if char in "0123456789.-":
                self.new += char
            elif event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
                try:
                    self.SetValue(float(self.new))
                except Exception:
                    self.SetValue(old_val)
                evt = wx.FocusEvent(wx.EVT_KILL_FOCUS.evtType[0], self.GetId())
                wx.PostEvent(self.GetEventHandler(), evt)
            elif event.GetKeyCode() == wx.WXK_ESCAPE:
                self.SetValue(old_val)
                evt = wx.FocusEvent(wx.EVT_KILL_FOCUS.evtType[0], self.GetId())
                wx.PostEvent(self.GetEventHandler(), evt)
            self.Refresh()
        event.StopPropagation()

    def MouseDown(self, evt):
        if evt.ShiftDown():
            self.DoubleClick(evt)
            return
        if self._enable:
            size = self.GetSize()
            if self.orient == wx.VERTICAL:
                self.pos = clamp(evt.GetPosition()[1], self.knobHalfSize, size[1] - self.knobHalfSize)
            else:
                self.pos = clamp(evt.GetPosition()[0], self.knobHalfSize, size[0] - self.knobHalfSize)
            self.value = self.scale()
            self.CaptureMouse()
            self.selected = False
            self.Refresh()
        evt.Skip()

    def MouseUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()

    def DoubleClick(self, event):
        if self._enable:
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
                    self.pos = clamp(evt.GetPosition()[1], self.knobHalfSize, size[1] - self.knobHalfSize)
                else:
                    self.pos = clamp(evt.GetPosition()[0], self.knobHalfSize, size[0] - self.knobHalfSize)
                self.value = self.scale()
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

    def setBackgroundColour(self, colour):
        self.backgroundColour = colour
        self.SetBackgroundColour(self.backgroundColour)
        self.Refresh()

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
            sliderColour = "#99A7CC"
        else:
            sliderColour = "#BBBBBB"
        if self.orient == wx.VERTICAL:
            w2 = (w - self.sliderWidth) // 2
            rec = wx.Rect(w2, 0, self.sliderWidth, h)
            brush = gc.CreateLinearGradientBrush(w2, 0, w2 + self.sliderWidth, 0, "#646986", sliderColour)
        else:
            h2 = self.sliderHeight // 4
            rec = wx.Rect(0, h2, w, self.sliderHeight)
            brush = gc.CreateLinearGradientBrush(0, h2, 0, h2 + self.sliderHeight, "#646986", sliderColour)
        gc.SetBrush(brush)
        gc.DrawRoundedRectangle(rec[0], rec[1], rec[2], rec[3], 2)

        if self.midictl is not None:
            if sys.platform == "win32" or sys.platform.startswith("linux"):
                dc.SetFont(wx.Font(6, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            else:
                dc.SetFont(wx.Font(9, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            dc.SetTextForeground("#FFFFFF")
            if self.orient == wx.VERTICAL:
                dc.DrawLabel(str(self.midictl), wx.Rect(w2, 2, self.sliderWidth, 12), wx.ALIGN_CENTER)
                dc.DrawLabel(str(self.midictl), wx.Rect(w2, h - 12, self.sliderWidth, 12), wx.ALIGN_CENTER)
            else:
                dc.DrawLabel(str(self.midictl), wx.Rect(2, 0, h, h), wx.ALIGN_CENTER)
                dc.DrawLabel(str(self.midictl), wx.Rect(w - h, 0, h, h), wx.ALIGN_CENTER)

        # Draw knob
        if self._enable:
            knobColour = "#888888"
        else:
            knobColour = "#DDDDDD"
        if self.orient == wx.VERTICAL:
            rec = wx.Rect(0, self.pos - self.knobHalfSize, w, self.knobSize - 1)
            if self.selected:
                brush = wx.Brush("#333333", wx.SOLID)
            else:
                brush = gc.CreateLinearGradientBrush(0, 0, w, 0, "#323854", knobColour)
            gc.SetBrush(brush)
            gc.DrawRoundedRectangle(rec[0], rec[1], rec[2], rec[3], 3)
        else:
            rec = wx.Rect(int(self.pos) - self.knobHalfSize, 0, self.knobSize - 1, h)
            if self.selected:
                brush = wx.Brush("#333333", wx.SOLID)
            else:
                brush = gc.CreateLinearGradientBrush(
                    self.pos - self.knobHalfSize, 0, self.pos + self.knobHalfSize, 0, "#323854", knobColour
                )
            gc.SetBrush(brush)
            gc.DrawRoundedRectangle(rec[0], rec[1], rec[2], rec[3], 3)

        dc.SetFont(self.font)

        # Draw text
        if self.selected and self.new:
            val = self.new
        else:
            if self.integer:
                val = "%d" % self.GetValue()
            elif abs(self.GetValue()) >= 1000:
                val = "%.0f" % self.GetValue()
            elif abs(self.GetValue()) >= 100:
                val = "%.1f" % self.GetValue()
            elif abs(self.GetValue()) >= 10:
                val = "%.2f" % self.GetValue()
            elif abs(self.GetValue()) < 10:
                val = "%.3f" % self.GetValue()
        if sys.platform.startswith("linux"):
            width = len(val) * (dc.GetCharWidth() - 3)
        else:
            width = len(val) * dc.GetCharWidth()
        dc.SetTextForeground("#FFFFFF")
        dc.DrawLabel(val, rec, wx.ALIGN_CENTER)

        # Send value
        if self.outFunction and self.propagate:
            self.outFunction(self.GetValue())
        self.propagate = True

        evt.Skip()


class ZyneB_ControlSlider(ZB_ControlSlider):
    def __init__(self, parent, minvalue, maxvalue, init=None, pos=(0, 0),
                 size=(200, 16), log=False, outFunction=None, integer=False,
                 powoftwo=False, backColour=None):
        ZB_ControlSlider.__init__(self, parent, minvalue, maxvalue, init, pos, size,
                                  log, outFunction, integer, powoftwo, backColour)

    def setValue(self, x):
        wx.CallAfter(self.SetValue, x)

    def MouseDown(self, evt):
        if vars.vars["MIDILEARN"]:
            if vars.vars["LEARNINGSLIDER"] is None:
                vars.vars["LEARNINGSLIDER"] = self
                self.Disable()
            elif vars.vars["LEARNINGSLIDER"] == self:
                vars.vars["LEARNINGSLIDER"].setMidiCtl(None)
                vars.vars["LEARNINGSLIDER"] is None
                self.Enable()
            evt.StopPropagation()
        else:
            ZB_ControlSlider.MouseDown(self, evt)


class ZB_ControlKnob(wx.Panel):
    def __init__(self, parent, minvalue, maxvalue, init=None, pos=(0, 0),
                 size=(44, 74), log=False, outFunction=None, integer=False,
                 backColour=None, label=''):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, pos=pos, size=size,
                          style=wx.NO_BORDER | wx.WANTS_CHARS)
        self.parent = parent
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.backColour = parent.GetBackgroundColour()
        self.foreColour = parent.GetForegroundColour()
        self.SetBackgroundColour(self.backColour)
        self.SetMinSize(self.GetSize())
        self.outFunction = outFunction
        self.integer = integer
        self.log = log
        self.label = label
        self.SetRange(minvalue, maxvalue)
        self.borderWidth = 0
        self.selected = False
        self._enable = True
        self.midictl = None
        self.new = ''
        self.floatPrecision = '%.3f'
        self.knobCenterPosX = int(size[0] / 2)
        self.knobRadius = 14
        self.knobCenterPosY = self.knobRadius + 18
        self.knobStartAngle = 18 * p_math_pi / 180  # 18° := start angle
        self.knobEndAngle = 2 * p_math_pi - self.knobStartAngle
        self.knobRec = wx.Rect(self.knobCenterPosX - self.knobRadius - 5,
                               self.knobCenterPosY - self.knobRadius - 5,
                               2 * self.knobRadius + 10, 2 * self.knobRadius + 10)

        if init is not None:
            self.SetValue(init)
            self.init = init
        else:
            self.SetValue(minvalue)
            self.init = minvalue

        if vars.constants["PLATFORM"] == "darwin":
            self.font = wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        else:
            self.font = wx.Font(7, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.MouseUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.DoubleClick)
        self.Bind(wx.EVT_MOTION, self.MouseMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_KEY_DOWN, self.keyDown)
        self.Bind(wx.EVT_KILL_FOCUS, self.LooseFocus)

    def setMidiCtl(self, x, propagate=True):
        self.propagate = propagate
        self.midictl = x
        self.Refresh()

    def getMidiCtl(self):
        return self.midictl

    def setFloatPrecision(self, x):
        self.floatPrecision = '%.' + '%df' % x
        self.Refresh()

    def getMinValue(self):
        return self.minvalue

    def getMaxValue(self):
        return self.maxvalue

    def Enable(self):
        self._enable = True
        self.Refresh()

    def Disable(self):
        self._enable = False
        self.Refresh()

    def getInit(self):
        return self.init

    def getLabel(self):
        return self.label

    def getLog(self):
        return self.log

    def SetRange(self, minvalue, maxvalue):
        self.minvalue = minvalue
        self.maxvalue = maxvalue

    def getRange(self):
        return [self.minvalue, self.maxvalue]

    def SetValue(self, value):
        if self.HasCapture():
            self.ReleaseMouse()
        value = clamp(value, self.minvalue, self.maxvalue)
        if self.log:
            t = toLog(value, self.minvalue, self.maxvalue)
            self.value = interpFloat(t, self.minvalue, self.maxvalue)
        else:
            t = tFromValue(value, self.minvalue, self.maxvalue)
            self.value = interpFloat(t, self.minvalue, self.maxvalue)
        if self.integer:
            self.value = int(self.value)
        self.selected = False
        self.Refresh()

    def GetValue(self):
        if self.log:
            t = tFromValue(self.value, self.minvalue, self.maxvalue)
            val = toExp(t, self.minvalue, self.maxvalue)
        else:
            val = self.value
        if self.integer:
            val = int(val)
        return val

    def LooseFocus(self, event):
        self.new = ""
        self.selected = False
        self.Refresh()
        event.Skip()

    def keyDown(self, event):
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
            elif event.GetKeyCode() < 256:
                char = chr(event.GetKeyCode())

            if char in "0123456789.-":
                self.new += char
            elif event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
                try:
                    self.SetValue(float(self.new))
                except Exception:
                    self.SetValue(old_val)
                evt = wx.FocusEvent(wx.EVT_KILL_FOCUS.evtType[0], self.GetId())
                wx.PostEvent(self.GetEventHandler(), evt)
            elif event.GetKeyCode() == wx.WXK_ESCAPE:
                self.SetValue(old_val)
                evt = wx.FocusEvent(wx.EVT_KILL_FOCUS.evtType[0], self.GetId())
                wx.PostEvent(self.GetEventHandler(), evt)
            self.Refresh()
            event.StopPropagation()

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
            w, h = self.GetSize()
            pos = event.GetPosition()

            # check for number field is pressed
            reclab = wx.Rect(5, 55, w-10, 13)
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
                        _rad = math.atan(_x / _y)
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
                self.selected = False
                self.Refresh()

    def setbackColour(self, colour):
        self.backColour = colour
        self.Refresh()

    def OnPaint(self, evt):
        w, h = self.GetSize()
        dc = wx.AutoBufferedPaintDC(self)

        dc.SetBrush(wx.Brush(self.backColour, wx.SOLID))
        dc.Clear()

        # Draw background
        dc.SetPen(wx.Pen(self.backColour, width=self.borderWidth, style=wx.SOLID))
        dc.DrawRectangle(0, 0, w, h)

        dc.SetFont(self.font)

        # Draw text label
        reclab = wx.Rect(0, 1, w, 9)
        dc.DrawLabel(self.label, reclab, wx.ALIGN_CENTER_HORIZONTAL)

        recval = wx.Rect(0, self.knobCenterPosY + self.knobRadius + 11, w, 9)

        if self.selected:
            dc.SetPen(wx.Pen('#AAAAAA'))
            dc.SetBrush(wx.Brush('#AAAAAA', wx.TRANSPARENT))
            dc.DrawRoundedRectangle(recval, 3)

        # Draw knob
        knobColour = wx.Colour(self.foreColour.red, self.foreColour.green, self.foreColour.blue)
        dc.SetPen(wx.Pen(knobColour, width=3, style=wx.SOLID))

        ph = interpFloat(tFromValue(self.value, self.minvalue, self.maxvalue),
                         self.knobStartAngle, self.knobEndAngle)
        lendx = self.knobCenterPosX - self.knobRadius * p_mathsin(ph)
        lendy = self.knobCenterPosY + self.knobRadius * p_mathcos(ph)

        dc.DrawLine(self.knobCenterPosX, self.knobCenterPosY, lendx, lendy)
        dc.SetPen(wx.Pen(self.foreColour, width=2, style=wx.SOLID))
        dc.SetBrush(wx.Brush(knobColour, wx.TRANSPARENT))
        dc.DrawCircle(self.knobCenterPosX, self.knobCenterPosY, self.knobRadius)
        dc.SetPen(wx.Pen(self.backColour, width=4, style=wx.SOLID))
        dc.DrawCircle(self.knobCenterPosX, self.knobCenterPosY, self.knobRadius + 3)

        # Draw text value
        if self.selected and self.new:
            val = self.new
        else:
            if self.integer:
                val = str(int(self.GetValue()))
            else:
                val = self.floatPrecision % self.GetValue()
        if vars.constants["PLATFORM"].startswith('linux'):
            width = len(val) * (dc.GetCharWidth() - 3)
        else:
            width = len(val) * dc.GetCharWidth()

        dc.DrawLabel(val, recval, wx.ALIGN_CENTER)

        # Send value
        if self.outFunction:
            self.outFunction(self.GetValue())

        evt.Skip()


class ZB_VuMeter(wx.Panel):
    def __init__(self, parent, size=(200, 11), numSliders=2,
                 orient=wx.HORIZONTAL, pos=wx.DefaultPosition, style=0):
        if orient == wx.HORIZONTAL:
            size = (size[0], numSliders * 5 + 1)
        else:
            size = (numSliders * 5 + 1, size[1])
        wx.Panel.__init__(self, parent, -1, pos=pos, size=size, style=style)
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

    def OnSize(self, evt):
        self.createBitmaps()
        wx.CallAfter(self.Refresh)

    def createBitmaps(self):
        w, h = self.GetSize()
        if w == 0 or h == 0:
            return

        b = wx.EmptyBitmap(w, h)
        f = wx.EmptyBitmap(w, h)
        dcb = wx.MemoryDC(b)
        dcf = wx.MemoryDC(f)
        dcb.SetPen(wx.Pen(wx.BLACK, width=1))
        dcf.SetPen(wx.Pen(wx.BLACK, width=1))
        if self.orient == wx.HORIZONTAL:
            height = 6
            steps = int(w / 10.0 + 0.5)
        else:
            width = 6
            steps = int(h / 10.0 + 0.5)
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
                dcb.DrawRectangle(i * 10, 0, 11, height)
                dcf.DrawRectangle(i * 10, 0, 11, height)
            else:
                ii = steps - 1 - i
                dcb.DrawRectangle(0, ii * 10, width, 11)
                dcf.DrawRectangle(0, ii * 10, width, 11)
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
            height = 6
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
            width = 6
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


class ZB_Keyboard(wx.Panel):
    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        poly=64,
        outFunction=None,
        style=wx.TAB_TRAVERSAL,
    ):
        wx.Panel.__init__(self, parent, id, pos, size, style)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.parent = parent
        self.outFunction = outFunction

        self.poly = poly
        self.gap = 0
        self.offset = 12
        self.w1 = 15
        self.w2 = int(self.w1 / 2) + 1
        self.hold = 1
        self.keyPressed = None

        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.MouseUp)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        self.white = (0, 2, 4, 5, 7, 9, 11)
        self.black = (1, 3, 6, 8, 10)
        self.whiteSelected = []
        self.blackSelected = []
        self.whiteVelocities = {}
        self.blackVelocities = {}
        self.whiteKeys = []
        self.blackKeys = []

        self.offRec = wx.Rect(900 - 55, 0, 28, 150)
        self.holdRec = wx.Rect(900 - 27, 0, 27, 150)

        self.keydown = []
        self.keymap = {
            90: 36,
            83: 37,
            88: 38,
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
            81: 60,
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
            notes.append((self.white[key % 7] + int(key / 7) * 12 + self.offset,
                          127 - self.whiteVelocities[key]))
        for key in self.blackSelected:
            notes.append((self.black[key % 5] + int(key / 5) * 12 + self.offset,
                          127 - self.blackVelocities[key]))
        notes.sort()
        return notes

    def reset(self):
        "Resets the keyboard state."
        for key in self.blackSelected:
            pit = self.black[key % 5] + int(key / 5) * 12 + self.offset
            note = (pit, 0)
            if self.outFunction:
                self.outFunction(note)
        for key in self.whiteSelected:
            pit = self.white[key % 7] + int(key / 7) * 12 + self.offset
            note = (pit, 0)
            if self.outFunction:
                self.outFunction(note)
        self.whiteSelected = []
        self.blackSelected = []
        self.whiteVelocities = {}
        self.blackVelocities = {}
        wx.CallAfter(self.Refresh)

    def setPoly(self, poly):
        "Sets the maximum number of notes that can be held at the same time."
        self.poly = poly

    def _setRects(self):
        w, h = self.GetSize()
        self.offRec = wx.Rect(w - 55, 0, 28, h)
        self.holdRec = wx.Rect(w - 27, 0, 27, h)
        num = int(w / self.w1)
        self.gap = w - num * self.w1
        self.whiteKeys = [wx.Rect(i * self.w1, 0, self.w1 - 1, h - 1) for i in range(num)]
        self.blackKeys = []
        height2 = int(h * 4 / 7)
        for i in range(int(num / 7) + 1):
            space2 = self.w1 * 7 * i
            off = int(self.w1 / 2) + space2 + 3
            self.blackKeys.append(wx.Rect(off, 0, self.w2, height2))
            off += self.w1
            self.blackKeys.append(wx.Rect(off, 0, self.w2, height2))
            off += self.w1 * 2
            self.blackKeys.append(wx.Rect(off, 0, self.w2, height2))
            off += self.w1
            self.blackKeys.append(wx.Rect(off, 0, self.w2, height2))
            off += self.w1
            self.blackKeys.append(wx.Rect(off, 0, self.w2, height2))
        wx.CallAfter(self.Refresh)

    def OnSize(self, evt):
        self._setRects()
        wx.CallAfter(self.Refresh)
        evt.Skip()

    def OnKeyDown(self, evt):
        if evt.HasAnyModifiers():
            evt.Skip()
            return

        if evt.GetKeyCode() in self.keymap and evt.GetKeyCode() not in self.keydown:
            self.keydown.append(evt.GetKeyCode())
            pit = self.keymap[evt.GetKeyCode()]
            deg = pit % 12

            total = len(self.blackSelected) + len(self.whiteSelected)
            note = None
            if self.hold:
                if deg in self.black:
                    which = self.black.index(deg) + int((pit - self.offset) / 12) * 5
                    if which in self.blackSelected:
                        self.blackSelected.remove(which)
                        del self.blackVelocities[which]
                        total -= 1
                        note = (pit, 0)
                    else:
                        if total < self.poly:
                            self.blackSelected.append(which)
                            self.blackVelocities[which] = 100
                            note = (pit, 100)

                elif deg in self.white:
                    which = self.white.index(deg) + int((pit - self.offset) / 12) * 7
                    if which in self.whiteSelected:
                        self.whiteSelected.remove(which)
                        del self.whiteVelocities[which]
                        total -= 1
                        note = (pit, 0)
                    else:
                        if total < self.poly:
                            self.whiteSelected.append(which)
                            self.whiteVelocities[which] = 100
                            note = (pit, 100)
            else:
                if deg in self.black:
                    which = self.black.index(deg) + int((pit - self.offset) / 12) * 5
                    if which not in self.blackSelected and total < self.poly:
                        self.blackSelected.append(which)
                        self.blackVelocities[which] = 100
                        note = (pit, 100)
                elif deg in self.white:
                    which = self.white.index(deg) + int((pit - self.offset) / 12) * 7
                    if which not in self.whiteSelected and total < self.poly:
                        self.whiteSelected.append(which)
                        self.whiteVelocities[which] = 100
                        note = (pit, 100)

            if note and self.outFunction and total < self.poly:
                self.outFunction(note)

            wx.CallAfter(self.Refresh)
        evt.StopPropagation()

    def OnKeyUp(self, evt):
        if evt.HasAnyModifiers():
            evt.Skip()
            return

        if evt.GetKeyCode() in self.keydown:
            del self.keydown[self.keydown.index(evt.GetKeyCode())]

        if not self.hold and evt.GetKeyCode() in self.keymap:
            pit = self.keymap[evt.GetKeyCode()]
            deg = pit % 12

            note = None
            if deg in self.black:
                which = self.black.index(deg) + int((pit - self.offset) / 12) * 5
                if which in self.blackSelected:
                    self.blackSelected.remove(which)
                    del self.blackVelocities[which]
                    note = (pit, 0)
            elif deg in self.white:
                which = self.white.index(deg) + int((pit - self.offset) / 12) * 7
                if which in self.whiteSelected:
                    self.whiteSelected.remove(which)
                    del self.whiteVelocities[which]
                    note = (pit, 0)

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
            note = (pit, 0)
            if self.outFunction:
                self.outFunction(note)
            self.keyPressed = None
            wx.CallAfter(self.Refresh)
        evt.Skip()

    def MouseDown(self, evt):
        w, h = self.GetSize()
        pos = evt.GetPosition()
        if self.holdRec.Contains(pos):
            if self.hold:
                self.hold = 0
                self.reset()
            else:
                self.hold = 1
            wx.CallAfter(self.Refresh)
            return
        if self.offUpRec.Contains(pos):
            self.offset += 12
            if self.offset > 60:
                self.offset = 60
            wx.CallAfter(self.Refresh)
            return
        if self.offDownRec.Contains(pos):
            self.offset -= 12
            if self.offset < 0:
                self.offset = 0
            wx.CallAfter(self.Refresh)
            return

        total = len(self.blackSelected) + len(self.whiteSelected)
        scanWhite = True
        note = None
        if self.hold:
            for i, rec in enumerate(self.blackKeys):
                if rec.Contains(pos):
                    pit = self.black[i % 5] + int(i / 5) * 12 + self.offset
                    if i in self.blackSelected:
                        self.blackSelected.remove(i)
                        del self.blackVelocities[i]
                        total -= 1
                        vel = 0
                    else:
                        hb = int(h * 4 / 7)
                        vel = int((hb - pos[1]) * 127 / hb)
                        if total < self.poly:
                            self.blackSelected.append(i)
                            self.blackVelocities[i] = int(127 - vel)
                    note = (pit, vel)
                    scanWhite = False
                    break
            if scanWhite:
                for i, rec in enumerate(self.whiteKeys):
                    if rec.Contains(pos):
                        pit = self.white[i % 7] + int(i / 7) * 12 + self.offset
                        if i in self.whiteSelected:
                            self.whiteSelected.remove(i)
                            del self.whiteVelocities[i]
                            total -= 1
                            vel = 0
                        else:
                            vel = int((h - pos[1]) * 127 / h)
                            if total < self.poly:
                                self.whiteSelected.append(i)
                                self.whiteVelocities[i] = int(127 - vel)
                        note = (pit, vel)
                        break
            if note and self.outFunction and total < self.poly:
                self.outFunction(note)
        else:
            self.keyPressed = None
            for i, rec in enumerate(self.blackKeys):
                if rec.Contains(pos):
                    pit = self.black[i % 5] + int(i / 5) * 12 + self.offset
                    vel = 0
                    if i not in self.blackSelected:
                        hb = int(h * 4 / 7)
                        vel = int((hb - pos[1]) * 127 / hb)
                        if total < self.poly:
                            self.blackSelected.append(i)
                            self.blackVelocities[i] = int(127 - vel)
                    note = (pit, vel)
                    self.keyPressed = (i, pit)
                    scanWhite = False
                    break
            if scanWhite:
                for i, rec in enumerate(self.whiteKeys):
                    if rec.Contains(pos):
                        pit = self.white[i % 7] + int(i / 7) * 12 + self.offset
                        vel = 0
                        if i not in self.whiteSelected:
                            vel = int((h - pos[1]) * 127 / h)
                            if total < self.poly:
                                self.whiteSelected.append(i)
                                self.whiteVelocities[i] = int(127 - vel)
                        note = (pit, vel)
                        self.keyPressed = (i, pit)
                        break
            if note and self.outFunction and total < self.poly:
                self.outFunction(note)
        wx.CallAfter(self.Refresh)
        evt.Skip()

    def OnPaint(self, evt):
        w, h = self.GetSize()
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBrush(wx.Brush("#000000", wx.SOLID))
        dc.Clear()
        dc.SetPen(wx.Pen("#000000", width=1, style=wx.SOLID))
        dc.DrawRectangle(0, 0, w, h)

        if sys.platform == "darwin":
            dc.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        else:
            dc.SetFont(wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        for i, rec in enumerate(self.whiteKeys):
            if i in self.whiteSelected:
                amp = int(self.whiteVelocities[i] * 1.5)
                dc.GradientFillLinear(rec, (250, 250, 250), (amp, amp, amp), wx.SOUTH)
                dc.SetBrush(wx.Brush("#CCCCCC", wx.SOLID))
                dc.SetPen(wx.Pen("#CCCCCC", width=1, style=wx.SOLID))
            else:
                dc.SetBrush(wx.Brush("#FFFFFF", wx.SOLID))
                dc.SetPen(wx.Pen("#CCCCCC", width=1, style=wx.SOLID))
                dc.DrawRectangle(rec)
            if i == (35 - (7 * int(self.offset / 12))):
                if i in self.whiteSelected:
                    dc.SetTextForeground("#FFFFFF")
                else:
                    dc.SetTextForeground("#000000")
                dc.DrawText("C", rec[0] + 3, rec[3] - 15)

        dc.SetPen(wx.Pen("#000000", width=1, style=wx.SOLID))
        for i, rec in enumerate(self.blackKeys):
            if i in self.blackSelected:
                amp = int(self.blackVelocities[i] * 1.5)
                dc.GradientFillLinear(rec, (250, 250, 250), (amp, amp, amp), wx.SOUTH)
                dc.DrawLine(rec[0], 0, rec[0], rec[3])
                dc.DrawLine(rec[0] + rec[2], 0, rec[0] + rec[2], rec[3])
                dc.DrawLine(rec[0], rec[3], rec[0] + rec[2], rec[3])
                dc.SetBrush(wx.Brush("#DDDDDD", wx.SOLID))
            else:
                dc.SetBrush(wx.Brush("#000000", wx.SOLID))
                dc.SetPen(wx.Pen("#000000", width=1, style=wx.SOLID))
                dc.DrawRectangle(rec)

        dc.SetBrush(wx.Brush(BACKGROUND_COLOUR, wx.SOLID))
        dc.SetPen(wx.Pen("#AAAAAA", width=1, style=wx.SOLID))
        dc.DrawRectangle(self.offRec)
        dc.DrawRectangle(self.holdRec)

        dc.SetTextForeground("#000000")
        dc.DrawText("oct", self.offRec[0] + 3, 15)
        x1, y1 = self.offRec[0], self.offRec[1]
        dc.SetBrush(wx.Brush("#000000", wx.SOLID))
        if sys.platform == "darwin":
            dc.DrawPolygon([wx.Point(x1 + 3, 36), wx.Point(x1 + 10, 29), wx.Point(x1 + 17, 36)])
            self.offUpRec = wx.Rect(x1, 28, x1 + 20, 10)
            dc.DrawPolygon([wx.Point(x1 + 3, 55), wx.Point(x1 + 10, 62), wx.Point(x1 + 17, 55)])
            self.offDownRec = wx.Rect(x1, 54, x1 + 20, 10)
        else:
            dc.DrawPolygon([wx.Point(x1 + 5, 38), wx.Point(x1 + 12, 31), wx.Point(x1 + 19, 38)])
            self.offUpRec = wx.Rect(x1, 30, x1 + 20, 10)
            dc.DrawPolygon([wx.Point(x1 + 5, 57), wx.Point(x1 + 12, 64), wx.Point(x1 + 19, 57)])
            self.offDownRec = wx.Rect(x1, 56, x1 + 20, 10)

        dc.DrawText("%d" % int(self.offset / 12), x1 + 9, 41)

        if self.hold:
            dc.SetTextForeground("#0000CC")
        else:
            dc.SetTextForeground("#000000")
        for i, c in enumerate("HOLD"):
            dc.DrawText(c, self.holdRec[0] + 8, int(self.holdRec[3] / 6) * i + 15)
        evt.Skip()
