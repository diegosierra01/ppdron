#!/usr/bin/env python3
import os
import csv
import pexpect
import src.settings as settings

from poormanslogging import info, warn, error

def scan_targets():
	"""
	Scans the surrounding networks for a predefined amount of time.
	Orders the found APs by power, and then returns the one with most IV captured (or the specified network in the essid parameter)
	The AP is represented by a dict, in the form:
		{'Privacy': 'WPA2 WPA', 'Authentication': 'PSK', 'channel': '1', 'ESSID': 'The Beardhouse', 'LAN IP': '0.  0.  0.  0', 'First time seen': '2015-12-15 04:10:22', 'Speed': '54', 'IV': '0', 'beacons': '25', 'ID-length': '14', 'Cipher': 'CCMP TKIP', 'Power': '-63', 'Last time seen': '2015-12-15 04:10:31', 'Key': '', 'BSSID': '38:60:77:A4:68:A1'}
	Notice that the keys are mapped to airodump-ng column names, EXCEPT for 'beacons' and 'IV'
	:param iface_mon: Monitoring interface with which to scan
	:param essid: If supplied, it gets the airodump information for this particular ESSID
	"""
	info("Scanning {t} seconds for target WiFi access points...".format(t=settings.AIRODUMP_SCAN_TIME))
	#  Delete old files:
	if os.path.exists(os.path.join(settings.OS_PATH,'PPDRON-01.csv')):
		os.remove(os.path.join(settings.OS_PATH,'PPDRON-01.csv'))
		os.remove(os.path.join(settings.OS_PATH,'PPDRON-01.cap'))
		os.remove(os.path.join(settings.OS_PATH,'PPDRON-01.kismet.csv'))
		os.remove(os.path.join(settings.OS_PATH,'PPDRON-01.kismet.netxml'))

	cmd_airodump = pexpect.spawn('airodump-ng -w PPDRON {i}'.format(i=settings.INTERFACE_MON))
	cmd_airodump.expect([pexpect.TIMEOUT, pexpect.EOF], settings.AIRODUMP_SCAN_TIME)
	cmd_airodump.close()

	with open(os.path.join(settings.OS_PATH,'PPDRON-01.csv'), 'r') as f:
		f.readline()  # skip empty line
		header = list(f.readline().split(', '))
		header = list(map(lambda x: x.replace('# ', '').strip(), header))  # cleanup
		d = csv.DictReader(f, delimiter=',', skipinitialspace=True, fieldnames=header)
		aps = []
		for e in d:
			if e.get('Power') is not None:
				aps.append(e)
			else:
				#  Nearing the end, there's the stations list,
				#  for which we don't care right now
				break
		if len(aps) == 0:
			error("No WiFi networks in range! Nothing we can do.")
			exit(1)
		if settings.TARGET_ESSID is None:
			for ap in aps:
				if '00' in ap.get('ESSID'):
					aps.remove(ap)
			aps = sorted(aps, key=lambda x: x.get('Power'))
			# From the top 2, get the one with most IV
			return sorted(aps[:2], key=lambda x: x.get('IV'), reverse=True)[0]
		else:
			ap_defined = None
			for ap in aps:
				if ap.get('ESSID') == settings.TARGET_ESSID:
					ap_defined = ap
					break
			if ap_defined is not None:
				return ap_defined
			else:
				error("AP Target not found! Ending...")
				exit(1)
