#! python
# Author: Rick Candell (rick.candell@nist.gov)
# Organization: National Institute of Standards and Technology
#               U.S. Department of Commerce
# License: Public Domain

import random
import simpy
import logging
from enum import Enum

class EventType(Enum):
	MACHINE_CREATED = 10
	MACHINE_WORK = 11

	THING_CREATED = 20
	THING_ENTER_MACH = 21
	THING_EXIT_MACH = 22
	THING_TRAVEL = 23

	PRODUCT_STORED = 50

	DIAGNOSTICS = 100


def loginfo(type, env, mach_id, thing_id, msg):
	log_str = str(env.now) + '\t' + str(type.value) + '\t' + str(mach_id) + '\t' + str(thing_id) + '\t' + msg
	print(log_str)
	logging.info(log_str)

class Rail(object):
	""" A Path represents the delay between to machine stations """
	def __init__(self, env, t_delay):
		self.env = env
		self.t_delay = t_delay
		self.path = simpy.Resource(env,1) # one path out from machine

	def travel(self, thing_id):
		
		# TODO: Place optical sensor reading here TCP

		yield self.env.timeout(self.t_delay)



class Machine(object):
	""" Machines do work on Thing objects """
	def __init__(self, env, mach_id, worktime, num_stations, path_delay):
		self.env = env
		self.mach_id = mach_id
		self.worktime = worktime
		self.station = simpy.Resource(env, num_stations)
		self.pathout = Rail(env, path_delay)

	def work(self, thing_id):

		# TODO: Place machine sensor reading here TCP

		# TODO:  Wait for command from controller to start work TCP

		yield self.env.timeout(self.worktime)
		loginfo(EventType.MACHINE_WORK, self.env, self.mach_id, thing_id, "machining work completed")
		#print("Machine %u completes work on Thing %u" % (self.mach_id, thing_id))

def thing(env, thing_id, machines, output_store):
	""" A thing goes to each machine and requests work to be done.
		Work is done and thing leaves to never come back """
	for mach in machines:
		with mach.station.request() as station_request:
			yield station_request
			loginfo(EventType.THING_ENTER_MACH, env, mach.mach_id, thing_id, "thing enters machine")
			yield env.process(mach.work(thing_id))
			loginfo(EventType.THING_EXIT_MACH, env, mach.mach_id, thing_id, "thing exits machine")
			with mach.pathout.path.request() as path_request:
				yield path_request
				loginfo(EventType.THING_TRAVEL, env, mach.mach_id, thing_id, "thing in transit")
				yield env.process(mach.pathout.travel(thing_id))
	loginfo(EventType.PRODUCT_STORED, env, -1, thing_id, "thing stored as product")
	output_store.put(1)
	loginfo(EventType.DIAGNOSTICS, env, -1, -1, "number of products " + str(output_store.level))

def setup(env, num_things, num_machines, num_stations, worktime, t_inter):
	""" Create the factory architecture """
	machines = []
	path_delays = [random.randint(1,3) for r in range(num_machines)]
	for mach_id in range(num_machines):
		m = Machine(env, mach_id, worktime, num_stations, path_delays[mach_id])
		machines.append(m)
		print ("Added machine %u" % mach_id)

	# create the storage bin for product output
	output_store = simpy.resources.container.Container(env, capacity=10000)

	# Create more things while the simulation is running
	thing_id = 0
	while True:
		loginfo(EventType.THING_CREATED, env, -1, thing_id, "thing created")
		#yield env.timeout(random.randint(t_inter-2, t_inter+2))
		yield env.timeout(t_inter)
		env.process(thing(env, thing_id, machines, output_store))
		thing_id += 1


RANDOM_SEED = 42
NUM_THINGS = 2**32
NUM_MACHINES = 4  # number of machines
NUM_STATIONS = 2  # Number of stations per machine
WORKTIME = 5      # Minutes at machine
T_INTER = 2       # Create a thing every NN minutes
SIM_TIME = 4000     # Simulation time in minutes

if __name__ == "__main__":

	logging.basicConfig(filename='sim.log', level=logging.INFO)
	
	print('Simple Factory')
	random.seed(RANDOM_SEED)  # This helps reproducing the results

	# Create an environment and start the setup process
	env = simpy.Environment()
	env.process(setup(env, NUM_THINGS, NUM_MACHINES, NUM_STATIONS, WORKTIME, T_INTER))

	# Execute simulation
	env.run(until=SIM_TIME)
