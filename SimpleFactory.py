#! python
# Author: Rick Candell (rick.candell@nist.gov)
# Organization: National Institute of Standards and Technology
#               U.S. Department of Commerce
# License: Public Domain

import time
import random
import simpy
import socket
import sys
from enum import Enum
import sfutils 
import logging
import threading
import json
from builtins import staticmethod

class EventType(Enum):

	FACTORY_STARTED = 1
	MACHINE_CREATED = 10
	MACHINE_WORK = 11
	PART_CREATED = 20
	PART_ENTER_MACH = 21
	PART_EXIT_MACH = 22
	PART_TRAVEL = 23
	PRODUCT_STORED = 50
	DIAGNOSTICS = 100

class SensorMessage(object):
	def __init__(self, part_id=-1, mach_id=-1, rail_id=-1, msg_str="n/a"):
		self.t = time.clock()
		self.mach_id = mach_id
		self.rail_id = rail_id
		self.part_id = part_id
		self.msg_str = msg_str

	def to_str(self):
		msg_d = {
			"time":self.t,
			"machine":self.mach_id,
			"rail":self.rail_id,
			"part":self.part_id,
			"msg":self.msg_str,
			 }
		msg = json.dumps(msg_d)
		return msg

class SensorTCPProxy(threading.Thread):

	BIND_ADDRS = [None]

	def __init__(self, env, host='localhost', port=9999, bind_addr=('localhost',0)):
		self.env = env		
		self.seqnum = 0
		self.host = host
		self.port = port
		self.bind_addr = bind_addr
		self.sock = 0
		self.connect()

	@staticmethod
	def add_bind_addrs(l_bind_addrs):
		pass

	def connect(self):
		try:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.bind(self.bind_addr)
			sfutils.logstr("socket bind to " + str(self.bind_addr))
			self.sock.connect((self.host, self.port))
			# print("connected")
		except socket.error as e:
			print(e)
			sys.exit(1)

	def send_msg(self, sensor_msg):
		payload = sensor_msg.to_str()
		self.send(payload)
# 		print("Wireless channel request. Cacpacity: %d"%WirelessChannel.capacity)
# 		with WirelessChannel.request() as ch_req:
# 			print("wireless channel acquired")
# 			self.send(payload)
# 			yield ch_req        


	def send(self, payload):
		#WirelessChannel.acquire_channel()
		self.seqnum += 1
		data = str(self.seqnum) + "\t" + payload
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

	def close(self):
		self.sock.close()

class Rail(object):
	""" A Rail represents the delay between to machine stations """
	def __init__(self, env, mach_id, t_delay, tcp_host, tcp_port):
		self.env = env
		self.t_delay = t_delay
		self.mach_id = mach_id
		self.rail = simpy.Resource(env,1) # one path out from machine
		self.tcpclient = SensorTCPProxy(self.env, tcp_host, tcp_port)

	def travel(self, part_id):
		
		# optical prximity sensor reading
		msg = SensorMessage(part_id=part_id, mach_id=self.mach_id, rail_id=0, msg_str="part in transit")
		self.tcpclient.send_msg(msg)	

		# wait for the transit delay to occur
		yield self.env.timeout(self.t_delay)


class Machine(object):
	""" Machines do work on Part objects """
	def __init__(self, env, mach_id, worktime, num_stations, rail_delay, tcp_host, tcp_port):
		self.env = env
		self.mach_id = mach_id
		self.worktime = worktime
		self.station = simpy.Resource(env, num_stations)
		self.rail = Rail(env, mach_id, rail_delay, tcp_host, tcp_port)
		self.tcpclient = SensorTCPProxy(self.env, tcp_host, tcp_port)

	def work(self, part_id):

		# TODO: Place machine sensor reading here TCP
		msg = SensorMessage(part_id=part_id, mach_id=self.mach_id, rail_id=0, msg_str="machine working")
		self.tcpclient.send_msg(msg)

		# TODO:  Wait for command from controller to start work TCP
		# left blank for now -- controller to be added later
		
		# do the work
		sfutils.loginfo(EventType.MACHINE_WORK, env, self.mach_id, part_id, "machine working")
		work_done = self.env.timeout(self.worktime)

		# finish the machining work
		yield work_done

# generator function for a part
def Part(env, part_id, machines, output_store):
	""" A part goes to each machine and requests work to be done.
		Work is done and part leaves to never come back """
	for mach in machines:
		with mach.station.request() as station_request:
			yield station_request
			sfutils.loginfo(EventType.PART_ENTER_MACH, env, mach.mach_id, part_id, "part enters machine")
			yield env.process(mach.work(part_id))
			sfutils.loginfo(EventType.PART_EXIT_MACH, env, mach.mach_id, part_id, "part exits machine")
			with mach.rail.rail.request() as rail_request:
				yield rail_request
				sfutils.loginfo(EventType.PART_TRAVEL, env, mach.mach_id, part_id, "part in transit")
				yield env.process(mach.rail.travel(part_id))
	
	# store the product
	sfutils.loginfo(EventType.PRODUCT_STORED, env, -1, part_id, "part stored as product")
	output_store.put(1)

	# tally the number of products in log file
	sfutils.loginfo(EventType.DIAGNOSTICS, env, -1, -1, "number of products " + str(output_store.level))


class Factory(object):

	def __init__(self, num_parts, num_machines, num_stations, worktime, t_inter, tcp_host, tcp_port, output_store_sz=10000):

		# parameters
		self.num_parts = num_parts
		self.num_machines = num_machines
		self.num_stations = num_stations
		self.worktime = worktime
		self.t_inter = t_inter
		self.tcp_host = tcp_host
		self.tcp_port = tcp_port
		self.output_store_sz = output_store_sz

	def run(self, env):
		sfutils.loginfo(EventType.FACTORY_STARTED, env, -1, -1, "factory starting")		
		env.process(self.setup(env))

	def setup(self, env):
		""" Create the factory architecture """
		machines = []
		rail_delays = [random.randint(1,3) for r in range(self.num_machines)]
		for mach_id in range(self.num_machines):
			m = Machine(env, mach_id, self.worktime, self.num_stations, rail_delays[mach_id], self.tcp_host, self.tcp_port)
			machines.append(m)
			# sfutils.logstr("Added machine %u" % mach_id)

		# create the storage bin for product output
		output_store = simpy.resources.container.Container(env, capacity=self.output_store_sz)
		sfutils.loginfo(EventType.PART_CREATED, env, -1, -1, "output storage container created with size %d"%output_store.capacity)

		# Create more parts while the simulation is running
		part_id = 0
		while True:
					
			# wait until the next part is ready (basic delay)
			#yield env.timeout(random.randint(t_inter-2, t_inter+2))
			yield env.timeout(self.t_inter)

			# produce new part on the line
			if part_id < self.num_parts:
				env.process(Part(env, part_id, machines, output_store))
				sfutils.loginfo(EventType.PART_CREATED, env, -1, part_id, "part created")

				# increment to next part number
				part_id += 1		
			else:
				return


def init_bind_addrs():
	SensorTCPProxy.BIND_ADDRS.append(('127.0.0.1',0))

if __name__ == "__main__":

	# run in real-time
	RUN_RT = True
	SIM_RT_FACTOR = 1.0 	# 
	SIM_TIME = 400     		# Simulation time in minutes	

	# model parameters
	RANDOM_SEED = 42
	NUM_PARTS = 10E6
	NUM_MACHINES = 4  # number of machines
	NUM_STATIONS = 1  # Number of stations per machine
	WORKTIME = 5      # seconds at each machine
	T_INTER = 2       # Create a part every NN minutes

	HOST, PORT = "localhost", 9999

	logging.basicConfig(filename='sf_plant.log', level=logging.INFO)

	print('Simple Factory')
	random.seed(RANDOM_SEED)  # This helps reproducing the results

	# Create an environment and start the setup process
	if RUN_RT:
		env = simpy.rt.RealtimeEnvironment(initial_time=0, factor=SIM_RT_FACTOR, strict=True)
	else:
		env = simpy.Environment()

	# create the wireless channel with N available channels
	global WirelessChannel
	WirelessChannel = simpy.Resource(env,1)

	# create the factory
	# env.process(setup(env, NUM_THINGS, NUM_MACHINES, NUM_STATIONS, WORKTIME, T_INTER, HOST, PORT))
	factory = Factory(NUM_PARTS, NUM_MACHINES, NUM_STATIONS, WORKTIME, T_INTER, HOST, PORT)
	factory.run(env)
	# env.process(setup(env, NUM_THINGS, NUM_MACHINES, NUM_STATIONS, WORKTIME, T_INTER, HOST, PORT))

	# Execute simulation
	env.run(until=SIM_TIME)


