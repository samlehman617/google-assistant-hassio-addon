#!/bin/bash

echo -e "connect $1" | bluetoothctl
echo -e "trust $1" | bluetoothctl

# Save a copy to /etc/asound.conf & prevent being overwritten
sudo cp /.asoundrc /etc/asound.conf
chmod a-w /.asoundrc
