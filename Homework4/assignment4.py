

#Name :    Johnathan Tang
#UCINetID: 63061294

#Import libraries 
import RPi.GPIO as GPIO
import time
import threading

GPIO.setmode(GPIO.BOARD)

# Assign buttons to GPIO
BTN_R = 12 # G18
BTN_G = 22 # G25
BTN_B = 15 # G22
BTN_Y = 13 # G27

#Assign LED to GPIO
LED_R = 31 # G6
LED_G = 29 # G5
LED_B = 33 # G13
LED_Y = 32 # G12

# Assign buttons to associated LED color 
btn2led = {
    BTN_R: LED_R,
    BTN_G: LED_G,
    BTN_B: LED_B,
    BTN_Y: LED_Y,
}

GPIO.setwarnings(False)
GPIO.setup([BTN_R, BTN_G, BTN_B, BTN_Y], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup([LED_R, LED_G, LED_B, LED_Y], GPIO.OUT, initial=GPIO.HIGH)

# Blink thread, handles blinking of RED and GREEN LED 
def blink_thread(BTNcolor):
    x = GPIO.HIGH
    y = GPIO.LOW
    blink = False
    blink_delay = 0.3 # blink delay, alternating between Red and Green LED

    # LED Blink Mode
    print("Enter Blinking Mode")
    while True:
        #If RED and GREEN buttons are simulatenouly pressed 
        #Blink RED and GREEN LEDs 
        if GPIO.input(BTN_G) and GPIO.input(BTN_R):
            print("Red and Green Pushed : Blinking Now")
            started = time.time()
            #While blinking, if another event occurs while blinking, stop blinking
            while True:
                if GPIO.input(BTNcolor):
                    GPIO.output([LED_R, LED_G, LED_B, LED_Y], True)
                    print("Button Pushed : Exiting Blinking Mode")
                    break
                #Stop blinking if no interrupts and 5 seconds has passed, this is our threshold
                threshold = 5 
                if time.time() - started > threshold:
                    GPIO.output([LED_R, LED_G, LED_B, LED_Y], True)
                    print("5 sec Passed : Exiting Blinking Mode")
                    break
                GPIO.output(LED_G, x)
                GPIO.output(LED_R, y)
                if x == GPIO.LOW:
                    x = GPIO.HIGH
                    y = GPIO.LOW
                else:
                    x = GPIO.LOW
                    y = GPIO.HIGH

                time.sleep(blink_delay)
            break
    #End of blinking 
    return

# Handles Blue and Yellow Button events
# Pressing either button will enable blink mode for Red and Green

def handle(pin):
    
    #Light corressponding LED when pushbutton of same color pressed 
    GPIO.output(btn2led[pin], not GPIO.input(pin))

    t = None
    if pin == BTN_B or BTN_Y:
        #Enter blue thread, if blue button pressed, activate blinking mode
        #if blinking mode already on, interrupt and turn off blinking
        if GPIO.input(BTN_B):
            print("Starting Blue Thread")
            t = threading.Thread(target=blink_thread(BTN_Y)) #entering thread 
            t.daemon = True
            t.start() # start thread 
            t.join()
            #Exit blue thread
            print("Finished Blue Thread")
            time.sleep(0.5)
        #Enter yellow thread, if yellow button pressed, light up Yellow Led and enable blink mode
        #if blinking mode already on, and if Blue Thread on, interrupt and turn off blinking 
        if GPIO.input(BTN_Y):
            print("Starting Yellow Thread")
            t = threading.Thread(target=blink_thread(BTN_B))
            t.daemon = True
            t.start()
            t.join()
            time.sleep(0.5)
            # Exit yellow thread
            print("Finished Yellow Thread")

#Handle button events 
GPIO.add_event_detect(BTN_R, GPIO.BOTH, handle)
GPIO.add_event_detect(BTN_G, GPIO.BOTH, handle)
GPIO.add_event_detect(BTN_B, GPIO.BOTH, handle)
GPIO.add_event_detect(BTN_Y, GPIO.BOTH, handle)

# endless loop with delay to wait for event detections 
while True:
    time.sleep(1e6)