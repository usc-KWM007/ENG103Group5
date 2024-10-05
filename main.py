from flask import Flask, render_template
from gpiozero import LED, Button, DistanceSensor, InputDevice
import sys
from time import sleep
import threading
import statistics
import adafruit_dht
import board

app = Flask(__name__)

lightled = LED(21)
lightbutton = Button(6)
rainsensor = InputDevice(17)
rainled = LED(20)
distancesensor = DistanceSensor(echo=22,trigger=27)
dht_device = adafruit_dht.DHT11(board.D23)

def sensorActivity():
	#arrary for holding measurements
	measurements=[]
	while True:
		#check rain sensor
		if rainsensor.is_active:
			rainled.off()
		else:
			rainled.on()
		try:
			temperature_c = dht_device.temperature
			temperature_f = temperature_c * (9 / 5) + 32

			humidity = dht_device.humidity

			print("Temp:{:.1f} C / {:.1f} F    Humidity: {}%".format(temperature_c, temperature_f, humidity))
		except RuntimeError as err:
			print(err.args[0])
		measurement = distancesensor.distance*100
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
		
		print(measurement, file=sys.stderr)
		print(measurements)
		sleep(1)


def buttonpress():
	#trigged by light button
	print("buttonpressed", file=sys.stderr)
	lightled.off() if lightled.is_lit else lightled.on()
	return

lightbutton.when_pressed =  buttonpress

@app.route('/')
def index():
	message = "lights are on" if lightled.is_lit else "Lights are off"
	return render_template('index.html', message=message)

@app.route('/Light/<state>')
def light_state(state):
	if state == 'on':
		lightled.on()
		message = "Lights are on"
	elif state == 'off':
		lightled.off()
		message = "Lights are off"
	else:
		message = "Invalid State"
	return render_template('index.html', message=message)

if __name__=="__main__":
    		try:
        		if __name__ == "__main__":
            			t1 = threading.Thread(target = app.run, kwargs=dict(host='0.0.0.0', port=80)).start()
            			#keep distance checking on seperate thread due to looping
            			t2 = threading.Thread(target = sensorActivity).start()
            			
            			
    		except KeyboardInterrupt: #clean up GPIO
        		print("Ending program")
        		
