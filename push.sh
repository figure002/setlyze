#!/bin/bash

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

notify-send "SETLyze" "Pushing to GiMaRIS central server..." -i gtk-dialog-info -u critical
echo "Pushing to GiMaRIS central server..."

# Mount samba share
mount -t smbfs -o username=student,password=Student123 //192.168.44.80/public/ /mnt/smbshare/

# Push to central server
bzr push /mnt/smbshare/Studenten_projecten/Serrano/setlyze/

if [ $? -eq 0 ]; then
	notify-send "SETLyze" "push: success" -i gtk-dialog-info -u critical
else
	notify-send "SETLyze" "push: error" -i dialog-warning -u critical
fi

# Unmount samba share
umount /mnt/smbshare/
