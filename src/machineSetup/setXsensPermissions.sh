#!/bin/bash
RULE_PATH=/etc/udev/rules.d/xsens.rules

if [ -e $RULE_PATH ]
then
    read -p "xSens rules already exist, overwrite? [y/N]: "
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        sudo rm $RULE_PATH
    else
        exit
    fi
fi

echo "Writing udev rules to ${RULE_PATH}..."
echo '# Set world read/write permissions for the xSens' | sudo tee --append $RULE_PATH
echo 'ATTRS{idVendor}=="2639", ATTRS{idProduct}=="0017", MODE="0664", GROUP="murs"' | sudo tee --append $RULE_PATH
echo 'SUBSYSTEM=="usb", GROUP="murs"' | sudo tee --append $RULE_PATH

echo "Reloading udev rules..."
sudo udevadm control --reload
