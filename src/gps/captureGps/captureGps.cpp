/* Copyright (c) Xsens Technologies B.V., 2006-2012. All rights reserved.

	  This source code is provided under the MT SDK Software License Agreement
and is intended for use only by Xsens Technologies BV and
	   those that have explicit written permission to use it from
	   Xsens Technologies BV.

	  THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
	   KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
	   IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
	   PARTICULAR PURPOSE.
 */

//--------------------------------------------------------------------------------
// Xsens device API example for an MTi / MTx / Mtmk4 device using the C++ API
//
//--------------------------------------------------------------------------------
#include <xsensdeviceapi.h> // The Xsens device API header
#include "serialkey.h"

#include <iostream>
#include <list>
#include <iomanip>
#include <stdexcept>

#include <xsens/xstime.h>
#include <xsens/xsmutex.h>

#include "conio.h" // for non ANSI _kbhit() and _getch()

//--------------------------------------------------------------------------------
// CallbackHandler is an object derived from XsCallback that can be attached to
// an XsDevice using the XsDevice::setCallbackHandler method.
// Various virtual methods which are automatically called by the XsDevice can be
// overridden (See XsCallback)
// Only the onPostProcess(...) method is overridden here. This method is called
// when a new data packet is available.
// Note that this method will be called from within the thread of the XsDevice so
// proper synchronisation is required.
// It is recommended to keep the implementation of these methods fast; therefore
// the only action here is to copy the packet to a queue where it can be
// retrieved later by the main thread to be displayed. All access to the queue is
// protected by a critical section because multiple threads are accessing it.
//--------------------------------------------------------------------------------
class CallbackHandler : public XsCallback
{
public:
	CallbackHandler(size_t maxBufferSize = 5) :
		m_maxNumberOfPacketsInBuffer(maxBufferSize),
		m_numberOfPacketsInBuffer(0)
	{
	}

	virtual ~CallbackHandler() throw()
	{
	}

	bool packetAvailable() const
	{
		XsMutexLocker lock(m_mutex);
		return m_numberOfPacketsInBuffer > 0;
	}

	XsDataPacket getNextPacket()
	{
		assert(packetAvailable());
		XsMutexLocker lock(m_mutex);
		XsDataPacket oldestPacket(m_packetBuffer.front());
		m_packetBuffer.pop_front();
		--m_numberOfPacketsInBuffer;
		return oldestPacket;
	}

protected:
	virtual void onDataAvailable(XsDevice*, const XsDataPacket* packet)
	{
		XsMutexLocker lock(m_mutex);
		assert(packet != 0);
		while (m_numberOfPacketsInBuffer >= m_maxNumberOfPacketsInBuffer)
		{
			(void)getNextPacket();
		}
		m_packetBuffer.push_back(*packet);
		++m_numberOfPacketsInBuffer;
		assert(m_numberOfPacketsInBuffer <= m_maxNumberOfPacketsInBuffer);
	}
private:
	mutable XsMutex m_mutex;

	size_t m_maxNumberOfPacketsInBuffer;
	size_t m_numberOfPacketsInBuffer;
	std::list<XsDataPacket> m_packetBuffer;
};

//--------------------------------------------------------------------------------
int main(void)
{
	if (!setSerialKey())
	{
		std::cout << "Invalid serial key." << std::endl;
		std::cout << "Press [ENTER] to continue." << std::endl; std::cin.get();
		return 1;
	}

	// Create XsControl object
	std::cout << "Creating XsControl object..." << std::endl;
	XsControl* control = XsControl::construct();
	assert(control != 0);

	try
	{
		// Scan for connected devices
		std::cout << "Scanning for devices..." << std::endl;
		XsPortInfoArray portInfoArray = XsScanner::scanPorts();

		// Find an MTi / MTx / MTmk4 device
		XsPortInfoArray::const_iterator mtPort = portInfoArray.begin();
		while (mtPort != portInfoArray.end() && !mtPort->deviceId().isMt9c() && !mtPort->deviceId().isMtMk4()) {++mtPort;}
		if (mtPort == portInfoArray.end())
		{
			throw std::runtime_error("No MTi / MTx / MTmk4 device found. Aborting.");
		}
		std::cout << "Found a device with id: " << mtPort->deviceId().toString().toStdString() << " @ port: " << mtPort->portName().toStdString() << ", baudrate: " << mtPort->baudrate() << std::endl;

		// Open the port with the detected device
		std::cout << "Opening port..." << std::endl;
		if (!control->openPort(mtPort->portName().toStdString(), mtPort->baudrate()))
		{
			throw std::runtime_error("Could not open port. Aborting.");
		}

		try
		{
			// Get the device object
			XsDevice* device = control->device(mtPort->deviceId());
			assert(device != 0);

			// Print information about detected MTi / MTx / MTmk4 device
			std::cout << "Device: " << device->productCode().toStdString() << " opened." << std::endl;

			// Create and attach callback handler to device
			CallbackHandler callback;
			device->addCallbackHandler(&callback);

			// Put the device in configuration mode
			std::cout << "Putting device into configuration mode..." << std::endl;
			if (!device->gotoConfig()) // Put the device into configuration mode before configuring the device
			{
				throw std::runtime_error("Could not put device into configuration mode. Aborting.");
			}

			// Configure the device. Note the differences between MTix and MTmk4
			std::cout << "Configuring the device..." << std::endl;
			if (device->deviceId().isMtMk4())
			{
				XsOutputConfigurationArray configArray;
				configArray.push_back(XsOutputConfiguration(XDI_PacketCounter, 10));
				configArray.push_back(XsOutputConfiguration(XDI_UtcTime, 10));
				configArray.push_back(XsOutputConfiguration(XDI_SampleTimeCoarse, 10));
				configArray.push_back(XsOutputConfiguration(XDI_SampleTimeFine, 10));

				configArray.push_back(XsOutputConfiguration(XDI_LatLon | XDI_SubFormatFp1632, 10));
				configArray.push_back(XsOutputConfiguration(XDI_AltitudeEllipsoid, 10));

				configArray.push_back(XsOutputConfiguration(XDI_Quaternion, 10));
				configArray.push_back(XsOutputConfiguration(XDI_VelocityXYZ, 10));

				configArray.push_back(XsOutputConfiguration(XDI_DeltaV, 10));
				configArray.push_back(XsOutputConfiguration(XDI_Acceleration, 10));
				configArray.push_back(XsOutputConfiguration(XDI_DeltaQ, 10));

				configArray.push_back(XsOutputConfiguration(XDI_GpsSol, 4));

				configArray.push_back(XsOutputConfiguration(XDI_MagneticField, 10));

				configArray.push_back(XsOutputConfiguration(XDI_BaroPressure, 10));
				configArray.push_back(XsOutputConfiguration(XDI_Temperature, 1));

				configArray.push_back(XsOutputConfiguration(XDI_StatusWord, 10));
				if (!device->setOutputConfiguration(configArray))
				{

					throw std::runtime_error("Could not configure MTmk4 device. Aborting.");
				}
			}
			else
			{
				throw std::runtime_error("Unknown device while configuring. Aborting.");
			}

			std::cout << "Configuring sync output..." << std::endl;
            if (device->deviceId().isMtMk4())
			{
				XsSyncSettingArray syncArray;
				// XsSyncLine line = XSL_Out1; // SyncOut 1
				XsSyncLine line = XSL_Bi1Out; // SyncOut 1
				XsSyncFunction function = XSF_IntervalTransitionMeasurement;
				XsSyncPolarity polarity = XSP_PositivePulse;
				uint32_t pulseWidth = 1000; // Microseconds
				int32_t offset = 0; // Microseconds
				uint16_t skipFirst = 0;
				uint16_t skipFactor = 399;	// 400Hz clock, results in 1Hz trigger out
				uint16_t clockPeriod = 0;	// Ignored
				uint8_t triggerOnce = 0;
				XsSyncSetting sync = XsSyncSetting(line, function, polarity, pulseWidth, offset, skipFirst, skipFactor, clockPeriod, triggerOnce);
				syncArray.push_back(sync);
				if (!device->setSyncSettings(syncArray))
				{

					throw std::runtime_error("Could not configure sync for MTmk4 device. Aborting.");
				}
			}
			else
			{
				throw std::runtime_error("Unknown device while configuring. Aborting.");
			}

			// Put the device in measurement mode
			std::cout << "Putting device into measurement mode..." << std::endl;
			if (!device->gotoMeasurement())
			{
				throw std::runtime_error("Could not put device into measurement mode. Aborting.");
			}

			std::cout << "\nMain loop (press any key to quit)" << std::endl;
			std::cout << std::string(79, '-') << std::endl;

			XsUtcTime utcTime;
			int utcFlag = -1;
			uint32_t status = 0;
			std::string statusString = std::string("------*");
			while (!_kbhit())
			{
				if (callback.packetAvailable())
				{
					// Retrieve a packet
					XsDataPacket packet = callback.getNextPacket();

					if (packet.containsUtcTime()) {
						utcTime = packet.utcTime();
						utcFlag = (int)utcTime.m_valid;
						// switch (utcTime.m_valid) {
						// 	case 0:
						// 		utcFlag = 'X';					// Indicates invalid, fresh data
						// 	case 1:
						// 		utcFlag = '1';	// Indicates valid, fresh data
						// 	case 2:
						// 		utcFlag = '2';	// Indicates valid, fresh data
						// 	case 3:
						// 		utcFlag = '3';	// Indicates valid, fresh data
						// 	case 4:
						// 		utcFlag = '4';	// Indicates valid, fresh data
						// 	default:
						// 		utcFlag = '?';	// Indicates valid, fresh data
						// }
					}

					std::cout << "\r"
					        << "UTC(" << utcFlag << "): " 
							<< std::setw(2) << std::setfill('0') << (int)utcTime.m_hour << ":" 
							<< std::setw(2) << std::setfill('0') <<(int)utcTime.m_minute << ":" 
							<< std::setw(2) << std::setfill('0') << (int)utcTime.m_second << "." 
							<< std::setw(3) << std::setfill('0') << utcTime.m_nano/1000000 << ", ";

					if (packet.containsStatus()) {
						status = packet.status();
						statusString = std::string("------+");
						if (status & 0x1) statusString[0] = 'S';	// Bit 0 - Selftest passed
						if (status & 0x2) statusString[1] = 'F';	// Bit 1 - Filter valid
						if (status & 0x4) statusString[2] = 'G';	// Bit 2 - GPS fixed
						if (status & 0x20) statusString[3] = 'Y';		// Bit 5 - Timestamp GPS synced
						if (status & 0x40) statusString[4] = 'Z';		// Bit 6 - Timestamp clock synced
						if (status & 0x100) std::cout << "CLIP ACC X! ";	// Bit 8
						if (status & 0x200) std::cout << "CLIP ACC Y! ";	// Bit 9
						if (status & 0x400) std::cout << "CLIP ACC Z! ";	// Bit 10
						if (status & 0x800) std::cout << "CLIP GYR X! ";	// Bit 11
						if (status & 0x1000) std::cout << "CLIP GYR Y! ";	// Bit 12
						if (status & 0x2000) std::cout << "CLIP GYR Z! ";	// Bit 13
						if (status & 0x4000) std::cout << "CLIP MAG X! ";	// Bit 14
						if (status & 0x8000) std::cout << "CLIP MAG Y! ";	// Bit 15
						if (status & 0x10000) std::cout << "CLIP MAG Z! ";	// Bit 16
						if (status & 0x80000) std::cout << '\n';		// Bit 19 - clipping on one or more sensors
						if (status & 0x400000) statusString[5] = 'O';	// Bit 22 - SyncOut marker
					}
					else {
						statusString[6] = '-';
					}

					std::cout << "Status: " << statusString << ", ";
					// Get the quaternion data
					XsQuaternion quaternion = packet.orientationQuaternion();
					std::cout << "q0:" << std::setw(5) << std::fixed << std::setprecision(2) << quaternion.m_w
							  << ",q1:" << std::setw(5) << std::fixed << std::setprecision(2) << quaternion.m_x
							  << ",q2:" << std::setw(5) << std::fixed << std::setprecision(2) << quaternion.m_y
							  << ",q3:" << std::setw(5) << std::fixed << std::setprecision(2) << quaternion.m_z
					;

					// Convert packet to euler
					XsEuler euler = packet.orientationEuler();
					std::cout << ",Roll:" << std::setw(7) << std::fixed << std::setprecision(2) << euler.m_roll
							  << ",Pitch:" << std::setw(7) << std::fixed << std::setprecision(2) << euler.m_pitch
							  << ",Yaw:" << std::setw(7) << std::fixed << std::setprecision(2) << euler.m_yaw
					;

					std::cout << std::flush;
				}
				XsTime::msleep(0);
			}
			_getch();
			std::cout << "\n" << std::string(79, '-') << "\n";
			std::cout << std::endl;
		}
		catch (std::runtime_error const & error)
		{
			std::cout << error.what() << std::endl;
		}
		catch (...)
		{
			std::cout << "An unknown fatal error has occured. Aborting." << std::endl;
		}

		// Close port
		std::cout << "Closing port..." << std::endl;
		control->closePort(mtPort->portName().toStdString());
	}
	catch (std::runtime_error const & error)
	{
		std::cout << error.what() << std::endl;
	}
	catch (...)
	{
		std::cout << "An unknown fatal error has occured. Aborting." << std::endl;
	}

	// Free XsControl object
	std::cout << "Freeing XsControl object..." << std::endl;
	control->destruct();

	std::cout << "Successful exit." << std::endl;

	std::cout << "Press [ENTER] to continue." << std::endl; std::cin.get();

	return 0;
}
