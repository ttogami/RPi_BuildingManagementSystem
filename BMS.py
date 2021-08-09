import RPi.GPIO as GPIO
#import modules for LCD
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
#import modules for DHT111
import Freenove_DHT as DHT
#import modules for CIMIS
import CIMIS
import time
#imports for pushbutton interrupt
import signal
import sys

ledPin = 12       # define ledPin
sensorPin = 13   # define sensorPin changed to GPIO 27
DHTPin = 11     #define the pin of DHT11
Door_Window_Button=37 #button is GPIO6
RED_LED=32 #GPIO 12
BLUE_LED=35 # GPIO 19
RED_BUTTON=38 #GPIO 20
BLUE_BUTTON=40 #GPIO 21



#global var
time_out=10 #if no motion detected after 10 sec turn off led
motionDetect_time=0
firstMotionDetect=0
door_window_open=0
last3Temp=[0,0,0]
count=0
feelsLikeTemp=70
desiredTemp=70
hvacControl=0 #0 if off, 1 if AC, 2 if Heat 

status="CLOSED"
def button_pressed(channel):

    global door_window_open
    global status
    print("Button pressed")
    if(door_window_open==0):
        door_window_open=1
        status="OPEN  "
    else:
        door_window_open=0
        status="CLOSED"


def setup():
    global last3Temp
    global count
    GPIO.setmode(GPIO.BOARD)        # use PHYSICAL GPIO Numbering
    GPIO.setup(ledPin, GPIO.OUT)    # set ledPin to OUTPUT mode
    GPIO.setup(BLUE_LED, GPIO.OUT)    # set ledPin to OUTPUT mode
    GPIO.setup(RED_LED, GPIO.OUT)    # set ledPin to OUTPUT mode
    GPIO.setup(sensorPin, GPIO.IN)  # set sensorPin to INPUT mode
    GPIO.setup(Door_Window_Button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RED_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BLUE_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #GPIO.add_event_detect(Door_Window_Button, GPIO.FALLING,callback=button_pressed, bouncetime=400)
    dht = DHT.DHT(DHTPin)   #create a DHT class object
    for i in range(0,15*3):
        chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
        if (chk is dht.DHTLIB_OK):      #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
            print("DHT11,OK!")
            last3Temp[count]=dht.temperature
            print(last3Temp[count])
            count=count+1
            if(count==3):
                break


def loop():
    global feelsLikeTemp
    global desiredTemp
    global hvacControl #0 if off, 1 if AC, 2 if Heat 
    global last3Temp
    global count
    global time_out
    global motionDetect_time
    global firstMotionDetect
    global status
    global door_window_open
    mcp.output(3,1)     # turn on LCD backlight
    lcd.begin(16,2)     # set number of LCD lines and columns
    dht = DHT.DHT(DHTPin)   #create a DHT class object

    while True:
        if(GPIO.input(Door_Window_Button)==False):
            print("Button Pressed")
            if(door_window_open==0):
                door_window_open=1
                lcd.clear()
                lcd.setCursor(0,0)
                lcd.message("DOOR/WINDOW OPEN")
                lcd.setCursor(0,1)
                lcd.message("  HVAC HALTED")
                status="OPEN "
                time.sleep(3)
            else:
                door_window_open=0
                lcd.clear()
                lcd.setCursor(0,0)
                lcd.message("DOOR/WIN CLOSED")
                lcd.setCursor(0,1)
                lcd.message("  HVAC RESUMED")
                status="CLOSED"
                time.sleep(3)
            lcd.clear()
        if(GPIO.input(BLUE_BUTTON)==False):
            if(desiredTemp>65):
                desiredTemp=desiredTemp-1
                if(desiredTemp==feelsLikeTemp -3):
                    lcd.clear()
                    lcd.setCursor(0,0)
                    lcd.message(" HVAC AC")
                    time.sleep(3)
                    lcd.clear()
        if(GPIO.input(RED_BUTTON)==False):
            if(desiredTemp<85):
                desiredTemp=desiredTemp+1
                if(desiredTemp==feelsLikeTemp+3):
                    lcd.clear()
                    lcd.setCursor(0,0)
                    lcd.message( "HVAC HEAT")
                    time.sleep(3)
                    lcd.clear()

        if GPIO.input(sensorPin)==GPIO.HIGH:
            GPIO.output(ledPin,GPIO.HIGH) # turn on led
            firstMotionDetect=firstMotionDetect+1
            if(firstMotionDetect==1):
                print ('motion detected >>>')
            motionDetect_time=time.time()
            #time.sleep(10) #wait for 10 seconds
        else :
            if(time.time()-motionDetect_time>=time_out):
                GPIO.output(ledPin,GPIO.LOW) # turn off led
                firstMotionDetect=0
            #print ('led turned off <<<')

        for i in range(0,15):
            chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
            if (chk is dht.DHTLIB_OK):      #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
                print("DHT11,OK!")
                break
        
        lcd.setCursor(0,1)
        if door_window_open==1:
            #lights off
            #HVAC OFF
            GPIO.output(BLUE_LED,GPIO.LOW) # turn off led
            GPIO.output(RED_LED,GPIO.LOW) # turn off led
            lcd.message("H: OFF")
        elif desiredTemp <= feelsLikeTemp -3:
            #AC ON
            #BLUE LIGHT ON
            GPIO.output(BLUE_LED,GPIO.HIGH) # turn on led
            GPIO.output(RED_LED,GPIO.LOW) 
            lcd.message("H:  AC")
        elif desiredTemp >= feelsLikeTemp+3:
            #HEAT ON
            #RED LIGHT ON
            GPIO.output(BLUE_LED,GPIO.LOW) 
            GPIO.output(RED_LED,GPIO.HIGH) # turn on led
            lcd.message("H:HEAT")
        else:
            GPIO.output(BLUE_LED,GPIO.LOW) 
            GPIO.output(RED_LED,GPIO.LOW) 
            lcd.message("H: OFF")
        
        lcd.setCursor(10,1)  # set cursor position
        if(firstMotionDetect>0):
            light=" ON"
        else:
            light="OFF"
        lcd.message( 'L:' +light +'\n' )
        lcd.setCursor(0,0)  # set cursor position
        last3Temp[count%3]=dht.temperature
        avg=last3Temp[0]+last3Temp[1]+last3Temp[2]
        avg=avg/3
        avg=(avg*(9/5)+32)
        count=count+1
        feelsLikeTemp=round(avg+ 0.05 * CIMIS.get_CIMIS_humidty())
        lcd.message("%d/%d"%(feelsLikeTemp,desiredTemp))
        lcd.setCursor(8,0)
        lcd.message("D:"+status)

def destroy():
    lcd.clear()
    GPIO.cleanup()                     # Release GPIO resource

PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.
# Create PCF8574 GPIO adapter.
try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:
    try:
        mcp = PCF8574_GPIO(PCF8574A_address)
    except:
        print ('I2C Address Error !')
        exit(1)
# Create LCD, passing in MCP GPIO adapter.
lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)

if __name__ == '__main__':     # Program entrance

    print ('Program is starting...')
    setup()

    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        destroy()