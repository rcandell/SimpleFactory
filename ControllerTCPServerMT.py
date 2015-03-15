#! /usr/bin/python
# Author: Rick Candell (rick.candell@nist.gov)
# Organization: National Institute of Standards and Technology
#               U.S. Department of Commerce
# License: Public Domain


from socket import *
import threading

def handler(clientsocket, clientaddr):
    print("Accepted connection from: ", clientaddr)

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
                print(data)
                #msg = "You sent me: %s" % data
                #clientsocket.send(msg.encode('utf-8'))
    clientsocket.close()

if __name__ == "__main__":

    host = 'localhost'
    port = 9999
    buf = 1024

    addr = (host, port)

    serversocket = socket(AF_INET, SOCK_STREAM)

    serversocket.bind(addr)

    serversocket.listen(200)

    while 1:
        print("Server is listening for connections\n")

        clientsocket, clientaddr = serversocket.accept()
        #threading.start_new_thread(handler, (clientsocket, clientaddr))
        threading.Thread(target=handler,args=(clientsocket, clientaddr)).start()

    # close the socket before exiting
    serversocket.close()
