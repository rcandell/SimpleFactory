#! python
# Author: Rick Candell (rick.candell@nist.gov)
# Organization: National Institute of Standards and Technology
#               U.S. Department of Commerce
# License: Public Domain

import random
import simpy
import socket
import sys
from enum import Enum
import sfutils 
import logging
import threading

class EventType(Enum):
	MACHINE_CREATED = 10
	MACHINE_WORK = 11
	THING_CREATED = 20
	THING_ENTER_MACH = 21
	THING_EXIT_MACH = 22
	THING_TRAVEL = 23
	PRODUCT_STORED = 50
	DIAGNOSTICS = 100


class SensorTCPProxy(threading.Thread):

	def __init__(self, host, port):
		self.seqnum = 0
		self.host = host
		self.port = port
		self.sock = 0
		self.connect()

	def connect(self):
		try:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.connect((self.host, self.port))
		except socket.error as e:
			print(e)
			sys.exit(1)

	def send(self, payload):
		self.seqnum += 1
		data = payload + " " + str(self.seqnum)
		try:
			self.sock.sendall(bytes(data + "\n", 'UTF-8'))
		    # Receive data from the server and shut down
			#received = self.sock.recv(1024)			
		except socket.error as e:
		    self.sock.close()
		    print(e)
		    print("Reconnecting")
		    self.connect()

		except socket.timeout as ex:
			logging.info("socket connection timeout")
			logging.info(ex)	

	def close():
		self.sock.close()

class Rail(object):
	""" A Rail represents the delay between to machine stations """
	def __init__(self, env, t_delay):
		self.env = env
		self.t_delay = t_delay
		self.rail = simpy.Resource(env,1) # one path out from machine

	def travel(self, thing_id):
		
		# TODO: Place optical sensor reading here TCP

		yield self.env.timeout(self.t_delay)



class Machine(object):
	""" Machines do work on Thing objects """
	def __init__(self, env, mach_id, worktime, num_stations, rail_delay, tcp_host, tcp_port):
		self.env = env
		self.mach_id = mach_id
		self.worktime = worktime
		self.station = simpy.Resource(env, num_stations)
		self.rail = Rail(env, rail_delay)
		self.tcpclient = SensorTCPProxy(tcp_host, tcp_port)

	def work(self, thing_id):

		# TODO: Place machine sensor reading here TCP
		self.tcpclient.send("Machine: " + str(self.mach_id) + " Thing: " + str(thing_id) + " working")

		# TODO:  Wait for command from controller to start work TCP

		yield self.env.timeout(self.worktime)
		sfutils.loginfo(EventType.MACHINE_WORK, self.env, self.mach_id, thing_id, "machining work completed")
		#print("Machine %u completes work on Thing %u" % (self.mach_id, thing_id))

def thing(env, thing_id, machines, output_store):
	""" A thing goes to each machine and requests work to be done.
		Work is done and thing leaves to never come back """
	for mach in machines:
		with mach.station.request() as station_request:
			yield station_request
			sfutils.loginfo(EventType.THING_ENTER_MACH, env, mach.mach_id, thing_id, "thing enters machine")
			yield env.process(mach.work(thing_id))
			sfutils.loginfo(EventType.THING_EXIT_MACH, env, mach.mach_id, thing_id, "thing exits machine")
			with mach.rail.rail.request() as rail_request:
				yield rail_request
				sfutils.loginfo(EventType.THING_TRAVEL, env, mach.mach_id, thing_id, "thing in transit")
				yield env.process(mach.rail.travel(thing_id))
	sfutils.loginfo(EventType.PRODUCT_STORED, env, -1, thing_id, "thing stored as product")
	output_store.put(1)
	sfutils.loginfo(EventType.DIAGNOSTICS, env, -1, -1, "number of products " + str(output_store.level))

def setup(env, num_things, num_machines, num_stations, worktime, t_inter, tcp_host, tcp_port):
	""" Create the factory architecture """
	machines = []
	rail_delays = [random.randint(1,3) for r in range(num_machines)]
	for mach_id in range(num_machines):
		m = Machine(env, mach_id, worktime, num_stations, rail_delays[mach_id], tcp_host, tcp_port)
		machines.append(m)
		print ("Added machine %u" % mach_id)

	# create the storage bin for product output
	output_store = simpy.resources.container.Container(env, capacity=10000)

	# Create more things while the simulation is running
	thing_id = 0
	while True:
		sfutils.loginfo(EventType.THING_CREATED, env, -1, thing_id, "thing created")
		#yield env.timeout(random.randint(t_inter-2, t_inter+2))
		yield env.timeout(t_inter)
		env.process(thing(env, thing_id, machines, output_store))
		thing_id += 1


RANDOM_SEED = 42
NUM_THINGS = 2**32
NUM_MACHINES = 4  # number of machines
NUM_STATIONS = 1  # Number of stations per machine
WORKTIME = 5      # Minutes at machine
T_INTER = 2       # Create a thing every NN minutes
SIM_TIME = 400     # Simulation time in minutes

if __name__ == "__main__":

	HOST, PORT = "localhost", 9999

	logging.basicConfig(filename='sim.log', level=logging.INFO)
	
	print('Simple Factory')
	random.seed(RANDOM_SEED)  # This helps reproducing the results

	# Create an environment and start the setup process
	env = simpy.Environment()
	env.process(setup(env, NUM_THINGS, NUM_MACHINES, NUM_STATIONS, WORKTIME, T_INTER, HOST, PORT))

	# Execute simulation
	env.run(until=SIM_TIME)


