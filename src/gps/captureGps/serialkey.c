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

#include "serialkey.h"
#include <xsens/xsstring.h>
#include <xsens/xscontrol.h>
#include <stdio.h>
#include <string.h>

int setSerialKey()
{
	XsString serial = XSSTRING_INITIALIZER;

	if (strcmp(SERIAL_KEY, "enter serial key here") == 0)
	{
		char serialKey[256];
		{
			FILE* fp;
			memset(serialKey, 0, 256);
			fp = fopen("serial.key", "r");
			if (fp)
			{
				fread(serialKey, 1, 30, fp);
				fclose(fp);

				XsString_assignCharArray(&serial, serialKey);
				if (XsControl_setSerialKey(&serial))
					return 1;
			}
		}

		// ask for serial key
		printf( "Please enter valid serial key\n"
				"If you built this example yourself you can enter the key in \"serialkey.h\"\n");
		scanf("%s", serialKey);
		
		XsString_assignCharArray(&serial, serialKey);
		
		if (XsControl_setSerialKey(&serial))
		{
			// store it
			FILE* fp = fopen("serial.key", "w");
			fwrite(serialKey, sizeof(char), strlen(serialKey), fp);
			fclose(fp);
			return 1;
		}
		return 0;
	}
	XsString_assignCharArray(&serial, SERIAL_KEY);
	return XsControl_setSerialKey(&serial);
}

