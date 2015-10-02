#!/bin/bash
RULE_PATH=/etc/udev/rules.d/digibase.rules

if [ -e $RULE_PATH ]
then
    read -p "Digibase rules already exist, overwrite? [y/N]: "
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        sudo rm $RULE_PATH
    else
        exit
    fi
fi

echo "Writing udev rules to ${RULE_PATH}..."
echo '# Set world read/write permissions for the Digibase' | sudo tee --append $RULE_PATH
echo 'SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTR{idVendor}=="0a2d", ATTR{idProduct}=="001f", MODE="0666"' | sudo tee --append $RULE_PATH

echo "Reloading udev rules..."
sudo udevadm control --reload
