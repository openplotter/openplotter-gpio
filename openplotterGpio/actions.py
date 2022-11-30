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

import os, subprocess, pigpio
from openplotterSettings import language

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
				items = i.split('-')
				host = items[0]
				gpio = items[1]
				if digitalList[i]['mode'] == 'out':
					self.available.append({'ID':i+'-high','name': host+'-'+'GPIO'+gpio+': '+_('turn it high'),"module": "openplotterGpio",'data':True,'default':'state=alert\nmessage=GPIO'+gpio+' is high\nsound=no\nvisual=yes','help':_('Allowed values for state:')+' normal, alert, warn, alarm, emergency'})
					self.available.append({'ID':i+'-low','name': host+'-'+'GPIO'+gpio+': '+_('turn it low'),"module": "openplotterGpio",'data':True,'default':'state=normal\nmessage=GPIO'+gpio+' is low\nsound=no\nvisual=yes','help':_('Allowed values for state:')+' normal, alert, warn, alarm, emergency'})

	def run(self,action,data):
		try:
			items = action.split('-')
			host = items[0]
			gpio = int(items[1])
			turn = items[2]

			pi = pigpio.pi(host)
			pi.set_mode(gpio, pigpio.OUTPUT)
			if turn == 'high': pi.write(gpio,1)
			elif turn == 'low': pi.write(gpio,0)
			pi.stop()

			key = 'notifications.GPIO'+str(gpio)
			state = ''
			message = ''
			sound = False
			visual = False
			lines = data.split('\n')
			for i in lines:
				line = i.split('=')
				if line[0].strip() == 'state': state = line[1].strip()
				elif line[0].strip() == 'message': message = line[1].strip()
				elif line[0].strip() == 'sound':
					if line[1].strip()=="yes": sound = True
				elif line[0].strip() == 'visual':
					if line[1].strip()=="yes": visual = True
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