# SimpleFactory
This is a simple factory simulation created with the PySim discrete event engine.  The code here models a single line of factory machines that operate on materials (or machine parts).  This simulator is used for the development of WiFi-based wireless test scenarios of interest to industrial users.

# Operation
The code is composed of the following items:
* Factory - modeled as a python generator function.  This is the top level containment object.
* Machines - modeled as a python class with as a generator function to perform work
* Rails = modeled as a python class and used to convey thing objects between machines
* Things - modeled as a python generator function
* Sensors - modeled as TC/IP client proxies

