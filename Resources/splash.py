import wx
import os
import Resources.variables as vars


def GetRoundBitmap(w, h, r=None):
    x = int(w/2)
    y = int(h/2)
    if r is None:
        if vars.constants["IS_WIN"]:
            r = int(h/2)
        else:
            r = int(h/2) - 5
    maskColour = wx.BLACK
    shownColour = wx.RED
    b = wx.Bitmap(w, h)
    dc = wx.MemoryDC(b)
    dc.SetBrush(wx.Brush(maskColour))
    dc.DrawRectangle(0, 0, w, h)
    dc.SetBrush(wx.Brush(shownColour))
    dc.SetPen(wx.Pen(shownColour, 0))
    dc.DrawCircle(x, y, r)
    dc.SelectObject(wx.NullBitmap)
    b.SetMaskColour(maskColour)
    return b


class ZyneSplashScreen(wx.Frame):
    def __init__(self, parent, img, mainframe):
        display = wx.Display(0)
        size = display.GetGeometry()[2:]
        wx.Frame.__init__(
            self, parent, -1, "", pos=(-1, -size[1]/6),
            style=wx.FRAME_SHAPED | wx.BORDER_NONE | wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP)

        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.bmp = wx.Bitmap(os.path.join(img), wx.BITMAP_TYPE_PNG)

        wx.CallAfter(mainframe.Show)

        self.w, self.h = self.FromDIP(self.bmp.GetSize())
        self.SetClientSize((self.w, self.h))

        if wx.Platform == "__WXGTK__":
            self.Bind(wx.EVT_WINDOW_CREATE, self.SetWindowShape)
        elif vars.constants["IS_WIN"]:
            # win draws a border around shaped bmp, that's why fake shaped frame
            self.hasShape = False
        else:
            self.SetWindowShape()

        wx.CallLater(3500, self.OnClose)

        self.Center(wx.BOTH)
        if vars.constants["IS_WIN"]:
            # win draws a border around shaped bmp, that's why fake shaped frame
            self.SetPosition(self.FromDIP(wx.Point(570, 200)))

        wx.CallAfter(self.Show)

    def SetWindowShape(self, evt=None):
        r = wx.Region(GetRoundBitmap(self.w, self.h))
        self.hasShape = self.SetShape(r)

    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        if vars.constants["IS_WIN"]:
            # win draws a border around shaped bmp, that's why fake shaped frame
            dc.SetBackground(wx.Brush(wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU)))
        else:
            dc.SetBackground(wx.Brush(wx.BLACK))
        dc.Clear()
        dc.DrawBitmap(self.bmp, 0, 0, True)
        dc.SetTextForeground(wx.BLACK)
        font = dc.GetFont()
        ptsize = font.GetPointSize()
        font.SetPointSize(ptsize + 4)
        if vars.constants["IS_WIN"]:
            font.SetFaceName("Consolas")
        else:
            font.SetFaceName("Monaco")
        dc.SetFont(font)
        dc.DrawLabel("Zyne_B", wx.Rect(self.FromDIP(50), self.FromDIP(230), self.FromDIP(400), self.FromDIP(18)), wx.ALIGN_LEFT)
        dc.DrawLabel("Modular Soft Synthesizer", wx.Rect(self.FromDIP(70), self.FromDIP(250), self.FromDIP(400), self.FromDIP(18)), wx.ALIGN_LEFT)
        font.SetPointSize(ptsize + 1)
        dc.SetFont(font)
        dc.DrawLabel("Olivier Bélanger (ajaxsoundstudio)",
                     wx.Rect(self.FromDIP(0), self.FromDIP(305), self.FromDIP(400), self.FromDIP(15)), wx.ALIGN_CENTER)
        dc.DrawLabel("Hans-Jörg Bibiko", wx.Rect(self.FromDIP(0), self.FromDIP(320), self.FromDIP(400), self.FromDIP(15)), wx.ALIGN_CENTER)
        dc.DrawLabel(f"Version {vars.constants['VERSION']} - {vars.constants['YEAR']}",
                     wx.Rect(self.FromDIP(0), self.FromDIP(340), self.FromDIP(400), self.FromDIP(15)), wx.ALIGN_CENTER)

    def OnClose(self):
        self.Destroy()
