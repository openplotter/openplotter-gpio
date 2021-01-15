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
from websocket import create_connection
try: from w1thermsensor import W1ThermSensor
except: pass

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

	def oneW(self,oneWlist):
		ticks = {}
		while True:
			time.sleep(0.1)
			try:
				for sensor in W1ThermSensor.get_available_sensors():
					sid = sensor.id
					if sid in oneWlist:
						sk = oneWlist[sid]['sk']
						if sk:
							offset = oneWlist[sid]['offset']
							value = str(offset+sensor.get_temperature(W1ThermSensor.KELVIN))
							if not sid in ticks: ticks[sid] = time.time()
							rate = oneWlist[sid]['rate']
							now = time.time()
							if now - ticks[sid] > rate:
								SignalK = '{"updates":[{"$source":"OpenPlotter.GPIO.1W.'+sid+'","values":[{"path":"'+sk+'","value":'+value+'}]}]}\n'
								try: 
									if self.ws: 
										self.ws.send(SignalK)
										ticks[sid] = time.time()
								except: 
									if self.ws: self.ws.close()
									self.ws = False
									return
			except: return

def main():
	conf2 = conf.Conf()
	enableX1 = False
	enableX2 = False

	data = conf2.get('GPIO', '1w')
	try: oneWlist = eval(data)
	except: oneWlist = {}
	for i in oneWlist:
		if oneWlist[i]['sk']: enableX1 = True

	if enableX1 or enableX2:
		process = Process()
		process.connect()

		if enableX1:
			x1 = threading.Thread(target=process.oneW, args=(oneWlist,), daemon=True)
			x1.start()
		#if enableX2:

		while True:
			if not process.ws: process.connect()
			if enableX1:
				if not x1.is_alive():
					x1.join()
					x1 = threading.Thread(target=process.oneW, args=(oneWlist,), daemon=True)
					x1.start()
			#if enableX2:
			
			time.sleep(5)


if __name__ == '__main__':
	main()