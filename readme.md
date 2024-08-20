> [!WARNING]
> Working on making this work for US. It is not ready for general use! Hard coded to work for Oregon and Washington, will support more states/countries in the future.

RepeaterBook to OpenGD77 w/Zones
=======
Python script to support the creation of OpenGD77 CPS files.

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

Usage
=====
Needs an installed Python3 interpreter and requires the modules
* requests
* json
* math
* csv
* sys
* pickle
* yaml

Edit  _convert.yaml_  for your needs, then call

`./convert.py`

The files  _Channels.csv_  and  _Zones.csv_  are created and should be imported into OpenGD77 CPS.