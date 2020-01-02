#imports
import colorsys
import datetime
import time
from rpi_ws281x import *
from gpiozero import *

#constants
LED_COUNT = 360
LED_STRIP = ws.WS2811_STRIP_RGB
LED_PIN = 21 #BCM pin (21 is actaully pin 40 on the gpio header)
LED_DMA = 10 #DMA channel to use on SPI (10 is recomended 5 WILL CORRUPT OS)
LED_CHANNEL = 0 #set to 1 for GPIOs 13, 19, 41, 45, 53
LED_FREQ = 800000 #should be 800khz 

#amount of time the clock will count down for
#the theoretical maximum is 99 hours, 99 mins, 99 seconds
#for the clock to display properly
HOURS = int(1)
MINUTES = int(0)
SECONDS = int(0)
HARD_END = None
#HARD_END = datetime.datetime(year = 2019, month = 11, day = 1, hour = 22, minute = 0, second = 0)

#enables hardware test mode
#will iterate through all possible characters in CHARDICT
#also toggles the colon on and off
#while running performs a color wheel though all hues
TEST_MODE = False
#how much time before going to the next character
TEST_MODE_TIMER = 2.0
#how much to increment hue by in test mode
TEST_MODE_HUE_ITERATOR = 0.02

#default saturation, value & strip brightness
SATURATION = 1
VALUE = 1
BRIGHTNESS = 200
CLOCK_HUE_ITERATOR = 0.00003
OHIO_RED = 0.33


# NOTHING SHOULD NEED TO BE TOUCHED BELOW THIS LINE
# maps characters to segments
CHARDICT = {
    #SHOULD ONLY BE 1 OR 0 INSIDE ARRAYS
    '\0' : [0, 0, 0, 0, 0, 0, 0],
    0 : [1, 1, 1, 1, 1, 1, 0],
    1 : [0, 0, 0, 1, 1, 0, 0],
    2 : [0, 1, 1, 0, 1, 1, 1],
    3 : [0, 0, 1, 1, 1, 1, 1],
    4 : [1, 0, 0, 1, 1, 0, 1],
    5 : [1, 0, 1, 1, 0, 1, 1],
    6 : [1, 1, 1, 1, 0, 1, 1],
    7 : [0, 0, 0, 1, 1, 1, 0],
    8 : [1, 1, 1, 1, 1, 1, 1],
    9 : [1, 0, 0, 1, 1, 1, 1],
    'o' : [1, 1, 1, 1, 1, 1, 0],
    'h' : [1, 1, 0, 1, 1, 0, 1],
    'i' : [1, 1, 0, 0, 0, 0, 0],
    "test" : [0, 1, 0, 1, 0, 1, 0]
}

#length of the individual segments for each character
SEGLENGTH = [11, 11, 12, 11, 11, 12, 12]
DOTSIZE = [4,4] # the colon dot is a 4x4 matrix in a chain
LOGOLENGTH = 34


#starting indicies for each character
CHAR1OFFSET = 0
CHAR2OFFSET = 82
COLONOFFSET = 164
CHAR3OFFSET = 196
CHAR4OFFSET = 278
LOGO_OFFSET = 360

#globals
allowStart = True #set this to true to override the button press and go straight into countdown
innerState = True
HueIterator = 0
endTime = datetime.datetime.now()
lastTime = datetime.datetime.now()

#Hardware definitions
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ, LED_DMA, False, BRIGHTNESS, LED_CHANNEL, LED_STRIP)
strip.begin()
startButton = button(13)

#functions
#TODO implement pixel setting
def Setpixel(idNo, red, green, blue):
    #print("Pixel: ", idNo, " R: ", red, " G: ", green, " B: ", blue)
    strip.setPixelColor(idNo, Color(red, green, blue))
    return

def SetColon(inner: bool, outer: bool, red: int, green: int, blue: int):
    qtrX = int(DOTSIZE[0] / 4)
    qtrY = int(DOTSIZE[1] / 4)
    for i in range(DOTSIZE[0]):
        for j in range(DOTSIZE[1]):
            if i in range(qtrX, DOTSIZE[0] - qtrX) and j in range(qtrY, DOTSIZE[1] - qtrY):
                # set the inner part of the first colon dot
                Setpixel(COLONOFFSET + DOTSIZE[0] * i + j, outer * red, outer * green, outer * blue)
                # set the inner part of the second colon dot
                Setpixel(COLONOFFSET + DOTSIZE[0] * i + j + DOTSIZE[0] * DOTSIZE[1], outer * red, outer * green, outer * blue)
            else:
                # set the outer part of the first colon dot
                Setpixel(COLONOFFSET + DOTSIZE[0] * i + j, inner * red, inner * green, inner * blue)
                # set the outer part of the second colon dot
                Setpixel(COLONOFFSET + DOTSIZE[0] * i + j + DOTSIZE[0] * DOTSIZE[1], inner * red, inner * green, inner * blue)

def SetLogo(offset: int, on : bool, red: int, green: int, blue: int):
    for i in range(LOGOLENGTH):
        Setpixel(i + LOGO_OFFSET, red * on, blue * on, green * on)

def SetCharacter(offset: int, character, red: int, green: int, blue: int):
    index = offset
    #iterate over the segments
    for i in range(len(SEGLENGTH)):
        #get if segment should be on or off
        #if character is not found segment defaults to off
        segment = CHARDICT.get(character, CHARDICT['\0'])[i]
        #figure out the length in pixels of the segment
        leds = SEGLENGTH[i]
        #iterate over the number of pixels
        for j in range(leds):
            if(i == 1 and j == 0): 
                index += 1 #skip these indicies
            if(i == 4 and j == 0): 
                index += 1 #skip these indicies
            Setpixel(index, red * segment, green * segment, blue * segment)
            index += 1

#when ready to count down set the end time used for the calculation of hours and minutes
# or defer to HARD_END if set
def setEndTime():
    global endTime
    if HARD_END is None:
        delta = datetime.timedelta(hours=HOURS, minutes=MINUTES, seconds=SECONDS)
        endTime = datetime.datetime.now() + delta
    else:
        endTime = HARD_END

def GetHoursRemaining():
    return int((endTime - datetime.datetime.now()).total_seconds() / 3600) 

def GetMinutesRemaining():
    return int((endTime - datetime.datetime.now()).total_seconds() / 60) % 60 

def GetSecondsRemaining():
    return (endTime - datetime.datetime.now()).total_seconds() % 60

# writes the hours and minutes and toggles the inner part of the colon
# should be called every second
def DisplayTime(hours: int, minutes: int, hue, sat = SATURATION, val = VALUE, allowToggle = True):
    global innerState

    #calculate the colors form HSV
    rgb = colorsys.hsv_to_rgb(hue, sat, val)
    r = int(rgb[0] * 255) if rgb[0] >= 0 else 0
    g = int(rgb[1] * 255) if rgb[1] >= 0 else 0
    b = int(rgb[2] * 255) if rgb[2] >= 0 else 0

    #write the characters into the buffer
    SetCharacter(CHAR1OFFSET, int(hours / 10 % 10), r, g, b)
    SetCharacter(CHAR2OFFSET, hours % 10, r, g, b)
    SetColon(True, innerState, r, g, b)
    SetCharacter(CHAR3OFFSET, int(minutes / 10 % 10), r, g, b)
    SetCharacter(CHAR4OFFSET, minutes % 10, r, g, b)
    SetLogo(LOGO_OFFSET, True, r, g, b)

    #show the buffer on the LED strip
    strip.show()
    
    if allowToggle: innerState = not innerState

#will write any mapped character to the display
#if character is unknown, null character is used
def DisplayChars(char1, char2, char3, char4, colonOuter: bool, colonInner: bool, logo: bool, hue, sat = SATURATION, val = VALUE):
    #calculate the colors from HSV
    rgb = colorsys.hsv_to_rgb(hue, sat, val)
    r = int(rgb[0] * 255) if rgb[0] >= 0 else 0
    g = int(rgb[1] * 255) if rgb[1] >= 0 else 0
    b = int(rgb[2] * 255) if rgb[2] >= 0 else 0

    # write the charcters to the buffer
    SetCharacter(CHAR1OFFSET, char1, r, g, b)
    SetCharacter(CHAR2OFFSET, char2, r, g, b)
    SetColon(colonOuter, colonInner, r, g, b)
    SetCharacter(CHAR3OFFSET, char3, r, g, b)
    SetCharacter(CHAR4OFFSET, char4, r, g, b)
    SetLogo(LOGO_OFFSET, logo, r, g, b)

    #show the buffer on the LED strip
    strip.show()


def HWDebug():
    global HueIterator
    toggle = False
    print("entering HW Debug")
    for char in CHARDICT:
        #display charcter from dict
        DisplayChars(char, char, char, char, toggle, toggle, toggle, HueIterator)

        #iterate the hue and toggle the colon state
        HueIterator = HueIterator + TEST_MODE_HUE_ITERATOR if HueIterator < 1 else 0
        toggle = not toggle

        #allow time for the leds to hold
        time.sleep(TEST_MODE_TIMER)
        

#main code
try: 
    if TEST_MODE:
        while True:
            HWDebug()

    else:
        # show OHIO on boot
        DisplayChars('o', 'h', 'i', 'o', False, False, True, OHIO_RED)

        #this is intended for use with the button
        while not allowStart:
            allowStart = startButton.is_pressed
            time.sleep(0.1)

        setEndTime()
        hours = GetHoursRemaining()
        minutes = GetMinutesRemaining()
        seconds = GetSecondsRemaining()

        #countdown loop   handles the actual countdown
        while datetime.datetime.now < endTime:
            #only run once every second
            if((datetime.datetime.now() - lastTime).total_seconds() % 0.05 > 0):
                #display the time remaining, if rolls negative then write 0
                if hours > 0:
                    DisplayTime(hours if hours > 0 else 0, minutes if minutes > 0 else 0, HueIterator, allowToggle=False)
                else:
                    DisplayTime(minutes if minutes > 0 else 0, seconds if seconds > 0 else 0, HueIterator, allowToggle=False)

                HueIterator = HueIterator + CLOCK_HUE_ITERATOR if HueIterator < 1 else 0

            if((datetime.datetime.now() - lastTime).total_seconds() > 1):
                lastTime = datetime.datetime.now()

                #calculate time left
                hours = GetHoursRemaining()
                minutes = GetMinutesRemaining()
                seconds = GetSecondsRemaining

                print(int(hours / 10 % 10), hours % 10, ":", int(minutes / 10 % 10), minutes % 10)

                #display the time remaining, if rolls negative then write 0
                if hours > 0:
                    DisplayTime(hours if hours > 0 else 0, minutes if minutes > 0 else 0, HueIterator, allowToggle=False)
                else:
                    DisplayTime(minutes if minutes > 0 else 0, seconds if seconds > 0 else 0, HueIterator, allowToggle=False)

                #iterate the hue
                HueIterator = HueIterator + CLOCK_HUE_ITERATOR if HueIterator < 1 else 0

        #post countdown loop  flashes 00:00
        while True:
            if((datetime.datetime.now() - lastTime).total_seconds() % 3 > 2):
                lastTime = datetime.datetime.now()
                DisplayChars(0, 0, 0, 0, True, True, True, HueIterator)

            elif((datetime.datetime.now() - lastTime).total_seconds() % 3 > 1):
                DisplayChars('\0', '\0', '\0', '\0', False, False, True, HueIterator)

except KeyboardInterrupt:
    print("User ordered stop\nHalting at", GetHoursRemaining(), ":", GetMinutesRemaining(), "\nEnd time was scheduled for:", endTime)

finally:
    DisplayChars('\0', '\0', '\0', '\0', False, False, False, 0)
