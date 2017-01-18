#/bin/sh

sudo ifconfig wlan0 10.20.0.101/16 up
sudo ifconfig wlan1 10.20.0.102/16 up
sudo ifconfig wlan2 10.20.0.103/16 up
sudo ifconfig wlan3 10.20.0.104/16 up

ifconfig -a
