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
			try:
				subprocess.check_output(['systemctl', 'is-active', 'pigpiod']).decode(sys.stdin.encoding)
				green = _('pigpiod running')
			except: red = _('pigpiod not running')
		else: black = _('pigpiod not running')

		return {'green': green,'black': black,'red': red}
