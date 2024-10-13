import RPi.GPIO as GPIO
from flask import Flask, request, jsonify
from time import sleep
import threading
import time

app = Flask(__name__)

# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

# Set up pin 11 for PWM (servo) and pin 13 for button input
GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button with pull-up resistor
GPIO.setup(15, GPIO.OUT)  # Red LED
GPIO.setup(16, GPIO.OUT)  # Door indicator

# Set up PWM for the servo
p = GPIO.PWM(11, 50)  # 50Hz frequency
p.start(0)

# Ultrasonic sensor setup
TRIG = 29
ECHO = 31
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

door_open = False
button_pressed = False
last_action_time = 0
auto_close_delay = 10  # Time in seconds before auto-closing the door
distance_threshold = 10  # 10 cm distance threshold

def measure_distance():
    # Measure distance using the ultrasonic sensor
    GPIO.output(TRIG, False)
    time.sleep(0.01)
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)

def toggle_door():
    global door_open, last_action_time
    if door_open:
        print("Closing door...")
        p.ChangeDutyCycle(8)  # 0 degrees (door closed)
        GPIO.output(16, GPIO.LOW)
        GPIO.output(15, GPIO.HIGH)
        sleep(1)
        door_open = False
    else:
        print("Opening door...")
        p.ChangeDutyCycle(5)  # 90 degrees (door open)
        GPIO.output(16, GPIO.HIGH)
        GPIO.output(15, GPIO.LOW)
        sleep(1)
        door_open = True
        last_action_time = time.time()

    p.ChangeDutyCycle(0)

@app.route('/trigger_door', methods=['POST'])
def trigger_door():
    action = request.json.get('action')
    distance = measure_distance()

    if distance <= distance_threshold:
        if action == 'open' and not door_open:
            toggle_door()
            return jsonify({'status': 'door opened', 'distance': distance}), 200
        elif action == 'close' and door_open:
            toggle_door()
            return jsonify({'status': 'door closed', 'distance': distance}), 200
        else:
            return jsonify({'status': 'door is already in the desired state', 'distance': distance}), 400
    else:
        return jsonify({'status': 'not in range', 'distance': distance}), 403  # 403 Forbidden if not within range

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def button_control():
    global button_pressed
    while True:
        button_state = GPIO.input(13)  # Read the button state
        if button_state == GPIO.LOW and not button_pressed:  # Button pressed (LOW state)
            print("Button pressed, toggling door...")
            toggle_door()
            button_pressed = True  # Mark button as pressed
        elif button_state == GPIO.HIGH and button_pressed:  # Button released (HIGH state)
            button_pressed = False  # Reset button press state
        sleep(0.1)  # Small delay to debounce the button

if __name__ == '__main__':
    # Start the Flask server in a new thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Main loop for button control
    try:
        button_control()  # Handle button input in the main thread
    except KeyboardInterrupt:
        pass

    # Clean up on exit
    p.stop()
    GPIO.cleanup()
