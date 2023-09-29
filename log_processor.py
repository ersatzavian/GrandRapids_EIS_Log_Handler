import struct
import csv
import pandas as pd
from enum import IntEnum
import os, time, datetime
import requests
import json

SAVVY_TOKEN = "4cb49fdf-6bd2-47bf-8306-23fb2852445e"

# we're faking our timestamps. This is how much to increment by between log entries in s
TIMESTAMP_INCREMENT_SEC = datetime.timedelta(seconds=0.1)

# values are 16-byte in packet unless noted here
class LogFmt(IntEnum):
	TACH = 0 		# resolution = 1
	CHT1 = 1 		# CHT and EGT resolution is all 1 degree (F?)
	CHT2 = 2
	CHT3 = 3
	CHT4 = 4
	CHT5 = 5
	CHT6 = 6
	EGT1 = 7
	EGT2 = 8
	EGT3 = 9
	EGT4 = 10
	EGT5 = 11
	EGT6 = 12
	AUX5 = 13
	AUX6 = 14
	ASPD = 15
	ALT = 16 		# altitude in 10s of ft, 2s complement
	VOLT = 17 		# resolution 100 mV
	FUELF = 18		# Fuel Flow resolution 0.1 gal/hr
	UNITT = 19 		# 1-byte internal instrument temp
	CARBT = 20 		# 1-byte carb temp, 2s complement
	ROCSGN = 21		# vert speed, 100 fpm resolution 2s complement
	OAT = 22		# unsigned 8-bit value offset by +50
	OILT = 23
	OILP = 24 		# 1-byte, resolution 1 psi?
	AUX1 = 25
	AUX2 = 26
	AUX3 = 27
	AUX4 = 28
	COOL = 29 		# coolant temp or tach3
	ETI = 30 		# hour meter, resolution 0.1 hour
	QTY = 31		# fuel qty resolution 0.1 gal
	HRS = 32 		# 1-byte, flight timer hours
	MIN = 33		# 1-byte
	SEC = 34 		# 1-byte
	ENDHRS = 35 	# 1-byte, fuel flow time til empty, hours
	ENDMINS = 36	# 1-byte, fuel flow time til empty, mins
	BARO = 37		# altimeter setting in inches of Hg, resolution 0.01"
	TACH2 = 38
	SPARE = 39		# 1-byte
	CHK = 40		# 1-byte checksum

directory = os.fsencode('./new_logs')
    
for file in os.listdir(directory):
    
    filename = os.fsdecode(file)
    
    # ignore hidden files like .DS_Store
    if filename.startswith('.'):
        continue

    this_flight_dict = {
        "Lcl Date": [],
        "Lcl Time": [],
        "UTCOfst": [],
        "tach": [],
        "cht2": [],
        "cht3": [],
        "egt1": [],
        "egt2": [],
        "egt3": [],
        "egt4": [],
        "volts": [],
        "unit_temp_f": [],
        "coolant_temp_f": [],
        "oil_temp_f": [],
        "oil_pres_psi": [],
        "amps": [],
        "aux2": [],
        "aux3": [],
        "aux4": [],
        "aux5": [],
        "aux6": [],
        "tach_hrs": [],
        "flight_hrs": []
    }

    # we're faking timestamps since neither the engine monitor nor the openlogger keep time
    timestamp = datetime.datetime.fromtimestamp(0)

    # 'rb' flag required to read text file in binary format
    with open('./new_logs/'+filename,'rb') as logfile:
        # largest log file I've managed to generate so far is 13.9 MB
        logbuffer = logfile.read()

    lines = logbuffer.split(b'\xfe\xff\xfe')
    # presume first and last packet are incomplete and dump them
    for idx, line in enumerate(lines[1:len(lines)-1]):
        try:
            unpacked_line = struct.unpack('>hhhhhhhhhhhhhhhhhhhbbbbhbhhhhhhhbbbbbhhbb', line)
        except:
            continue
            # TODO all logs seem to have a bad packet at same index? (6)
            print("Bad packet at idx %d" % idx)

        # we're faking timestamps, just slap a date in there instead of calling strftime 
        this_flight_dict["Lcl Date"].append("2012-04-20")
        this_flight_dict["Lcl Time"].append(timestamp.strftime("%H:%M:%S.%f"))
        timestamp = timestamp + TIMESTAMP_INCREMENT_SEC
        # fake the UTC offset as well
        this_flight_dict["UTCOfst"].append("-08:00:00")
        this_flight_dict["tach"].append(unpacked_line[LogFmt.TACH])
        this_flight_dict["cht2"].append(unpacked_line[LogFmt.CHT2])
        this_flight_dict["cht3"].append(unpacked_line[LogFmt.CHT3])
        this_flight_dict["egt1"].append(unpacked_line[LogFmt.EGT1])
        this_flight_dict["egt2"].append(unpacked_line[LogFmt.EGT2])
        this_flight_dict["egt3"].append(unpacked_line[LogFmt.EGT3])
        this_flight_dict["egt4"].append(unpacked_line[LogFmt.EGT4])
        this_flight_dict["volts"].append(unpacked_line[LogFmt.VOLT] * 0.1)
        this_flight_dict["unit_temp_f"].append(unpacked_line[LogFmt.UNITT])
        this_flight_dict["coolant_temp_f"].append(unpacked_line[LogFmt.COOL])
        this_flight_dict["oil_temp_f"].append(unpacked_line[LogFmt.OILT])
        this_flight_dict["oil_pres_psi"].append(unpacked_line[LogFmt.OILP])
        this_flight_dict["amps"].append(unpacked_line[LogFmt.AUX1])
        this_flight_dict["aux2"].append(unpacked_line[LogFmt.AUX2])
        this_flight_dict["aux3"].append(unpacked_line[LogFmt.AUX3])
        this_flight_dict["aux4"].append(unpacked_line[LogFmt.AUX4])
        this_flight_dict["aux5"].append(unpacked_line[LogFmt.AUX5])
        this_flight_dict["aux6"].append(unpacked_line[LogFmt.AUX6])
        this_flight_dict["tach_hrs"].append(unpacked_line[LogFmt.ETI] * 0.1)
        this_flight_dict["flight_hrs"].append(unpacked_line[LogFmt.HRS] + (unpacked_line[LogFmt.MIN] / 60) + (unpacked_line[LogFmt.SEC] / 3600))

    print("%s : Tach from %.1f to %.1f (%d lines)" % (filename, 
        this_flight_dict["tach_hrs"][0],
        this_flight_dict["tach_hrs"][len(this_flight_dict["tach_hrs"])-1],
        idx))
    
    output_filename = "%s_%d_to_%d.csv" % (os.path.splitext(filename)[0], 
        this_flight_dict["tach_hrs"][0], 
        this_flight_dict["tach_hrs"][len(this_flight_dict["tach_hrs"])-1])

    # this semi-magic line of metadata is required to mimic a garmin log for Savvy's log parsers
    metadata_row = ["#airframe_info","log_version=\"1.00\"","airframe_name=\"Kitfox\"","unit_software_part_number=\"001\"","unit_software_version=\"01\"","system_software_part_number=\"00\"","system_id=\"123\"","mode=NORMAL"]
    
    # this row of units / formats must correspond to the column headers listed above
    units_row = ["#yyyy-mm-dd","hh:mm:ss.ms","hh:mm:ss","rpm","deg F","deg F","deg F","deg F","deg F","deg F","volts","deg F","deg F","deg F","psi","amps","hours","hh:mm:ss"]

    # newline param required to avoid inserting empty lines after written lines
    with open("./processed_logs/%s" % output_filename, mode='w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(metadata_row)
        csvwriter.writerow(units_row)

    pd.DataFrame(this_flight_dict).to_csv("./processed_logs/%s" % output_filename, mode='a', index=False)
    # os.remove("./new_logs/%s" % filename)
    
    # upload to savvy aircraft mx directly
    # https://github.com/savvyaviation/api-docs

    # Use token to get aircraft ID
    r = requests.post("https://apps.savvyaviation.com/get-aircraft/",
        data={'token': SAVVY_TOKEN})
    acft_id = r.json()[0]["id"]
    print(r.json())

    print("Uploading %s" % output_filename)
    with open("./processed_logs/%s" % output_filename, 'rb') as f:
        r = requests.post("https://apps.savvyaviation.com/upload_files_api/%s/" % acft_id,
            data={'token': SAVVY_TOKEN},
            files={'file': f})
        print(r)
        print(r.json())
