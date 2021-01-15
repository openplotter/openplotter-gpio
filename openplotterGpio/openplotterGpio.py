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

import wx, os, webbrowser, subprocess, time, sys, ujson, requests, uuid
from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform
from openplotterSettings import gpio
from openplotterSettings import selectKey
from openplotterSignalkInstaller import connections
try: from w1thermsensor import W1ThermSensor
except: pass
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
		self.aproveSK = self.toolbar1.AddTool(105, _('Approve device'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.onAproveSK, self.aproveSK)
		self.connectionSK = self.toolbar1.AddTool(106, _('Allowed devices'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.onConnectionSK, self.connectionSK)
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
		self.notebook.AddPage(self.seatalk, ' Seatalk 1')
		self.il = wx.ImageList(24, 24)
		img0 = self.il.Add(wx.Bitmap(self.currentdir+"/data/openplotter-24.png", wx.BITMAP_TYPE_PNG))
		img1 = self.il.Add(wx.Bitmap(self.currentdir+"/data/openplotter-24.png", wx.BITMAP_TYPE_PNG))
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
		self.ShowStatusBarBLACK(' ')
		try:
			subprocess.check_output(['systemctl', 'is-enabled', 'pigpiod']).decode(sys.stdin.encoding)
			self.toolbar33.ToggleTool(3301,True)
		except: self.toolbar33.ToggleTool(3301,False)

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
			self.ShowStatusBarYELLOW(result[1]+_(' Press "Allowed devices".'))
		elif result[0] == 'approved':
			self.ShowStatusBarGREEN(result[1])

		self.readSeatalk()
		self.readOneW()

	def onApply(self):
		enable = False
		if self.oneWlist: enable = True
		if enable:
			subprocess.Popen([self.platform.admin, 'python3', self.currentdir+'/service.py', 'openplotter-gpio-read', 'restart'])
			self.ShowStatusBarGREEN(_('GPIO service is enabled'))
		else:
			subprocess.Popen([self.platform.admin, 'python3', self.currentdir+'/service.py', 'openplotter-gpio-read', 'stop'])
			self.ShowStatusBarBLACK(_('There is nothing to send. GPIO service is disabled'))
			
	###########################################################################

	def pageOneW(self):
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
						if gpioBCM == '4': line = 'dtoverlay=w1-gpio'
						else: line = 'dtoverlay=w1-gpio,gpiopin='+gpioBCM
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
			self.readOneW()
			self.onApply()
		dlg.Destroy()

	def onRemoveOneWCon(self,e):
		selected = self.listOneW.GetFirstSelected()
		if selected == -1: return
		sid = self.listOneW.GetItemText(selected, 1)
		del self.oneWlist[sid]
		self.conf.set('GPIO', '1w', str(self.oneWlist))
		self.readOneW()
		self.onApply()

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
				else:
					sk = ''
					rate = ''
					offset = ''
				self.listOneW.Append([sensor.type_name,sensor.id,sk,rate,offset])

	###########################################################################

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
		self.addSeatalkCon = self.toolbar33.AddTool(3302, _('Add'), wx.Bitmap(self.currentdir+"/data/sk.png"))
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
			self.ShowStatusBarGREEN(_('Seatalk 1 service is enabled'))
		else:
			subprocess.call([self.platform.admin, 'python3', self.currentdir+'/service.py', 'seatalk', 'stop'])
			self.onRefresh()
			self.ShowStatusBarBLACK(_('Seatalk 1 service is disabled'))

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
