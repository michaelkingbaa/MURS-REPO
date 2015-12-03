#!/bin/bash

INSTALLER_PATH=/vagrant/installers
FLYCAPTURE_ARCHIVE=flycapture2-2.8.3.1-amd64-pkg.tgz
FLYCAPTURE_INSTALLER_PATH=flycapture2-2.8.3.1-amd64
FLYCAPTURE_INSTALL_SCRIPT=install_flycapture.sh
FLYCAPTURE_SDK_PATH=/usr/src/flycapture

CUR_PATH=`pwd`

if [ ! -d ${FLYCAPTURE_SDK_PATH} ]; then
    echo "FlyCapture not found, installing dependencies..."
    sudo apt-get install -y libraw1394-11 libgtkmm-2.4-1c2a libglademm-2.4-1c2a libgtkglextmm-x11-1.2-dev libgtkglextmm-x11-1.2 libusb-1.0-0
    
    cd ${INSTALLER_PATH}
    if [ ! -d ${FLYCAPTURE_INSTALLER_PATH} ]; then
        if [ ! -e ${FLYCAPTURE_ARCHIVE} ]; then
            echo "Missing FlyCapture install tarball!"
            exit
        fi
        tar xzvf ${FLYCAPTURE_ARCHIVE}
    fi
    cd ${FLYCAPTURE_INSTALLER_PATH}
    echo "********************************************************************************"
    echo "*** Installing Flycapture software - when prompted for a user, use 'vagrant' ***"
    echo "*** Answer yes to all prompts                                                ***"
    echo "********************************************************************************"
    sudo sh ${FLYCAPTURE_INSTALL_SCRIPT}
else
    echo "FlyCapture already installed!"
fi

cd ${CUR_PATH}