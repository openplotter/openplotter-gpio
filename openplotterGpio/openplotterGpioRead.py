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

import threading, time, pigpio, math, ujson
from openplotterSettings import conf
from openplotterSettings import platform
from websocket import create_connection
try: from w1thermsensor import W1ThermSensor, Unit
except: pass

class rpmReader:
	def __init__(self, pi, gpio, pulses_per_rev=1.0, weighting=0.0, min_RPM=5.0):
		self.pi = pi
		self.gpio = gpio
		self.pulses_per_rev = pulses_per_rev
		self.counter = 0
		if min_RPM > 1000.0: min_RPM = 1000.0
		elif min_RPM < 1.0: min_RPM = 1.0
		self.min_RPM = min_RPM
		self._watchdog = 200
		if weighting < 0.0: weighting = 0.0
		elif weighting > 0.99: weighting = 0.99
		self._new = 1.0 - weighting
		self._old = weighting
		self._high_tick = None
		self._period = None
		pi.set_mode(gpio, pigpio.INPUT)
		self._cb = pi.callback(gpio, pigpio.RISING_EDGE, self._cbf)
		pi.set_watchdog(gpio, self._watchdog)

	def _cbf(self, gpio, level, tick):
		if level == 1:
			self.counter = self.counter+(1/self.pulses_per_rev)
			if self._high_tick is not None:
				t = pigpio.tickDiff(self._high_tick, tick)
				if self._period is not None: self._period = (self._old * self._period) + (self._new * t)
				else: self._period = t
			self._high_tick = tick
		elif level == 2:
			if self._period is not None:
				if self._period < 2000000000:
					self._period += (self._watchdog * 1000)

	def RPM(self):
		RPM = 0.0
		if self._period is not None:
			RPM = 60000000.0 / (self._period * self.pulses_per_rev)
			if RPM < self.min_RPM: RPM = 0.0
		return RPM

	def cancel(self):
		self.pi.set_watchdog(self.gpio, 0)
		self._cb.cancel()

############################################################################################

class Process:
	def __init__(self):
		self.ws = False
		self.instances = {}

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
							value = str(offset+sensor.get_temperature(Unit.KELVIN))
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
			except Exception as e: 
				print(_('1W error: ')+str(e))
				return

	def pulse(self,pulselist):
		self.instances = {}
		try:
			for i in pulselist:
				if pulselist[i]['revCounter'] or pulselist[i]['revolutions'] or pulselist[i]['linearSpeed'] or pulselist[i]['distance']:
					items = i.split('-')
					host = items[0]
					gpio = items[1]
					pi = pigpio.pi(host)
					self.instances[i] = {'pi': pi ,'instance': rpmReader(pi, int(gpio), pulses_per_rev=pulselist[i]['pulsesPerRev'], weighting=pulselist[i]['weighting'], min_RPM=pulselist[i]['minRPM'])}
		except: return

		ticks = {}
		while True:
			time.sleep(0.1)
			try:
				for i in pulselist:
					values = ''
					if not i in ticks: ticks[i] = time.time()
					rate = pulselist[i]['rate']
					radius = pulselist[i]['radius']
					calibration = pulselist[i]['calibration']
					rpm = self.instances[i]['instance'].RPM()
					counter = self.instances[i]['instance'].counter
					hertz = rpm/60
					rps = rpm*(math.pi/30)
					if radius: 
						lSpeed = rps*radius
						distance = counter*(2*math.pi*radius)
						linearSpeedSK = pulselist[i]['linearSpeed']
						if linearSpeedSK: values += '{"path":"'+linearSpeedSK+'","value":'+str(lSpeed*calibration)+'},'
						distanceSK = pulselist[i]['distance']
						if distanceSK: values += '{"path":"'+distanceSK+'","value":'+str(distance)+'},'
					revolutionsSK = pulselist[i]['revolutions']
					if revolutionsSK: values += '{"path":"'+revolutionsSK+'","value":'+str(hertz)+'},'
					revCounterSK = pulselist[i]['revCounter']
					if revCounterSK: values += '{"path":"'+revCounterSK+'","value":'+str(counter)+'},'
					if time.time() - ticks[i] > rate:
						if values:		
							SignalK='{"updates":[{"$source":"OpenPlotter.GPIO.pulses.'+i+'","values":['
							SignalK+=values[0:-1]+']}]}\n'	
							try: 
								if self.ws: 
									self.ws.send(SignalK)
									ticks[i] = time.time()
							except: 
								if self.ws: self.ws.close()
								self.ws = False
								break
			except Exception as e: 
				print(_('Pulses error: ')+str(e))
				break

		for i in self.instances:
			self.instances[i]['instance'].cancel()
			self.instances[i]['pi'].stop()
		self.instances = {}

	def subscribe(self,pulselist):
		paths = ''
		pathsList = {}
		for i in pulselist:
			path = pulselist[i]['resetCounter']
			if path: 
				paths += '{"path":"'+path+'"},'
				pathsList[i] = path

		if paths:		
			SignalK='{"context": "vessels.self","subscribe":['
			SignalK+=paths[0:-1]+']}\n'	
			try: 
				if self.ws: self.ws.send(SignalK)
			except: 
				if self.ws: self.ws.close()
				self.ws = False
				return

		while True:
			time.sleep(0.1)
			try:
				try: 
					if self.ws: result = self.ws.recv()
				except: 
					if self.ws: self.ws.close()
					self.ws = False
					return
				data = ujson.loads(result)
				if 'updates' in data:
					for update in data['updates']:
						source = 'OpenPlotter'
						if '$source' in update: source = update['$source']
						if 'values' in update:
							for value in update['values']:
								if 'path' in value:
									for i in pathsList:
										if value['path'] == pathsList[i]:
											if 'value' in value:
												if value['value'] == True:
													if i in self.instances:
														if 'instance' in self.instances[i]: 
															self.instances[i]['instance'].counter = 0
													SignalK = '{"updates":[{"$source":"'+source+'","values":[{"path":"'+value['path']+'","value": false}]}]}\n'
													try: 
														if self.ws: self.ws.send(SignalK)
													except: 
														if self.ws: self.ws.close()
														self.ws = False
														return												
			except Exception as e: 
				print(_('resetCounter error: ')+str(e))
				return

############################################################################################

def main():
	conf2 = conf.Conf()
	enableX1 = False
	enableX2 = False
	enableX3 = False

	data = conf2.get('GPIO', '1w')
	try: oneWlist = eval(data)
	except: oneWlist = {}
	for i in oneWlist:
		if oneWlist[i]['sk']: enableX1 = True

	# {"host-xx":{"rate": 1,"pulsesPerRev": 1, "weighting": 0.0, "minRPM": 5, "revCounter": "aaa.aaa", "resetCounter": "bbb.bbb", "revolutions": "ccc.ccc", "radius": 0.16, "calibration": 1, "linearSpeed": "ddd.ddd", "distance": "eee.eee"}, ...}
	data = conf2.get('GPIO', 'pulses')
	try: pulselist = eval(data)
	except: pulselist = {}
	for i in pulselist:
		if pulselist[i]['revCounter'] or pulselist[i]['revolutions'] or pulselist[i]['linearSpeed'] or pulselist[i]['distance']: enableX2 = True
		if pulselist[i]['resetCounter']: enableX3 = True

	if enableX1 or enableX2 or enableX3:
		process = Process()
		process.connect()

		if enableX1:
			x1 = threading.Thread(target=process.oneW, args=(oneWlist,), daemon=True)
			x1.start()
		if enableX2:
			x2 = threading.Thread(target=process.pulse, args=(pulselist,), daemon=True)
			x2.start()
		if enableX3:
			x3 = threading.Thread(target=process.subscribe, args=(pulselist,), daemon=True)
			x3.start()

		while True:
			if not process.ws: process.connect()
			if enableX1:
				if not x1.is_alive():
					x1.join()
					x1 = threading.Thread(target=process.oneW, args=(oneWlist,), daemon=True)
					x1.start()
			if enableX2:
				if not x2.is_alive():
					x2.join()
					x2 = threading.Thread(target=process.pulse, args=(pulselist,), daemon=True)
					x2.start()
			if enableX3:
				if not x3.is_alive():
					x3.join()
					x3 = threading.Thread(target=process.subscribe, args=(pulselist,), daemon=True)
					x3.start()
			time.sleep(5)

if __name__ == '__main__':
	main()