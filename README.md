ENG103 task 3 Group 5

Home Automation Project.
Flask server/script that supports: 
Turning on a LED via physical button and website
Ultrasonic sensor to detect if someone walks in front on it to turn on the lights
Temperature and humidity sensor that reports to the website and controls two RGB lights
Rainsensor to turn on a blue LED and send a message to Slack
Webcam stream to the flask server with a toggle
Data on the flask website can be refreshed with a button

Tested on a Raspberry Pi 4b 4gb
Standard LED's and RGBLED's
Ultrasonic sensor: HC-SR04
Temperature and Humidity: DHT11 using digital output
Raindrop sensor: Ardiuno rain drop module FR-04 using digital output
Webcam: Microsoft Lifecam vx-3000 (has power draw issues, recommended using a powered USB hub)

Install with (using a python3 environment):
pip install -r requirements.txt
opencv and configparser are also required

Run with:
sudo -E python3 ENG103Group5/main.py or alternative
