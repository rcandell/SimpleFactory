#! python
# Author: Rick Candell (rick.candell@nist.gov)
# Organization: National Institute of Standards and Technology
#               U.S. Department of Commerce
# License: Public Domain

import time
import simpy
import socket
import sys
from enum import Enum
from builtins import staticmethod
import sfutils 
import logging
import threading
from SimpleFactoryConfiguration import *
from numpy import random
from queue import Queue

sfc = None

class EventType(Enum):

	# factory info
	FACTORY_STARTED = 1
	MACHINE_CREATED = 10
	
	# machine info
	MACHINE_WORK = 11
	MACHINE_DONE = 12
	
	# part info
	PART_ENTER_FACTORY = 20
	PART_ENTER_MACH = 21
	PART_EXIT_MACH = 22
	PART_TRAVEL = 23
	
	# product info
	PRODUCT_STORED = 50
	
	# diagnostic info
	DIAGNOSTICS = 100

class SensorMessage(object):
	
	SEQ_NUM = 0
	
	def __init__(self, part_id=None, mach_id=None, rail_id=None, msg_str="n/a"):
		self.t = (str(time.time()) + "000000")[:17]
		self.seq_num = self.next_seq_num()
		self.mach_id = mach_id
		self.rail_id = rail_id
		self.part_id = part_id
		self.msg_str = msg_str
		
	def next_seq_num(self):
		SensorMessage.SEQ_NUM += 1
		return SensorMessage.SEQ_NUM

	def to_str(self):
		msg_d = {
			"time":self.t,
			"seqnum":self.seq_num,
			"machine":self.mach_id,
			"rail":self.rail_id,
			"part":self.part_id,
			"msg":self.msg_str,
			 }
		msg = json.dumps(msg_d)
		return msg

class SensorTCPProxy(threading.Thread):

	BIND_ADDRS = [None]
	
	class NoBindAddress(Exception):
		pass

	def __init__(self, env, remote_addr=('localhost', 9999), bind_addr=None):
		threading.Thread.__init__(self,target=self.thread_worker, daemon=True)
		self.msg_queue = Queue(maxsize=10)
		self.env = env		
		self.seqnum = 0
		self.remote_addr = remote_addr
		self.thread_name = super(SensorTCPProxy,self).getName()
		
		if bind_addr == None:
			raise SensorTCPProxy.NoBindAddress()
		else:
			self.bind_addr = bind_addr
		self.sock = None
		self.connect()
		super(SensorTCPProxy,self).start()
		
	def __del__(self):
		self.disconnect()

	@staticmethod
	def add_bind_addrs(l_bind_addrs):
		pass

	def connect(self):
		try:
			#print("Remote addr: \n" + self.remote_addr[0] + "\n" + str(self.remote_addr[1]))
			#print("Bind addr: \n" + self.bind_addr[0] + "\n" + str(self.bind_addr[1]))	
			sfutils.logdebug(str(self.bind_addr) + " connecting to" + str(self.remote_addr))
			self.sock = socket.create_connection(self.remote_addr, 10, self.bind_addr)
			sfutils.logstr(str(self.bind_addr) + " connected to" + str(self.remote_addr))
		except socket.error as e:
			print(e)
			sys.exit(1)

	def send_msg(self, sensor_msg):
		payload = sensor_msg.to_str()
		self.send(payload) 


	def send(self, data):
		self.msg_queue.put(data)

	def thread_worker(self):
		while True:
			data = self.msg_queue.get()
			if data is None:
				break
			else:
				#sfutils.logdebug(self.bind_addr[0] + " current queue size = " + str(self.msg_queue.qsize()))
				try:
					#self.connect()
					self.sock.sendall(bytes(data + "\n", 'UTF-8'))
					sfutils.logstr(msg=data, screen=False)
					# Receive data from the server and shut down
					#received = self.sock.recv(1024)			
					#self.sock.close()
				except socket.error as ex:
					sfutils.logstr("socket error")
					logging.info(ex)	
					print(ex)
					self.sock.close()
					self.sock = None
					sfutils.logstr("reconnecting")
					self.connect()

				except socket.timeout as ex:
					logging.info("socket connection timer expired")
					logging.info(ex)	

				# indicate that the message is processed
				self.msg_queue.task_done()

	def disconnect(self):
		if self.sock != None:
			self.sock.shutdown(socket.SHUT_RDWR)
			self.sock.close()

class Rail(object):
	""" A Rail represents the delay between to machine stations """
	def __init__(self, env, mach_id, t_delay, remote_addr, bind_addr, tcpproxy=None):
		self.env = env
		self.t_delay = t_delay
		self.mach_id = mach_id
		self.railResource = simpy.Resource(env,1) # one path out from machine
		if tcpproxy == None:
			sfutils.logdebug("For machine " + str(self.mach_id) + " rail, creating tcp proxy")
			self.tcpproxy = SensorTCPProxy(self.env, remote_addr, bind_addr=bind_addr)
		else:
			sfutils.logdebug("For machine " + str(self.mach_id) + " rail, using machine tcp proxy")
			self.tcpproxy = tcpproxy

	def travel(self, part_id):
		
		# optical proximity sensor reading
		msg = SensorMessage(part_id=part_id, mach_id=self.mach_id, rail_id=0, msg_str="part in transit")
		self.tcpproxy.send_msg(msg)	

		# wait for the transit delay to occur
		yield self.env.timeout(self.t_delay)


class Machine(object):
	""" Machines do work on Part objects """
	def __init__(self, env, mach_id, worktime, num_stations, remote_addr, bind_addr=('127.0.0.1',0)):
		self.env = env
		self.mach_id = mach_id
		self.worktime = worktime
		self.num_parts = 0
		self.station = simpy.Resource(env, num_stations)
		sfutils.logdebug("For machine " + str(self.mach_id) + ", creating tcp proxy")
		self.tcpclient = SensorTCPProxy(self.env, remote_addr, bind_addr=bind_addr)
		self.rail = None

	def addRail(self, rail=None):
		self.rail = rail

	def part_enters(self, part_id):
		sfutils.loginfo(EventType.PART_ENTER_MACH, env, self.mach_id, part_id, "part entered machine")
		msg = SensorMessage(part_id=part_id, mach_id=self.mach_id, rail_id=0, msg_str="part entered machine")
		self.tcpclient.send_msg(msg)		

	def work(self, part_id):
		
		# calculate machine wait time for this iteration
		scale = 0.2*self.worktime # 20% of average work time for machine
		this_work_time = self.worktime + scale*(random.rand()-0.5) 

		# send msg that machine is working
		msg = SensorMessage(part_id=part_id, mach_id=self.mach_id, rail_id=0, msg_str="machine working")
		self.tcpclient.send_msg(msg)

		# TODO:  Wait for command from controller to start work TCP
		# left blank for now -- controller to be added later
		
		# do the work
		sfutils.loginfo(EventType.MACHINE_WORK, env, self.mach_id, part_id, "machine working")
		yield self.env.timeout(this_work_time)	

		# transmit that machine is done
		machine_done_str = "machine done" + \
			", work_time: " + str(this_work_time) + \
			", num_parts: " + str(self.num_parts)
		msg = SensorMessage(part_id=part_id, mach_id=self.mach_id, rail_id=0, msg_str=machine_done_str)
		self.tcpclient.send_msg(msg)
		sfutils.loginfo(EventType.MACHINE_DONE, env, self.mach_id, part_id, machine_done_str)

# generator function for a part
def Part(env, part_id, machines, output_store):
	""" A part goes to each machine and requests work to be done.
		Work is done and part leaves to never come back """
	for mach in machines:
		with mach.station.request() as station_request:
			
			yield station_request
			mach.part_enters(part_id)
			
			yield env.process(mach.work(part_id))
			sfutils.loginfo(EventType.PART_EXIT_MACH, env, mach.mach_id, part_id, "part exits machine")
			
			with mach.rail.railResource.request() as rail_request:
				
				yield rail_request
				sfutils.loginfo(EventType.PART_TRAVEL, env, mach.mach_id, part_id, "part in transit")
				
				yield env.process(mach.rail.travel(part_id))
	
	# store the product
	sfutils.loginfo(EventType.PRODUCT_STORED, env, None, part_id, "part stored as product")
	output_store.put(1)

	# tally the number of products in log file
	sfutils.loginfo(EventType.DIAGNOSTICS, env, None, None, "number of products " + str(output_store.level))


class Factory(object):

	def __init__(self, num_parts, num_machines, num_stations, worktime, t_inter, remote_addr, output_store_sz=10000):

		# parameters
		self.machines = []
		self.rails = []		
		self.num_parts = num_parts
		self.num_machines = num_machines
		self.num_stations = num_stations
		self.worktime = worktime
		self.t_inter = t_inter
		self.remote_addr = remote_addr
		self.output_store_sz = output_store_sz
		self.output_store = None
		
	def __str__(self, *args, **kwargs):
		return object.__str__(self, *args, **kwargs)

	def setup(self, env):

		""" Create the factory architecture """
		machine = []
		rail_delay = sfc.RAIL_DELAY

		for mach_id in range(0,4):
			machine = Machine(env, mach_id+1, self.worktime, self.num_stations, self.remote_addr, (sfc.client_addrs[mach_id],0))
			rail = Rail(env, machine.mach_id, rail_delay, self.remote_addr, (sfc.client_addrs[mach_id],0), tcpproxy=None)
			machine.addRail(rail)
			self.machines.append(machine)
			self.rails.append(rail)

		# create the storage bin for product output
		self.output_store = simpy.resources.container.Container(env, capacity=self.output_store_sz)
		sfutils.loginfo(EventType.PART_ENTER_FACTORY, env, None, None, "output storage container created with size %d"%self.output_store.capacity)

	def run(self, env):
		sfutils.loginfo(EventType.FACTORY_STARTED, env, None, None, "factory starting")		
		env.process(self.work(env))

	def work(self, env):
		# Create more parts while the simulation is running
		part_id = 0
		while part_id < self.num_parts:
			
			# calculate wait time between parts
			scale = 0.2*self.t_inter # 20% of average 
			this_inter = self.t_inter + scale*(random.rand()-0.5) 
			yield env.timeout(this_inter)

			# produce new part on the line
			env.process(Part(env, part_id, self.machines, self.output_store))
			sfutils.loginfo(EventType.PART_ENTER_FACTORY, env, None, part_id, "part created")

			# increment to next part number
			part_id += 1	
	


# def init_bind_addrs():
	# SensorTCPProxy.BIND_ADDRS.append(('127.0.0.1',0))

if __name__ == "__main__":

	print('Simple Factory')
	
	# network configuration
	sfc = SimpleFactoryConfiguration()

	# prepare random seed	
	RANDOM_SEED = sfc.RANDOM_SEED
	random.seed(RANDOM_SEED)
	
	# prepare the runtime parameters
	RUN_RT = sfc.RUN_RT
	SIM_RT_FACTOR = sfc.SIM_RT_FACTOR 	
	NUM_PARTS = sfc.NUM_PARTS
	NUM_MACHINES = sfc.NUM_MACHINES
	NUM_STATIONS = sfc.NUM_STATIONS
	WORKTIME = sfc.WORKTIME
	T_INTER = sfc.T_INTER
	REMOTE_ADDR = sfc.server_addr
	LOGGING_PATH = sfc.logging_path
	LOGGING_LEVEL = sfc.logging_level

	# configure the logging utility for the plant process
	if LOGGING_LEVEL == "DEBUG":
		sfutils.init_logging(fname=LOGGING_PATH, level=logging.DEBUG)	
	else:
		sfutils.init_logging(fname=LOGGING_PATH, level=logging.INFO)	

	# log header to log file
	sfutils.logheader()

	# Create an environment and start the setup process
	if RUN_RT:
		sfutils.logstr("attempting to run in real-time with wall clock")
		env = simpy.rt.RealtimeEnvironment(initial_time=0, factor=1, strict=False)
	else:
		env = simpy.Environment()

	# create the factory
	print(NUM_PARTS, NUM_MACHINES, NUM_STATIONS, WORKTIME, T_INTER, REMOTE_ADDR)
	factory = Factory(NUM_PARTS, NUM_MACHINES, NUM_STATIONS, WORKTIME, T_INTER, REMOTE_ADDR)
	factory.setup(env)
	factory.run(env)

	# Execute simulation
	env.run()