> [!WARNING]
> This is still a work in progress and may not work 100% correctly.

Repeater book now requires an valid email to make calls and eventually will need an api key. More details can be found here <https://www.repeaterbook.com/wiki/doku.php?id=api&s[]=api>

RepeaterBook supports OpenGD77!

It's tucked away under Export->Radioddity->OpenGD77 Channels File. You can then load it in to OpenGD77 CPS using File->CSV-Append CSV.

This script creates zones with channels. It makes it a bit easier for organizing and importing into OpenGD77. 

RepeaterBook to OpenGD77 w/Zones
=======
Python script to support the creation of OpenGD77 CPS files. Supports North America and Rest of World (in theory).

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
* yaml (which is pyyaml)

Install Python: https://www.python.org/downloads/

Run these commands in terminal:

`pip install requests`

`pip install pyyaml`

Edit  _convert.yaml_  for your needs, then call

`python3 convert.py`

The files  _Channels.csv_  and  _Zones.csv_  are created and should be imported into OpenGD77 CPS.
