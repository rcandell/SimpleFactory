#! /usr/bin/python
# Author: Rick Candell (rick.candell@nist.gov)
# Organization: National Institute of Standards and Technology
#               U.S. Department of Commerce
# License: Public Domain


import sfutils
import socket
import threading

def handler(clientsocket, clientaddr):
    sfutils.logstr("Accepted connection")
    sfutils.logstr(str(clientsocket)) 
    
    while 1:
        try:
            data = clientsocket.recv(1024)
        except Exception as e:
            print(e)
        finally:
            if not data:
                break
            else:
                data = data.decode('utf-8')
                data = data.replace('\n', '')
                sfutils.logstrjson(data)
    
    sfutils.logstr("shutting down socket")
    sfutils.logstr(clientsocket)            
    clientsocket.shutdown(socket.SHUT_RDWR)
    clientsocket.close()

if __name__ == "__main__":
    
    # initialize the logger
    sfutils.init_logging('sf_server.log', sfutils.logging.INFO)    

    host = 'localhost'
    port = 9999
    buf = 1024

    addr = (host, port)

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

