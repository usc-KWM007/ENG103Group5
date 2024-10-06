from flask import Flask, render_template
from gpiozero import LED, Button, DistanceSensor, InputDevice, RGBLED
import sys
from time import sleep
import threading
import statistics
import adafruit_dht
import board

app = Flask(__name__)

lightled = LED(21)
lightbutton = Button(6, bounce_time=0.05)
recordbutton = Button(5, bounce_time=0.05)
rainsensor = InputDevice(17)
rainled = LED(20)
distancesensor = DistanceSensor(echo=22,trigger=27)
dht_device = adafruit_dht.DHT11(board.D23)
#red green blue
humidityled = RGBLED(13,19,26)
templed = RGBLED(25,12,16)

#global variables for holding sensor data and recording status
#defaults/layout
sensorData = {"rain":"Rain data is unavaliable","temperature":"Temperature data is unavaliable","humidity":"Humidity data is unavaliable","lightLED":"Light status is unavaliable"}
cloudrecording = False

def rainActivity():
		global sensorData
		#check rain sensor
		if rainsensor.is_active:
			rainled.off()
			sensorData["rain"] = "It is not raining"
		else:
			rainled.on()
			sensorData["rain"] = "It is raining!"
		return

def temperaturehumidityActivity():
	try:
			temp = dht_device.temperature
			humidity = dht_device.humidity
			
			global sensorData
			sensorData["temperature"] = "The temperature is "+str(temp)+"C"
			sensorData["humidity"] = "The humidity is "+str(humidity)+"%"
			
			print("temp "+str(temp)+" humidity "+str(humidity))
			#Temp logic
			if temp >= 30:
				templed.color=(1,0,0)
			elif 20 <= temp:
				templed.color=(0,1,0)
			else:
				templed.color=(0,0,1)
			
			#Humidity logic
			if humidity >= 80:
				humidityled.color=(1,0,0)
			elif 40 <= humidity:
				humidityled.color=(0,1,0)
			else:
				humidityled.color=(0,0,1)
	except RuntimeError as err:
			print(err.args[0])
	return
	
def distanceActivity(measurements):
	measurement = distancesensor.distance*100
	print(measurement)
	#avoid adding connection errors to array
	if isinstance(measurement, float):
			#check if array is getting long
			if len(measurements) > 10:
				measurements.pop(0)
				#create average once array is populated
				average = statistics.mean(measurements)
				print("average"+str(average))
				#check big changes
				if (average-1) >= measurement or measurement >= (average+1):
					#if light is on and there is activity turn on light
					if lightled.is_lit == False:
						lightled.on()
			
			measurements.append(measurement)
	return measurements
	

def sensorActivity():
	#arrary for holding measurements
	measurements=[]
	while True:
		#loop through sensors
		rainActivity()
		temperaturehumidityActivity()
		measurements=distanceActivity(measurements)
		print(measurements, file=sys.stderr)
		sleep(1)
	return

def buttonpress():
	#trigged by light button
	print("buttonpressed", file=sys.stderr)
	lightled.off() if lightled.is_lit else lightled.on()
	return

def recordbuttonpress():
	print("recordbuttonpressed", file=sys.stderr)
	global cloudrecording
	cloudrecording = False if cloudrecording else True
	return
	

#event listener for button press to call function
lightbutton.when_pressed =  buttonpress
recordbutton.when_pressed = recordbuttonpress

@app.route('/')
def index():
	global cloudrecording
	sensorData['lightLED'] = "lights are on" if lightled.is_lit else "Lights are off"
	message = sensorData if cloudrecording else {"not_recording":"Currently not recording, press record or press the record button to start recording"}
	return render_template('index.html', message=message)

@app.route('/Light/<state>')
def light_state(state):
	global cloudrecording
	message = sensorData if cloudrecording else {"not_recording":"Currently not recording, press record or press the record button to start recording"}
	if state == 'on':
		lightled.on()
		sensorData['lightLED'] = "Lights are on"
		
	elif state == 'off':
		lightled.off()
		sensorData['lightLED'] = "Lights are off"
		
	else:
		sensorData['lightLED'] = "Light status is unknown"
	return render_template('index.html', message=message)

@app.route('/Record')
def toggle_recording():
	recordbuttonpress()
	global cloudrecording
	sensorData['lightLED'] = "lights are on" if lightled.is_lit else "Lights are off"
	message = sensorData if cloudrecording else {"not_recording":"Currently not recording, press record or press the record button to start recording"}
	return render_template('index.html', message=message)

if __name__=="__main__":
    		try:
        		if __name__ == "__main__":
            			t1 = threading.Thread(target = app.run, kwargs=dict(host='0.0.0.0', port=80)).start()
            			#keep distance checking on seperate thread due to looping
            			t2 = threading.Thread(target = sensorActivity).start()
            			
            			
    		except KeyboardInterrupt: #clean up GPIO
        		print("Ending program")
        		
