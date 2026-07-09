import serial
import time

ser = serial.Serial('/dev/ttyACM1', 115200, timeout=1)
ser.flushInput()

pin = 36  # replace with the correct pin number

# Send two-byte command: [pin, 0]
ser.write(chr(pin) + chr(0))

# Wait briefly to give Teensy time to respond
time.sleep(0.05)

# Read 1 byte
t = ser.read(1)
print("Raw read: {!r}".format(t))

if t:
    print("Decoded value: {}".format(ord(t)))
else:
    print("No response")
