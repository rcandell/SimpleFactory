#! python
# Author: Rick Candell (rick.candell@nist.gov)
# Organization: National Institute of Standards and Technology
#               U.S. Department of Commerce
# License: Public Domain


import socketserver

class ControllerTCPHandler(socketserver.StreamRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        
        # read the sensor message
        self.data = self.rfile.readline().strip()
        print ("%s wrote:" % self.client_address[0])
        print (self.data.decode('utf-8'))        

        # log the sensor message

        # write the response message
        self.wfile.write(self.data.upper())

if __name__ == "__main__":

    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = socketserver.TCPServer((HOST, PORT), ControllerTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()

    