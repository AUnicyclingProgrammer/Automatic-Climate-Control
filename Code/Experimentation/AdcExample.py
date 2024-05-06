# Following this guide: https://circuitdigest.com/microcontroller-projects/interfacing-pcf8591-adc-dac-module-with-raspberry-pi

import smbus
import time

# Address of the device on the i2c bus
address = 0x4a

# Address of the channels that can be queried
A0 = 0x40
A1 = 0x41
A2 = 0x42
A3 = 0x43

bus = smbus.SMBus(1)

def ReadAnalogValue(busAddress, channelAddress):
    bus.write_byte(busAddress, channelAddress)
    value = bus.read_byte(busAddress)

    return value

# while True:
#     bus.write_byte(address,A0)
#     value = bus.read_byte(address)
#     print(value)
#     time.sleep(0.1)

while True:
    for channelAddress in [A0, A1, A2, A3]:
        bus.write_byte(address,channelAddress)
        value = bus.read_byte(address)
        print(f"Addr: {channelAddress} | V: {value} [] ", end="")
    print("")
    time.sleep(0.5)
