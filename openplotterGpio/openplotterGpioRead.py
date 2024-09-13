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

import threading, time, math, ujson, ssl, subprocess, sys, gpiod
from openplotterSettings import conf
from openplotterSettings import platform
from websocket import create_connection
from openplotterSignalkInstaller import connections
try: from w1thermsensor import W1ThermSensor, Unit
except: pass
from gpiod.line import Edge, Bias, Direction, Value as gpiodValue
from datetime import timedelta

class Process:
	def __init__(self, conf):
		self.ws = False
		self.instances = {}
		if conf.get('GENERAL', 'debug') == 'yes': self.debug = True
		else: self.debug = False
		self.chip = '/dev/gpiochip0'

	def connect(self):
		self.platform = platform.Platform()
		uri = self.platform.ws+'localhost:'+self.platform.skPort+'/signalk/v1/stream?subscribe=none'
		skConnections = connections.Connections('GPIO')
		token = skConnections.token
		if token:
			headers = {'Authorization': 'Bearer '+token}
			self.ws = create_connection(uri, header=headers, sslopt={"cert_reqs": ssl.CERT_NONE})

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
									else: return
								except Exception as e: 
									if self.debug: 
										print('Error connecting Signal K server: '+str(e))
										sys.stdout.flush()
									if self.ws: self.ws.close()
									self.ws = False
									return
			except Exception as e: 
				if self.debug: 
					print('Reading GPIO 1W error: '+str(e))
					sys.stdout.flush()
				return

	def pulse(self,pulselist):
		self.instances = {}
		config = {}
		for i in pulselist:
			if pulselist[i]['revCounter'] or pulselist[i]['revolutions'] or pulselist[i]['linearSpeed'] or pulselist[i]['distance']:
				try:
					self.instances[i] = {'rev':0,'old':time.monotonic_ns(),'new':time.monotonic_ns(),'tms':time.time(),'event':'','pulses':0}
					if pulselist[i]['pull'] == 'up': bias = Bias.PULL_UP
					elif pulselist[i]['pull'] == 'down': bias = Bias.PULL_DOWN
					else: bias = Bias.DISABLED
					config[int(i)] = gpiod.LineSettings(edge_detection=Edge.BOTH,bias=bias)
				except Exception as e: 
					if self.debug: 
						print('Error setting GPIO pulse: '+str(e))
						sys.stdout.flush()

		if self.instances:
			with gpiod.request_lines(self.chip,consumer="watch-pulses",config=config) as request:
				while True:
					for event in request.read_edge_events():
						try:
							gpio = str(event.line_offset)
							if event.event_type != self.instances[gpio]['event']:
								self.instances[gpio]['event'] = event.event_type
								if event.event_type == event.Type.FALLING_EDGE:
									self.instances[gpio]['pulses'] = self.instances[gpio]['pulses']+1
									if self.instances[gpio]['pulses'] == pulselist[gpio]['pulsesPerRev']:
										self.instances[gpio]['pulses'] = 0
										self.instances[gpio]['rev'] = self.instances[gpio]['rev']+1
										self.instances[gpio]['old'] = self.instances[gpio]['new']
										self.instances[gpio]['new'] = event.timestamp_ns
										if time.time() - self.instances[gpio]['tms'] > pulselist[gpio]['rate']:
											values = ''
											if pulselist[gpio]['revCounter']: values += '{"path":"'+pulselist[gpio]['revCounter']+'","value":'+str(self.instances[gpio]['rev'])+'},'
											if pulselist[gpio]['revolutions'] or pulselist[gpio]['radius']:
												if self.instances[gpio]['new']-self.instances[gpio]['old'] >= 1000000000: 
													rpm = 0
													hertz = 0
												else: 
													rpm = 60000000000/(self.instances[gpio]['new']-self.instances[gpio]['old'])
													hertz = rpm/60
												rps = rpm*(math.pi/30)
												if pulselist[gpio]['revolutions']: values += '{"path":"'+pulselist[gpio]['revolutions']+'","value":'+str(hertz)+'},'
												if pulselist[gpio]['radius']:
													if pulselist[gpio]['linearSpeed']:
														lSpeed = rps*pulselist[gpio]['radius']
														calibration = pulselist[gpio]['calibration']
														values += '{"path":"'+pulselist[gpio]['linearSpeed']+'","value":'+str(lSpeed*calibration)+'},'
													if pulselist[gpio]['distance']:
														distance = self.instances[gpio]['rev']*((2*math.pi)*pulselist[gpio]['radius'])
														values += '{"path":"'+pulselist[gpio]['distance']+'","value":'+str(distance)+'},'
											if values:		
												SignalK ='{"updates":[{"$source":"OpenPlotter.GPIO.pulses.'+gpio+'","values":['
												SignalK += values[0:-1]+']}]}\n'	
												try: 
													if self.ws: 
														self.ws.send(SignalK)
														self.instances[gpio]['tms'] = time.time()
													else: return
												except Exception as e: 
													if self.debug: 
														print('Error connecting Signal K server: '+str(e))
														sys.stdout.flush()
													if self.ws: self.ws.close()
													self.ws = False
													return
						except Exception as e:
							if self.debug: 
								print('Error reading GPIO digital: '+str(e))
								sys.stdout.flush()


	def subscribe(self,pulselist):
		paths = ''
		pathsList = {}
		for i in pulselist:
			if pulselist[i]['revCounter'] or pulselist[i]['distance']:
				path = 'notifications.GPIO'+i+'.reset'
				paths += '{"path":"'+path+'"},'
				pathsList[i] = path

		if paths:		
			SignalK='{"context": "vessels.self","subscribe":['
			SignalK+=paths[0:-1]+']}\n'	
			try: 
				if self.ws: self.ws.send(SignalK)
				else: return
			except Exception as e: 
				if self.debug: 
					print('Error connecting Signal K server: '+str(e))
					sys.stdout.flush()
				if self.ws: self.ws.close()
				self.ws = False
				return

		while True:
			try:
				try: 
					if self.ws: result = self.ws.recv()
					else: return
				except Exception as e: 
					if self.debug: 
						print('Error connecting Signal K server: '+str(e))
						sys.stdout.flush()
					if self.ws: self.ws.close()
					self.ws = False
					return
				data = ujson.loads(result)
				if 'updates' in data:
					for update in data['updates']:
						if 'values' in update:
							for value in update['values']:
								if 'path' in value:
									for i in pathsList:
										if value['path'] == pathsList[i]:
											if 'value' in value:
												if 'message' in value['value']:
													if 'request' in value['value']['message']:
														if i in self.instances:
															if 'rev' in self.instances[i]:
																values = ''
																self.instances[i]['rev'] = 0
																if pulselist[i]['revCounter']: 
																	values += '{"path":"'+pulselist[i]['revCounter']+'","value":'+str(self.instances[i]['rev'])+'},'
																if pulselist[i]['distance'] and pulselist[i]['radius']:
																	distance = self.instances[i]['rev']*((2*math.pi)*pulselist[i]['radius'])
																	values += '{"path":"'+pulselist[i]['distance']+'","value":'+str(distance)+'},'
																if values:		
																	SignalK ='{"updates":[{"$source":"OpenPlotter.GPIO.pulses.'+i+'","values":['
																	SignalK += values[0:-1]+']}]}\n'	
																	try: 
																		if self.ws: 
																			self.ws.send(SignalK)
																		else: return
																	except Exception as e: 
																		if self.debug: 
																			print('Error connecting Signal K server: '+str(e))
																			sys.stdout.flush()
																		if self.ws: self.ws.close()
																		self.ws = False
																		return
																command = ['set-notification','notifications.GPIO'+i+'.reset','normal','done']
																process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
																out, err = process.communicate()
																if err:
																	if self.debug: 
																		print('Error sending pulses GPIO notification: '+str(err))
																		sys.stdout.flush()
			except Exception as e: 
				if self.debug: 
					print('Failed to reset GPIO pulses: '+str(e))
					sys.stdout.flush()
				return

	def digital(self,digitalList):
		config = {}
		for i in digitalList:
			if digitalList[i]['mode'] == 'in':
				try:
					if digitalList[i]['pull'] == 'up': bias = Bias.PULL_UP
					elif digitalList[i]['pull'] == 'down': bias = Bias.PULL_DOWN
					else: bias = Bias.DISABLED
					if digitalList[i]['init']:
						with gpiod.request_lines(self.chip,consumer="get-line-value",config={int(i): gpiod.LineSettings(direction=Direction.INPUT,bias=bias,debounce_period=timedelta(milliseconds=10))}) as request:
							value = request.get_value(int(i))
							if value == gpiodValue.ACTIVE: self.setnot(i,digitalList[i],'h')
							elif value == gpiodValue.INACTIVE: self.setnot(i,digitalList[i],'l')
					config[int(i)] = gpiod.LineSettings(edge_detection=Edge.BOTH,bias=bias,debounce_period=timedelta(milliseconds=10))
				except Exception as e: 
					if self.debug: 
						print('Error setting GPIO digital: '+str(e))
						sys.stdout.flush()
		with gpiod.request_lines(self.chip,consumer="watch-digital",config=config) as request:
			while True:
				for event in request.read_edge_events():
					try:
						gpio = str(event.line_offset)
						if event.event_type is event.Type.FALLING_EDGE: self.setnot(gpio,digitalList[gpio],'l')
						if event.event_type is event.Type.RISING_EDGE: self.setnot(gpio,digitalList[gpio],'h')
					except Exception as e: 
						if self.debug: 
							print('Error reading GPIO digital: '+str(e))
							sys.stdout.flush()

	def setnot (self,gpio,conf,state):
		command = ['set-notification']
		if state == 'l': 
			if conf['low']['visual']: command.append('-v')
			if conf['low']['sound']: command.append('-s')
		if state == 'h': 
			if conf['high']['visual']: command.append('-v')
			if conf['high']['sound']: command.append('-s')
		command.append('notifications.GPIO'+gpio)
		if state == 'l': 
			command.append(conf['low']['state'])
			command.append(conf['low']['message'])
		if state == 'h': 
			command.append(conf['high']['state'])
			command.append(conf['high']['message'])
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = process.communicate()
		if err:
			if self.debug: 
				print('Error sending digital GPIO notification: '+str(err))
				sys.stdout.flush()

############################################################################################

def main():
	if sys.argv[1] != '1':
		conf2 = conf.Conf()
		enableX1 = False
		enableX2 = False
		enableX3 = False
		enableX4 = False

		data = conf2.get('GPIO', '1w')
		try: oneWlist = eval(data)
		except: oneWlist = {}
		for i in oneWlist:
			if oneWlist[i]['sk']: enableX1 = True

		data = conf2.get('GPIO', 'pulses')
		try: pulselist = eval(data)
		except: pulselist = {}
		for i in pulselist:
			if pulselist[i]['revCounter'] or pulselist[i]['revolutions'] or pulselist[i]['linearSpeed'] or pulselist[i]['distance']: enableX2 = True
			if pulselist[i]['revCounter'] or pulselist[i]['distance']: enableX3 = True

		data = conf2.get('GPIO', 'digital')
		try: digitalList = eval(data)
		except: digitalList = {}
		if digitalList: enableX4 = True

		if enableX1 or enableX2 or enableX3 or enableX4:
			process = Process(conf2)
			try: process.connect()
			except Exception as e: 
				if process.debug: 
					print('Error connecting to SK: '+str(e))
					sys.stdout.flush()

			if enableX1:
				x1 = threading.Thread(target=process.oneW, args=(oneWlist,), daemon=True)
				x1.start()
			if enableX2:
				x2 = threading.Thread(target=process.pulse, args=(pulselist,), daemon=True)
				x2.start()
			if enableX3:
				x3 = threading.Thread(target=process.subscribe, args=(pulselist,), daemon=True)
				x3.start()
			if enableX4:
				x4 = threading.Thread(target=process.digital, args=(digitalList,), daemon=True)
				x4.start()

			while True:
				if not process.ws: 
					try: process.connect()
					except Exception as e: 
						if process.debug: 
							print('Error connecting to SK: '+str(e))
							sys.stdout.flush()
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
				if enableX4:
					if not x4.is_alive():
						x4.join()
						x4 = threading.Thread(target=process.digital, args=(digitalList,), daemon=True)
						x4.start()
				time.sleep(5)

if __name__ == '__main__':
	main()