#!/usr/bin/env python3

from time import sleep
try:
	import RPi.GPIO as GPIO
except:
	print("Could not import RPi.GPIO")
import serial
import os.path

wakeup = 23
reset = 24

FRAME_B  = 0xA5
FRAME_E0 = 0xCC
FRAME_E1 = 0x33
FRAME_E2 = 0xC3
FRAME_E3 = 0x3C

CMD_HANDSHAKE		= 0x00	#handshake
CMD_SET_BAUD		= 0x01	#set baud
CMD_READ_BAUD		= 0x02	#read baud
CMD_MEMORYMODE		= 0x07	#set memory mode
CMD_STOPMODE		= 0x08	#enter stop mode 
CMD_UPDATE			= 0x0A	#update
CMD_SCREEN_ROTATION	= 0x0D	#set screen rotation
CMD_LOAD_FONT		= 0x0E	#load font
CMD_LOAD_PIC		= 0x0F	#load picture

CMD_SET_COLOR		= 0x10	#set color
CMD_SET_EN_FONT		= 0x1E	#set english font
CMD_SET_CH_FONT		= 0x1F	#set chinese font

CMD_DRAW_PIXEL		= 0x20	#set pixel
CMD_DRAW_LINE		= 0x22	#draw line
CMD_FILL_RECT		= 0x24	#fill rectangle
CMD_DRAW_CIRCLE		= 0x26	#draw circle
CMD_FILL_CIRCLE		= 0x27	#fill circle
CMD_DRAW_TRIANGLE	= 0x28	#draw triangle
CMD_FILL_TRIANGLE	= 0x29	#fill triangle
CMD_CLEAR			= 0x2E	#clear screen use back color

CMD_DRAW_STRING		= 0x30	#draw string

CMD_DRAW_BITMAP		= 0x70

# Memory modes
MEM_NAND			= 0
MEM_TF				= 1

# Colors
WHITE				= 0x03
GRAY				= 0x02
DARK_GRAY			= 0x01
BLACK				= 0x00

# ASCII Fonts
ASCII32				= 0x01
ASCII48				= 0x02
ASCII64				= 0x03

if not 'GPIO' in globals():
	print("GPIO not found -> GPIO deactivated")
else:
	GPIO.setmode(GPIO.BOARD)

if os.path.exists("/dev/ttyAMA0"):
	port = serial.Serial("/dev/ttyAMA0", baudrate = 115200, timeout = 2)
elif os.path.exists("/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0"):
	port = serial.Serial("/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0", baudrate = 115200, timeout = 2)
else:
	raise Exception("No serial device found.")

print("Serial device: " + port.port)

def epd_init():
	if not 'GPIO' in globals():
		print("GPIO not found -> epd_init deactivated")
	else:
		if GPIO.getmode() != GPIO.BOARD:
			raise Exception("GPIO.setmode must be GPIO.Board).")
		GPIO.setup(wakeup, GPIO.OUT, initial=GPIO.HIGH)
		GPIO.setup(reset, GPIO.OUT, initial=GPIO.HIGH)

def epd_wakeup():
	if not 'GPIO' in globals():
		print("GPIO not found -> epd_wakeup deactivated")
	else:
		GPIO.output(wakeup, GPIO.LOW)
		sleep(0.000010)
		GPIO.output(wakeup, GPIO.HIGH)
		sleep(0.000500)
		GPIO.output(wakeup, GPIO.LOW)
		sleep(0.010)

def epd_clean():	
	if not 'GPIO' in globals():
		print("GPIO not found -> epd_clean deactivated")
	else:
		GPIO.cleanup()
	
def _verify(array):
	result = 0
	for elem in array:
		result = result ^ elem
	return [result]

def _putchars(data):
	print("writing: ", end="")
	for byte in data:
		print(hex(byte), end=" ")
	print()
	if port.write(data) != len(data):
		raise Exception("port.write didn't write the complete data")
	sleep(0.1)

def _shorts_to_bytes(shorts):
	 # "Arrayfy" parameters if necessary
	if not isinstance(shorts, list):
		shorts = [shorts]
	# Check parameters
	for short in shorts:
		if not isinstance(short, int) or short < 0 or short > 2**16:
			raise Exception("at least one parameter 'shorts' is not a short. Short: " + short)
	ret = []
	for short in shorts:
		ret += short.to_bytes(2, byteorder = 'big')
	return ret

def _send_command(command, parameters=[]):
	# "Arrayfy" parameters if necessary
	if not isinstance(parameters, list):
		parameters = [parameters]
	# Check parameters
	if not isinstance(command, int) or command < 0 or command > 255:
		raise Exception("command is not in valid range/type. Command: " + command)
	for param in parameters:
		if not isinstance(param, int) or command < 0 or command > 255:
			raise Exception("at least one parameter is no byte. Parameter: " + param)
	# Generate frame-length (2 byte array)
	buffer_length = _shorts_to_bytes(9 + len(parameters))
	
	buffer = [
		FRAME_B,		# Beginning of each command
		
		] + buffer_length + [	# Frame length 2bytes (short)
		command			# Command selection byte
		] + parameters + [	# Parameter/Data array
		FRAME_E0,		# Add Endbytes (x4)
		FRAME_E1,
		FRAME_E2,
		FRAME_E3
	]
	buffer += _verify(buffer)	# Add Parity byte
	_putchars(bytearray(buffer))	# Send Command-frame

def epd_set_memory(mode):
	_send_command(CMD_MEMORYMODE, mode)

def epd_set_color(frontcolor, backcolor):
	_send_command(CMD_SET_COLOR, [frontcolor, backcolor])

def epd_clear():
	_send_command(CMD_CLEAR)

def epd_draw_circle(centerx, centery, radius):
	_send_command(CMD_DRAW_CIRCLE, _shorts_to_bytes([centerx, centery, radius]))

def epd_update():
	_send_command(CMD_UPDATE)

def epd_handshake():
	_send_command(CMD_HANDSHAKE)

def epd_read():
	while port.inWaiting() > 0:
		print(port.read(), end="")
	print()

def epd_set_en_font(font):
	_send_command(CMD_SET_EN_FONT, font)

def epd_disp_string(string, x, y):
	if isinstance(string, str):
		string = string.encode()
	if isinstance(string, bytes) or isinstance(string, bytearray):
		string = list(string)
	_send_command(CMD_DRAW_STRING, _shorts_to_bytes([x, y]) + string + [0])

# Main code.
# init
try:
	epd_init()
	epd_wakeup()
	epd_set_memory(MEM_NAND)
	epd_handshake()


	# draw
	epd_set_color(BLACK, WHITE)
	epd_clear()
	for i in range(1, 10):
		epd_draw_circle(399, 299, i * 30)
	epd_set_en_font(ASCII32)
	epd_disp_string(b'Simon', 0, 0)
	epd_update()
	
	sleep(0.2)
	epd_read()
	p = input('> ')
	epd_disp_string(p, 0, 32)
	epd_update()
finally:
	port.close()
	epd_clean()
