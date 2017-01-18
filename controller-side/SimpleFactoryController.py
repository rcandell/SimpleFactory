#! /usr/bin/python
# Author: Rick Candell (rick.candell@nist.gov)
# Organization: National Institute of Standards and Technology
#               U.S. Department of Commerce
# License: Public Domain


import sfutils
import socket
import threading
from SimpleFactoryConfiguration import *

def handler(clientsocket, clientaddr):
    sfutils.logstr("Accepted connection")
    sfutils.logstr(str(clientsocket))
    
    while 1:
        try:
            data = None
            data = clientsocket.recv(1024)
            if not data:
                break
        except Exception as e:            
            print(e)
        finally:
            if data is None:
                break
            else:
                data = data.decode('utf-8')
                data = data.replace('\n', '')
                sfutils.logstrtabdelim(data)
    
    sfutils.logstr("shutting down socket")
    sfutils.logstr(str(clientsocket))            
    clientsocket.shutdown(socket.SHUT_RDWR)
    clientsocket.close()

if __name__ == "__main__":
    
	# initialize the logger
	sfutils.init_logging('sf_server.log', sfutils.logging.INFO)    

	sfc = SimpleFactoryConfiguration()
	host = '10.10.0.100'
	port = 19999
	buf = 1024

	#print( "Server address is: " + host + ":" + port   )
	addr = sfc.server_addr #(host, port)
	print( "Server address is: " + addr[0] + ":" + str(addr[1])   )

	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(addr)

	serversocket.listen(128)
	print("Server is listening for connections\n")

	while 1:
		clientsocket, clientaddr = serversocket.accept()
		threading.Thread(target=handler,args=(clientsocket, clientaddr)).start()

	# close the socket before exiting
	serversocket.shutdown(socket.SHUT_RDWR)
	serversocket.close()

