from __future__ import print_function
import json
from urllib.request import urlopen
import urllib
from datetime import datetime, timedelta
import time


#App Key for et.water.ca.gov to request and access weather data for our program 
#This app key was given from registration for developer account 

#For this project we want to reference Irvine, whose station is indexed as 75 
app_key = 'a248a1ef-7fec-4143-b89e-9448804b615b'
irvine_station  = 75            
#This will be called from the main function to index the current hour that 
#we need to use to get CIMIS data from. Current_hour is the same index during runtime 
#that we used in the main program. Since we are within 24 Hour formatting, there is a special case 
#when current_hour = 0. In this case it is midnight so we want to grab CIMIS data from the previous day. 
#If this isn't the case we grab data from time as is. 
def cimis_hour (current_hour):
  
    date = datetime.now().strftime('%Y-%m-%d')

    #call cimis_url to get data from url parsed for cimis_url 
    data = cimis_url(app_key, irvine_station , date, date)
    #if data received is null or None, return None and main function will prompt 
    #user that something has gone wrong or data is not avalible 
    if data is None:
        return None
    #else return data received from CIMIS using 3D array which indexes the hour of retrieval, 
    #category of data, and the actual value itself 
    #GlyRelHum, HlyAirTmp, HlyEto are protocols used to address data in CIMIS 
    else:
        data_received = cimis_data( data[current_hour-1]['HlyRelHum']['Value'], data[current_hour-1]['HlyAirTmp']['Value'],data[current_hour-1]['HlyEto']['Value'])
        #return data to main function 
        return data_received
   
#This function pings and sends a request to et.water.ca.gov 
#since we want our request to be dynamic such that we only want 
#certain data from a specific time frame we need to parse our own url 
#once url is generated, send request and listen for response 
#if sucessfull, extract and return data, else simply return none and main funciton 
#will prompt user accordingly 
def cimis_url(app_key, irvine_station , start, end):
    request_data = ['hly-air-tmp','hly-eto','hly-rel-hum']

    dataItems = ','.join(request_data)
    
    url = ('http://et.water.ca.gov/api/data?appKey=' + app_key + 
           '&targets=' + str(irvine_station ) + 
           '&startDate=' + start + 
           '&endDate=' + end + 
           '&dataItems=' + dataItems +'&unitOfMeasure=M')
    try:
        content = urlopen(url).read().decode('utf-8')        
        data = json.loads(content)
    except: 
        print("CIMIS Request Failed....")
        data = None
            
    if(data is None):
        return None    
    else:
        return data['Data']['Providers'][0]['Records']
        
        
        
#CIMIS class to delegate and store weather information
#If main program calls for instance, get_temperature(), assuming a class 
#has been created, the function will return the temperature recorded from 
#CIMIS rather than the local DHT module. For our purposes we only need humidity, temperature
#and ETO 
class cimis_data:
    def __init__(self, humidity, temperature, eto):
        self.humidity = humidity
        self.temperature = temperature
        self.eto = eto
    def get_humidity(self):
        return self.humidity
    def get_temperature(self):
        return self.temperature
    def get_eto(self):
        return self.eto