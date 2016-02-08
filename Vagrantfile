# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  # Download an Ubuntu 14.04 box with the desktop GUI
  config.vm.box = "box-cutter/ubuntu1404-desktop"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  #config.vm.synced_folder ".", "/murs"

  def usbfilter_exists(machine_name, vendor_id, product_id)
    #
    # Determine if a usbfilter with the provided Vendor/Product ID combination
    # already exists on this VM.
    #
    # TODO: Use a more reliable way of retrieving this information.
    #
    # NOTE: The "machinereadable" output for usbfilters is more
    #       complicated to work with (due to variable names including
    #       the numeric filter index) so we don't use it here.
    #
    machine_id_filepath = ".vagrant/machines/" + machine_name + "/virtualbox/id"

    if not File.exists? machine_id_filepath
      # VM hasn't been created yet.
      return false
    end

    vm_info = `VBoxManage showvminfo $(<#{machine_id_filepath})`
    filter_match = "VendorId:         #{vendor_id}\nProductId:        #{product_id}\n"
    return vm_info.include? filter_match
  end

  def better_usbfilter_add(vb, machine_name, vendor_id, product_id, filter_name)
    #
    # This is a workaround for the fact VirtualBox doesn't provide
    # a way for preventing duplicate USB filters from being added.
    #
    # TODO: Implement this in a way that it doesn't get run multiple
    #       times on each Vagrantfile parsing.
    #
    if not usbfilter_exists(machine_name, vendor_id, product_id)
      vb.customize ["usbfilter", "add", "0",
                    "--target", :id,
                    "--name", filter_name,
                    "--vendorid", vendor_id,
                    "--productid", product_id
                    ]
    end
  end

  # common vm configuration
  config.vm.provision "shell", inline: <<-SHELL
    groupadd -f murs
    usermod -g murs vagrant    
  SHELL

  # rad VM configuration
  config.vm.define "rad" do |rad|
    rad.vm.hostname = "rad"
    rad.vm.provider "virtualbox" do |vb|
      # Display the VirtualBox GUI when booting the machine
      vb.gui = true

      vb.name = "murs_rad"
    
      # Customize the amount of memory on the VM:
      vb.memory = 2048
      vb.cpus = 2
      vb.customize ["modifyvm", :id, "--vram", 64]
      vb.customize ["modifyvm", :id, "--accelerate3d", "on"]
    end
    rad.vm.provision "shell", inline: <<-SHELL
      sudo apt-get update
    SHELL
  end

  # context VM configuration
  config.vm.define "context" do |context|
    context.vm.hostname = "context"
    context.vm.provider "virtualbox" do |vb|
      # Display the VirtualBox GUI when booting the machine
      vb.gui = true

      vb.name = "murs_context"
    
      # Customize the amount of memory on the VM:
      vb.memory = 2048
      vb.cpus = 2
      vb.customize ["modifyvm", :id, "--vram", 64]
      vb.customize ["modifyvm", :id, "--accelerate3d", "on"]

      # Enable USB
      vb.customize ["modifyvm", :id, "--usb", "on"]
      # Enable USB3
      vb.customize ["modifyvm", :id, "--usbxhci", "on"]
      # Add a USB filter for the Point Grey Grasshopper3 Camera
      better_usbfilter_add(vb, context.vm.hostname, "1e10", "3300", "Point Grey Grasshopper3 Camera")
      # Add a USB filter for the xSens GPS/INS
      better_usbfilter_add(vb, context.vm.hostname, "2639", "0017", "xSens MTi-G-700 GPS-INS")
      better_usbfilter_add(vb, context.vm.hostname, "0403", "d38b", "Xsens USB-serial converter")
    end
    context.vm.provision "shell", inline: <<-SHELL
      sudo apt-get update
      # Point Grey SDK requirements
      sudo apt-get install -y libraw1394-11 libgtkmm-2.4-1c2a libglademm-2.4-1c2a libgtkglextmm-x11-1.2-dev libgtkglextmm-x11-1.2 libusb-1.0-0
      source /vagrant/src/machineSetup/updateGrub.sh
      # xSens SDK requirements
      sudo apt-get install -y realpath sharutils liblapack3
      # xSens firmware updater requirements
      sudo apt-get install -y libssh2-1

      # Add to dialout group to access xSens
      usermod -a -G dialout vagrant
    SHELL
  end


end
