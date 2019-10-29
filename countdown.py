#imports
import colorsys
import datetime
import time

#constant globals
NUMLEDS = 360
DATAPIN = 10

HOURS = int(25)
MINUTES = int(0)
SECONDS = int(0)

#enables hardware test mode
#will iterate through all possible characters in CHARDICT
#also toggles the colon on and off
#while running performs a color wheel though all hues
TEST_MODE = True
#how much time before going to the next character
TEST_MODE_TIMER = 4.0
#how much to increment hue by in test mode
TEST_MODE_HUE_ITERATOR = 10

#default saturation & value
SATURATION = 255
VALUE = 175


# NOTHING SHOULD NEED TO BE TOUCHED BELOW THIS LINE
# should only be 0 or 1 in the arrays
# maps characters to segments
CHARDICT = {
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
    'o' : [0, 1, 1, 1, 1, 1, 1],
    'h' : [1, 0, 1, 1, 0, 1, 1],
    'i' : [0, 0, 0, 0, 0, 1, 1],
    "test" : [0, 1, 0, 1, 0, 1, 0]
}

#length of the individual segments for each character
SEGLENGTH = [11, 11, 12, 11, 11, 12, 12]

DOTSIZE = [4,4] # the colon dot is a 4x4 matrix in a chain

CHAR1OFFSET = 0
CHAR2OFFSET = 82
COLONOFFSET = 164
CHAR3OFFSET = 196
CHAR4OFFSET = 278

#changing globals
endTime = datetime.datetime.now()
lastTime = datetime.datetime.now()
allowStart = False
innerState = True
HueIterator = 0

#functions
#TODO implement pixel setting
def Setpixel(idNo, red, green, blue):
    print("Pixel: ", idNo, " R: ", red, " G: ", green, " B: ", blue)

def SetColon(inner: bool, outer: bool, red: int, green: int, blue: int):
    qtrX = int(DOTSIZE[0] / 4)
    qtrY = int(DOTSIZE[1] / 4)
    for i in range(DOTSIZE[0]):
        for j in range(DOTSIZE[1]):
            if i in range(qtrX, DOTSIZE[0] - qtrX) and j in range(qtrY, DOTSIZE[1] - qtrY):
                # set the inner part of the first colon dot
                Setpixel(COLONOFFSET + DOTSIZE[0] * i + j, inner * red, inner * green, inner * blue)
                # set the inner part of the second colon dot
                Setpixel(COLONOFFSET + DOTSIZE[0] * i + j + DOTSIZE[0] * DOTSIZE[1], inner * red, inner * green, inner * blue)
            else:
                # set the outer part of the first colon dot
                Setpixel(COLONOFFSET + DOTSIZE[0] * i + j, outer * red, outer * green, outer * blue)
                # set the outer part of the second colon dot
                Setpixel(COLONOFFSET + DOTSIZE[0] * i + j + DOTSIZE[0] * DOTSIZE[1], outer * red, outer * green, outer * blue)

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
            if(i == 4 and j == 1): 
                index += 1 #skip these indicies
            Setpixel(index, red * segment, green * segment, blue * segment)
            index += 1

#when ready to count down set the end time used for the calculation of hours and minutes
def setEndTime():
    global endTime
    delta = datetime.timedelta(hours=HOURS, minutes=MINUTES, seconds=SECONDS)
    endTime = datetime.datetime.now() + delta

def GetHoursRemaining():
    return int((endTime - datetime.datetime.now()).total_seconds() / 3600) 

def GetMinutesRemaining():
    return int((endTime - datetime.datetime.now()).total_seconds() / 60) % 60 

# writes the hours and minutes and toggles the inner part of the colon
# should be called every second
def DisplayTime(hours: int, minutes: int, hue: int, sat: int = SATURATION, val: int = VALUE):
    global innerState
    rgb = colorsys.hsv_to_rgb(hue, sat, val)
    SetCharacter(0, hours / 10 % 10, rgb[0], rgb[1], rgb[2])
    SetCharacter(82, hours % 10, rgb[0], rgb[1], rgb[2])
    SetColon(True, innerState, rgb[0], rgb[1], rgb[2])
    SetCharacter(196, minutes / 10 % 10, rgb[0], rgb[1], rgb[2])
    SetCharacter(278, minutes % 10, rgb[0], rgb[1], rgb[2])
    innerState = False

#will write any mapped character to the display
#if character is unknown
def DisplayChars(char1, char2, char3, char4, colonOuter: bool, colonInner: bool, hue: int, sat: int = SATURATION, val: int = VALUE):
    rgb = colorsys.hsv_to_rgb(hue, sat, val)
    r = rgb[0] if rgb[0] >= 0 else 0
    g = rgb[1] if rgb[1] >= 0 else 0
    b = rgb[2] if rgb[2] >= 0 else 0
    SetCharacter(0, char1, r, g, b)
    SetCharacter(82, char2, r, g, b)
    SetColon(colonOuter, colonInner, r, g, b)
    SetCharacter(196, char3, r, g, b)
    SetCharacter(278, char4, r, g, b)

def CountDown():
    global lastTime, HueIterator 
    #only run once every second
    if((datetime.datetime.now - lastTime).total_seconds < 1): return
    lastTime = datetime.datetime.now()

    #calculate time left
    hours = GetHoursRemaining()
    minutes = GetMinutesRemaining()

    #display the time remaining, if rolls negative then write 0
    DisplayTime(hours if hours > 0 else 0, minutes if minutes > 0 else 0, HueIterator)

    #iterate the hue
    HueIterator = HueIterator + 1 if HueIterator < 360 else 0
    #TODO implement a done


def HWDebug():
    global HueIterator
    toggle = False
    for char in CHARDICT:
        #display charcter from dict
        DisplayChars(char, char, char, char, toggle, toggle, HueIterator)

        #iterate the hue and toggle the colon state
        HueIterator = HueIterator + TEST_MODE_HUE_ITERATOR if HueIterator < 360 else 0
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
        DisplayChars('o', 'h', 'i', 'o', False, False, 0)

        while not allowStart:
            #TODO poll GPIO and set to allowStart
            time.sleep(0.01)

        while True:
            CountDown()

except KeyboardInterrupt:
    print("User ordered stop")
    DisplayChars('\0', '\0', '\0', '\0', False, False, 0)