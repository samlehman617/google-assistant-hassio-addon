#!/bin/bash

# Connect to device
echo -e "connect $1" | bluetoothctl
echo -e "trust $1" | bluetoothctl

# Change bluetooth device in sound config
search="00:00:00:00:00:00"
sed 's/$search/$1/g' .asoundrc

# Save a copy to /etc/asound.conf & prevent being overwritten
sudo cp /.asoundrc /etc/asound.conf
sudo cp /.asoundrc ~/.asoundrc
chmod a-w /.asoundrc
