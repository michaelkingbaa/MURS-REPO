#!/bin/bash

# This updates GRUB to set the usbfs memory size at boot time

if grep -q usbcore.usbfs_memory_mb=1000 /etc/default/grub; then
    echo "Already updated."
else
    echo "Not in file, updating..."
    sudo sed -i 's/\(GRUB_CMDLINE_LINUX_DEFAULT=\)"\([^"]*\)"/\1"\2 usbcore.usbfs_memory_mb=1000"/' /etc/default/grub
    sudo update-grub
    echo "Done."
fi