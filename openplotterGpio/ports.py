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

import os, sys, subprocess
from openplotterSettings import language

class Ports:
	def __init__(self,conf,currentLanguage):
		self.conf = conf
		currentdir = os.path.dirname(os.path.abspath(__file__))
		language.Language(currentdir,'openplotter-gpio',currentLanguage)
		self.connections = []

	def usedPorts(self):
		try:
			subprocess.check_output(['systemctl', 'is-enabled', 'pigpiod']).decode(sys.stdin.encoding)
			self.connections.append({'id':'GPIO', 'description':'GPIO (pigpiod)', 'data':'', 'type':'TCP', 'mode':'server', 'address':'localhost', 'port':'8888', 'editable':'0'})
		except: pass

		return self.connections
