

import logging

def loginfo(type, env, mach_id, thing_id, msg):
	log_str = str(env.now) + '\t' + str(type.value) + '\t' + str(mach_id) + '\t' + str(thing_id) + '\t' + msg
	print(log_str)
	logging.info(log_str)