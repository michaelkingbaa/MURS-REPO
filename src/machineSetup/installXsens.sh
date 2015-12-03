#!/bin/bash

INSTALLER_PATH=/vagrant/installers
XSENS_ARCHIVE=MT_Software_Suite_Linux_4.3.tar.gz
XSENS_DOWNLOAD_URL=https://www.xsens.com/download/MT/4.3/MT_Software_Suite_Linux_4.3.tar.gz
XSENS_INSTALLER_PATH=MT_Software_Suite_Linux_4.3
XSENS_INSTALL_SCRIPT=mtsdk_linux_4.3.sh
XSENS_SDK_PATH=/usr/local/xsens

CUR_PATH=`pwd`

# Install SDK
if [ ! -e ${XSENS_SDK_PATH} ]; then
    echo "xSens SDK not found, installing dependencies..."
    # SDK requirements
    sudo apt-get install -y realpath sharutils liblapack3
    # Firmware updater requirements
    sudo apt-get install -y libssh2-1

    cd ${INSTALLER_PATH}
    if [ ! -d ${XSENS_INSTALLER_PATH} ]; then
        if [ ! -e $XSENS_ARCHIVE ]; then
            echo "Downloading SDK"
            wget ${XSENS_DOWNLOAD_URL}
        fi
        tar xzvf ${XSENS_ARCHIVE}
    fi
    cd ${XSENS_INSTALLER_PATH}
    echo "*******************************************************"
    echo "*** Installing xSens SDK - use the default location ***"
    echo "*******************************************************"
    sudo ./${XSENS_INSTALL_SCRIPT}

    echo "Run setXsensPermissions.sh to set the udev rule."
else
    echo "xSens SDK already installed!"
fi

cd ${CUR_PATH}
