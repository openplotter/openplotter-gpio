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

import os, sys, subprocess, ujson, time
from openplotterSettings import language
from openplotterSettings import platform
from openplotterSignalkInstaller import connections

class Start():
	def __init__(self, conf, currentLanguage):
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
			out = subprocess.check_output('raspi-config nonint get_pi_type', shell=True).decode(sys.stdin.encoding)
			out = out.replace("\n","")
			out = out.strip()
		except: out = ''
		if out != '5':
			try:
				subprocess.check_output(['systemctl', 'is-active', 'pigpiod']).decode(sys.stdin.encoding)
				msg = _('pigpiod running')
				if not green: green = msg
				else: green+= ' | '+msg
			except: 
				msg = _('pigpiod not running')
				if red: red += '\n   '+msg
				else: red = msg
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
				msg = _('Seatalk1 enabled')
				if not black: black = msg
				else: black+= ' | '+msg
			else: 
				msg = _('Seatalk1 disabled')
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
				if not black: black = msg
				else: black+= ' | '+msg
			except:
				msg =_('Please enable 1W interface in Preferences -> Raspberry Pi configuration -> Interfaces.')
				if red: red += '\n   '+msg
				else: red = msg
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
			if not black: black = msg
			else: black+= ' | '+msg
		else:
			msg = _('pulses disabled')
			if not black: black = msg
			else: black+= ' | '+msg

		#digital
		data = self.conf.get('GPIO', 'digital')
		try: digitalList = eval(data)
		except: digitalList = {}
		if digitalList:
			msg = _('digital enabled')
			if not black: black = msg
			else: black+= ' | '+msg
		else:
			msg = _('digital disabled')
			if not black: black = msg
			else: black+= ' | '+msg

		#service
		if oneWlist or pulseslist or digitalList:
			try:
				subprocess.check_output(['systemctl', 'is-active', 'openplotter-gpio-read.service']).decode(sys.stdin.encoding)
				msg = _('service running')
				if not green: green = msg
				else: green+= ' | '+msg
			except: 
				msg = _('service not running')
				if red: red += '\n   '+msg
				else: red = msg
		else:
			try:
				subprocess.check_output(['systemctl', 'is-active', 'openplotter-gpio-read.service']).decode(sys.stdin.encoding)
				msg = _('service running')
				if red: red += '\n   '+msg
				else: red = msg
			except: 
				msg = _('service not running')
				if not black: black = msg
				else: black+= ' | '+msg

		#access
		skConnections = connections.Connections('GPIO')
		result = skConnections.checkConnection()
		if result[0] =='error':
			if not red: red = result[1]
			else: red+= '\n    '+result[1]
		if result[0] =='validated':
			msg = _('Access to Signal K server validated')
			if not black: black = msg
			else: black+= ' | '+msg

		return {'green': green,'black': black,'red': red}
