from micropython import const
import time
import math
import board
import busio
from adafruit_bus_device import i2c_device
try:
    from struct import unpack
except ImportError:
    from ustruct import unpack

ADXL345_DEFAULT_ADDRESS = const(0x53) # Assumes ALT address pin low

# Conversion Factors
MG2G_MULTIPLIER = 0.004 # 4mg per lsb
PI = 3.14159265359

# Offsets
xOffset = 0.0
yOffset = 0.0
zOffset = 0.1

i2c = busio.I2C(board.SCL, board.SDA)
i2cDevice = i2c_device.I2CDevice(i2c, ADXL345_DEFAULT_ADDRESS)

while not i2c.try_lock():
    pass

devices = i2c.scan()
# OR
[hex(devices) for devices in i2c.scan()]
while len(devices) < 1:
    devices = i2c.scan()
device = devices[0]
print("Found device @ address: 0x{0:02X}".format(device),end='\n\n')

def read_register(register, length):
    buffer = bytearray(6)
    buffer[0] = register & 0xFF
    i2cDevice.write(buffer, start=0, end=1)
    i2cDevice.readinto(buffer, start=0, end=length)
    return buffer[0:length]

def write_register_byte(register, value):
    buffer = bytearray(2)
    buffer[0] = register & 0xFF
    buffer[1] = value & 0xFF
    i2cDevice.write(buffer, start=0, end=2)

def initialization(i2cDevice, address):
    # Set the 'Rate' bits to 100Hz (0x0A = 0b0101: default value)
    write_register_byte(0x2C, 0x0A)
    # Set the 'Measure' bit (@ D3) to 1 to enable measurement
    # ('1' at D3 = 0b1000 = 2^3 = 8 = 0x08 in hex)
    write_register_byte(0x2D, 0x08)
    # Set the 'INT_ENABLE' to 0 for "no interrupts"
    write_register_byte(0x2E, 0x0)
    # Set the 'DATA_FORMAT' (0x00 = 0b00 = 0: default value)
    write_register_byte(0x31, 0b0)

def acceleration():
    """ The x, y, z acceleration values returned in a 3-tuple in Gs """
    x, y, z = unpack('<hhh', read_register(0x32, 6))
    x = x * MG2G_MULTIPLIER + xOffset
    y = y * MG2G_MULTIPLIER + yOffset
    z = z * MG2G_MULTIPLIER + zOffset

    # Fix the '-0.0' issue on the X-Axis
    if((x > -0.005) and (x < 0.005)):
        x = 0.0

    # Fix the '-0.0' issue on the Y-Axis
    if((y > -0.005) and (y < 0.005)):
        y = 0.0

    # Fix the '-0.0' issue on the Z-Axis
    if((z > -0.005) and (z < 0.005)):
        z = 0.0

    return (x, y, z)

def tilt(xComponent, zComponent):
    if(zComponent != 0):
        xTetha = math.atan(xComponent / zComponent) * 360.0 / (2.0 * PI)
    else:
        xTetha = 90.0
    return xTetha

def awe(yComponent, zComponent):
    if(zComponent != 0):
        yTetha = math.atan(yComponent / zComponent) * 360.0 / (2.0 * PI)
    else:
        yTetha = 90.0
    return yTetha

try:
    initialization(i2c, ADXL345_DEFAULT_ADDRESS)
    while True:
        x, y, z = acceleration()
        tiltAngle = tilt(x, z)
        aweAngle = awe(y, z)
        print("X accel:\t{:.1f} G\nY accel:\t{:.1f} G\nZ accel:\t{:.1f} G".format(x, y, z),end='\n')
        print("Tilt(x-axis):\t{:.1f} Deg".format(tiltAngle),end='\n')
        print("Awe(y-axis):\t{:.1f} Deg".format(aweAngle),end='\n\n')
        time.sleep(1.0) # 1.0Hz
finally:
    i2c.unlock()

