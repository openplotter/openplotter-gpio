#!/usr/bin/env python3

# This file is part of Openplotter.
# Copyright (C) 2021 by Sailoog <https://github.com/openplotter/openplotter-gpio>
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

import threading, time
from openplotterSettings import conf
from openplotterSettings import platform
from w1thermsensor import W1ThermSensor
from websocket import create_connection

class Process:
	def __init__(self):
		self.ws = False

	def connect(self):
		self.conf = conf.Conf()
		self.platform = platform.Platform()
		uri = self.platform.ws+'localhost:'+self.platform.skPort+'/signalk/v1/stream?subscribe=none'
		token = self.conf.get('GPIO', 'token')
		if token:
			headers = {'Authorization': 'Bearer '+token}
			self.ws = create_connection(uri, header=headers)

	def oneW(self):
		while True:
			for sensor in W1ThermSensor.get_available_sensors():
				path = 'sensors.'+sensor.id
				SignalK = '{"updates":[{"$source":"OpenPlotter.GPIO.1W.'+sensor.id+'","values":[{"path":"'+path+'","value":'+str(sensor.get_temperature())+'}]}]}\n'
				try: 
					if self.ws: self.ws.send(SignalK)
				except: 
					if self.ws: self.ws.close()
					self.ws = False
					return
	'''
	def twoW(self):
		while True:
			for sensor in W1ThermSensor.get_available_sensors():
				path = 'sensors2.'+sensor.id
				SignalK = '{"updates":[{"$source":"OpenPlotter.GPIO.1W.'+sensor.id+'","values":[{"path":"'+path+'","value":'+str(sensor.get_temperature())+'}]}]}\n'
				try: 
					if self.ws: self.ws.send(SignalK)
				except: 
					if self.ws: self.ws.close()
					self.ws = False
					return
	'''

def main():
	process = Process()
	process.connect()
	x1 = threading.Thread(target=process.oneW, daemon=True)
	x1.start()
	#x2 = threading.Thread(target=process.twoW, daemon=True)
	#x2.start()
	while True:
		if not process.ws: process.connect()
		if not x1.is_alive():
			x1.join()
			x1 = threading.Thread(target=process.oneW, daemon=True)
			x1.start()
		#if not x2.is_alive():
			#x2.join()
			#x2 = threading.Thread(target=process.twoW, daemon=True)
			#x2.start()
		time.sleep(5)


if __name__ == '__main__':
	main()