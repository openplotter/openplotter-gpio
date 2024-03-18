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

import os, sys, subprocess
from openplotterSettings import conf
from openplotterSettings import language
from .version import version

def main():
	conf2 = conf.Conf()
	currentdir = os.path.dirname(os.path.abspath(__file__))
	currentLanguage = conf2.get('GENERAL', 'lang')
	package = 'openplotter-gpio'
	language.Language(currentdir, package, currentLanguage)

	print(_('Installing python packages...'))
	try:
		subprocess.call(['pip3', 'install', 'w1thermsensor', '-U', '--break-system-packages'])
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

	'''
	try:
		out = subprocess.check_output('raspi-config nonint get_pi_type', shell=True).decode(sys.stdin.encoding)
		out = out.replace("\n","")
		out = out.strip()
	except: out = ''
	if out != '5':
		print(_('Enabling pigpiod service...'))
		try:
			subprocess.call(['systemctl', 'enable', 'pigpiod'])
			subprocess.call(['systemctl', 'restart', 'pigpiod'])
			subprocess.call(['systemctl', 'daemon-reload'])
			print(_('DONE'))
		except Exception as e: print(_('FAILED: ')+str(e))
	'''

	print(_('Setting version...'))
	try:
		conf2.set('APPS', 'gpio', version)
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

if __name__ == '__main__':
	main()