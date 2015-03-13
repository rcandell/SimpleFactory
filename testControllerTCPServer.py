#! python
# Author: Rick Candell (rick.candell@nist.gov)
# Organization: National Institute of Standards and Technology
#               U.S. Department of Commerce
# License: Public Domain


import socket
import sys

HOST, PORT = "localhost", 9999
data = " ".join(sys.argv[1:])

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    print ("Sending " + data)
    sock.sendall(bytes(data + "\n", 'UTF-8'))

    # Receive data from the server and shut down
    received = str(sock.recv(1024), "utf-8")
    
finally:
    sock.close()

print ("Sent:     %s" % data)
print ("Received: %s" % received)
