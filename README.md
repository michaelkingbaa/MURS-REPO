# DNDO MURS - Mobile Urban Radiation Search

## Setting up the Vagrant VMs
### The Vagrantfile defines two VMs:
1. 'rad' for the radiation detection system
2. 'context' for the contextual sensor system

### There are some differences in vagrant usage with a multi machine configuration that should be noted
1. Standard vagrant commands (up, halt, destroy, etc.) will apply to both machines
2. To perform a vagrant command on a specific machine, append the machine name after the command, e.g. `vagrant up rad`
3. `vagrant ssh` doesn't work, you must specify the machine, e.g. `vagrant ssh rad`

### Other notes:
1. Both VMs map the path /vagrant to the murs repo folder on the host

### Prerequsites - VirtualBox > 5.0 and Vagrant > 1.7.3
* VirtualBox
  * Download and install both the platform package and the Extension Pack from [here](https://www.virtualbox.org/wiki/Downloads)
  * Alternately, on Mac OSX using homebrew cask:
    * `brew update && brew cask install virtualbox && brew cask install virtualbox-extension-pack`

* Vagrant
  * Download and install from [here](http://www.vagrantup.com/downloads)
  * Alternately, on Mac OSX using homebrew cask:
    * `brew update && brew cask install vagrant`

### Building the rad VM
1. Build the VM - from the root of the murs repo
  * `vagrant up rad`
2. SSH into the VM
  * `vagrant ssh rad`

### Building the contextual VM
1. Build the VM - from the root of the murs repo
  * `vagrant up context`
2. SSH into the VM
  * `vagrant ssh context`
3. Install the Point Grey software
  * `source /vagrant/src/machineSetup/installFlyCapture.sh`
    * Yes for all prompts, use 'vagrant' for the user to be added to the udev rule group
4. Restart the VM
  * `exit`
  * `vagrant halt context`
  * `vagrant up context`

VM GUI login - user: vagrant, pw: vagrant

