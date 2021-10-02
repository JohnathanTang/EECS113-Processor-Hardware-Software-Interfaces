
from time import sleep, strftime
from datetime import datetime
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD

import threading


mcp = None
lcd = None
lcd_thread = None 
on_off_toggle = False

incoming_message = None

#Initialize LCD 
#Since we are adopting the Adafruit_LCD1602 as our lCD driver 
#we need to create a LCD object in respect to that driver so we 
#can access it's functions. 
def lcd_setup():

    #Declare global variables used for this API 
    #lcd_thread works with Adafruit_LCD1602 functionaility 
    #on_off_toggle works as a boolean variable to determine when we need to 
    #turn off the displau 
    #MCP refers to the MCP GPIO adapter, we want to pass in the PCF8574 address 
	global lcd
	global lcd_thread
	global on_off_toggle
	global mcp
    
    #Initialize PCF8574 address to use PCF8574 chip 
	PCF8574_address = 0x27  
	PCF8574A_address = 0x3F
	try:
		mcp = PCF8574_GPIO(PCF8574_address)
	except:
		try:
			mcp = PCF8574_GPIO(PCF8574A_address)
		except:
			print (' LCD Address Failed...')
		exit(1)
	
    
    #Use Adafruit_CharLCD API to initiazlize LCD 
	lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)
    
    #Toggle LCD backlighting to see displayed characters 
    #clearly and initialize 16x2 dimension for display since we are using
    #most if not the entire displau 
	mcp.output(3,1)     # turn on LCD backlight
	lcd.begin(16,2)     # set number of LCD lines and columns

    #start lcd_thread, make sure on_off_toggle is off so we can display 
	on_off_toggle = False
	lcd_thread = threading.Thread(target = lcd_thread)
	lcd_thread.daemon = True
	lcd_thread.start()
    

#LCD Thread
#For most of the runtime we want to constantly display current time 
#To do this we check if there is any incomin display request from main program, 
#stop displaying current time for 3 seconds, during that 3 seconds we want to display
#the message from main. 

def lcd_thread():
	global incoming_message
	while not on_off_toggle:
		lcd.clear()
		lcd.setCursor(0, 0)
		if(incoming_message is not None):
			lcd.message(incoming_message)
			incoming_message = None
			sleep(3)
        #Per second update to LCD to replicate live time update. Therefore, we want to delay the display 
        #update once per second to replicate a real timer that increments by seconds
        #First line of LCD shows date, which only updates day every 24 hours 
        #Second line of LCD shows current time, which updates once per second 
		else:
			lcd.message(datetime.now().strftime('Date: %m-%d-%Y') + "\n" + datetime.now().strftime('Time: %H:%M:%S'))
			sleep(1)
    
#This function facilitates what gets printed to the LCD based on the message we 
#receive from main program. "Type" refers to the source of data (i.e DHT or CIMIS) 
def display_data(counter, temperature, humidity, type) :
    global incoming_message 
    message = type + " Data #"+ str(counter) + "\nT:" + str(temperature) + " H:" + str(humidity)
    while(incoming_message is not None):
        sleep(1)
    incoming_message = message
