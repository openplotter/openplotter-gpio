#!/usr/bin/env python3

# This file is part of OpenPlotter.
# Copyright (C) 2022 by Sailoog <https://github.com/openplotter/openplotter-gpio>
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

import wx, os, webbrowser, subprocess, time, sys, ujson, requests, uuid
from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform
from openplotterSettings import gpio
from openplotterSettings import selectKey
from openplotterSignalkInstaller import connections
from w1thermsensor import W1ThermSensor
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
		self.aproveSK = self.toolbar1.AddTool(105, _('Approve'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.onAproveSK, self.aproveSK)
		self.connectionSK = self.toolbar1.AddTool(106, _('Allowed'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.onConnectionSK, self.connectionSK)
		self.toolbar1.AddSeparator()
		self.refresh = self.toolbar1.AddTool(104, _('Refresh'), wx.Bitmap(self.currentdir+"/data/refresh.png"))
		self.Bind(wx.EVT_TOOL, self.onRefresh, self.refresh)
		self.toolbar1.AddSeparator()
		toolRescue = self.toolbar1.AddCheckTool(107, _('Rescue'), wx.Bitmap(self.currentdir+"/data/rescue.png"))
		self.Bind(wx.EVT_TOOL, self.onToolRescue, toolRescue)
		if self.conf.get('GENERAL', 'rescue') == 'yes': self.toolbar1.ToggleTool(107,True)

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
		self.notebook.AddPage(self.seatalk, _(' Seatalk1 input'))
		self.il = wx.ImageList(24, 24)
		img0 = self.il.Add(wx.Bitmap(self.currentdir+"/data/digital.png", wx.BITMAP_TYPE_PNG))
		img1 = self.il.Add(wx.Bitmap(self.currentdir+"/data/pulses.png", wx.BITMAP_TYPE_PNG))
		img2 = self.il.Add(wx.Bitmap(self.currentdir+"/data/temp.png", wx.BITMAP_TYPE_PNG))
		img3 = self.il.Add(wx.Bitmap(self.currentdir+"/data/seatalk.png", wx.BITMAP_TYPE_PNG))
		self.notebook.AssignImageList(self.il)
		self.notebook.SetPageImage(0, img0)
		self.notebook.SetPageImage(1, img1)
		self.notebook.SetPageImage(2, img2)
		self.notebook.SetPageImage(3, img3)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar1, 0, wx.EXPAND)
		vbox.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(vbox)

		if not self.platform.isRPI: self.toolbar1.EnableTool(103,False)

		self.pageDigital()
		self.pageOneW()
		self.pagePulses()
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
		#TODO
		if self.notebook.GetSelection() == 1 or self.notebook.GetSelection() == 3: self.ShowStatusBarRED('Coming soon')
		else:
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

	def onAproveSK(self,e):
		if self.platform.skPort: 
			url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/security/access/requests'
			webbrowser.open(url, new=2)

	def onConnectionSK(self,e):
		if self.platform.skPort: 
			url = self.platform.http+'localhost:'+self.platform.skPort+'/admin/#/security/devices'
			webbrowser.open(url, new=2)

	def restart_SK(self, msg):
		if self.platform.skDir:
			if msg == 0: msg = _('Restarting Signal K server... ')
			seconds = 12
			subprocess.call([self.platform.admin, 'python3', self.currentdir+'/service.py', 'sk', 'restart'])
			for i in range(seconds, 0, -1):
				self.ShowStatusBarYELLOW(msg+str(i))
				time.sleep(1)
			self.ShowStatusBarGREEN(_('Signal K server restarted'))

	def stopGpioRead(self):
		subprocess.call(['pkill', '-f', 'openplotter-gpio-read'])

	def onRefresh(self, e=0):
		self.ShowStatusBarBLACK(' ')

		#self.readSeatalk()
		self.readOneW()
		#self.readPulses()
		self.readDigital()

		enable = False
		if self.oneWlist: enable = True
		#if self.gpioPulses: enable = True
		if self.gpioDigital: enable = True
		if enable:
			test = subprocess.check_output(['ps','aux']).decode(sys.stdin.encoding)
			if not 'openplotter-gpio-read' in test:
				if self.conf.get('GENERAL', 'rescue') != 'yes': 
					subprocess.Popen('openplotter-gpio-read')
					self.ShowStatusBarGREEN(_('GPIO service is enabled'))
				else:
					self.ShowStatusBarRED(_('GPIO is in rescue mode'))
			else:
				if self.conf.get('GENERAL', 'rescue') == 'yes': 
					self.stopGpioRead()
					self.ShowStatusBarRED(_('GPIO is in rescue mode'))
				else:
					self.ShowStatusBarGREEN(_('GPIO service is enabled'))
		else: 
			self.stopGpioRead()
			self.ShowStatusBarBLACK(_('There is nothing to send. GPIO service is disabled'))

		try: subprocess.check_output(['systemctl', 'is-enabled', 'pigpiod']).decode(sys.stdin.encoding)
		except: self.ShowStatusBarRED('pigpiod is disabled')

		self.toolbar1.EnableTool(105,False)
		skConnections = connections.Connections('GPIO')
		result = skConnections.checkConnection()
		if result[0] == 'pending':
			self.toolbar1.EnableTool(105,True)
			self.ShowStatusBarYELLOW(result[1]+_(' Press "Approve" and then "Refresh".'))
		elif result[0] == 'error':
			self.ShowStatusBarRED(result[1])
		elif result[0] == 'repeat':
			self.ShowStatusBarYELLOW(result[1]+_(' Press "Refresh".'))
		elif result[0] == 'permissions':
			self.ShowStatusBarYELLOW(result[1]+_(' Press "Allowed".'))
		elif result[0] == 'approved':
			self.ShowStatusBarGREEN(result[1])

	def onToolRescue(self,e):
		if self.toolbar1.GetToolState(107): self.conf.set('GENERAL', 'rescue', 'yes')
		else: self.conf.set('GENERAL', 'rescue', 'no')
		self.onRefresh()

	###########################################################################

	def pageDigital(self):
		self.listDigital = wx.ListCtrl(self.digital, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listDigital.InsertColumn(0, _('Host'), width=75)
		self.listDigital.InsertColumn(1, 'GPIO', width=70)
		self.listDigital.InsertColumn(2, _('Mode'), width=70)
		self.listDigital.InsertColumn(3, _('High'), width=210)
		self.listDigital.InsertColumn(4, _('Low'), width=210)
		self.listDigital.InsertColumn(5, _('Initial state'), width=150)
		self.listDigital.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListDigitalSelected)
		self.listDigital.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListDigitalDeselected)
		self.listDigital.SetTextColour(wx.BLACK)

		self.toolbar6 = wx.ToolBar(self.digital, style=wx.TB_TEXT | wx.TB_VERTICAL)
		self.addDigital = self.toolbar6.AddTool(603, _('Add input'), wx.Bitmap(self.currentdir+"/data/chip.png"))
		self.Bind(wx.EVT_TOOL, self.onAddDigital, self.addDigital)
		self.addDigitalOut = self.toolbar6.AddTool(604, _('Add output'), wx.Bitmap(self.currentdir+"/data/chip.png"))
		self.Bind(wx.EVT_TOOL, self.onAddDigitalOut, self.addDigitalOut)
		self.editDigital= self.toolbar6.AddTool(601, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.onEditDigital, self.editDigital)
		self.removeDigital= self.toolbar6.AddTool(602, _('Remove'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.onRemoveDigital, self.removeDigital)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.listDigital, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar6, 0, wx.EXPAND, 0)

		self.digital.SetSizer(sizer)

	def onListDigitalSelected(self,e):
		self.onListDigitalDeselected()
		selected = self.listDigital.GetFirstSelected()
		if selected == -1: return
		self.toolbar6.EnableTool(601,True)
		self.toolbar6.EnableTool(602,True)

	def onListDigitalDeselected(self,e=0):
		self.toolbar6.EnableTool(601,False)
		self.toolbar6.EnableTool(602,False)

	def onAddDigital(self,e):
		edit = {}
		self.setDigital(edit)

	def onAddDigitalOut(self,e):
		edit = {}
		self.setDigitalOut(edit)

	def onEditDigital(self,e):
		selected = self.listDigital.GetFirstSelected()
		if selected == -1: return
		host = self.listDigital.GetItemText(selected, 0)
		gpio = self.listDigital.GetItemText(selected, 1)
		index = host+'-'+gpio
		edit = self.gpioDigital[index]
		edit['host'] = host
		edit['gpio'] = gpio
		if self.gpioDigital[index]['mode'] == 'in': self.setDigital(edit)
		elif self.gpioDigital[index]['mode'] == 'out': self.setDigitalOut(edit)

	def setDigital(self,edit):
		dlg = editDigital(edit)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			if dlg.localhost.GetValue(): host = 'localhost'
			else: host = dlg.host.GetValue()
			gpio = dlg.gpio.GetValue()
			index = host+'-'+gpio
			if edit:
				oldIndex = edit['host']+'-'+edit['gpio']
				if oldIndex != index: del self.gpioDigital[oldIndex]
			pull = str(dlg.pull.GetValue())
			init = dlg.init.GetValue()
			stateH = dlg.stateH.GetValue()
			messageH = dlg.messageH.GetValue()
			visualH = dlg.visualH.GetValue()
			soundH = dlg.soundH.GetValue()
			stateL = dlg.stateL.GetValue()
			messageL = dlg.messageL.GetValue()
			visualL = dlg.visualL.GetValue()
			soundL = dlg.soundL.GetValue()
			self.gpioDigital[index] = {"mode":"in","pull": pull, "init": init, "high":{"state":stateH,"message":messageH,"visual":visualH,"sound":soundH},"low":{"state":stateL,"message":messageL,"visual":visualL,"sound":soundL}}
			self.conf.set('GPIO', 'digital', str(self.gpioDigital))
			self.stopGpioRead()
			self.onRefresh()
		dlg.Destroy()

	def setDigitalOut(self,edit):
		dlg = editDigitalOut(edit)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			if dlg.localhost.GetValue(): host = 'localhost'
			else: host = dlg.host.GetValue()
			gpio = dlg.gpio.GetValue()
			index = host+'-'+gpio
			if edit:
				oldIndex = edit['host']+'-'+edit['gpio']
				if oldIndex != index: del self.gpioDigital[oldIndex]
			self.gpioDigital[index] = {"mode":"out"}
			self.conf.set('GPIO', 'digital', str(self.gpioDigital))
			self.stopGpioRead()
			self.onRefresh()
			self.ShowStatusBarBLACK(_('You can turn GPIO outputs high or low using "Actions" in the Notifications app'))
		dlg.Destroy()

	def onRemoveDigital(self,e):
		selected = self.listDigital.GetFirstSelected()
		if selected == -1: return
		host = self.listDigital.GetItemText(selected, 0)
		gpio = self.listDigital.GetItemText(selected, 1)
		index = host+'-'+gpio
		del self.gpioDigital[index]
		self.conf.set('GPIO', 'digital', str(self.gpioDigital))
		self.stopGpioRead()
		self.onRefresh()

	def readDigital(self):
		self.listDigital.DeleteAllItems()
		self.onListDigitalDeselected()
		data = self.conf.get('GPIO', 'digital')
		try: self.gpioDigital = eval(data)
		except: self.gpioDigital = {}
		if self.gpioDigital:
			for i in self.gpioDigital:
				items = i.split('-')
				host = items[0]
				gpio = items[1]
				if self.gpioDigital[i]['mode'] == 'in':
					if self.gpioDigital[i]['init']: init = _('yes')
					else: init = _('no')
					high = str(self.gpioDigital[i]['high'])
					low = str(self.gpioDigital[i]['low'])
					self.listDigital.Append([host, gpio, _('input'), high, low, init])
				elif self.gpioDigital[i]['mode'] == 'out': self.listDigital.Append([host, gpio, _('output'), '', '', ''])
				self.listDigital.SetItemBackgroundColour(self.listDigital.GetItemCount()-1,(255,220,100))

	###########################################################################

	def pagePulses(self):
		pass
		'''
		self.listPulses = wx.ListCtrl(self.pulses, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listPulses.InsertColumn(0, _('Host'), width=75)
		self.listPulses.InsertColumn(1, 'GPIO', width=50)
		self.listPulses.InsertColumn(2, _('Revolutions'), width=115)
		self.listPulses.InsertColumn(3, _('Counter'), width=115)
		self.listPulses.InsertColumn(4, _('Reset'), width=115)
		self.listPulses.InsertColumn(5, _('Speed'), width=115)
		self.listPulses.InsertColumn(6, _('Distance'), width=115)
		self.listPulses.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListlistPulsesSelected)
		self.listPulses.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListlistPulsesDeselected)
		self.listPulses.SetTextColour(wx.BLACK)

		self.toolbar5 = wx.ToolBar(self.pulses, style=wx.TB_TEXT | wx.TB_VERTICAL)
		self.addPulses = self.toolbar5.AddTool(503, _('Add'), wx.Bitmap(self.currentdir+"/data/chip.png"))
		self.Bind(wx.EVT_TOOL, self.onAddPulses, self.addPulses)
		self.editPulses= self.toolbar5.AddTool(501, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.onEditPulses, self.editPulses)
		self.removePulses = self.toolbar5.AddTool(502, _('Remove'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.onRemovePulses, self.removePulses)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.listPulses, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar5, 0, wx.EXPAND, 0)

		self.pulses.SetSizer(sizer)
		'''
	def onListlistPulsesSelected(self,e):
		self.onListlistPulsesDeselected()
		selected = self.listPulses.GetFirstSelected()
		if selected == -1: return
		self.toolbar5.EnableTool(501,True)
		self.toolbar5.EnableTool(502,True)

	def onListlistPulsesDeselected(self,e=0):
		self.toolbar5.EnableTool(501,False)
		self.toolbar5.EnableTool(502,False)

	def onAddPulses(self,e):
		edit = {}
		self.setPulses(edit)

	def onEditPulses(self,e):
		selected = self.listPulses.GetFirstSelected()
		if selected == -1: return
		host = self.listPulses.GetItemText(selected, 0)
		gpio = self.listPulses.GetItemText(selected, 1)
		index = host+'-'+gpio
		edit = {"host": host, "gpio": gpio, "rate": self.gpioPulses[index]['rate'],"pulsesPerRev": self.gpioPulses[index]['pulsesPerRev'],"pull": self.gpioPulses[index]['pull'], "weighting": self.gpioPulses[index]['weighting'], "minRPM": self.gpioPulses[index]['minRPM'], "counterSK": self.gpioPulses[index]['revCounter'], "resetSK": self.gpioPulses[index]['resetCounter'], "revolutionsSK": self.gpioPulses[index]['revolutions'], "radius": self.gpioPulses[index]['radius'], "calibration": self.gpioPulses[index]['calibration'], "speedSK": self.gpioPulses[index]['linearSpeed'], "distanceSK": self.gpioPulses[index]['distance']}
		self.setPulses(edit)

	def setPulses(self,edit):
		dlg = editPulses(edit)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			if dlg.localhost.GetValue(): host = 'localhost'
			else: host = dlg.host.GetValue()
			gpio = dlg.gpio.GetValue()
			index = host+'-'+gpio
			if edit:
				oldIndex = edit['host']+'-'+edit['gpio']
				if oldIndex != index: del self.gpioPulses[oldIndex]
			rate = float(dlg.rate.GetValue())
			pulsesPerRev = int(dlg.pulses.GetValue())
			pull = str(dlg.pull.GetValue())
			weighting = float(dlg.weighting.GetValue())
			minRPM = int(dlg.minRPM.GetValue())
			revCounter = str(dlg.counterSK.GetValue())
			resetCounter = str(dlg.resetSK.GetValue())
			revolutions = str(dlg.revolutionsSK.GetValue())
			if dlg.radius.GetValue(): radius = float(dlg.radius.GetValue())
			else: radius = ''
			calibration = float(dlg.calibration.GetValue())
			linearSpeed = str(dlg.speedSK.GetValue())
			distance = str(dlg.distanceSK.GetValue())
			self.gpioPulses[index] = {"rate": rate, "pulsesPerRev": pulsesPerRev, "pull": pull, "weighting": weighting, "minRPM": minRPM, "revCounter": revCounter, "resetCounter": resetCounter, "revolutions": revolutions, "radius": radius, "calibration": calibration, "linearSpeed": linearSpeed, "distance": distance}
			self.conf.set('GPIO', 'pulses', str(self.gpioPulses))
			self.stopGpioRead()
			self.onRefresh()
		dlg.Destroy()

	def onRemovePulses(self,e):
		selected = self.listPulses.GetFirstSelected()
		if selected == -1: return
		host = self.listPulses.GetItemText(selected, 0)
		gpio = self.listPulses.GetItemText(selected, 1)
		index = host+'-'+gpio
		del self.gpioPulses[index]
		self.conf.set('GPIO', 'pulses', str(self.gpioPulses))
		self.stopGpioRead()
		self.onRefresh()

	def readPulses(self):
		self.listPulses.DeleteAllItems()
		self.onListlistPulsesDeselected()
		data = self.conf.get('GPIO', 'pulses')
		try: self.gpioPulses = eval(data)
		except: self.gpioPulses = {}
		if self.gpioPulses:
			for i in self.gpioPulses:
				items = i.split('-')
				host = items[0]
				gpio = items[1]
				self.listPulses.Append([host, gpio, self.gpioPulses[i]['revolutions'], self.gpioPulses[i]['revCounter'], self.gpioPulses[i]['resetCounter'], self.gpioPulses[i]['linearSpeed'], self.gpioPulses[i]['distance']])
				if self.gpioPulses[i]['revolutions'] or self.gpioPulses[i]['revCounter'] or self.gpioPulses[i]['linearSpeed'] or self.gpioPulses[i]['distance']:
					self.listPulses.SetItemBackgroundColour(self.listPulses.GetItemCount()-1,(255,220,100))

	###########################################################################

	def pageOneW(self):
		if self.platform.isRPI:
			self.listOneW = wx.ListCtrl(self.oneW, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
			self.listOneW.InsertColumn(0, _('Type'), width=80)
			self.listOneW.InsertColumn(1, 'ID', width=110)
			self.listOneW.InsertColumn(2, _('Signal K key'), width=370)
			self.listOneW.InsertColumn(3, _('Rate'), width=75)
			self.listOneW.InsertColumn(4, _('Offset'), width=75)
			self.listOneW.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListlistOneWSelected)
			self.listOneW.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListlistOneWDeselected)
			self.listOneW.SetTextColour(wx.BLACK)

			self.toolbar34 = wx.ToolBar(self.oneW, style=wx.TB_TEXT)
			setOneWpin = self.toolbar34.AddTool(3401, _('Set 1W GPIO'), wx.Bitmap(self.currentdir+"/data/chip.png"))
			self.Bind(wx.EVT_TOOL, self.onSetOneWpin, setOneWpin)

			self.toolbar4 = wx.ToolBar(self.oneW, style=wx.TB_TEXT | wx.TB_VERTICAL)
			self.editOneWCon= self.toolbar4.AddTool(401, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
			self.Bind(wx.EVT_TOOL, self.onEditOneWCon, self.editOneWCon)
			self.removeOneWCon = self.toolbar4.AddTool(402, _('Clear'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
			self.Bind(wx.EVT_TOOL, self.onRemoveOneWCon, self.removeOneWCon)

			h1 = wx.BoxSizer(wx.HORIZONTAL)
			h1.Add(self.listOneW, 1, wx.EXPAND, 0)
			h1.Add(self.toolbar4, 0, wx.EXPAND, 0)

			sizer = wx.BoxSizer(wx.VERTICAL)
			sizer.Add(self.toolbar34, 0, wx.EXPAND, 0)
			sizer.Add(h1, 1, wx.EXPAND, 0)

			self.oneW.SetSizer(sizer)
		else:
			text1 = wx.StaticText(self.oneW, label=_('This feature is only for Raspberry Pi'))
			hbox1 = wx.BoxSizer(wx.HORIZONTAL)
			hbox1.AddStretchSpacer(1)
			hbox1.Add(text1, 0, wx.ALL | wx.EXPAND, 5)
			hbox1.AddStretchSpacer(1)
			vbox = wx.BoxSizer(wx.VERTICAL)
			vbox.AddStretchSpacer(1)
			vbox.Add(hbox1, 0, wx.ALL | wx.EXPAND, 5)
			vbox.AddStretchSpacer(1)
			self.oneW.SetSizer(vbox)

	def onSetOneWpin(self, e):
		try: 
			out = subprocess.check_output('ls /sys/bus/w1/', shell=True).decode(sys.stdin.encoding)
		except: 
			self.ShowStatusBarRED(_('Please enable 1W interface in Preferences -> Raspberry Pi configuration -> Interfaces.'))
			return
		gpios = gpio.Gpio()
		gpioBCM = '4'
		config = '/boot/config.txt'
		boot = '/boot'
		try: file = open(config, 'r')
		except:
			config = '/boot/firmware/config.txt'
			boot = '/boot/firmware'
			file = open(config, 'r')
		while True:
			line = file.readline()
			if not line: break
			if 'dtoverlay=w1-gpio' in line:
				items = line.split(',')
				for i in items:
					if 'gpiopin=' in i:
						items2 = i.split('=')
						gpioBCM = items2[1].strip()
		file.close()
		gpioBCM = 'GPIO '+gpioBCM
		pin = '0'
		for i in gpios.gpioMap:
			if gpioBCM == i['BCM']: pin = i['physical']
		dlg = gpio.GpioMap(['GPIO'], pin)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			gpioBCM = dlg.selected['BCM'].replace('GPIO ','')
			if gpioBCM:
				file = open(config, 'r')
				file1 = open('config.txt', 'w')
				exists = False
				while True:
					line = file.readline()
					if not line: break
					if 'dtoverlay=w1-gpio' in line:
						if gpioBCM == '4': line = 'dtoverlay=w1-gpio\n'
						else: line = 'dtoverlay=w1-gpio,gpiopin='+gpioBCM+'\n'
					file1.write(line)
				file.close()
				file1.close()
				if os.system('diff config.txt '+config+' > /dev/null'):
					dlg = wx.MessageDialog(None, _(
						'OpenPlotter will restart. Are you sure?'),
						_('Question'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
					if dlg.ShowModal() == wx.ID_YES:
						os.system(self.platform.admin+' mv config.txt '+boot)
						os.system('shutdown -r now')
					else: os.system('rm -f config.txt')
				else: os.system('rm -f config.txt')
		dlg.Destroy()

	def onListlistOneWSelected(self,e):
		self.onListlistOneWDeselected()
		selected = self.listOneW.GetFirstSelected()
		if selected == -1: return
		self.toolbar4.EnableTool(401,True)
		self.toolbar4.EnableTool(402,True)

	def onListlistOneWDeselected(self,e=0):
		self.toolbar4.EnableTool(401,False)
		self.toolbar4.EnableTool(402,False)

	def onEditOneWCon(self,e):
		selected = self.listOneW.GetFirstSelected()
		if selected == -1: return
		sid = self.listOneW.GetItemText(selected, 1)
		sk = self.listOneW.GetItemText(selected, 2)
		rate = self.listOneW.GetItemText(selected, 3)
		offset = self.listOneW.GetItemText(selected, 4)
		dlg = edit1W(sid,sk,rate,offset)
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			sk = str(dlg.SKkey.GetValue())
			rate = dlg.rate.GetValue()
			if not rate: rate = 1.0
			offset = dlg.offset.GetValue()
			if not offset: offset = 0.0
			if not sk: del self.oneWlist[sid]
			else: self.oneWlist[sid] = {'sk':sk,'rate':float(rate),'offset':float(offset)}
			self.conf.set('GPIO', '1w', str(self.oneWlist))
			self.stopGpioRead()
			self.onRefresh()
		dlg.Destroy()

	def onRemoveOneWCon(self,e):
		selected = self.listOneW.GetFirstSelected()
		if selected == -1: return
		sid = self.listOneW.GetItemText(selected, 1)
		del self.oneWlist[sid]
		self.conf.set('GPIO', '1w', str(self.oneWlist))
		self.stopGpioRead()
		self.onRefresh()

	def readOneW(self):
		self.listOneW.DeleteAllItems()
		self.onListlistOneWDeselected()
		data = self.conf.get('GPIO', '1w')
		try: self.oneWlist = eval(data)
		except: self.oneWlist = {}
		try: out = subprocess.check_output('ls /sys/bus/w1/', shell=True).decode(sys.stdin.encoding)
		except:
			if self.oneWlist:
				for i in self.oneWlist:
					self.listOneW.Append(['',i,self.oneWlist[i]['sk'],self.oneWlist[i]['rate'],self.oneWlist[i]['offset']])
					self.listOneW.SetItemBackgroundColour(self.listOneW.GetItemCount()-1,(255,0,0))
		else: 
			for sensor in W1ThermSensor.get_available_sensors():
				if sensor.id in self.oneWlist:
					sk = self.oneWlist[sensor.id]['sk']
					rate = self.oneWlist[sensor.id]['rate']
					offset = self.oneWlist[sensor.id]['offset']
					self.listOneW.Append([sensor.type.name,sensor.id,sk,rate,offset])
					self.listOneW.SetItemBackgroundColour(self.listOneW.GetItemCount()-1,(255,220,100))
				else:
					sk = ''
					rate = ''
					offset = ''
					self.listOneW.Append([sensor.type.name,sensor.id,sk,rate,offset])
			if self.oneWlist:
				for i in self.oneWlist:
					exist = False
					for sensor in W1ThermSensor.get_available_sensors():
						if i == sensor.id:
							exist = True
							break
					if not exist:
						self.listOneW.Append(['',i,self.oneWlist[i]['sk'],self.oneWlist[i]['rate'],self.oneWlist[i]['offset']])
						self.listOneW.SetItemBackgroundColour(self.listOneW.GetItemCount()-1,(255,0,0))

	###########################################################################

	def pageSeatalk(self):
		pass
		'''
		if self.platform.isRPI:
			self.listSeatalk = wx.ListCtrl(self.seatalk, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
			self.listSeatalk.InsertColumn(0, 'GPIO', width=100)
			self.listSeatalk.InsertColumn(1, _('Invert signal'), width=200)
			self.listSeatalk.InsertColumn(2, _('SK connection ID'), width=270)
			self.listSeatalk.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListlistSeatalkSelected)
			self.listSeatalk.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListlistSeatalkDeselected)
			self.listSeatalk.SetTextColour(wx.BLACK)

			self.toolbar3 = wx.ToolBar(self.seatalk, style=wx.TB_TEXT | wx.TB_VERTICAL)
			self.addSeatalkCon = self.toolbar3.AddTool(303, _('Add'), wx.Bitmap(self.currentdir+"/data/sk.png"))
			self.Bind(wx.EVT_TOOL, self.onAddSeatalkCon, self.addSeatalkCon)
			self.editSeatalkCon= self.toolbar3.AddTool(301, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
			self.Bind(wx.EVT_TOOL, self.onEditSeatalkCon, self.editSeatalkCon)
			self.removeSeatalkCon = self.toolbar3.AddTool(302, _('Remove'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
			self.Bind(wx.EVT_TOOL, self.onRemoveSeatalkCon, self.removeSeatalkCon)

			sizer = wx.BoxSizer(wx.HORIZONTAL)
			sizer.Add(self.listSeatalk, 1, wx.EXPAND, 0)
			sizer.Add(self.toolbar3, 0, wx.EXPAND, 0)

			self.seatalk.SetSizer(sizer)
		else:
			text1 = wx.StaticText(self.seatalk, label=_('This feature is only for Raspberry Pi.'))
			hbox1 = wx.BoxSizer(wx.HORIZONTAL)
			hbox1.AddStretchSpacer(1)
			hbox1.Add(text1, 0, wx.ALL | wx.EXPAND, 5)
			hbox1.AddStretchSpacer(1)
			vbox = wx.BoxSizer(wx.VERTICAL)
			vbox.AddStretchSpacer(1)
			vbox.Add(hbox1, 0, wx.ALL | wx.EXPAND, 5)
			vbox.AddStretchSpacer(1)
			self.seatalk.SetSizer(vbox)
		'''
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
					if enabled: self.listSeatalk.SetItemBackgroundColour(self.listSeatalk.GetItemCount()-1,(255,220,100))
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

################################################################################

class edit1W(wx.Dialog):

	def __init__(self,sid,sk,rate,offset):
		self.platform = platform.Platform()
		title = _('Editing sensor ')+sid

		wx.Dialog.__init__(self, None, title=title, size=(450, 180))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		panel = wx.Panel(self)

		titl = wx.StaticText(panel, label=_('Signal K key'))
		self.SKkey = wx.TextCtrl(panel)
		self.SKkey.SetValue(sk)

		self.edit_skkey = wx.Button(panel, label=_('Edit'))
		self.edit_skkey.Bind(wx.EVT_BUTTON, self.onEditSkkey)

		if not self.platform.skDir:
			self.SKkey.Disable()
			self.edit_skkey.Disable()

		self.rate_list = ['1.0', '5.0', '30.0', '60.0', '300.0']
		self.rate_label = wx.StaticText(panel, label=_('Rate (seconds)'))
		self.rate = wx.ComboBox(panel, choices=self.rate_list, style=wx.CB_READONLY)
		self.rate.SetValue(rate)

		self.offset_label = wx.StaticText(panel, label=_('Offset'))
		self.offset = wx.TextCtrl(panel)
		self.offset.SetValue(offset)

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)

		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		hbox2.Add(self.SKkey, 1, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		hbox2.Add(self.edit_skkey, 0, wx.RIGHT | wx.EXPAND, 5)

		vbox1 = wx.BoxSizer(wx.HORIZONTAL)
		vbox1.Add(self.rate_label, 0, wx.ALL | wx.EXPAND, 5)
		vbox1.Add(self.rate, 1, wx.ALL| wx.EXPAND, 5)
		vbox1.Add(self.offset_label, 0, wx.ALL| wx.EXPAND, 5)
		vbox1.Add(self.offset, 1, wx.ALL | wx.EXPAND, 5)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.AddStretchSpacer(1)
		hbox.Add(cancelBtn, 0, wx.EXPAND, 0)
		hbox.Add(okBtn, 0, wx.LEFT | wx.EXPAND, 10)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(5)
		vbox.Add(titl, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 10)
		vbox.AddSpacer(5)
		vbox.Add(hbox2, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(5)
		vbox.Add(vbox1, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		vbox.Add(hbox, 0, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.panel = panel

		self.Centre() 

	def onEditSkkey(self,e):
		dlg = selectKey.SelectKey(self.SKkey.GetValue(),0)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			self.SKkey.SetValue(key)
		dlg.Destroy()

################################################################################

class editPulses(wx.Dialog):

	def __init__(self,edit):
		if edit: title = _('Editing GPIO pulses')
		else: title = _('Adding GPIO pulses')

		wx.Dialog.__init__(self, None, title=title, size=(800, 370))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		panel = wx.Panel(self)

		self.localhost = wx.CheckBox(panel, label=_('localhost'))
		self.localhost.Bind(wx.EVT_CHECKBOX, self.onLocalhost)
		self.host = wx.TextCtrl(panel)
		if edit: 
			if edit['host'] == 'localhost': 
				self.localhost.SetValue(True)
				self.host.Disable()
			else: 
				self.host.SetValue(edit['host'])
				self.host.Enable()
		else: 
			self.localhost.SetValue(True)
			self.host.Disable()
		self.gpio = wx.TextCtrl(panel, style=wx.CB_READONLY)
		selectGpio =wx.Button(panel, label='GPIO')
		selectGpio.Bind(wx.EVT_BUTTON, self.onSelectGpio)
		if edit: self.gpio.SetValue(edit['gpio'])

		rateLabel = wx.StaticText(panel, label=_('Rate (seconds)'))
		self.rate = wx.TextCtrl(panel)
		if edit: self.rate.SetValue(str(edit['rate']))
		else: self.rate.SetValue('1')

		pulsesLabel = wx.StaticText(panel, label=_('Pulses per revolution'))
		self.pulses = wx.TextCtrl(panel)
		if edit: self.pulses.SetValue(str(edit['pulsesPerRev']))
		else: self.pulses.SetValue('1')

		pullLabel= wx.StaticText(panel, label = _('internal pull resistor'))
		self.pull = wx.ComboBox(panel, choices = [_('none'),'up','down'], style=wx.CB_READONLY)
		if edit: self.pull.SetValue(edit['pull'])
		else: self.pull.SetValue('down')

		vline1 = wx.StaticLine(panel)

		weightingLabel = wx.StaticText(panel, label=_('Weighting'))
		self.weighting = wx.TextCtrl(panel)
		if edit: self.weighting.SetValue(str(edit['weighting']))
		else: self.weighting.SetValue('0')

		minRPMLabel = wx.StaticText(panel, label=_('Min RPM'))
		self.minRPM = wx.TextCtrl(panel)
		if edit: self.minRPM.SetValue(str(edit['minRPM']))
		else: self.minRPM.SetValue('5')

		revolutionsSKLabel = wx.StaticText(panel, label=_('Revolutions (Hz)'))
		self.revolutionsSK = wx.TextCtrl(panel)
		revolutionsSKedit = wx.Button(panel, label='Signal K')
		revolutionsSKedit.Bind(wx.EVT_BUTTON, self.onRevolutionsSKedit)
		if edit: self.revolutionsSK.SetValue(str(edit['revolutionsSK']))

		counterSKLabel = wx.StaticText(panel, label=_('Revolutions counter'))
		self.counterSK = wx.TextCtrl(panel)
		counterSKedit = wx.Button(panel, label='Signal K')
		counterSKedit.Bind(wx.EVT_BUTTON, self.onCounterSKedit)
		if edit: self.counterSK.SetValue(str(edit['counterSK']))

		resetSKLabel = wx.StaticText(panel, label=_('Reset (counter, distance)'))
		self.resetSK = wx.TextCtrl(panel)
		resetSKedit = wx.Button(panel, label='Signal K')
		resetSKedit.Bind(wx.EVT_BUTTON, self.onResetSKedit)
		if edit: self.resetSK.SetValue(str(edit['resetSK']))

		vline2 = wx.StaticLine(panel)

		radiusLabel = wx.StaticText(panel, label=_('Radius (m)'))
		self.radius = wx.TextCtrl(panel)
		if edit: self.radius.SetValue(str(edit['radius']))

		speedSKLabel = wx.StaticText(panel, label=_('Speed (m/s)'))
		self.speedSK = wx.TextCtrl(panel)
		speedSKedit = wx.Button(panel, label='Signal K')
		speedSKedit.Bind(wx.EVT_BUTTON, self.onSpeedSKedit)
		if edit: self.speedSK.SetValue(str(edit['speedSK']))

		calibrationLabel = wx.StaticText(panel, label=_('Speed calibration'))
		self.calibration = wx.TextCtrl(panel)
		if edit: self.calibration.SetValue(str(edit['calibration']))
		else: self.calibration.SetValue('1.0')

		distanceSKLabel = wx.StaticText(panel, label=_('Distance (m)'))
		self.distanceSK = wx.TextCtrl(panel)
		distanceSKedit = wx.Button(panel, label='Signal K')
		distanceSKedit.Bind(wx.EVT_BUTTON, self.onDistanceSKedit)
		if edit: self.distanceSK.SetValue(str(edit['distanceSK']))

		defaults = wx.Button(panel, label=_('Set defaults'))
		defaults.Bind(wx.EVT_BUTTON, self.onDefaults)
		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)
		okBtn.Bind(wx.EVT_BUTTON, self.ok)

		column1h00 = wx.BoxSizer(wx.HORIZONTAL)
		column1h00.Add(self.localhost, 0, wx.ALL | wx.EXPAND, 5)
		column1h00.Add(self.host, 1, wx.ALL | wx.EXPAND, 5)

		column1h0 = wx.BoxSizer(wx.HORIZONTAL)
		column1h0.Add(self.gpio, 0, wx.ALL | wx.EXPAND, 5)
		column1h0.Add(selectGpio, 0, wx.ALL | wx.EXPAND, 5)

		column1h1 = wx.BoxSizer(wx.HORIZONTAL)
		column1h1.Add(rateLabel, 0, wx.ALL | wx.EXPAND, 5)
		column1h1.Add(self.rate, 0, wx.ALL | wx.EXPAND, 5)

		column1h2 = wx.BoxSizer(wx.HORIZONTAL)
		column1h2.Add(pulsesLabel, 0, wx.ALL | wx.EXPAND, 5)
		column1h2.Add(self.pulses, 0, wx.ALL | wx.EXPAND, 5)

		column1h3 = wx.BoxSizer(wx.HORIZONTAL)
		column1h3.Add(pullLabel, 0, wx.ALL | wx.EXPAND, 5)
		column1h3.Add(self.pull, 0, wx.ALL | wx.EXPAND, 5)

		column2h0 = wx.BoxSizer(wx.HORIZONTAL)
		column2h0.Add(self.revolutionsSK, 1, wx.ALL | wx.EXPAND, 5)
		column2h0.Add(revolutionsSKedit, 0, wx.ALL | wx.EXPAND, 5)

		column2h1 = wx.BoxSizer(wx.HORIZONTAL)
		column2h1.Add(self.counterSK, 1, wx.ALL | wx.EXPAND, 5)
		column2h1.Add(counterSKedit, 0, wx.ALL | wx.EXPAND, 5)

		column2h2 = wx.BoxSizer(wx.HORIZONTAL)
		column2h2.Add(self.resetSK, 1, wx.ALL | wx.EXPAND, 5)
		column2h2.Add(resetSKedit, 0, wx.ALL | wx.EXPAND, 5)

		column2h3 = wx.BoxSizer(wx.HORIZONTAL)
		column2h3.Add(weightingLabel, 0, wx.ALL | wx.EXPAND, 5)
		column2h3.Add(self.weighting, 0, wx.ALL | wx.EXPAND, 5)

		column2h4 = wx.BoxSizer(wx.HORIZONTAL)
		column2h4.Add(minRPMLabel, 0, wx.ALL | wx.EXPAND, 5)
		column2h4.Add(self.minRPM, 0, wx.ALL | wx.EXPAND, 5)

		column3h0 = wx.BoxSizer(wx.HORIZONTAL)
		column3h0.Add(radiusLabel, 0, wx.ALL | wx.EXPAND, 5)
		column3h0.Add(self.radius, 0, wx.ALL | wx.EXPAND, 5)

		column3h1 = wx.BoxSizer(wx.HORIZONTAL)
		column3h1.Add(self.speedSK, 1, wx.ALL | wx.EXPAND, 5)
		column3h1.Add(speedSKedit, 0, wx.ALL | wx.EXPAND, 5)

		column3h2 = wx.BoxSizer(wx.HORIZONTAL)
		column3h2.Add(self.distanceSK, 1, wx.ALL | wx.EXPAND, 5)
		column3h2.Add(distanceSKedit, 0, wx.ALL | wx.EXPAND, 5)

		column3h3 = wx.BoxSizer(wx.HORIZONTAL)
		column3h3.Add(calibrationLabel, 0, wx.ALL | wx.EXPAND, 5)
		column3h3.Add(self.calibration, 0, wx.ALL | wx.EXPAND, 5)

		column1 = wx.BoxSizer(wx.VERTICAL)
		column1.Add(column1h00, 0, wx.ALL | wx.EXPAND, 5)
		column1.Add(column1h0, 0, wx.ALL | wx.EXPAND, 5)
		column1.Add(column1h1, 0, wx.ALL | wx.EXPAND, 5)
		column1.Add(column1h2, 0, wx.ALL | wx.EXPAND, 5)
		column1.Add(column1h3, 0, wx.ALL | wx.EXPAND, 5)

		column2 = wx.BoxSizer(wx.VERTICAL)
		column2.Add(column2h3, 0, wx.ALL | wx.EXPAND, 5)
		column2.Add(column2h4, 0, wx.ALL | wx.EXPAND, 5)
		column2.Add(revolutionsSKLabel, 0, wx.LEFT | wx.EXPAND, 10)
		column2.Add(column2h0, 0, wx.ALL | wx.EXPAND, 5)
		column2.AddSpacer(5)
		column2.Add(counterSKLabel, 0, wx.LEFT | wx.EXPAND, 10)
		column2.Add(column2h1, 0, wx.ALL | wx.EXPAND, 5)
		column2.AddSpacer(5)
		column2.Add(resetSKLabel, 0, wx.LEFT | wx.EXPAND, 10)
		column2.Add(column2h2, 0, wx.ALL | wx.EXPAND, 5)

		column3 = wx.BoxSizer(wx.VERTICAL)
		column3.Add(column3h0, 0, wx.ALL | wx.EXPAND, 5)
		column3.AddSpacer(5)
		column3.Add(speedSKLabel, 0, wx.LEFT | wx.EXPAND, 10)
		column3.Add(column3h1, 0, wx.ALL | wx.EXPAND, 5)
		column3.AddSpacer(5)
		column3.Add(column3h3, 0, wx.ALL | wx.EXPAND, 5)
		column3.AddSpacer(5)
		column3.Add(distanceSKLabel, 0, wx.LEFT | wx.EXPAND, 10)
		column3.Add(column3h2, 0, wx.ALL | wx.EXPAND, 5)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(column1, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
		hbox.Add(vline1, 0, wx.EXPAND, 0)
		hbox.Add(column2, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
		hbox.Add(vline2, 0, wx.EXPAND, 0)
		hbox.Add(column3, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

		actionbox = wx.BoxSizer(wx.HORIZONTAL)
		actionbox.AddStretchSpacer(1)
		actionbox.Add(defaults, 0, wx.EXPAND, 0)
		actionbox.Add(cancelBtn, 0, wx.LEFT | wx.EXPAND, 10)
		actionbox.Add(okBtn, 0, wx.LEFT | wx.EXPAND, 10)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(5)
		vbox.Add(hbox, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		vbox.Add(actionbox, 0, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.panel = panel

		self.Centre() 

	def onLocalhost(self,e):
		if self.localhost.GetValue(): self.host.Disable()
		else: self.host.Enable()
		self.gpio.SetValue('')

	def onSelectGpio(self,e):
		if not self.localhost.GetValue():
			if not self.host.GetValue():
				wx.MessageBox(_('Enter the host name.'), _('Error'), wx.OK | wx.ICON_ERROR)
				return
		gpioPin = '0'
		gpioBCM = self.gpio.GetValue()
		if gpioBCM:
			gpioBCM = 'GPIO '+gpioBCM
			gpios = gpio.Gpio()
			for i in gpios.gpioMap:
				if gpioBCM == i['BCM']: gpioPin = i['physical']
		if self.localhost.GetValue(): dlg = gpio.GpioMap(['GPIO'],gpioPin)
		else: dlg = gpio.GpioMap(['GPIO'],gpioPin, self.host.GetValue())
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			gpioBCM = dlg.selected['BCM'].replace('GPIO ','')
			self.gpio.SetValue(gpioBCM)
		dlg.Destroy()

	def onRevolutionsSKedit(self,e):
		dlg = selectKey.SelectKey(self.revolutionsSK.GetValue(),0)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			self.revolutionsSK.SetValue(key)
		dlg.Destroy()

	def onCounterSKedit(self,e):
		dlg = selectKey.SelectKey(self.counterSK.GetValue(),0)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			self.counterSK.SetValue(key)
		dlg.Destroy()

	def onResetSKedit(self,e):
		dlg = selectKey.SelectKey(self.resetSK.GetValue(),0)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			self.resetSK.SetValue(key)
		dlg.Destroy()

	def onSpeedSKedit(self,e):
		dlg = selectKey.SelectKey(self.speedSK.GetValue(),0)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			self.speedSK.SetValue(key)
		dlg.Destroy()

	def onDistanceSKedit(self,e):
		dlg = selectKey.SelectKey(self.distanceSK.GetValue(),0)
		res = dlg.ShowModal()
		if res == wx.OK:
			key = dlg.selected_key.replace(':','.')
			self.distanceSK.SetValue(key)
		dlg.Destroy()

	def onDefaults(self,e):
		self.rate.SetValue('1')
		self.pulses.SetValue('1')
		self.pull.SetValue('down')
		self.weighting.SetValue('0')
		self.minRPM.SetValue('5')
		self.calibration.SetValue('1.0')

	def ok(self,e):
		if not self.localhost.GetValue():
			if not self.host.GetValue():
				wx.MessageBox(_('Enter the host name.'), _('Error'), wx.OK | wx.ICON_ERROR)
				return
		if not self.gpio.GetValue():
			wx.MessageBox(_('Enter the GPIO.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return
		try: test = float(self.rate.GetValue())
		except:
			wx.MessageBox(_('"Rate" value has to be a number.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return
		try: test = int(self.pulses.GetValue())
		except:
			wx.MessageBox(_('"Pulses per revolution" value has to be a number.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return
		try: test = float(self.weighting.GetValue())
		except:
			wx.MessageBox(_('"Weighting" value has to be a number.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return
		try: test = int(self.minRPM.GetValue())
		except:
			wx.MessageBox(_('"Min RPM" value has to be a number.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return
		if self.speedSK.GetValue() or self.distanceSK.GetValue():
			if not self.radius.GetValue():
				wx.MessageBox(_('To get "Speed" or "Distance" enter the radius.'), _('Error'), wx.OK | wx.ICON_ERROR)
				return
		if self.radius.GetValue():
			try: test = float(self.radius.GetValue())
			except:
				wx.MessageBox(_('"Radius" value has to be a number.'), _('Error'), wx.OK | wx.ICON_ERROR)
				return
		try: test = float(self.calibration.GetValue())
		except:
			wx.MessageBox(_('"Speed calibration" value has to be a number.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return
		self.EndModal(wx.ID_OK)

################################################################################

class editDigital(wx.Dialog):

	def __init__(self,edit):
		if edit: title = _('Editing GPIO digital input')
		else: title = _('Adding GPIO digital input')

		wx.Dialog.__init__(self, None, title=title, size=(500, 410))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		panel = wx.Panel(self)

		self.localhost = wx.CheckBox(panel, label=_('localhost'))
		self.localhost.Bind(wx.EVT_CHECKBOX, self.onLocalhost)
		self.host = wx.TextCtrl(panel)
		if edit: 
			if edit['host'] == 'localhost': 
				self.localhost.SetValue(True)
				self.host.Disable()
			else: 
				self.host.SetValue(edit['host'])
				self.host.Enable()
		else: 
			self.localhost.SetValue(True)
			self.host.Disable()

		self.init = wx.CheckBox(panel, label=_('Send initial state'))
		if edit: self.init.SetValue(edit['init'])
		else: self.init.SetValue(True)

		self.gpio = wx.TextCtrl(panel, style=wx.CB_READONLY)
		selectGpio =wx.Button(panel, label='GPIO')
		selectGpio.Bind(wx.EVT_BUTTON, self.onSelectGpio)
		if edit: self.gpio.SetValue(edit['gpio'])

		pullLabel= wx.StaticText(panel, label = _('internal pull resistor'))
		self.pull = wx.ComboBox(panel, choices = [_('none'),'up','down'], style=wx.CB_READONLY)
		if edit: self.pull.SetValue(edit['pull'])
		else: self.pull.SetValue('down')

		self.notLabel = wx.StaticText(panel, label = 'notifications.GPIO'+self.gpio.GetValue())
		font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.notLabel.SetFont(font)

		highLabel= wx.StaticText(panel, label = _('High'))

		stateHlabel= wx.StaticText(panel, label = _('state:'))
		self.stateH = wx.ComboBox(panel, choices = ['normal','alert','warn','alarm','emergency'], style=wx.CB_READONLY)
		if edit: self.stateH.SetValue(edit['high']['state'])
		else: self.stateH.SetValue('alert')

		messageHlabel= wx.StaticText(panel, label = _('message:'))
		self.messageH = wx.TextCtrl(panel)
		if edit: self.messageH.SetValue(edit['high']['message'])

		methodHlabel= wx.StaticText(panel, label = _('method:'))
		self.visualH = wx.CheckBox(panel, label=_('visual'))
		self.soundH = wx.CheckBox(panel, label=_('sound'))
		if edit: 
			self.visualH.SetValue(edit['high']['visual'])
			self.soundH.SetValue(edit['high']['sound'])

		lowLabel= wx.StaticText(panel, label = _('Low'))

		stateLlabel= wx.StaticText(panel, label = _('state:'))
		self.stateL = wx.ComboBox(panel, choices = ['normal','alert','warn','alarm','emergency'], style=wx.CB_READONLY)
		if edit: self.stateL.SetValue(edit['low']['state'])
		else: self.stateL.SetValue('normal')

		messageLlabel= wx.StaticText(panel, label = _('message:'))
		self.messageL = wx.TextCtrl(panel)
		if edit: self.messageL.SetValue(edit['low']['message'])

		methodLlabel= wx.StaticText(panel, label = _('method:'))
		self.visualL = wx.CheckBox(panel, label=_('visual'))
		self.soundL = wx.CheckBox(panel, label=_('sound'))
		if edit: 
			self.visualL.SetValue(edit['low']['visual'])
			self.soundL.SetValue(edit['low']['sound'])

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)
		okBtn.Bind(wx.EVT_BUTTON, self.ok)

		h1 = wx.BoxSizer(wx.HORIZONTAL)
		h1.Add(self.localhost, 0, wx.ALL | wx.EXPAND, 5)
		h1.Add(self.host, 1, wx.ALL | wx.EXPAND, 5)
		h1.Add(self.init, 0, wx.ALL | wx.EXPAND, 5)

		h2 = wx.BoxSizer(wx.HORIZONTAL)
		h2.Add(self.gpio, 1, wx.ALL | wx.EXPAND, 5)
		h2.Add(selectGpio, 0, wx.ALL | wx.EXPAND, 5)
		h2.AddSpacer(10)
		h2.Add(pullLabel, 0,  wx.UP | wx.EXPAND, 10)
		h2.AddSpacer(5)
		h2.Add(self.pull, 1, wx.ALL | wx.EXPAND, 5)

		h4 = wx.BoxSizer(wx.HORIZONTAL)
		h4.Add(self.visualH, 1, wx.ALL | wx.EXPAND, 0)
		h4.Add(self.soundH, 1, wx.ALL | wx.EXPAND, 0)

		h5 = wx.BoxSizer(wx.HORIZONTAL)
		h5.Add(self.visualL, 1, wx.ALL | wx.EXPAND, 0)
		h5.Add(self.soundL, 1, wx.ALL | wx.EXPAND, 0)

		v1 = wx.BoxSizer(wx.VERTICAL)
		v1.Add(highLabel, 0, wx.ALL | wx.EXPAND, 5)
		v1.Add(stateHlabel, 0, wx.ALL | wx.EXPAND, 5)
		v1.Add(self.stateH, 0, wx.ALL | wx.EXPAND, 5)
		v1.Add(messageHlabel, 0, wx.ALL | wx.EXPAND, 5)
		v1.Add(self.messageH, 0, wx.ALL | wx.EXPAND, 5)
		v1.Add(methodHlabel, 0, wx.ALL | wx.EXPAND, 5)
		v1.Add(h4, 0, wx.ALL | wx.EXPAND, 5)

		v2 = wx.BoxSizer(wx.VERTICAL)
		v2.Add(lowLabel, 0, wx.ALL | wx.EXPAND, 5)
		v2.Add(stateLlabel, 0, wx.ALL | wx.EXPAND, 5)
		v2.Add(self.stateL, 0, wx.ALL | wx.EXPAND, 5)
		v2.Add(messageLlabel, 0, wx.ALL | wx.EXPAND, 5)
		v2.Add(self.messageL, 0, wx.ALL | wx.EXPAND, 5)
		v2.Add(methodLlabel, 0, wx.ALL | wx.EXPAND, 5)
		v2.Add(h5, 0, wx.ALL | wx.EXPAND, 5)

		h3 = wx.BoxSizer(wx.HORIZONTAL)
		h3.Add(v1, 1, wx.ALL | wx.EXPAND, 0)
		h3.Add(v2, 1, wx.ALL | wx.EXPAND, 0)

		actionbox = wx.BoxSizer(wx.HORIZONTAL)
		actionbox.AddStretchSpacer(1)
		actionbox.Add(cancelBtn, 0, wx.LEFT | wx.EXPAND, 10)
		actionbox.Add(okBtn, 0, wx.LEFT | wx.EXPAND, 10)

		h6 = wx.BoxSizer(wx.HORIZONTAL)
		h6.AddStretchSpacer(1)
		h6.Add(self.notLabel, 0, wx.ALL | wx.EXPAND, 0)
		h6.AddStretchSpacer(1)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(5)
		vbox.Add(h1, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.Add(h2, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(10)
		vbox.Add(h6, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(10)
		vbox.Add(h3, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		vbox.Add(actionbox, 0, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.panel = panel

		self.Centre() 

	def onLocalhost(self,e):
		if self.localhost.GetValue(): self.host.Disable()
		else: self.host.Enable()
		self.gpio.SetValue('')

	def onSelectGpio(self,e):
		if not self.localhost.GetValue():
			if not self.host.GetValue():
				wx.MessageBox(_('Enter the host name.'), _('Error'), wx.OK | wx.ICON_ERROR)
				return
		gpioPin = '0'
		gpioBCM = self.gpio.GetValue()
		if gpioBCM:
			gpioBCM = 'GPIO '+gpioBCM
			gpios = gpio.Gpio()
			for i in gpios.gpioMap:
				if gpioBCM == i['BCM']: gpioPin = i['physical']
		if self.localhost.GetValue(): dlg = gpio.GpioMap(['GPIO'],gpioPin)
		else: dlg = gpio.GpioMap(['GPIO'],gpioPin, self.host.GetValue())
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			gpioBCM = dlg.selected['BCM'].replace('GPIO ','')
			self.gpio.SetValue(gpioBCM)
			self.notLabel.SetLabel('notifications.GPIO'+self.gpio.GetValue())
		dlg.Destroy()

	def ok(self,e):
		if not self.localhost.GetValue():
			if not self.host.GetValue():
				wx.MessageBox(_('Enter the host name.'), _('Error'), wx.OK | wx.ICON_ERROR)
				return
		if not self.gpio.GetValue():
			wx.MessageBox(_('Enter the GPIO.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return

		self.EndModal(wx.ID_OK)

################################################################################

class editDigitalOut(wx.Dialog):

	def __init__(self,edit):
		if edit: title = _('Editing GPIO digital output')
		else: title = _('Adding GPIO digital output')

		wx.Dialog.__init__(self, None, title=title, size=(300, 180))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		panel = wx.Panel(self)

		self.localhost = wx.CheckBox(panel, label=_('localhost'))
		self.localhost.Bind(wx.EVT_CHECKBOX, self.onLocalhost)
		self.host = wx.TextCtrl(panel)
		if edit: 
			if edit['host'] == 'localhost': 
				self.localhost.SetValue(True)
				self.host.Disable()
			else: 
				self.host.SetValue(edit['host'])
				self.host.Enable()
		else: 
			self.localhost.SetValue(True)
			self.host.Disable()

		self.gpio = wx.TextCtrl(panel, style=wx.CB_READONLY)
		selectGpio =wx.Button(panel, label='GPIO')
		selectGpio.Bind(wx.EVT_BUTTON, self.onSelectGpio)
		if edit: self.gpio.SetValue(edit['gpio'])

		self.notLabel = wx.StaticText(panel, label = 'notifications.GPIO'+self.gpio.GetValue())
		font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.notLabel.SetFont(font)

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		okBtn = wx.Button(panel, wx.ID_OK)
		okBtn.Bind(wx.EVT_BUTTON, self.ok)

		h1 = wx.BoxSizer(wx.HORIZONTAL)
		h1.Add(self.localhost, 0, wx.ALL | wx.EXPAND, 5)
		h1.Add(self.host, 1, wx.ALL | wx.EXPAND, 5)

		h2 = wx.BoxSizer(wx.HORIZONTAL)
		h2.Add(self.gpio, 1, wx.ALL | wx.EXPAND, 5)
		h2.Add(selectGpio, 0, wx.ALL | wx.EXPAND, 5)

		actionbox = wx.BoxSizer(wx.HORIZONTAL)
		actionbox.AddStretchSpacer(1)
		actionbox.Add(cancelBtn, 0, wx.LEFT | wx.EXPAND, 10)
		actionbox.Add(okBtn, 0, wx.LEFT | wx.EXPAND, 10)

		h6 = wx.BoxSizer(wx.HORIZONTAL)
		h6.AddStretchSpacer(1)
		h6.Add(self.notLabel, 0, wx.ALL | wx.EXPAND, 0)
		h6.AddStretchSpacer(1)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(5)
		vbox.Add(h1, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.Add(h2, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(10)
		vbox.Add(h6, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		vbox.Add(actionbox, 0, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.panel = panel

		self.Centre() 

	def onLocalhost(self,e):
		if self.localhost.GetValue(): self.host.Disable()
		else: self.host.Enable()
		self.gpio.SetValue('')

	def onSelectGpio(self,e):
		if not self.localhost.GetValue():
			if not self.host.GetValue():
				wx.MessageBox(_('Enter the host name.'), _('Error'), wx.OK | wx.ICON_ERROR)
				return
		gpioPin = '0'
		gpioBCM = self.gpio.GetValue()
		if gpioBCM:
			gpioBCM = 'GPIO '+gpioBCM
			gpios = gpio.Gpio()
			for i in gpios.gpioMap:
				if gpioBCM == i['BCM']: gpioPin = i['physical']
		if self.localhost.GetValue(): dlg = gpio.GpioMap(['GPIO'],gpioPin)
		else: dlg = gpio.GpioMap(['GPIO'],gpioPin, self.host.GetValue())
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			gpioBCM = dlg.selected['BCM'].replace('GPIO ','')
			self.gpio.SetValue(gpioBCM)
			self.notLabel.SetLabel('notifications.GPIO'+self.gpio.GetValue())
		dlg.Destroy()

	def ok(self,e):
		if not self.localhost.GetValue():
			if not self.host.GetValue():
				wx.MessageBox(_('Enter the host name.'), _('Error'), wx.OK | wx.ICON_ERROR)
				return
		if not self.gpio.GetValue():
			wx.MessageBox(_('Enter the GPIO.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return

		self.EndModal(wx.ID_OK)

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
