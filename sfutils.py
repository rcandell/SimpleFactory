
import time
import logging

def init_logging(fname, level=logging.INFO):
	logging.basicConfig(filename=fname, level=level)

def loginfo(lcode, env, mach_id, thing_id, msg):
	log_str = "%20s" % str(time.time()) + "\t" + str(env.now) + '\t' + \
		"%20s" % lcode.name + '\t' + str(mach_id) + '\t' + \
		str(thing_id) + '\t' + msg
	print(log_str)
	logging.info(log_str)

def logstr(msg):
	msg = str(time.time()) + "\t" + msg
	logging.info(msg)
	print(msg)

def logstrjson(msg):
	msg = "{ time:" + str(time.time()) + ", data:" + msg
	logging.info(msg)
	print(msg)