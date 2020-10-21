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
import subprocess, sys, ujson
from openplotterSettings import gpio
from openplotterSettings import platform

class Gpio:
	def __init__(self,conf):
		self.conf = conf
		self.platform = platform.Platform()
		self.used = [] # {'app':'xxx', 'id':'xxx', 'physical':'n'}

	def usedGpios(self):
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
			self.gpio = gpio.Gpio()
			gpioMap = self.gpio.gpioMap
			ground = False
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
					for ii in gpioMap:
						if usedGpio == ii['BCM']:
							ground = True
							self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':ii['physical']})
			if ground:
				self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':'1'})
				self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':'6'})
				self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':'9'})
				self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':'14'})
				self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':'17'})
				self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':'20'})
				self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':'25'})
				self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':'30'})
				self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':'34'})
				self.used.append({'app':'GPIO', 'id':'Seatalk 1', 'physical':'39'})
				
		return self.used