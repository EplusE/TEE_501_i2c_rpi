# -*- coding: utf-8 -*-
"""
Read functions for measurement values of the TEE501 Sensor via I2c interface.

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


# pylint: disable=E0401
from smbus2 import SMBus, i2c_msg
# pylint: enable=E0401
CRC8_ONEWIRE_POLY = 0x31
CRC8_ONEWIRE_START = 0xFF


def get_status_string(status_code):
    """Return string from status_code."""
    status_string = {
        0: "Success",
        1: "Not acknowledge error",
        2: "Checksum error",
        3: "Measurement error",
        4: "error wrong input for change_periodic_measurment_time",
        6: "error wrong input for change_measurment_resolution",
    }

    if status_code < len(status_string):
        return status_string[status_code]
    return "Unknown error"


def calc_crc8(buf, start, end):
    ''' calculate crc8 checksum  '''
    crc_val = CRC8_ONEWIRE_START
    for j in range(start, end):
        cur_val = buf[j]
        for _ in range(8):
            if ((crc_val ^ cur_val) & 0x80) != 0:
                crc_val = (crc_val << 1) ^ CRC8_ONEWIRE_POLY
            else:
                crc_val = crc_val << 1
            cur_val = cur_val << 1
    crc_val &= 0xFF
    return crc_val


class TEE501():
    """Implements communication with TEE501 over i2c with a specific address."""

    def __init__(self, i2c_address):
        self.i2c_address = i2c_address


    def get_single_shot_temp_clock_stretching_disabled(self):
        """Let the sensor take a measurement and return the temperature value."""
        i2c_response = self.wire_write_read([0x24, 0x1D],6)
        if (i2c_response[2] == calc_crc8(i2c_response, 0, 2)) :
            temperature = ((float)(i2c_response[0]) * 256 + i2c_response[1]) / 100
            return temperature
        else:
            raise Warning(get_status_string(2))


    def get_single_shot_temp(self):
        """Let the sensor take a measurement and return the temperature value."""
        i2c_response = self.wire_write_read([0x2C, 0x1B],6)
        if (i2c_response[2] == calc_crc8(i2c_response, 0, 2)) :
            temperature = ((float)(i2c_response[0]) * 256 + i2c_response[1]) / 100
            return temperature
        else:
            raise Warning(get_status_string(2))


    def get_periodic_measurment_temp(self):
        """Get the last measurment from the periodic measurment for temperature"""
        i2c_response = self.wire_write_read([0xE0, 0x00],6)
        if (i2c_response[2] == calc_crc8(i2c_response, 0, 2)):
            temperature = ((float)(i2c_response[0]) * 256 + i2c_response[1]) / 100
            return temperature
        else:
            raise Warning(get_status_string(2))


    def change_periodic_measurment_time(self, milli_sec):
        """chnage the time between measuremnts in the periodic measurment mode"""
        if  milli_sec < 3276751:
            value = milli_sec/50
            send_bytes = [0,0]
            send_bytes[1] = int(value / 255)
            send_bytes[0] = int(value % 256)
            self.wire_write([0x72,0xA7,0x10,send_bytes[0],send_bytes[1],
                             calc_crc8([0x10, send_bytes[0],send_bytes[1]],0,3)])
        else:
            raise Warning(get_status_string(4))


    def read_periodic_measurment_time(self):
        """reads the time between measuremnts in the periodic measurment mode"""
        i2c_response = self.wire_write_read([0x72,0xA7,0x10],2)
        value = i2c_response[1] * 256 + i2c_response[0]
        return value * 0.05


    def change_measurment_resolution(self, meas_res_temp): 		#8 - 14 Bit
        """change the resolution of the measurments"""
        if (7 < meas_res_temp < 15):
            send_byte = (meas_res_temp - 8)
            self.wire_write([0x72,0xA7,0x0F,send_byte,calc_crc8([0x0F,send_byte],0,2)])
        else:
            raise Warning(get_status_string(6))


    def read_measurment_resolution(self):
        """reads the resolution of the measurments"""
        i2c_response = self.wire_write_read([0x72,0xA7,0x0F],1)
        i2c_response[0] = (i2c_response[0] << 5) & 255
        i2c_response[0] = i2c_response[0] >> 5
        return i2c_response[0] + 8


    def start_periodic_measurment(self):
        """starts the periodic measurment"""
        self.wire_write([0x20,0x1E])


    def end_periodic_measurment(self):
        """ends the periodic measurment"""
        self.wire_write([0x30,0x93])


    def read_identification(self):
        """reads the identification number"""
        i2c_response = self.wire_write_read([0x70,0x29],9)
        if i2c_response[8] == calc_crc8(i2c_response, 0, 8):
            return i2c_response
        else:
            raise Warning(get_status_string(2))


    def reset(self):
        """resets the sensor"""
        self.wire_write([0x30,0xA2])


    def new_measurment_ready(self):
        """get information if a new measurment is ready"""
        i2c_response = self.wire_write_read([0xF3,0x52],3)
        if i2c_response[2] == calc_crc8(i2c_response, 0, 2):
            return  i2c_response[0] >> 7
        else:
            raise Warning(get_status_string(2))


    def clear_statusregister_1(self):
        """clear the status register 1"""
        self.wire_write([0x30,0x41])


    def wire_write_read(self,  buf, receiving_bytes):
        """write a command to the sensor to get different answers like temperature values,..."""
        write_command = i2c_msg.write(self.i2c_address, buf)
        read_command = i2c_msg.read(self.i2c_address, receiving_bytes)
        with SMBus(1) as eth501_communication:
            eth501_communication.i2c_rdwr(write_command,read_command)
        return list(read_command)


    def wire_write(self, buf):
        """write to the sensor"""
        write_command = i2c_msg.write(self.i2c_address, buf)
        with SMBus(1) as eth501_communication:
            eth501_communication.i2c_rdwr(write_command)
