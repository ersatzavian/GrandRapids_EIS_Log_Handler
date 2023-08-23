import struct
import pandas as pd
from enum import IntEnum
import os, time, datetime

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
    
# Watch out for DS_Store files - disable creation of these with:
# defaults write com.apple.desktopservices DSDontWriteNetworkStores true
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    
    this_flight_dict = {
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
        "aux1": [],
        "aux2": [],
        "aux3": [],
        "aux4": [],
        "aux5": [],
        "aux6": [],
        "tach_hrs": [],
        "flight_hrs": []
    }

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
        this_flight_dict["aux1"].append(unpacked_line[LogFmt.AUX1])
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
    
    pd.DataFrame(this_flight_dict).to_csv("./processed_logs/%s" % output_filename, index=False)
    # os.remove("./new_logs/%s" % filename)
    
    # TODO upload to savvy aircraft mx directly
    #     https://github.com/savvyaviation/api-docs
    
#     token = "4cb49fdf-6bd2-47bf-8306-23fb2852445e"
#     with open("./processed_logs/%s" % output_filename, 'rb') as f:
#         r = requests.post("https://apps.savvyaviation.com/upload_files_api/15678/",
#             form={'token': token}
#             files={'report.xls': f})
    