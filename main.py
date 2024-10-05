from flask import Flask, render_template
from gpiozero import LED, Button
import sys

app = Flask(__name__)

lightled = LED(21)
lightbutton = Button(6)

def buttonpress():
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
	while True:
    		try:
        		if __name__ == "__main__":
            			app.run(host='0.0.0.0', port=80)
    		except KeyboardInterrupt: #clean up GPIO
        		print("Ending program")
