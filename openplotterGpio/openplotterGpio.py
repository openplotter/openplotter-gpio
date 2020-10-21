#!/usr/bin/env python3

# This file is part of Openplotter.
# Copyright (C) 2020 by Sailoog <https://github.com/openplotter/openplotter-gpio>
#
# Openplotter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Openplotter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openplotter. If not, see <http://www.gnu.org/licenses/>.

import wx, os, webbrowser, subprocess, time, sys, ujson
from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform
from openplotterSettings import gpio
from .version import version

class MyFrame(wx.Frame):
	def __init__(self):
		self.conf = conf.Conf()
		self.conf_folder = self.conf.conf_folder
		self.platform = platform.Platform()
		self.currentdir = os.path.dirname(os.path.abspath(__file__))
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		self.language = language.Language(self.currentdir,'openplotter-gpio',self.currentLanguage)

		wx.Frame.__init__(self, None, title='GPIO '+version, size=(800,444))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		icon = wx.Icon(self.currentdir+"/data/openplotter-gpio.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)
		self.CreateStatusBar()
		font_statusBar = self.GetStatusBar().GetFont()
		font_statusBar.SetWeight(wx.BOLD)
		self.GetStatusBar().SetFont(font_statusBar)

		self.toolbar1 = wx.ToolBar(self, style=wx.TB_TEXT)
		toolHelp = self.toolbar1.AddTool(101, _('Help'), wx.Bitmap(self.currentdir+"/data/help.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolHelp, toolHelp)
		if not self.platform.isInstalled('openplotter-doc'): self.toolbar1.EnableTool(101,False)
		toolSettings = self.toolbar1.AddTool(102, _('Settings'), wx.Bitmap(self.currentdir+"/data/settings.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolSettings, toolSettings)
		self.toolbar1.AddSeparator()
		toolGpio = self.toolbar1.AddTool(103, _('GPIO Map'), wx.Bitmap(self.currentdir+"/data/chip.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolGpio, toolGpio)
		self.toolbar1.AddSeparator()
		self.refresh = self.toolbar1.AddTool(104, _('Refresh'), wx.Bitmap(self.currentdir+"/data/refresh.png"))
		self.Bind(wx.EVT_TOOL, self.onRefresh, self.refresh)

		self.notebook = wx.Notebook(self)
		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onTabChange)
		self.digital = wx.Panel(self.notebook)
		self.oneW = wx.Panel(self.notebook)
		self.seatalk = wx.Panel(self.notebook)
		self.pulses = wx.Panel(self.notebook)
		self.connections = wx.Panel(self.notebook)
		self.notebook.AddPage(self.digital, _('Digital'))
		self.notebook.AddPage(self.pulses, _('Pulses'))
		self.notebook.AddPage(self.oneW, '1W')
		self.notebook.AddPage(self.connections, _('Connections'))
		self.notebook.AddPage(self.seatalk, ' Seatalk 1')
		self.il = wx.ImageList(24, 24)
		img0 = self.il.Add(wx.Bitmap(self.currentdir+"/data/openplotter-24.png", wx.BITMAP_TYPE_PNG))
		img1 = self.il.Add(wx.Bitmap(self.currentdir+"/data/openplotter-24.png", wx.BITMAP_TYPE_PNG))
		img2 = self.il.Add(wx.Bitmap(self.currentdir+"/data/openplotter-24.png", wx.BITMAP_TYPE_PNG))
		img3 = self.il.Add(wx.Bitmap(self.currentdir+"/data/connections.png", wx.BITMAP_TYPE_PNG))
		img4 = self.il.Add(wx.Bitmap(self.currentdir+"/data/seatalk.png", wx.BITMAP_TYPE_PNG))
		self.notebook.AssignImageList(self.il)
		self.notebook.SetPageImage(0, img0)
		self.notebook.SetPageImage(1, img1)
		self.notebook.SetPageImage(2, img2)
		self.notebook.SetPageImage(3, img3)
		self.notebook.SetPageImage(4, img4)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar1, 0, wx.EXPAND)
		vbox.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(vbox)

		self.pageDigital()
		self.pageOneW()
		self.pagePulses()
		self.pageConnections()
		self.pageSeatalk()

		self.onRefresh()

		maxi = self.conf.get('GENERAL', 'maximize')
		if maxi == '1': self.Maximize()

		self.Centre()

	def ShowStatusBar(self, w_msg, colour):
		self.GetStatusBar().SetForegroundColour(colour)
		self.SetStatusText(w_msg)

	def ShowStatusBarRED(self, w_msg):
		self.ShowStatusBar(w_msg, (130,0,0))

	def ShowStatusBarGREEN(self, w_msg):
		self.ShowStatusBar(w_msg, (0,130,0))

	def ShowStatusBarBLACK(self, w_msg):
		self.ShowStatusBar(w_msg, wx.BLACK) 

	def ShowStatusBarYELLOW(self, w_msg):
		self.ShowStatusBar(w_msg,(255,140,0)) 

	def onTabChange(self, event):
		try:
			self.SetStatusText('')
		except:pass

	def OnToolHelp(self, event): 
		url = "/usr/share/openplotter-doc/gpio/gpio_app.html"
		webbrowser.open(url, new=2)

	def OnToolSettings(self, event=0): 
		subprocess.call(['pkill', '-f', 'openplotter-settings'])
		subprocess.Popen('openplotter-settings')

	def OnToolGpio(self,e):
		dlg = gpio.GpioMap()
		res = dlg.ShowModal()
		dlg.Destroy()

	def pageDigital(self):
		text1 = wx.StaticText(self.digital, label=_('Coming soon.'))

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.AddStretchSpacer(1)
		hbox1.Add(text1, 0, wx.ALL | wx.EXPAND, 5)
		hbox1.AddStretchSpacer(1)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddStretchSpacer(1)
		vbox.Add(hbox1, 0, wx.ALL | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		self.digital.SetSizer(vbox)

	def pageOneW(self):
		text1 = wx.StaticText(self.oneW, label=_('Coming soon.'))

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.AddStretchSpacer(1)
		hbox1.Add(text1, 0, wx.ALL | wx.EXPAND, 5)
		hbox1.AddStretchSpacer(1)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddStretchSpacer(1)
		vbox.Add(hbox1, 0, wx.ALL | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		self.oneW.SetSizer(vbox)

	def pagePulses(self):
		text1 = wx.StaticText(self.pulses, label=_('Coming soon.'))

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.AddStretchSpacer(1)
		hbox1.Add(text1, 0, wx.ALL | wx.EXPAND, 5)
		hbox1.AddStretchSpacer(1)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddStretchSpacer(1)
		vbox.Add(hbox1, 0, wx.ALL | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		self.pulses.SetSizer(vbox)

	def pageConnections(self):
		text1 = wx.StaticText(self.connections, label=_('Coming soon.'))

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.AddStretchSpacer(1)
		hbox1.Add(text1, 0, wx.ALL | wx.EXPAND, 5)
		hbox1.AddStretchSpacer(1)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddStretchSpacer(1)
		vbox.Add(hbox1, 0, wx.ALL | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		self.connections.SetSizer(vbox)

	def restart_SK(self, msg):
		if self.platform.skDir:
			if msg == 0: msg = _('Restarting Signal K server... ')
			seconds = 12
			subprocess.call([self.platform.admin, 'python3', self.currentdir+'/service.py', 'sk', 'restart'])
			for i in range(seconds, 0, -1):
				self.ShowStatusBarYELLOW(msg+str(i))
				time.sleep(1)
			self.ShowStatusBarGREEN(_('Signal K server restarted'))

	def onRefresh(self, e=0):
		try:
			subprocess.check_output(['systemctl', 'is-enabled', 'pigpiod']).decode(sys.stdin.encoding)
			self.toolbar33.ToggleTool(3301,True)
		except: self.toolbar33.ToggleTool(3301,False)

		self.SetStatusText('')

		self.readSeatalk()

	#############################################################################################3

	def pageSeatalk(self):
		self.listSeatalk = wx.ListCtrl(self.seatalk, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listSeatalk.InsertColumn(0, 'GPIO', width=100)
		self.listSeatalk.InsertColumn(1, _('Invert signal'), width=200)
		self.listSeatalk.InsertColumn(2, _('SK connection ID'), width=270)
		self.listSeatalk.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListlistSeatalkSelected)
		self.listSeatalk.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListlistSeatalkDeselected)
		self.listSeatalk.SetTextColour(wx.BLACK)

		self.toolbar33 = wx.ToolBar(self.seatalk, style=wx.TB_TEXT)
		enableSeatalk = self.toolbar33.AddCheckTool(3301, _('Enable Seatalk 1 reception'), wx.Bitmap(self.currentdir+"/data/seatalk.png"))
		self.Bind(wx.EVT_TOOL, self.onEnableSeatalk, enableSeatalk)
		self.addSeatalkCon = self.toolbar33.AddTool(3302, _('Add SK Connection'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.onAddSeatalkCon, self.addSeatalkCon)

		self.toolbar3 = wx.ToolBar(self.seatalk, style=wx.TB_TEXT | wx.TB_VERTICAL)
		self.editSeatalkCon= self.toolbar3.AddTool(301, _('Edit Connection'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.onEditSeatalkCon, self.editSeatalkCon)
		self.removeSeatalkCon = self.toolbar3.AddTool(302, _('Remove Connection'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.onRemoveSeatalkCon, self.removeSeatalkCon)

		h1 = wx.BoxSizer(wx.HORIZONTAL)
		h1.Add(self.listSeatalk, 1, wx.EXPAND, 0)
		h1.Add(self.toolbar3, 0, wx.EXPAND, 0)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.toolbar33, 0, wx.EXPAND, 0)
		sizer.Add(h1, 1, wx.EXPAND, 0)

		self.seatalk.SetSizer(sizer)

	def onEnableSeatalk(self, e):
		if self.toolbar33.GetToolState(3301):
			subprocess.call([self.platform.admin, 'python3', self.currentdir+'/service.py', 'seatalk', 'start'])
			self.onRefresh()
			self.ShowStatusBarGREEN(_('Seatalk 1 enabled'))
		else:
			subprocess.call([self.platform.admin, 'python3', self.currentdir+'/service.py', 'seatalk', 'stop'])
			self.onRefresh()
			self.ShowStatusBarRED(_('Seatalk 1 disabled'))

	def onListlistSeatalkSelected(self,e):
		self.onListlistSeatalkDeselected()
		selected = self.listSeatalk.GetFirstSelected()
		if selected == -1: return
		self.toolbar3.EnableTool(301,True)
		self.toolbar3.EnableTool(302,True)

	def onListlistSeatalkDeselected(self,e=0):
		self.toolbar3.EnableTool(301,False)
		self.toolbar3.EnableTool(302,False)

	def onAddSeatalkCon(self,e):
		if self.platform.skPort: 
			ID = ''
			gpio = '' 
			gpioInvert = ''
			dlg = addSeatalkConn()
			res = dlg.ShowModal()
			if res == wx.ID_OK:
				ID = dlg.ID.GetValue()
				gpio = dlg.gpio.GetValue()
				gpioInvert = dlg.gpioInvert.GetValue()
				if not ID or not gpio:
					self.ShowStatusBarRED(_('Fill in all fields'))
					dlg.Destroy()
					return
				if len(gpio) == 6: gpio = gpio.replace(' ','0')
				if len(gpio) == 7: gpio = gpio.replace(' ','')
				from openplotterSignalkInstaller import editSettings
				skSettings = editSettings.EditSettings()
				c = 0
				while True:
					if skSettings.connectionIdExists(ID):
						ID = ID+str(c)
						c = c + 1
					else: break
				if skSettings.setSeatalkConnection(ID, gpio, gpioInvert): 
					self.restart_SK(0)
					self.onRefresh()
				else: self.ShowStatusBarRED(_('Failed. Error creating connection in Signal K'))
			dlg.Destroy()
		else: 
			self.ShowStatusBarRED(_('Please install "Signal K Installer" OpenPlotter app'))
			self.OnToolSettings()

	def onEditSeatalkCon(self,e):
		selected = self.listSeatalk.GetFirstSelected()
		if selected == -1: return
		skId = self.listSeatalk.GetItemText(selected, 2)
		url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/serverConfiguration/connections/'+skId
		webbrowser.open(url, new=2)

	def onRemoveSeatalkCon(self,e):
		selected = self.listSeatalk.GetFirstSelected()
		if selected == -1: return
		skId = self.listSeatalk.GetItemText(selected, 2)
		from openplotterSignalkInstaller import editSettings
		skSettings = editSettings.EditSettings()
		if skSettings.removeConnection(skId): 
			self.restart_SK(0)
			self.onRefresh()
		else: self.ShowStatusBarRED(_('Failed. Error removing connection in Signal K'))

	def readSeatalk(self):
		self.listSeatalk.DeleteAllItems()
		self.onListlistSeatalkDeselected()
		try:
			setting_file = self.platform.skDir+'/settings.json'
			with open(setting_file) as data_file:
				data = ujson.load(data_file)
		except: data = {}
		if 'pipedProviders' in data:
			data = data['pipedProviders']
		else:
			data = []
		for i in data:
			dataType = ''
			subOptions = ''
			skId = ''
			enabled = False
			gpio = ''
			gpioInvert = False
			gpioInvert2 = _('no')
			try:
				dataType = i['pipeElements'][0]['options']['type']
				if dataType == 'Seatalk':
					subOptions = i['pipeElements'][0]['options']['subOptions']
					skId = i['id']
					enabled = i['enabled']
					if 'gpio' in subOptions: gpio = subOptions['gpio']
					if 'gpioInvert' in subOptions: 
						gpioInvert = subOptions['gpioInvert']
						if gpioInvert: gpioInvert2 = _('yes')
					self.listSeatalk.Append([gpio,gpioInvert2,skId])
					if self.toolbar33.GetToolState(3301) and enabled: self.listSeatalk.SetItemBackgroundColour(self.listSeatalk.GetItemCount()-1,(255,220,100))
			except: pass

################################################################################

class addSeatalkConn(wx.Dialog):
	def __init__(self):
		title = _('Add SK Connection')

		wx.Dialog.__init__(self, None, title=title, size=(260, 230))
		panel = wx.Panel(self)

		idLabel = wx.StaticText(panel, label=_('ID'))
		self.ID = wx.TextCtrl(panel)

		gpioLabel = wx.StaticText(panel, label='GPIO')
		self.gpio = wx.TextCtrl(panel, style=wx.CB_READONLY)

		selectGpio =wx.Button(panel, label=_('Select'))
		selectGpio.Bind(wx.EVT_BUTTON, self.onSelectGpio)

		self.gpioInvert = wx.CheckBox(panel, 333, label=_('Invert signal'))

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.Add(idLabel, 0, wx.LEFT | wx.EXPAND, 10)
		hbox1.Add(self.ID, 1, wx.LEFT |  wx.RIGHT | wx.EXPAND, 10)

		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		hbox2.Add(gpioLabel, 0, wx.LEFT | wx.EXPAND, 10)
		hbox2.Add(self.gpio, 1, wx.LEFT |  wx.RIGHT | wx.EXPAND, 10)
		hbox2.Add(selectGpio, 1, wx.LEFT |  wx.RIGHT | wx.EXPAND, 10)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.AddStretchSpacer(1)
		hbox.Add(cancelBtn, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
		hbox.Add(okBtn, 0, wx.RIGHT | wx.EXPAND, 10)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(10)
		vbox.Add(hbox1, 0, wx.EXPAND, 0)
		vbox.AddSpacer(20)
		vbox.Add(hbox2, 0, wx.EXPAND, 0)
		vbox.AddSpacer(20)
		vbox.Add(self.gpioInvert, 0, wx.LEFT | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		vbox.Add(hbox, 0, wx.EXPAND, 0)
		vbox.AddSpacer(10)

		panel.SetSizer(vbox)
		self.panel = panel

		self.Centre() 

	def onSelectGpio(self,e):
		dlg = gpio.GpioMap(['GPIO'],'0')
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			self.gpio.SetValue(dlg.selected['BCM'])
		dlg.Destroy()

	def OnDelete(self,e):
		self.EndModal(wx.ID_DELETE)

################################################################################

def main():
	try:
		platform2 = platform.Platform()
		if not platform2.postInstall(version,'gpio'):
			subprocess.Popen(['openplotterPostInstall', platform2.admin+' gpioPostInstall'])
			return
	except: pass

	app = wx.App()
	MyFrame().Show()
	time.sleep(1)
	app.MainLoop()

if __name__ == '__main__':
	main()
