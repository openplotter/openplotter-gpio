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

import os, subprocess, gpiod, sys
from openplotterSettings import language
from gpiod.line import Direction, Value

class Actions:
	def __init__(self,conf,currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(os.path.abspath(__file__))
		language.Language(currentdir,'openplotter-gpio',currentLanguage)
		if self.conf.get('GENERAL', 'debug') == 'yes': self.debug = True
		else: self.debug = False
		self.available = []

		data = self.conf.get('GPIO', 'digital')
		try: digitalList = eval(data)
		except: digitalList = {}
		if digitalList:
			for i in digitalList:
				if digitalList[i]['mode'] == 'out':
					self.available.append({'ID':i+'-high','name': 'GPIO'+i+': '+_('turn it high'),"module": "openplotterGpio",'data':True,'default':'state=alert\nmessage=GPIO'+i+' is high\nsound=no\nvisual=yes','help':_('Allowed values for state:')+' normal, alert, warn, alarm, emergency'})
					self.available.append({'ID':i+'-low','name': 'GPIO'+i+': '+_('turn it low'),"module": "openplotterGpio",'data':True,'default':'state=normal\nmessage=GPIO'+i+' is low\nsound=no\nvisual=yes','help':_('Allowed values for state:')+' normal, alert, warn, alarm, emergency'})

		data = self.conf.get('GPIO', 'pulses')
		try: pulsesList = eval(data)
		except: pulsesList = {}
		if pulsesList:
			for i in pulsesList:
				if pulsesList[i]['revCounter'] or pulsesList[i]['distance']:
					self.available.append({'ID':i+'-reset','name': 'GPIO'+i+': '+_('reset counter and distance'),"module": "openplotterGpio",'data':False,'default':'','help':''})

	def run(self,action,data):
		try:
			state = ''
			message = ''
			sound = False
			visual = False

			if '-high' in action or '-low' in action:
				items = action.split('-')
				gpio = items[0]
				turn = items[1]
				data0 = self.conf.get('GPIO', 'digital')
				try: digitalList = eval(data0)
				except: digitalList = {}
				if gpio in digitalList:
					if turn == 'low': value = Value.INACTIVE
					elif turn == 'high': value = Value.ACTIVE
					try:
						out = subprocess.check_output('raspi-config nonint get_pi_type', shell=True).decode(sys.stdin.encoding)
						out = out.replace("\n","")
						out = out.strip()
					except: out = ''
					if out == '5': chip = '/dev/gpiochip4'
					elif out == '4': chip = '/dev/gpiochip0'
					else: chip = ''
					if chip:
						with gpiod.request_lines(chip,consumer="toggle-line-value",config={int(gpio): gpiod.LineSettings(direction=Direction.OUTPUT)}) as request:
							request.set_value(int(gpio), value)
					key = 'notifications.GPIO'+gpio
					lines = data.split('\n')
					for i in lines:
						line = i.split('=')
						if line[0].strip() == 'state': state = line[1].strip()
						elif line[0].strip() == 'message': message = line[1].strip()
						elif line[0].strip() == 'sound':
							if line[1].strip()=="yes": sound = True
						elif line[0].strip() == 'visual':
							if line[1].strip()=="yes": visual = True
				else: return
			elif '-reset' in action:
				items = action.split('-')
				gpio = items[0]
				key = 'notifications.GPIO'+gpio+'.reset'
				state = 'normal'
				message = 'request'

			command = ['set-notification']
			if sound: command.append('-s')
			if visual: command.append('-v')
			command.append(key)
			command.append(state)
			command.append(message)
			process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = process.communicate()
			if err:
				if self.debug:
					err = err.decode()
					err = err.replace('\n','')
					print('Error setting notification: '+str(err))

		except Exception as e: 
			if self.debug: print('Error processing openplotter-gpio actions: '+str(e))