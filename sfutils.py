
import time
import logging

def init_logging(fname, level=logging.INFO):
	logging.basicConfig(filename=fname, level=level)

def logheader():
	log_str = "wall_clock, sim_time, log_code, machine_id, part_id, text_msg"
	print(log_str)
	logging.info(log_str)

def loginfo(lcode, env, mach_id, part_id, msg):
	log_str = "%20s" % str(time.time()) + "\t" + str(env.now) + '\t' + \
		"%20s" % lcode.name + '\t' + str(mach_id) + '\t' + \
		str(part_id) + '\t' + msg
	print(log_str)
	logging.info(log_str)

def logstr(msg, screen=True):
	msg = "* " + str(time.time()) + "\t" + msg
	logging.info(msg)
	if screen is True:
		print(msg)

def logstrjson(msg, screen=True):
	msg = "{ time:" + str(time.time()) + ", data:" + msg
	logging.info(msg)
	if screen is True:
		print(msg)
		
		
