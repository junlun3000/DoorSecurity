import RPi.GPIO as GPIO  # Import the standard Raspberry Pi GPIO library
from time import sleep
import time
from deep_face import FaceDetection

# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)   # Use physical pin numbering

# Set up pin 11 for PWM (servo) and pin 13 for button input
GPIO.setup(11, GPIO.OUT)   # Set pin 11 as an output for the servo
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set pin 13 as input for the button, with pull-up resistor
GPIO.setup(15, GPIO.OUT)   # Set pin 15 as red LED
GPIO.setup(16, GPIO.OUT)   # Set pin 16 as another indicator (for the door state)

# Set up PWM for the servo
p = GPIO.PWM(11, 50)  # Set pin 11 as a PWM pin with a frequency of 50Hz
p.start(0)            # Start PWM with 0% duty cycle

# Set up ultrasonic sensor
TRIG = 29
ECHO = 31
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Initialize variables
door_open = False  # Track the state of the door (False = closed, True = open)
button_pressed = False  # Track the state of the button (to handle button debouncing)
last_action_time = 0
auto_close_delay = 10
distance_threshold = 10  # Set the threshold distance for ultrasonic sensor (10 cm)

def measure_distance():
    # Ensure trigger is off
    GPIO.output(TRIG, False)
    time.sleep(0.01)
    
    # Send a 10us pulse to TRIG
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        
    # Calculate pulse duration
    pulse_duration = pulse_end - pulse_start
    
    # Convert to distance
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    
    return distance

# Function to move the servo to the open or closed position
def toggle_door():
    global door_open, last_action_time
    if door_open:
        print("Closing door...")
        p.ChangeDutyCycle(8)  # 0 degrees (door closed)
        GPIO.output(16, GPIO.LOW)
        GPIO.output(15, GPIO.HIGH)
        sleep(1)                # Wait for the servo to move
        door_open = False        # Update the state to closed
    else:
        print("Opening door...")
        p.ChangeDutyCycle(5)  # 90 degrees (door open)
        GPIO.output(16, GPIO.HIGH)
        GPIO.output(15, GPIO.LOW)
        sleep(1)                # Wait for the servo to move
        door_open = True         # Update the state to open
        last_action_time = time.time()
    
    p.ChangeDutyCycle(0)

try:

    fd = FaceDetection()
    username = input("Please enter the username: ")

    if fd.verify_user(username):  # Example for verification
         


    while True:
        button_state = GPIO.input(13)  # Read the button state
        current_time = time.time()

        # Measure distance
        distance = measure_distance()
        print(f"Distance: {distance} cm")

        #Inside the door
        if button_state == GPIO.LOW and not button_pressed:  # Button pressed (LOW state)
                print("Object within range, button pressed, toggling door...")
                toggle_door()             # Trigger door toggle
                button_pressed = True     # Mark button as pressed

        elif button_state == GPIO.HIGH and button_pressed:  # Button released (HIGH state)
                button_pressed = False    # Reset button press state

        #Outside the door
        # Check if object is within 10 cm range
        if distance < distance_threshold:
            

        else:
            p.ChangeDutyCycle(0)
        # Auto-close after delay
        # if door_open and (current_time - last_action_time >= auto_close_delay):
        #     print("The door has been open for more than 10 seconds, closing now.")
        #     toggle_door()

        sleep(0.1)  # Short delay to debounce the button and prevent bouncing effects

except KeyboardInterrupt:  # Exit the loop when Ctrl+C is pressed
    pass

# Clean up everything
p.stop()            # Stop the PWM
GPIO.cleanup()      # Reset the GPIO pins to their default state
