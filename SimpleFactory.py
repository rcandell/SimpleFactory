#! python
# Author: Rick Candell (rick.candell@nist.gov)
# Organization: National Institute of Standards and Technology
#               U.S. Department of Commerce
# License: Public Domain

import random
import simpy

class Rail(object):
	""" A Path represents the delay between to machine stations """
	def __init__(self, env, t_delay):
		self.env = env
		self.t_delay = t_delay
		self.path = simpy.Resource(env,1) # one path out from machine

	def travel(self, thing_id):
		yield self.env.timeout(self.t_delay)
		print( "Thing %u traveled to next at %.3f" % (thing_id, self.env.now))

		# TODO: Place optical sensor reading here TCP



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
		print("Machine %u completes work on Thing %u" % (self.mach_id, thing_id))

def thing(env, thing_id, machines):
	""" A thing goes to each machine and requests work to be done.
		Work is done and thing leaves to never come back """
	for mach in machines:
		with mach.station.request() as request:
			yield request
			print('Thing %u enters machine %u at %.3f.' % (thing_id, mach.mach_id, env.now))
			yield env.process(mach.work(thing_id))
			print('Thing %u leaves machine %u at %.3f.' % (thing_id, mach.mach_id, env.now))
			with mach.pathout.path.request() as request:
				yield request
				yield env.process(mach.pathout.travel(thing_id))

def setup(env, num_things, num_machines, num_stations, worktime, t_inter):
	""" Create the factory architecture """
	machines = []
	path_delays = [random.randint(1,3) for r in range(num_machines)]
	for mach_id in range(num_machines):
		m = Machine(env, mach_id, worktime, num_stations, path_delays[mach_id])
		machines.append(m)
		print ("Added machine %u" % mach_id)

	# Create more things while the simulation is running
	for thing_id in range(num_things):
		print('Thing %u generated' % thing_id)
		#yield env.timeout(random.randint(t_inter-2, t_inter+2))
		yield env.timeout(t_inter)
		env.process(thing(env, thing_id, machines))


RANDOM_SEED = 42
NUM_THINGS = 100
NUM_MACHINES = 4  # number of machines
NUM_STATIONS = 2  # Number of stations per machine
WORKTIME = 5      # Minutes at machine
T_INTER = 2       # Create a thing every NN minutes
SIM_TIME = 4000     # Simulation time in minutes

if __name__ == "__main__":
	
	print('Simple Factory')
	random.seed(RANDOM_SEED)  # This helps reproducing the results

	# Create an environment and start the setup process
	env = simpy.Environment()
	env.process(setup(env, NUM_THINGS, NUM_MACHINES, NUM_STATIONS, WORKTIME, T_INTER))

	# Execute simulation
	env.run(until=SIM_TIME)
