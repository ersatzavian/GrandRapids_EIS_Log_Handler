
import struct
import pandas as pd
from enum import IntEnum
from influxdb_client_3 import InfluxDBClient3, Point
import os, time, datetime

# influxdb free account limit is 5MB/5min
MAX_RECORD_SIZE_PTS = 1024

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

token = "0u8Ud5cDxvyPgGrk2hh_vGofD8kf3WRFvulWSCBCqF4Zs7gR5nJ3pdPUAr9sLdkBOlCZeCtc3LxeabEekIvRNQ=="
org = "EIS Datalogger"
database = "Testdata"
host = "https://us-east-1-1.aws.cloud2.influxdata.com"

client = InfluxDBClient3(host=host, token=token, org=org)

# 'rb' flag required to read text file in binary format
with open('TESTLOG.TXT','rb') as logfile:
	# largest log file I've managed to generate so far is 13.9 MB
	logbuffer = logfile.read()

lines = logbuffer.split(b'\xfe\xff\xfe')
print("Read %d points from log file." % len(lines))

# array of influx "point" objects, to be posted 
record = []
# presume first and last packet are incomplete and dump them
for idx, line in enumerate(lines[1:len(lines)-1]):
	try:
		unpacked_line = struct.unpack('>hhhhhhhhhhhhhhhhhhhbbbbhbhhhhhhhbbbbbhhbb', line)
	except:
		print("Bad packet at idx %d" % idx)

	point = (
	Point("engine_logs")
	.tag("flight_num", 1)
	.field("tach", unpacked_line[LogFmt.TACH])
	.field("cht2", unpacked_line[LogFmt.CHT2])
	.field("cht3", unpacked_line[LogFmt.CHT3])
	.field("egt1", unpacked_line[LogFmt.EGT1])
	.field("egt2", unpacked_line[LogFmt.EGT2])
	.field("egt3", unpacked_line[LogFmt.EGT3])
	.field("egt4", unpacked_line[LogFmt.EGT4])
	.field("volts", unpacked_line[LogFmt.VOLT] * 0.1)
	.field("unit_temp_f", unpacked_line[LogFmt.UNITT])
	.field("coolant_temp_f", unpacked_line[LogFmt.COOL])
	.field("oil_temp_f", unpacked_line[LogFmt.OILT])
	.field("oil_pres_psi", unpacked_line[LogFmt.OILP])
	.field("aux1", unpacked_line[LogFmt.AUX1])
	.field("aux2", unpacked_line[LogFmt.AUX2])
	.field("aux3", unpacked_line[LogFmt.AUX3])
	.field("aux4", unpacked_line[LogFmt.AUX4])
	.field("aux5", unpacked_line[LogFmt.AUX5])
	.field("aux6", unpacked_line[LogFmt.AUX6])
	.field("tach_hrs", unpacked_line[LogFmt.ETI] * 0.1)
	.field("flight_hrs", unpacked_line[LogFmt.HRS] + (unpacked_line[LogFmt.MIN] / 60) + (unpacked_line[LogFmt.SEC] / 3600))
	)
	record.append(point)

	# post points to the server in managed chunks
	if(len(record) >= MAX_RECORD_SIZE_PTS):
		client.write(database=database, record=record)
		print("-",end="")
		record = []

print("Processed %d lines" % idx)
client.write(database=database, record=record)
print("Posted to server")
