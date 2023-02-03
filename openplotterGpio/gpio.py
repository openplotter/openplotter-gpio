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

import subprocess, sys, ujson
from openplotterSettings import gpio
from openplotterSettings import platform

class Gpio:
	def __init__(self,conf):
		self.conf = conf
		self.platform = platform.Platform()
		self.gpio = gpio.Gpio()
		self.gpioMap = self.gpio.gpioMap
		self.used = [] # {'app':'xxx', 'id':'xxx', 'physical':'n'}

	def usedGpios(self):
		ground = False
		power3 = False

		#seatalk
		try:
			setting_file = self.platform.skDir+'/settings.json'
			with open(setting_file) as data_file:
				data = ujson.load(data_file)
		except: data = {}
		if 'pipedProviders' in data:
			data = data['pipedProviders']
		else:
			data = []
		if data:
			for i in data:
				dataType = ''
				subOptions = ''
				usedGpio = ''
				try:
					dataType = i['pipeElements'][0]['options']['type']
					if dataType == 'Seatalk':
						subOptions = i['pipeElements'][0]['options']['subOptions']
						if 'gpio' in subOptions: usedGpio = subOptions['gpio']
				except: pass
				if usedGpio:
					if usedGpio[4] == '0': usedGpio = usedGpio.replace('0', ' ')
					else: usedGpio = usedGpio.replace('GPIO', 'GPIO ')
					for ii in self.gpioMap:
						if usedGpio == ii['BCM']:
							ground = True
							self.used.append({'app':'GPIO', 'id':'Seatalk1', 'physical':ii['physical']})

		#1W
		try: subprocess.check_output('ls /sys/bus/w1/', shell=True).decode(sys.stdin.encoding)
		except: pass
		else:
			gpioBCM = '4'
			pin = '7'
			config = '/boot/config.txt'
			try: 
				file = open(config, 'r')
			except:
				config = '/boot/firmware/config.txt'
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
			for i in self.gpioMap:
				if gpioBCM == i['BCM']:
					ground = True
					power3 = True
					pin = i['physical']
					self.used.append({'app':'GPIO', 'id':'1W', 'physical':pin})

		#pulses
		data = self.conf.get('GPIO', 'pulses')
		try: pulselist = eval(data)
		except: pulselist = {}
		for i in pulselist:
			gpioBCM = 'GPIO '+i
			for ii in self.gpioMap:
				if gpioBCM == ii['BCM']:
					ground = True
					power3 = True
					pin = ii['physical']
					self.used.append({'app':'GPIO', 'id':'pulses', 'physical':pin})

		#digital
		data = self.conf.get('GPIO', 'digital')
		try: digitalList = eval(data)
		except: digitalList = {}
		for i in digitalList:
			items = i.split('-')
			if items[0] == 'localhost':
				gpioBCM = 'GPIO '+items[1]
				for ii in self.gpioMap:
					if gpioBCM == ii['BCM']:
						pin = ii['physical']
						if digitalList[i]['mode'] == 'in':
							ground = True
							power3 = True
							self.used.append({'app':'GPIO', 'id':'digital input', 'physical':pin})
						elif digitalList[i]['mode'] == 'out':
							ground = True
							self.used.append({'app':'GPIO', 'id':'digital output', 'physical':pin})
		#common
		if power3:
			self.used.append({'app':'GPIO', 'id':'power', 'physical':'1'})
			self.used.append({'app':'GPIO', 'id':'power', 'physical':'17'})
		if ground:
			self.used.append({'app':'GPIO', 'id':'ground', 'physical':'1'})
			self.used.append({'app':'GPIO', 'id':'ground', 'physical':'6'})
			self.used.append({'app':'GPIO', 'id':'ground', 'physical':'9'})
			self.used.append({'app':'GPIO', 'id':'ground', 'physical':'14'})
			self.used.append({'app':'GPIO', 'id':'ground', 'physical':'17'})
			self.used.append({'app':'GPIO', 'id':'ground', 'physical':'20'})
			self.used.append({'app':'GPIO', 'id':'ground', 'physical':'25'})
			self.used.append({'app':'GPIO', 'id':'ground', 'physical':'30'})
			self.used.append({'app':'GPIO', 'id':'ground', 'physical':'34'})
			self.used.append({'app':'GPIO', 'id':'ground', 'physical':'39'})
		return self.used
