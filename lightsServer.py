#!/usr/bin/python
from rpi_ws281x import *
import time
#import socket
#from thread import start_new_thread
import subprocess
import shlex
import threading
import select
from socket import socket, AF_INET, SOL_SOCKET, SOCK_DGRAM, SO_REUSEADDR, SOL_SOCKET, SO_BROADCAST, gethostbyname, gethostname
# LED strip configuration:
LED_COUNT      = 8       # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 100     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0
#LED_STRIP      = ws.SK6812_STRIP_RGBW
LED_STRIP      = ws.SK6812W_STRIP
#LED_STRIP      = ws.WS2811_STRIP_GRB

LED_2_COUNT      = 16      # Number of LED pixels.
LED_2_PIN        = 13      # GPIO pin connected to the pixels (must support PWM! GPIO 13 or 18 on RPi 3).
LED_2_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_2_DMA        = 11      # DMA channel to use for generating signal (Between 1 and 14)
LED_2_BRIGHTNESS = 100     # Set to 0 for darkest and 255 for brightest
LED_2_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_2_CHANNEL    = 1       # 0 or 1
LED_2_STRIP      = ws.WS2811_STRIP_GRB

# Colores
BLANK	       = Color(0, 0, 0)
TURN_COLOR     = Color(255, 170, 0)
TURN_COLOR2    = Color(255, 170, 0, 25)
RED	      	   = Color(255, 0, 0)
RED2	       = Color(255, 0, 0, 50)
BREAK_COLOR    = Color(190, 10, 48)
BREAK_COLOR2   = Color(187, 10, 48, 25)

#connected = False

def allRed(strip):
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, RED)
		strip.show()

def allBlank(strip):
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, BLANK)
		strip.show()

def turnLeft(strip, strip2, color, turnTime=0.1):
	allBlank(strip)
	allBlank(strip2)
	for i in range((strip.numPixels()//4)+1):
		strip.setPixelColor(i, color)
		strip.setPixelColor((strip.numPixels()//2)-i, color)
		strip.show()
		time.sleep(turnTime/(strip.numPixels()//4))
	for i in range(strip2.numPixels()/2):
		strip2.setPixelColor(i+strip2.numPixels()/2, color)
		strip2.show()
		time.sleep(turnTime/(strip2.numPixels()//4))
	time.sleep(0.3)
	allBlank(strip)
	allBlank(strip2)
	time.sleep(0.3)

def turnRight(strip, strip2, color, turnTime=0.1):
	allBlank(strip)
	allBlank(strip2)
	strip.setPixelColor(0, color)
	for i in range((strip.numPixels()//4)+1):
		strip.setPixelColor(strip.numPixels()-i, color)
		strip.setPixelColor((strip.numPixels()//2)+i, color)
		strip.show()
		time.sleep(turnTime/(strip.numPixels()//4))
	for i in range(strip2.numPixels()/2):
		strip2.setPixelColor(i, color)
		strip2.show()
		time.sleep(turnTime/(strip2.numPixels()//4))
	time.sleep(0.3)
	allBlank(strip)
	allBlank(strip2)
	time.sleep(0.3)

def brakeLight(strip, strip2, color):
	for j in range(0, 255, 3):
		for i in range(strip.numPixels()):
			strip.setPixelColor(i, color)
			strip.setBrightness(j)
			strip.show()
		for i in range(strip2.numPixels()):
			strip2.setPixelColor(i, color)
			strip2.setBrightness(j)
			strip2.show()
		#time.sleep(0.1)
	time.sleep(0.3)
	allBlank(strip)
	allBlank(strip2)

def setBright(strip, strip2, brightest):
	if 0 <= brightest <= 9:
		bright = brightest*255//9
		strip.setBrightness(bright)
		strip2.setBrightness(bright)
		strip.show()
		strip2.show()

def broadcast():
	puerto = 5555
	message = "BikeView"
	sock = socket(AF_INET, SOCK_DGRAM)
	sock.bind(('', 0))
	sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
	while not connected:
		print("broadcasting")
		sock.sendto(message.encode(), ('<broadcast>', puerto))
		time.sleep(3)

def getip():
	testIP = "8.8.8.8"
	s = socket(AF_INET, SOCK_DGRAM)
	s.connect((testIP, 0))
	return s.getsockname()[0]

if __name__ == '__main__':
	# Create NeoPixel object with appropriate configuration.
	ledRing = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
	sideStrips = Adafruit_NeoPixel(LED_2_COUNT, LED_2_PIN, LED_2_FREQ_HZ, LED_2_DMA, LED_2_INVERT, LED_2_BRIGHTNESS, LED_2_CHANNEL, LED_2_STRIP)
	# Intialize the library (must be called once before other functions).
	ledRing.begin()
	sideStrips.begin()
	#global connected
	connected = False
	trasmiting = False
	host = getip()
	port = 8000
	received = ''
	mySocket = socket()
	mySocket.setblocking(False)
	mySocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	try:
		mySocket.bind((host,port))
		mySocket.listen(10)
		inputs = [mySocket]
		print('running server...')
		while True:
			bthread = threading.Thread(target=broadcast, args=())
			bthread.daemon = True
			bthread.start()
			ready, [], [] = select.select(inputs, [], [])
			for s in ready:
				if s is mySocket:
					conn, addr = mySocket.accept()
					conn.setblocking(False)
					inputs.append(conn)
					print ("Connection from: " + str(addr))
					connected = True
				else:
					while True:
						readyq = select.select([conn], [], [], 0)
						#[],[],excep = select.select([], [], [conn], 0)
						if readyq[0]:
							received = conn.recv(1).decode()
							conn.send(received+"\n".encode())
							print(received)
						if received == 'r': # Turn right lights
							turnRight(ledRing, sideStrips, TURN_COLOR)
						elif received == 'l': # Turn left lights
							turnLeft(ledRing, sideStrips, TURN_COLOR)
						elif received == 'n': # Night lights
							allRed(ledRing)
							allRed(sideStrips)
						elif received == 'b': # Brake lights
							brakeLight(ledRing, sideStrips, RED)
						elif received == 'k': # Red blinking lights
							allRed(ledRing)
							allRed(sideStrips)
							time.sleep(0.1)
							allBlank(ledRing)
							allBlank(sideStrips)
							time.sleep(0.1)
						elif received == 'o': # Lights off
							allBlank(ledRing)
							allBlank(sideStrips)
						elif received == 'v': # Video trasmiting
							if not trasmiting:
								trasmiting = True
								raspivid = "raspivid -t 0 -w 1280 -h 720 -fps 30 -b 3000000 -n -pf baseline -o -"
								socat = "socat -b 1024 - UDP4-DATAGRAM:"
								port = ":5000"
								args1 = shlex.split(raspivid)
								args2 = shlex.split(socat+str(addr[0])+port)
								#print(args2)
								p1 = subprocess.Popen(args1, stdout=subprocess.PIPE)
								p2 = subprocess.Popen(args2,  stdin=p1.stdout)
								p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits
						elif received == 'w':
							if trasmiting:
								trasmiting = False
								p2.terminate()
								p1.terminate()
						elif received == 'c':
							time.sleep(0.01)
						elif received.isdigit():
							setBright(ledRing, sideStrips, int(received))
						else:
							print(received + ' Connection close')
							if trasmiting:
								trasmiting = False
								p2.terminate()
								p1.terminate()
							connected = False
							#conn.shutdown(1)
							conn.close()
							inputs.remove(s)
							break
	except Exception as e:
		print("Got exception ")
		print(e)
		pass
	finally:
		try:
			inputs.remove(s)
		except:
			pass
		try:
			conn.close()
			print("disconnected")
			conn.shutdown(1)
		except:
			pass
