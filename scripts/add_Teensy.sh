#! /bin/bash
# Opens location for adding Teensy to udev rules in Linux

message = \'Password required to modify the udev rules\'
gnome-terminal -e '\
   sh -c "echo \"Password required to modify the udev rules\" && \
   sudo geany /etc/udev/rules.d/99-usb-serial.rules && \
   echo \"Refreshing udev rules...\" && \
   sudo udevadm trigger && \
   echo -e \"Complete! New Teensy should appear in this list:\" && \
   ls -l /dev/teensy** && \
   sleep 5s"'
