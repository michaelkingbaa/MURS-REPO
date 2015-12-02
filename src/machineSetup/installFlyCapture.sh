#!/bin/bash

cd /vagrant/installers
tar xzvf flycapture2-2.8.3.1-amd64-pkg.tgz
cd flycapture2-2.8.3.1-amd64
echo "********************************************************************************"
echo "*** Installing Flycapture software - when prompted for a user, use 'vagrant' ***"
echo "*** Answer yes to all prompts                                                ***"
echo "********************************************************************************"
sudo sh install_flycapture.sh