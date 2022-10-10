# -*- coding: utf-8 -*-
"""
Example script reading measurement values from the TEE501 Sensor via I2c interface.

Copyright 2022 E+E Elektronik Ges.m.b.H.

Disclaimer:
This application example is non-binding and does not claim to be complete with regard
to configuration and equipment as well as all eventualities. The application example
is intended to provide assistance with the TEE501 sensor module design-in and is provided "as is".
You yourself are responsible for the proper operation of the products described.
This application example does not release you from the obligation to handle the product safely
during application, installation, operation and maintenance. By using this application example,
you acknowledge that we cannot be held liable for any damage beyond the liability regulations
described.

We reserve the right to make changes to this application example at any time without notice.
In case of discrepancies between the suggestions in this application example and other E+E
publications, such as catalogues, the content of the other documentation takes precedence.
We assume no liability for the information contained in this document.
"""


import time
from tee501_i2c_library import TEE501


# Definition
CSV_DELIMETER = ","


TEE_501 = TEE501(0x48)

# read device identification
try:
    print("identification: " + ''.join('{:02x}'.format(x) for x in TEE_501.read_identification()))

except Warning as exception:
    print("Exception: " + str(exception))

# print csv header
print("temperature")

for i in range(30):

    try:
        temperature = TEE_501.get_single_shot_temp()

        print('%0.2f °C' % temperature)

    except Warning as exception:
        print("Exception: " + str(exception))

    finally:
        time.sleep(0.5)
