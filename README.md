# DNDO MURS - Mobile Urban Radiation Search

## Setting up the Vagrant VM
This requires Vagrant and VirtualBox > 5.0!
Vagrant: http://www.vagrantup.com/downloads
Note that Vagrant must be > 1.7.3 in order to support VirtualBox 5
On Mac OSX using homebrew, instead of installing from a download, one can use:
brew update && brew cask install vagrant

VirtualBox: https://www.virtualbox.org/wiki/Downloads
For VirtualBox, you also need to install the Extension Pack

### Build the VM - from the root of the murs repo
1) vagrant up

### SSH into the VM
2) vagrant ssh

### Setup the usbfs memory size
3) source /vagrant/src/machineSetup/updateGrub.sh

### Install the Point Grey software
4) source /vagrant/src/machineSetp/installFlyCapture
    Yes for all prompts, use 'vagrant' for the user to be added to the udev rule group

### To add a USB device to the VM:
1) Shutdown the vm - vagrant halt
2) In the VirtualBox manager find murs_contextual_vm and select Settings
3) Select Ports from the top bar, then the USB tab.
4) Enable the USB controller then select USB 3.0
5) To the right of the Device Filters box, select the icon with a plus symbol
6) Select the device, e.g. Point Grey Grasshopper3
