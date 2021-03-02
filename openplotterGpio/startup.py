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

import time, os, sys, subprocess, ujson
from openplotterSettings import language
from openplotterSettings import platform
from openplotterSignalkInstaller import connections

class Start():
	def __init__(self, conf, currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(os.path.abspath(__file__))
		language.Language(currentdir,'openplotter-gpio',currentLanguage)
		
		self.initialMessage = ''

	def start(self): 
		green = ''
		black = ''
		red = ''

		return {'green': green,'black': black,'red': red}

class Check():
	def __init__(self, conf, currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(os.path.abspath(__file__))
		language.Language(currentdir,'openplotter-gpio',currentLanguage)
		
		self.initialMessage = _('Checking GPIO...')

	def check(self):
		platform2 = platform.Platform()
		green = ''
		black = ''
		red = ''

		#pigpiod
		try:
			subprocess.check_output(['systemctl', 'is-active', 'pigpiod']).decode(sys.stdin.encoding)
			green = _('pigpiod running')
		except: red = ' ↳'+_('pigpiod not running')

		#seatalk
		try:
			setting_file = platform2.skDir+'/settings.json'
			with open(setting_file) as data_file:
				data = ujson.load(data_file)
		except: data = {}
		if 'pipedProviders' in data:
			data = data['pipedProviders']
		else:
			data = []
		seatalkExists = False
		for i in data:
			try:
				if i['pipeElements'][0]['options']['type'] == 'Seatalk' and i['enabled']: seatalkExists = True
			except: pass
		if seatalkExists:
			msg = _('Seatalk 1 enabled')
			if not green: green = msg
			else: green+= ' | '+msg
		else: 
			msg = _('Seatalk 1 disabled')
			if not black: black = msg
			else: black+= ' | '+msg

		#1W
		data = self.conf.get('GPIO', '1w')
		try: oneWlist = eval(data)
		except: oneWlist = {}
		if oneWlist:
			try: 
				subprocess.check_output('ls /sys/bus/w1/', shell=True).decode(sys.stdin.encoding)
				msg = _('1W enabled')
				if not green: green = msg
				else: green+= ' | '+msg
			except:
				msg =' ↳'+ _('Please enable 1W interface in Preferences -> Raspberry Pi configuration -> Interfaces.')
				if not red: red = msg
				else: red+= '\n'+msg
		else:
			try: 
				subprocess.check_output('ls /sys/bus/w1/', shell=True).decode(sys.stdin.encoding)
				msg = _('1W enabled')
				if not black: black = msg
				else: black+= ' | '+msg
			except:
				msg = _('1W disabled')
				if not black: black = msg
				else: black+= ' | '+msg

		#pulses
		data = self.conf.get('GPIO', 'pulses')
		try: pulseslist = eval(data)
		except: pulseslist = {}
		if pulseslist:
			msg = _('pulses enabled')
			if not green: green = msg
			else: green+= ' | '+msg
		else:
			msg = _('pulses disabled')
			if not black: black = msg
			else: black+= ' | '+msg

		#service
		if oneWlist or pulseslist:
			try:
				subprocess.check_output(['systemctl', 'is-active', 'openplotter-gpio-read']).decode(sys.stdin.encoding)
				msg = _('GPIO service running')
				if not green: green = msg
				else: green+= ' | '+msg
			except:
				msg = ' ↳'+_('GPIO service not running')
				if not red: red = msg
				else: red+= '\n'+msg
		else:
			try:
				subprocess.check_output(['systemctl', 'is-active', 'openplotter-gpio-read']).decode(sys.stdin.encoding)
				msg = ' ↳'+_('GPIO service running')
				if not red: red = msg
				else: red+= '\n'+msg
			except:
				msg = _('GPIO service not running')
				if not black: black = msg
				else: black+= ' | '+msg

		#access
		skConnections = connections.Connections('GPIO')
		result = skConnections.checkConnection()
		if result[0] == 'pending' or result[0] == 'error' or result[0] == 'repeat' or result[0] == 'permissions':
			if not red: red = ' ↳'+result[1]
			else: red+= '\n'+' ↳'+result[1]
		if result[0] == 'approved' or result[0] == 'validated':
			msg = _('Access to Signal K server validated')
			if not green: green = msg
			else: green+= ' | '+msg

		return {'green': green,'black': black,'red': red}
