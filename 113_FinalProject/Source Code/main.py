import RPi.GPIO as GPIO
#IMPORT LCD
import LCD as LCD
#Import CIMIS 
from CIMIS import cimis_hour
from CIMIS import cimis_data
#Import DHT
import Freenove_DHT as DHT

#Date and time 
#Threading 
from datetime import datetime
import threading
import time

#define the pins
dht_pin = 11      #GPIO 17
pir_pin = 22      #GPIO 25
led_pin = 40      #GPIO 21


#Initialize DHT class object
dht = None

#DECLARE CONSTANTS 
HOUR = 60 * 60
START_HOUR = -1 
TOTAL_HOURS = 24 #RUN FOR 24 HOURS 

#DECLARE TEMP AND HUMIDITY ARRAY TO STORE DATA 
temperature_array = [None] * 24
humidity_array = [None] * 24

#Setup all the sensor pins and GPIO library
def setup():
    global dht
    #console_main("Setting Up GPIO")
    GPIO.setmode(GPIO.BOARD)       
    
    #Setup DHT , create DHT class
    dht = DHT.DHT(dht_pin)  
    
    #Set LED off by default initially 
    GPIO.setup(led_pin, GPIO.OUT, initial = GPIO.HIGH) 

    #Setup LCD Display
    LCD.lcd_setup()

    #Setup PIR sensor 
    GPIO.setup(pir_pin, GPIO.IN)




#*********************DHT Functions****************************************

#Use DHT-11 to grab local temperature
def get_local_temperature():
    check = None
    while ( check is not dht.DHTLIB_OK ):  #Use Freenove_DHT class to check temp
        check = dht.readDHT11()            #Read from DHT
    return dht.temperature               #Return temperature read from DHT 
    
    
#Use DHT-11 to grab local humidity 
def get_local_humidity():
    check = None
    while ( check is not dht.DHTLIB_OK ):  #Use Freenove_DHT class to check humidity  
        check = dht.readDHT11()            #Read from DHT                 
    return dht.humidity                  #Return humidity from DHT 
    
    

    

#**************************************** Main Thread ***************************************************

#Main loop of the program. Aquires cimis data every hour and waits for local data
#Computes time to irrigate and turns on the relay
def mainloop():
    #console_main("Starting main loop")
    current_hour = START_HOUR
    hours_passed = 0
    #To sync main thread and data thread such that they run properly 
    #We only want to use main loop once per hour to handle data collected 
    #from data thread, that's why we sleep Main thread for an hour 
    time.sleep( HOUR )
    
    total_delay = 0
    #Irrigiation Loop 
    #For every hour passed within a day, we want to run this loop 
    
    while ( hours_passed < TOTAL_HOURS ):
        delay_hour = time.time()
        #Pull CIMIS data every hour 
        
        console_data("\n******************** CIMIS REPORT **************************************")
        cimis_type = "CIMIS"
        print("Pulling CIMIS Data. Hour: " + str(current_hour)+"......")

        #Retrieve the cimis data for the past hour
        data = cimis_hour(current_hour )   

        #Check to see if there is an error pulling data from CIMIS 
        #Data could either not be availible or there was an error pulling 
        while( data is None or data.get_humidity() is None or data.get_temperature() is None ):
            if data is None:
                console_main("[ERROR]Failed to pull from CIMIS. Reattempt in one hour... ")
            else:
                console_main("[ERROR]CIMIS Data Not Availible. Try Again in One Hour")
            #wait for next hour before pulling from CIMIS again, for that hour
            time.sleep( HOUR )  
            
            #Repull data
            console_main("Repull for Hour: " + str(current_hour))
            data = cimis_hour( current_hour )

        #If data pulls successfully, print and store 
        
        print("CIMIS Data for Hour: " + str(current_hour))
        #Print CIMIS data 
        cimis_humidity = data.get_humidity()
        cimis_temperature = data.get_temperature() 
        cimis_eto = data.get_eto() 
        
        #Print CIMIS to console
        print(" \nTemperature: "+ cimis_temperature + " \nHumidity:"+ cimis_humidity+ " \nETO:"+ cimis_eto)
              
        #Print CIMIS to display : Hour, Temp, Humidity
        LCD.display_data(current_hour, data.get_temperature(), data.get_humidity(), cimis_type)
        
        
        #Access temperature and humidity array to grab data 
        #We can use current_hour as our index to access approriate data
        dht_temp = temperature_array[current_hour]
        dht_humidity = humidity_array[current_hour]       

        
        #Clear data from the index so data doesn't overlap 
        temperature_array[current_hour] = None
        humidity_array[current_hour] = None
        
        
        #***************************** Irrigation Process ***************************************************************************************
        #Calculate how long to irrigate for the current hour based on cimis data and local temperature
        #Do irrigation process 
        #do_irrigation(current_hour, data, dht_temp, dht_humidity,hours_passed)
        irrigation_time = irrigation_calculation(data, dht_temp, dht_humidity)
       
        #If irrigation calculation returns 0, no need to irrigate 
        if irrigation_time != 0 :
            GPIO.output(led_pin, GPIO.HIGH) 
            console_data("\n\n******************** IRRIGATION REPORT **************************************")
            console_main("[Irrigation]Irrigate for " + str(irrigation_time) + " seconds")
            
            #Set start and stop time for irrigation 
            start_time = time.time()
            stop_time = 0
            total_time = start_time + irrigation_time + stop_time
            
            #Run irrigation till either PIR sensor detects motion 
            #or if timer runs out (total time) 
            while( time.time() < total_time ):
                #if PIR sensor detects motion, stop irrigation immediatly 
                #otherwise irrigate until timer stops
                if( GPIO.input(pir_pin) == GPIO.HIGH  ):
                    if(stop_time < 60):
                        GPIO.output(led_pin, GPIO.LOW)
                        console_main("[Motion Detected]Irrigation Stopped")
                        time.sleep(10)
                        stop_time = stop_time + 10
        #If no irrigation required 
        else:
            console_main("[No irrigation required]\n\n")


        #Irrigation done
        console_main("[Irrigation]Irrigation Done\n\n")
        current_hour = (current_hour +1) % 24
        hours_passed = hours_passed + 1

        delay_hour = time.time() - delay_hour
        total_delay = total_delay + delay_hour

        if( total_delay < HOUR):
            time.sleep(HOUR - total_delay)
            total_delay = 0
        else:
            total_delay = total_delay - HOUR
                    
            
#************************** Data Handling Thread ******************************************************************

#Thread to handle data 
#This thread will use CIMIS data and properly store to either temperature or humidity array 
def data_thread():
    
    current_time  = START_HOUR
    hours_passed = 0
    accum_temp = 0
    accum_humidity = 0 
    average_temp = 0
    average_humidity = 0
    ONE_HOUR = 60
    #We want to repeat loop until 24 hours has passed, such that hours passed
    #only increments with every hour 

    while ( hours_passed < TOTAL_HOURS ):
        console_data("\n\n******************** LOCAL DHT REPORT **************************************\n")
        dht_type = "DHT"
        #Collect one hour worth of data 
        # "i" represents the index, for our purposes this is the minute 
        for i in range (0,ONE_HOUR,1):
            #Get time of pulling data
            pull_time = time.time()
            #Get current local temperature
            local_temp = get_local_temperature()
            #Get current local humidity 
            local_humidity = get_local_humidity()
            if local_humidity > 100:
                local_humidity = local_humidity - 100
                
            #LED and PIR demo
            # if(GPIO.input(pir_pin) == GPIO.HIGH):
                # print("Motion Detected, Turning LED Off")
                # GPIO.output(led_pin, GPIO.LOW) 
            
            #Accumulate and store local temperature and humidity  
            accum_temp = accum_temp + local_temp
            accum_humidity = accum_humidity + local_humidity
            
            #Print local data to console 
            console_data("  DHT Data #"+ str(i+1) + ":        Temp:" +  str(local_temp) + "       Humidity:" + str(local_humidity)) 
            #Print local data to LCD 
            LCD.display_data(i+1, local_temp, local_humidity, dht_type)
            
            pull_time = time.time() - pull_time
            #Sleep for one minute
            if i is not (ONE_HOUR - 1):
                time.sleep ( ONE_HOUR - pull_time )  
            
            
        average_temp = calculate_avg(accum_temp)
        average_humidity = calculate_avg(accum_humidity) 
        
        #After hour has passed, record and store data to arrays 
        #We also want to prompt console and LCD that hour has passed 
        console_data("\n\n******************** ONE HOUR REPORT **************************************")
        average_type = "Avg"
        print("Averages:")
        print("Temperature: " + str(round(average_temp,1)) + " , Humidity: " + str(round(average_humidity)) )
        LCD.display_data(current_time , average_temp, average_humidity, average_type)
        
        #Store average temperature and humidity to array to tabulate data 
        temperature_array[current_time ] = average_temp
        humidity_array[current_time ] = average_humidity
        
        #To prep for next hour, stall for one minute since we only record data
        #in increments of 1 minute 
        time.sleep ( ONE_HOUR - pull_time )
        current_time  = (current_time  +1) % TOTAL_HOURS
        #Increment hours_passed, loop again 
        hours_passed = hours_passed + 1
        
        #Reset Values 
        average_temp = 0 
        average_humidity = 0 
        accum_temp = 0 
        accum_humidity = 0 

        
#Returns current time : string class 
#Format: Hour:Minute:Second
def time_now():
    return datetime.now().strftime('[%H:%M:%S]')

#Print Current Time to Console 
#Format: Hour:Minute:Second [Data Thread] + 'message' from thread
def console_data(message):
    print( datetime.now().strftime('[%H:%M]')  + message )

#Print Main Thread to Console 
#Format: Hour:Minute:Second [Main Thread] + 'status' from main thread 
def console_main(message):
    print( datetime.now().strftime('[%H:%M]') + message )


def calculate_avg(data):
    return data/60 

#CLEAR AND CLEAN GPIO MODULES 
def cleanup():
    console_main("Program Complete. Cleaning Now")
    #Clear GPIO initialization 
    GPIO.cleanup()
    #Validate cleanup with console message 
    console_main("Program Cleaned. Bye ^.^")

#returns the time to irrigate in seconds based on the cimis data and local average temperature and humidity
def irrigation_calculation(data, local_temp, local_humidity):
    #Declare constants to calculate appropriate time for irrigation 
    #These include plant factor, area of irrigation, irrigation efficiency, and water debit per hour 
    #These values are given per instruction PDF 
    plant_factor = 1.0  
    area_irrigate = 200 
    irrigation_eff = 0.75 
    water_debit = 1020 
    conversion_constant = 0.62 
    
    #Modify ETO for our purposes 
    eto_humiditiy = float(data.get_humidity()) / local_humidity
    eto_temp = local_temp / float(data.get_temperature())
    modified_eto = float(data.get_eto()) * eto_humiditiy * eto_temp
 
    #Calculate how many gallon needed per hour for irrigation 
    num_gallons = modified_eto * plant_factor * area_irrigate * conversion_constant / irrigation_eff 
    gallon_per_hour = num_gallons / float(24) 
    #This will be the time needed to fully irrigate 
    irrigation_time = gallon_per_hour / water_debit 

    return irrigation_time * 60 * 60

#Main Program 
if __name__ == '__main__':
    t = None
    try:
        #Prompt start of program, get and display current time 
        #This time will be used to reference time elapsed 
        print("Program Starting. Current Time:",time.strftime( "%H:%M:%S" ,time.localtime(time.time())) )
        START_HOUR = time.localtime(time.time()).tm_hour
        

        #Begin setup
        setup()
        #Create new data thread and begin pulling data 
        t = threading.Thread(target = data_thread)
        t.daemon = True
        t.start()

        #Run Main Thread 
        mainloop()
        
        #Join Threads
        t.join()
    #Dummy except     
    except KeyboardInterrupt:
        print("Interrupt Detected")
    #Cleanup after end of program to avoid data confliction 
    finally:
        cleanup()

