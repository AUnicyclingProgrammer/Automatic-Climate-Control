# Just following the sparkfun guide found
# here: https://learn.sparkfun.com/tutorials/python-programming-tutorial-getting-started-with-the-raspberry-pi/all#experiment-4-i2c-temperature-sensor
# Improving using thie library: https://github.com/sparkfun/Qwiic_TMP102_Py

from __future__ import print_function
import qwiic_tmp102
import time
import sys

def runExample():

	print("\nSparkFun Qwiic TMP102 Sensor Test Example\n")
	myTmpSensor = qwiic_tmp102.QwiicTmp102Sensor()

	if myTmpSensor.is_connected == False:
		print("The Qwiic TMP102 Sensor device isn't connected to the system. Please check your connection", \
			file=sys.stderr)
		return

	myTmpSensor.begin()

	print("Initialized.")

	while True:
		print ("Temp in F: ", myTmpSensor.read_temp_f())
		print ("Temp in C: ", myTmpSensor.read_temp_c())
		print ("--------------------------------------------")
		time.sleep(0.5)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example 1")
		sys.exit(0)

# Old stuff
""" 
import time
import smbus

i2c_ch = 1

# TMP102 address on the I2C bus
i2c_address = 0x48

# Register addresses
reg_temp = 0x00
reg_config = 0x01

# Calculate the 2's complement of a number
def twos_comp(val, bits):
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val

# Read temperature registers and calculate Celsius
def read_temp():

    # Read temperature registers
    val = bus.read_i2c_block_data(i2c_address, reg_temp, 2)
    # NOTE: val[0] = MSB byte 1, val [1] = LSB byte 2
    #print ("!shifted val[0] = ", bin(val[0]), "val[1] = ", bin(val[1]))

    temp_c = (val[0] << 4) | (val[1] >> 4)
    #print (" shifted val[0] = ", bin(val[0] << 4), "val[1] = ", bin(val[1] >> 4))
    #print (bin(temp_c))

    # Convert to 2s complement (temperatures can be negative)
    temp_c = twos_comp(temp_c, 12)

    # Convert registers value to temperature (C)
    temp_c = temp_c * 0.0625

    return temp_c

# Initialize I2C (SMBus)
bus = smbus.SMBus(i2c_ch)

# Read the CONFIG register (2 bytes)
val = bus.read_i2c_block_data(i2c_address, reg_config, 2)
print("Old CONFIG:", val)

# Set to 4 Hz sampling (CR1, CR0 = 0b10)
val[1] = val[1] & 0b00111111
val[1] = val[1] | (0b10 << 6)

# Write 4 Hz sampling back to CONFIG
bus.write_i2c_block_data(i2c_address, reg_config, val)

# Read CONFIG to verify that we changed it
val = bus.read_i2c_block_data(i2c_address, reg_config, 2)
print("New CONFIG:", val)

# Print out temperature every second
while True:
    temperature = read_temp()
    temp_f = temperature * (9/5) + 32
    # print(round(temperature, 2), "C")
    print(round(temp_f, 2), "F")
    time.sleep(1)
 """