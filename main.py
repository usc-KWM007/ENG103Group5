from flask import Flask, render_template, Response
from gpiozero import LED, Button, DistanceSensor, InputDevice, RGBLED
import sys
from time import sleep
import threading
import statistics
import adafruit_dht
import board
import cv2
import json
import requests
import configparser

app = Flask(__name__)

#Set sensors and pins
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
cameraStatus = False
camera = cv2.VideoCapture(0)

#API for slack
config = configparser.ConfigParser()
config.read('config.py')
slack_webhook = config['API_KEY']['API_KEY']


#global variables for holding sensor data and recording status
#defaults/layout
sensorData = {"rain":"Rain data is unavaliable","temperature":"Temperature data is unavaliable","humidity":"Humidity data is unavaliable","lightLED":"Light status is unavaliable"}
cloudrecording = False
#used as a counter to stop slack spam
sentSlack = 0

#used to read rain sensor
def rainActivity():
		global sensorData
		global sentSlack
		#check rain sensor and turn on/off light accordingly
		if rainsensor.is_active:
			rainled.off()
			sensorData["rain"] = "It is not raining"
			sentSlack = 0
			
		else:
			rainled.on()
			sensorData["rain"] = "It is raining!"
			#if its raining send the status to slack
			if sentSlack == 0:
				sentSlack = 1
				try:
					slack_message = {"text": "Warning! It is raining!."}
					response = requests.post(slack_webhook, data=json.dumps(slack_message),headers={'Content-Type': 'application/json'})
					if response.status_code != 200:
						print('Request to slack returned an error %s, the response is:\n%s' % (response.status_code, response.text))
				except:
					print("Failed to send to slack")
			
			return

#used to read temperature and humidity sensor
def temperaturehumidityActivity():
	try:
			temp = dht_device.temperature
			humidity = dht_device.humidity
		
			global sensorData
			sensorData["temperature"] = "The temperature is "+str(temp)+"C"
			sensorData["humidity"] = "The humidity is "+str(humidity)+"%"
			
			#Temp logic and change LED light
			if temp >= 30:
				templed.color=(1,0,0)
			elif 20 <= temp:
				templed.color=(0,1,0)
			else:
				templed.color=(0,0,1)
			
			#Humidity logic and change LED light
			if humidity >= 80:
				humidityled.color=(1,0,0)
			elif 40 <= humidity:
				humidityled.color=(0,1,0)
			else:
				humidityled.color=(0,0,1)
	except RuntimeError as err:
			print(err.args[0])
	return
	
#Used to read ultra sonic sensor
def distanceActivity(measurements):
	measurement = distancesensor.distance*100
	#avoid adding connection errors to array
	if isinstance(measurement, float):
			#check if array is getting long
			if len(measurements) > 10:
				measurements.pop(0)
				#create average once array is populated
				average = statistics.mean(measurements)
				#check big changes
				if (average-1) >= measurement or measurement >= (average+1):
					#if light is on and there is activity turn on light
					if lightled.is_lit == False:
						lightled.on()
			
			measurements.append(measurement)
	return measurements
	
#main loop to call each sensor function every second
def sensorActivity():
	#arrary for holding measurements
	measurements=[]
	while True:
		#loop through sensors
		rainActivity()
		temperaturehumidityActivity()
		measurements=distanceActivity(measurements)
		sleep(1)
	return

#used to read and return frames from the camera and in the correct format
def generate_frames():
	global cameraStatus
	while cameraStatus:
		success, frame = camera.read()
		if not success:
			break
		else:
			ret, buffer = cv2.imencode('.jpg', frame)
			frame = buffer.tobytes()
			yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def buttonpress():
	#trigged by light button
	print("buttonpressed", file=sys.stderr)
	lightled.off() if lightled.is_lit else lightled.on()
	return

def recordbuttonpress():
	#triggered by record button and website toggle
	print("recordtoggled", file=sys.stderr)
	global cloudrecording
	cloudrecording = False if cloudrecording else True
	return
	

#event listener for button press to call function
lightbutton.when_pressed =  buttonpress
recordbutton.when_pressed = recordbuttonpress


		
#default route
@app.route('/')
def index():
	#check light and recording status
	global cloudrecording
	sensorData['lightLED'] = "lights are on" if lightled.is_lit else "Lights are off"
	message = sensorData if cloudrecording else {"not_recording":"is not active"}
	#return sensor data
	return render_template('index.html', message=message)

#routes for turning on/off the lights
@app.route('/Light/<state>')
def light_state(state):
	#check recording status
	global cloudrecording
	message = sensorData if cloudrecording else {"not_recording":"is not active"}
	#turn on/off lights accordingly
	if state == 'on':
		lightled.on()
		sensorData['lightLED'] = "Lights are on"
		
	elif state == 'off':
		lightled.off()
		sensorData['lightLED'] = "Lights are off"
		
	else:
		sensorData['lightLED'] = "Light status is unknown"
	return render_template('index.html', message=message)

#route for toggling recording to the cloud
@app.route('/Record')
def toggle_recording():
	recordbuttonpress()
	global cloudrecording
	sensorData['lightLED'] = "lights are on" if lightled.is_lit else "Lights are off"
	message = sensorData if cloudrecording else {"not_recording":"is not active"}
	return render_template('index.html', message=message)

#route for toggling camera
@app.route('/togglecamera')
def toggleCamera():
	global cameraStatus
	global camera
	#turn off camera to reduce power draw when not in use
	if cameraStatus:
		cameraStatus=False
		#disconnect and stop recording
		camera.release()
		#reconnect not recording
		camera = cv2.VideoCapture(0)
	else:
		cameraStatus=True
	global cloudrecording
	message = sensorData if cloudrecording else {"not_recording":"is not active"}
	return render_template('index.html', message=message)

#route for sending frames from the camera, multi-part
@app.route('/securityfeed')
def securityfeed():
	return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

#start line
if __name__=="__main__":
    		try:
            		t1 = threading.Thread(target = app.run, kwargs=dict(host='0.0.0.0', port=80, threaded=True)).start()
            		#keep distance checking on seperate thread due to looping and blocking main thread
            		t2 = threading.Thread(target = sensorActivity).start()
            			
            			
    		except KeyboardInterrupt: #clean up GPIO and disconnect camera
        		print("Ending program")
        		camera.release()

        		
