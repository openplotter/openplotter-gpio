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

import threading, time, pigpio, math, ujson, ssl, subprocess, sys
#import RPi.GPIO as GPIO
from openplotterSettings import conf
from openplotterSettings import platform
from websocket import create_connection
from openplotterSignalkInstaller import connections
try: from w1thermsensor import W1ThermSensor, Unit
except: pass

class rpmReader:
	def __init__(self, TACH, pulses_per_rev=1.0, pull='down'):
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		if pull== 'up': GPIO.setup(TACH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		elif pull == 'down': GPIO.setup(TACH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		else: GPIO.setup(TACH, GPIO.IN)
		GPIO.add_event_detect(TACH, GPIO.FALLING, self.fell)
		self.t = time.time()
		self.rpm = 0
		self.counter = 0
		self.pulsesCounter = 0
		self.pulses_per_rev = pulses_per_rev
		
	def fell(self,n):
		dt = time.time() - self.t
		if dt < 0.01: return # reject spuriously short pulses
		freq = 1 / dt
		self.rpm = (freq / self.pulses_per_rev) * 60
		self.pulsesCounter = self.pulsesCounter + 1
		if self.pulsesCounter == self.pulses_per_rev:
			self.counter = self.counter + 1
			self.pulsesCounter = 0
			self.t = time.time()
		
	def cancel(self):
		GPIO.cleanup()
		sys.exit()

############################################################################################

class Process:
	def __init__(self):
		self.ws = False
		self.instances = {}
		self.conf = conf.Conf()
		if self.conf.get('GENERAL', 'debug') == 'yes': self.debug = True
		else: self.debug = False

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
								except: 
									if self.ws: self.ws.close()
									self.ws = False
									return
			except Exception as e: 
				if self.debug: print('Reading GPIO 1W error: '+str(e))
				return

	def pulse(self,pulselist):
		self.instances = {}
		for i in pulselist:
			if pulselist[i]['revCounter'] or pulselist[i]['revolutions'] or pulselist[i]['linearSpeed'] or pulselist[i]['distance']:
				try:
					self.instances[i] = {'instance': rpmReader(int(i), pulses_per_rev=pulselist[i]['pulsesPerRev'], pull=pulselist[i]['pull'])}
				except Exception as e: 
					if self.debug: print('Creating GPIO pulses error: '+str(e))

		if self.instances:
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
						rpm = self.instances[i]['instance'].rpm
						counter = self.instances[i]['instance'].counter
						if time.time() - self.instances[i]['instance'].t > 2: # min rpm = 30
							hertz = 0
							rps = 0
						else:
							hertz = rpm/60
							rps = rpm*(math.pi/30)
						if radius: 
							lSpeed = rps*radius
							distance = counter*((2*math.pi)*radius)
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
									else:
										for i in self.instances:
											self.instances[i]['instance'].cancel()
										self.instances = {}
										return
								except: 
									if self.ws: self.ws.close()
									self.ws = False
									for i in self.instances:
										self.instances[i]['instance'].cancel()
									self.instances = {}
									return
				except Exception as e: 
					if self.debug: print('Reading GPIO pulses error: '+str(e))
					return

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
			except: 
				if self.ws: self.ws.close()
				self.ws = False
				return

		while True:
			time.sleep(0.01)
			try:
				try: 
					if self.ws: result = self.ws.recv()
					else: return
				except: 
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
															if 'instance' in self.instances[i]: 
																self.instances[i]['instance'].counter = 0
																command = ['set-notification','notifications.GPIO'+i+'.reset','normal','done']
																process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
																out, err = process.communicate()
																if err:
																	if self.debug: print('Error sending pulses GPIO notification: '+str(err))										
			except Exception as e: 
				if self.debug: print('Failed to reset GPIO pulses: '+str(e))
				return

	def digital(self,digitalList):
		instances2 = {}
		for i in digitalList:
			if digitalList[i]['mode'] == 'in':
				try:
					items = i.split('-')
					host = items[0]
					gpio = int(items[1])
					pi = pigpio.pi(host)
					if not pi.connected: continue
					pi.set_mode(gpio, pigpio.INPUT)
					if digitalList[i]['pull'] == 'up': pi.set_pull_up_down(gpio, pigpio.PUD_UP)
					elif digitalList[i]['pull'] == 'down': pi.set_pull_up_down(gpio, pigpio.PUD_DOWN)
					else: pi.set_pull_up_down(gpio, pigpio.PUD_OFF)
					instances2[i] = {'pi': pi, 'gpio': gpio, 'high': digitalList[i]['high'], 'low': digitalList[i]['low'], 'init': digitalList[i]['init'], 'old':'init'}
				except Exception as e: 
					if self.debug: print('Creating GPIO digital error: '+str(e))

		if instances2:
			while True:
				for i in instances2:
					try:
						level = instances2[i]['pi'].read(instances2[i]['gpio'])
						if instances2[i]['old'] != level:
							if instances2[i]['old'] == 'init' and not instances2[i]['init']: pass
							else:
								command = ['set-notification']
								if level == 0: 
									if instances2[i]['low']['visual']: command.append('-v')
									if instances2[i]['low']['sound']: command.append('-s')
								if level == 1: 
									if instances2[i]['high']['visual']: command.append('-v')
									if instances2[i]['high']['sound']: command.append('-s')
								command.append('notifications.GPIO'+str(instances2[i]['gpio']))
								if level == 0: 
									command.append(instances2[i]['low']['state'])
									command.append(instances2[i]['low']['message'])
								if level == 1: 
									command.append(instances2[i]['high']['state'])
									command.append(instances2[i]['high']['message'])
								process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
								out, err = process.communicate()
								if err:
									if self.debug: print('Error sending digital GPIO notification: '+str(err))
							instances2[i]['old'] = level
					except Exception as e: 
						if self.debug: print('Reading GPIO digital error: '+str(e))
						for i in instances2:
							instances2[i]['pi'].stop()
						instances2 = {}
						return
				time.sleep(0.01)

############################################################################################

def main():
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

	'''
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
	'''

	if enableX1 or enableX2 or enableX3 or enableX4:
		process = Process()
		try: process.connect()
		except Exception as e: 
			if process.debug: print('Error connecting to SK: '+str(e))

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
					if process.debug: print('Error connecting to SK: '+str(e))
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