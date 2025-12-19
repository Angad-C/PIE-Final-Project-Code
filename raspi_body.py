import evdev
from evdev import ecodes
import pigpio
import time
import select

pi = pigpio.pi()
if not pi.connected:
    print("pigpiod not running")
    exit()

LEFT = 22
RIGHT = 23
STEP_PIN = 24
DIR_PIN = 4
stepsPerRevolution = 400 

pi.set_mode(LEFT, pigpio.OUTPUT)
pi.set_mode(RIGHT, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)
pi.set_mode(STEP_PIN, pigpio.OUTPUT)
pi.write(DIR_PIN, 1)
# # Initialize to stop (50% duty is neutral for tank mode)
pi.set_PWM_frequency(LEFT,50)
pi.set_PWM_frequency(RIGHT,50)

pi.set_servo_pulsewidth(LEFT, 1500)
pi.set_servo_pulsewidth(RIGHT, 1500)

device = None
for path in evdev.list_devices():
    dev = evdev.InputDevice(path)
    if "Joystick Controller" in dev.name:
        device = dev
        break

if device is None:
    print("Joystick not found")
    exit()

print(f"Connected to {device.name}")

right_stick = -99
left_stick = -99
head_position = 22
current_head_position = head_position
button_pressed = False

last_input_time = time.time()
DEADMAN_TIMEOUT = 0.3  # seconds

try:
    while True:
        # Non-blocking input wait (50 ms max)
        r, _, _ = select.select([device.fd], [], [], 0.05)
        if r:
            for event in device.read():
                last_input_time = time.time()

                if event.type == ecodes.EV_ABS:
                    if event.code == ecodes.ABS_X:
                        right_stick = event.value
                    elif event.code == ecodes.ABS_Y:
                        left_stick = event.value
                    elif event.code == ecodes.ABS_RX:
                        head_position = event.value

                elif event.type == ecodes.EV_KEY:
                    if event.code == ecodes.BTN_TRIGGER:
                        button_pressed = (event.value == 1)
        print("right_stick: ", right_stick)
        print("left stick: ", left_stick)
        print("head_position: ", head_position)


#------------------right motor-------------------------------------
        if -right_stick > 103:
            speed = 1500 + 70*(-right_stick - 103)/24
        elif -right_stick < 93:
            speed = 1500 - 70*(93 + right_stick)/24
        else: 
            speed = 1500

        if speed > 1000 and speed < 2000:
            print(f"Right Motor Speed: {speed}") 
            pi.set_servo_pulsewidth(LEFT, speed)

# ----------------------left motor--------------------------------
        if -left_stick > 103: 
            speed = 1500 + 70*(-left_stick - 103)/24
        elif -left_stick < 93:
            speed = 1500 - 70*(93 + left_stick)/24
        else:
            speed = 1500

        if speed > 1000 and speed < 2000: 
            pi.set_servo_pulsewidth(RIGHT, speed) 
            # head motor 
            print(f"Left Motor Speed: {speed}") 

#-----------------------head--------------------------------------   
        if not head_position == current_head_position: 
            if head_position < current_head_position: 
                pi.write(DIR_PIN, 1)
                current_head_position = head_position
                for i in range(stepsPerRevolution):
                    pi.write(STEP_PIN, 1)
                    time.sleep(0.0005)  # 2000 µs
                    pi.write(STEP_PIN, 0)
                    time.sleep(0.0005) 
                
            elif head_position > current_head_position: 
                pi.write(DIR_PIN, 0)
                current_head_position = head_position
                for i in range(stepsPerRevolution):
                    pi.write(STEP_PIN, 1)
                    time.sleep(0.000
                    5)  # 2000 µs
                    pi.write(STEP_PIN, 0)
                    time.sleep(0.0005) 
    
            time.sleep(0.05) 

        time.sleep(0.1) 


except Exception as e:
    print("\nStopping motors error")
    pi.set_servo_pulsewidth(RIGHT, 1500)
    pi.set_servo_pulsewidth(LEFT, 1500)
    pi.stop()

except KeyboardInterrupt:
    print("\nStopping motors (Ctrl-C)")
    pi.set_servo_pulsewidth(RIGHT, 1500)
    pi.set_servo_pulsewidth(LEFT, 1500)
    pi.stop()

finally:
    print("stop")
    pi.set_servo_pulsewidth(RIGHT, 1500)
    pi.set_servo_pulsewidth(LEFT, 1500)
    pi.stop()
