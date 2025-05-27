#!/usr/bin/python3
'''
Created on 19.06.2024

@author: sesth - Thomas Hoffmann <da1th@darc.de>

Gets 2m and 70cm band repeaters from repeaterbook and creates Zones.csv and Channels.csv for OpenGD77 CPS.
Needs configuration in convert.yaml.
The list of zones should be inside of the given country. Each Zone has the following values:
Name, Latitude, Longitude, MaxDistance (Radius in km). OpenGD77 is limited to 1024 channels, you have to limit zones
distances to avoid truncating the channel list during import.
Default 'TG List' is 'BM' (Brandmeister).

Based on repeaerbook API: <https://www.repeaterbook.com/wiki/doku.php?id=api>
Please note: Program is tested for 'Outside of North America', North America may have different data structures.
I'm working with German localized OpenGD77 CPS and therefore the created CSV files use German locale!

Repeaterbook limits the download rate. Make your first query with Mode: 'Dump' to write the raw query result into
a local dump.bin file. Then use Mode: 'Load' to avoid further queries when fine tuning the script and parameters
for your needs. Mode: 'Default' makes repeaterbook queries and makes no dump.bin files, it is for normal use with
proven parameters.   
'''

import requests
import json
import math
import csv
import sys
import pickle
import yaml

# globals for get_distance lambda expression
lat = 0.0
lon = 0.0

#Calculate the orthodrom between two positions
def distance(lat1, lon1, lat2, lon2):
	earthRadius = 6371.0  # km
	phi1 = math.radians(lat1)
	phi2 = math.radians(lat2)
	deltaPhi = math.radians(lat2 - lat1)
	deltaLambda = math.radians(lon2 - lon1)

	a = math.sin(deltaPhi / 2) * math.sin(deltaPhi / 2) + math.cos(phi1) * math.cos(phi2) * math.sin(deltaLambda / 2) * math.sin(deltaLambda / 2);
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));

	d = earthRadius * c  # in km
	return d

#Download repeaters from repeaterbook (json format)
def get_repeaters(url):
	headers = {
	    'User-Agent': 'Toms channel creator 0.1, <da1th@darc.de>',
	    'From': 'da1th@darc.de'
	}
	response = requests.get(url, headers=headers)
	if(response.status_code < 400 ):
		result = []
		repeaters = json.loads(response.content)['results']
#		print(repeaters)
		for rep in repeaters:
			if(rep['Operational Status'] == 'On-air' and (rep['DMR'] == 'Yes' or rep['FM Analog'] == 'Yes')):
#				print(rep)
				result.append(rep)
		return result
	else:
		print(response.status_code)
		return None

#Map repeaterbook entry to GD77 channel format
def map_rep2chn(rep):
	chn = {}
	chn['Contact'] = 'None' if(rep['DMR'] == 'Yes') else ''
	chn['Timeslot'] = '1' if(rep['DMR'] == 'Yes') else ''
	chn['DMR ID'] = 'None'		# Default is empty, set your own DMR ID if you work with different IDs per channel!
	chn['TS1_TA_Tx'] = 'Text' if(rep['DMR'] == 'Yes') else ''
	chn['TS2_TA_Tx ID'] = 'Text' if(rep['DMR'] == 'Yes') else ''
	chn['Squelch'] = '' if(rep['DMR'] == 'Yes') else 'Disabled'
	chn['Power'] = 'Master'
	chn['Rx Only'] = 'No'
	chn['Zone Skip'] = 'No'
	chn['All Skip'] = 'No'
	chn['TOT'] = 495
	chn['VOX'] = 'Off'
	chn['No Beep'] = 'No'
	chn['No Eco'] = 'No'
	chn['APRS'] = 'None'
#	chn[''] = rep['State ID']
#	chn[''] = rep['Rptr ID']
	chn['Tx Frequency'] = rep['Input Freq'].replace('.', ',')
	chn['Rx Frequency'] = rep['Frequency'].replace('.', ',')
	if(rep['DMR'] != 'Yes'):
		chn['TX Tone'] = rep['PL'].replace('.', ',') if(rep['PL'] != 'CSQ') else 'None'
		chn['RX Tone'] = rep['TSQ'].replace('.', ',') if(rep['TSQ'] != '') else 'None'
#	chn[''] = rep['Landmark']
#	chn[''] = rep['Region']
#	chn[''] = rep['State']
#	chn[''] = rep['Country']
	chn['Latitude'] = rep['Lat'].replace('.', ',')
	chn['Longitude'] = rep['Long'].replace('.', ',')
	chn['Use location'] = 'Yes'
#	chn[''] = rep['Precise']
	band = ' '
	if(float(rep['Input Freq']) > 146):
		band = '#'
	chn['Channel Name'] = (band + rep['Callsign'] + ' '  + rep['Nearest City'])[:15]
#	chn[''] = rep['Use']
#	chn[''] = rep['Operational Status']
#	chn[''] = rep['ARES']
#	chn[''] = rep['RACES']
#	chn[''] = rep['SKYWARN']
#	chn[''] = rep['CANWARN']
#	chn[''] = rep['AllStar Node']
#	chn[''] = rep['EchoLink Node']
#	chn[''] = rep['IRLP Node']
#	chn[''] = rep['Wires Node']
	if(rep['FM Analog'] == 'Yes'):
		if('Channel Type' in chn):
			chn['Channel Type'].append('Analogue')
		else:
			chn['Channel Type'] = ['Analogue']
	chn['Bandwidth (kHz)'] = rep['FM Bandwidth'].replace('.', ',').replace(' kHz', '') if (not rep['FM Bandwidth'] is None) else None
#	chn[''] = rep['DMR']
	if(rep['DMR'] == 'Yes'):
		chn['TG List'] = 'BM'
		if('Channel Type' in chn):
			chn['Channel Type'].append('Digital')
		else:
			chn['Channel Type'] = ['Digital']
	chn['Colour Code'] = rep['DMR Color Code']
#	chn[''] = rep['D-Star']
#	chn[''] = rep['NXDN']
#	chn[''] = rep['APCO P-25']
#	chn[''] = rep['P-25 NAC']
#	chn[''] = rep['M17']
#	chn[''] = rep['M17 CAN']
#	chn[''] = rep['Tetra']
#	chn[''] = rep['Tetra MCC']
#	chn[''] = rep['Tetra MNC']
#	chn[''] = rep['System Fusion']
#	chn[''] = rep['YSF DG ID Uplink']
#	chn[''] = rep['YSF DG IS Downlink']
#	chn[''] = rep['YSF DSC']
#	chn[''] = rep['Notes']
#	chn[''] = rep['Last Update']
	return chn	

#Extract channel name from zone channel dictionary - lambda expression for zone sort
def get_channelNameDistance(chnND):
	return chnND[1]

#Extract channel name from channel dictionary - lambda expression for channel sort
def get_distance(chnDict):
	return distance(float(chnDict['Latitude'].replace(',', '.')), float(chnDict['Longitude'].replace(',', '.')), lat, lon)

def main(argv):
	cf = "convert.yaml"
	if(len(argv) > 0):
		cf = argv[0]
	with open(cf,"r") as conffile:
		data = yaml.load(conffile,Loader=yaml.SafeLoader)

	myCountry = data['Country']		# Repeaterbook query for this country
	myZones = data['Zones']
	mode = data['Mode']
	
	if(mode == 'Load'):
		with open('dump.bin', 'rb') as dumpfile:
			channels2m = pickle.load(dumpfile)
			channels70cm = pickle.load(dumpfile)
	else:
		# 2m Band
		url = f'https://www.repeaterbook.com/api/exportROW.php?country={myCountry}&frequency=14%'
		channels2m = get_repeaters(url)
		url = f'https://www.repeaterbook.com/api/exportROW.php?country={myCountry}&frequency=43%'
		channels70cm = get_repeaters(url)
		if(mode == 'Dump'):
			with open('dump.bin', 'wb') as dumpfile:
				pickle.dump(channels2m, dumpfile)
				pickle.dump(channels70cm, dumpfile)
	channelTypesDict = {}
	channels = []
	channelHeading = ['Channel Number', 'Channel Name', 'Channel Type', 'Rx Frequency', 'Tx Frequency', 'Bandwidth (kHz)', 'Colour Code', 'Timeslot', 'Contact', 'TG List', 'DMR ID', 'TS1_TA_Tx', 'TS2_TA_Tx ID', 'RX Tone', 'TX Tone', 'Squelch', 'Power', 'Rx Only', 'Zone Skip', 'All Skip', 'TOT', 'VOX', 'No Beep', 'No Eco', 'APRS', 'Latitude', 'Longitude', 'Use location']
	rowct = 0
	for zoneName in myZones:
		global lat
		global lon
		lat = myZones[zoneName]['Latitude']
		lon = myZones[zoneName]['Longitude']
		zchannels = []
		for row in list(channels2m) + list(channels70cm):
			dist = distance(float(row['Lat']), float(row['Long']), myZones[zoneName]['Latitude'], myZones[zoneName]['Longitude'])
			if(dist > myZones[zoneName]['MaxDistance']):
				continue
			chn = map_rep2chn(row)
			# add channel name to zone
			for t in chn['Channel Type']:
				if (t == 'Digital'):
					channelName = chn ['Channel Name'].replace(' ', '.')
				else:
					channelName = chn ['Channel Name']
				zone = zoneName + ' ' + t
				# channelName isn't unique, need to recognize duplicates! Use dictonary instead of list!
				if(zone in channelTypesDict):
					channelTypesDict[zone].append([channelName, dist])
				else:
					channelTypesDict[zone] = list([[channelName, dist]])
			rowct += 1
			chn['Channel Number'] = rowct
			# fill empty columns
			for k in channelHeading:
				if(not k in chn):
					chn[k] = None
			# make a copy of the row for each Channel Type
			for t in chn['Channel Type']:
				wchn = chn.copy()
				wchn ['Channel Type'] = t
				if (t == 'Digital'):
					wchn ['Channel Name'] = chn ['Channel Name'].replace(' ', '.')
				zchannels.append(wchn)
		# sort channels based on ascending distance in current zone
		zchannels.sort(key=get_distance)
		# add sorted channel to global channel list
		channels += zchannels

	with open('Channels.csv', 'wt', newline='') as csvoutfile:
		chnwriter = csv.writer(csvoutfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		chnwriter.writerow(channelHeading)
#		channels.sort(key=get_channelName)
		chno = 1
		for chn in channels:
			chn['Channel Number'] = chno
			chnwriter.writerow(chn[k] for k in channelHeading)
			chno += 1

	with open('Zones.csv', 'wt', newline='') as csvoutfile:
		znswriter = csv.writer(csvoutfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		rowct = max(rowct, 180)
		znswriter.writerow(['Zone Name'] + list(f'Channel{i}' for i in range(1, rowct)))
		for elem in channelTypesDict:
			channelTypesDict[elem].sort(key=get_channelNameDistance)
			znswriter.writerow([elem] + list((str(nd[0]) for nd in channelTypesDict[elem])) + list([None for i in range(rowct - len(channelTypesDict[elem]) -1)]))

	exit(0)
	

if __name__ == '__main__':
	main(sys.argv[1:])
