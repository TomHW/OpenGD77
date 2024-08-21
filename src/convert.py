#!/usr/bin/python3
'''
Created on 19.06.2024

@author: sesth - Thomas Hoffmann <do3thm@tibeto.de>
@author: desertblade - Ben Williams 

Gets 2m and 70cm band repeaters from repeaterbook and creates Zones.csv and Channels.csv for OpenGD77 CPS.
Needs configuration in convert.yaml.
The list of zones should be inside of the given country. Each Zone has the following values:
Name, Latitude, Longitude, MaxDistance (Radius in km). OpenGD77 is limited to 1024 channels, you have to limit zones
distances to avoid truncating the channel list during import.
Default 'TG List' is 'BM' (Brandmeister).

Based on repeaerbook API: <https://www.repeaterbook.com/wiki/doku.php?id=api>

Please note: This should work globally, desertblade has validated Germany and US outputs. Still doing testing.

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
import time

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
	    'User-Agent': 'Toms channel creator 0.2',
	    'From': 'do3thm@tibeto.de'
	}
	response = requests.get(url, headers=headers)
	if(response.status_code < 400 ):
		result = []
		try:
			repeaters = json.loads(response.content)['results']
		except ValueError as e:
			print(response.content)
			print("If rate limited wait 5 to 10 minutes")
			quit(1)
		else:
			# print(repeaters)
			for rep in repeaters:
				#  TODO: Add Digital channels back, excluding them for now
				# if(rep['Operational Status'] == 'On-air' and (rep['DMR'] == 'No' or rep['FM Analog'] == 'Yes')):
				if(rep['Operational Status'] == 'On-air' and rep['Use'] == 'OPEN' and rep['FM Analog'] == 'Yes'):
					# print(rep)
					result.append(rep)
			return result
	else:
		print(response.status_code)
		return None

#Map repeaterbook entry to GD77 channel format
def map_rep2chn(rep, decimal):
	chn = {}
	chn['Contact'] = 'None'
	chn['DMR ID'] = 'None'
	# chn['TS1_TA_Tx'] = 'Off'
	# chn['TS2_TA_Tx ID'] = 'Off'
	chn['Power'] = 'Master'
	chn['Rx Only'] = 'No'
	chn['Zone Skip'] = 'No'
	chn['All Skip'] = 'No'
	chn['TOT'] = 0 # Was 495
	chn['VOX'] = 'No'
	chn['No Beep'] = 'No'
	chn['No Eco'] = 'No'
	chn['APRS'] = 'No'
#	chn[''] = rep['State ID']
#	chn[''] = rep['Rptr ID']
#	chn[''] = rep['Landmark']
#	chn[''] = rep['Region']
#	chn[''] = rep['State']
#	chn[''] = rep['Country']

	if (decimal == 'Comma'):
		# EU likes commas over periods
		chn['Tx Frequency'] = rep['Input Freq'].replace('.', ',')
		chn['Rx Frequency'] = rep['Frequency'].replace('.', ',')
		chn['TX Tone'] = rep['PL'].replace('.', ',') if rep['PL'] != 'CSQ' else None
		chn['RX Tone'] = rep['TSQ'].replace('.', ',')
		chn['Latitude'] = rep['Lat'].replace('.', ',')
		chn['Longitude'] = rep['Long'].replace('.', ',')
	else:
		chn['Tx Frequency'] = rep['Input Freq']
		chn['Rx Frequency'] = rep['Frequency']
		chn['RX Tone'] = rep['TSQ']  # rep['PL'] if rep['PL'] != 'CSQ' else None
		chn['TX Tone'] = rep['PL'] if rep['PL'] != 'CSQ' else None # Added this
		chn['Latitude'] = rep['Lat']
		chn['Longitude'] = rep['Long']

	chn['Squelch'] = "Disabled"
#	chn[''] = rep['Precise']
	chn['Channel Name'] = (rep['Callsign'] + ' '  + rep['Nearest City'])[:16]
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
#	chn[''] = rep['DMR']
	if(rep['DMR'] == 'Yes'):
		chn['TG List'] = 'BM'
		if('Channel Type' in chn):
			chn['Channel Type'].append('Digital')
		else:
			chn['Channel Type'] = ['Digital']

	chn['Colour Code'] = rep['DMR Color Code']
	chn['DMR ID'] = rep['DMR ID']
	if('FM Bandwidth' in rep):
		# ROW has 'FM Bandwidth' in response
		chn['Bandwidth (kHz)'] = rep['FM Bandwidth'].replace('.', ',').replace(' kHz', '') if (not rep['FM Bandwidth'] is None) else None
	else:
		chn['Bandwidth (kHz)'] = '25' # NA uses wide band for Analog, overwrite digital narrow band when creating csv	

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
	with open("convert.yaml","r") as conffile:
		data = yaml.load(conffile,Loader=yaml.SafeLoader)

	myCountry = data['Country'] # Repeaterbook query for this country
	myZones = data['Zones']
	mode = data['Mode']
	decimal = data['Decimal']
	myQuery = "https://www.repeaterbook.com/api/"



	if(mode == 'Load'):
		with open('dump.bin', 'rb') as dumpfile:
			channels2m = pickle.load(dumpfile)
			channels70cm = pickle.load(dumpfile)
	else:
		# Lets figure out what endpoint to hit
		if (myCountry == 'United States' or myCountry == 'Canada'):
			myQuery += 'export.php?country=' + myCountry
		else: 
			myQuery += 'exportROW.php?country=' + myCountry

		print(f'Preparing to call {myQuery}')

		# Lets make some calls!
		# if States are included need to make a call per state
		if 'States' in data.keys():
			# Create some empty arrays
			channels2m = []
			channels70cm = []
		
			for state in data['States']:
				print(f'Calling {state} 2m')
				time.sleep(10) # Lets be respectful of not hitting the endpoint too quickly
				url = f'{myQuery}&state={state}&frequency=14%' # 2m Band
				channels2m += get_repeaters(url)
				time.sleep(30) # Lets be respectful of not hitting the endpoint too quickly
				print(f'Calling {state} 70cm')
				url = f'{myQuery}&state={state}&frequency=4%' # 70cm band
				channels70cm += get_repeaters(url)
				time.sleep(10) # Lets be respectful of not hitting the endpoint too quickly
		else: # rest of world and Canada
			print('Calling 2m')
			url = f'{myQuery}&frequency=14%' # 2m Band
			channels2m = get_repeaters(url)
			print('Calling 70cm')
			url = f'{myQuery}&frequency=4%' # 70cm band
			channels70cm = get_repeaters(url)

		if(mode == 'Dump'):
			print('Dumping output......')
			with open('dump.bin', 'wb') as dumpfile:
				pickle.dump(channels2m, dumpfile)
				pickle.dump(channels70cm, dumpfile)

	channelTypesDict = {}
	channels = []
	channelHeading = ['Channel Number', 'Channel Name', 'Channel Type', 'Rx Frequency', 'Tx Frequency', 'Bandwidth (kHz)', 'Colour Code', 'Timeslot', 'Contact', 'TG List', 'DMR ID', 'TS1_TA_Tx ID', 'TS2_TA_Tx ID', 'RX Tone', 'TX Tone', 'Squelch', 'Power', 'Rx Only', 'Zone Skip', 'All Skip', 'TOT', 'VOX', 'No Beep', 'No Eco', 'APRS', 'Latitude', 'Longitude']
	rowct = 0
	maxZoneChannels = 80 # OpenGD77 supports 80 channels per Zone
	for zoneName in myZones:
		global lat
		global lon
		lat = myZones[zoneName]['Latitude']
		lon = myZones[zoneName]['Longitude']
		zchannels = []
		zchannelsDMR = [] # For DMR Channels
		for row in list(channels2m) + list(channels70cm):
			dist = distance(float(row['Lat']), float(row['Long']), myZones[zoneName]['Latitude'], myZones[zoneName]['Longitude'])
			if(dist > myZones[zoneName]['MaxDistance']):
				continue
			chn = map_rep2chn(row, decimal)
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
					if (myCountry == 'United States' or myCountry == 'Canada'):
						wchn ['Bandwidth (kHz)'] = '12.5' # Setting to Narrow Band for digital in NA
					zchannelsDMR.append(wchn)
				else:
					zchannels.append(wchn)
		
		# sort channels based on ascending distance in current zone
		zchannels.sort(key=get_distance)
		zchannelsDMR.sort(key=get_distance)

		# Trimming to only maxZoneChannels 
		del zchannels[maxZoneChannels:]
		del zchannelsDMR[maxZoneChannels:]
 
		# add channel name to Analogue Zone
		for ch in zchannels:
			channelName = ch['Channel Name']
			zone = zoneName
		# 	# TODO: Zone name could be better
		# 	# zone = zoneName + ' ' + t
			if(zone in channelTypesDict):
				channelTypesDict[zone].append([channelName, dist])
			else:
				channelTypesDict[zone] = list([[channelName, dist]])


		# add channel name to Analogue Zone
		for ch in zchannelsDMR:
			channelName = ch['Channel Name']
			zone = zoneName + ' DMR'
		# 	# TODO: Zone name could be better
		# 	# zone = zoneName + ' ' + t
			if(zone in channelTypesDict):
				channelTypesDict[zone].append([channelName, dist])
			else:
				channelTypesDict[zone] = list([[channelName, dist]])

		# add sorted channel to global channel list
		channels += zchannels
		channels += zchannelsDMR

	with open('Channels.csv', 'wt', newline='') as csvoutfile:
		print('Creating Channels.csv')
		chnwriter = csv.writer(csvoutfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		chnwriter.writerow(channelHeading)
#		channels.sort(key=get_channelName)
		chno = 1
		for chn in channels:
			chn['Channel Number'] = chno
			chnwriter.writerow(chn[k] for k in channelHeading)
			chno += 1

	with open('Zones.csv', 'wt', newline='') as csvoutfile:
		print('Creating Zones.csv')
		znswriter = csv.writer(csvoutfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		znswriter.writerow(['Zone Name'] + list(f'Channel{i}' for i in range(1, maxZoneChannels + 1)))
		for elem in channelTypesDict:
			channelTypesDict[elem].sort(key=get_channelNameDistance)
			znswriter.writerow([elem] + list((str(nd[0]) for nd in channelTypesDict[elem])) + list([None for i in range(maxZoneChannels - len(channelTypesDict[elem]) -1)]))

	exit(0)
	

if __name__ == '__main__':
	main(sys.argv[1:])
