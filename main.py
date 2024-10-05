from flask import Flask, render_template
from gpiozero import LED

app = Flask(__name__)

lightled = LED(21)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/Light/<state>')
def light_state(state):
	if state == 'on':
		lightled.on()
		message = "LED is on"
	elif state == 'off':
		lightled.off()
		message = "Led is off"
	else:
		message = "Invalid State"
	return render_template('index.html', message=message)#

if __name__=="__main__":
	while True:
    		try:
        		if __name__ == "__main__":
            			app.run(host='0.0.0.0', port=80)
    		except KeyboardInterrupt:
        		print("Ending program")
