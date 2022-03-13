##from ST7789 import *
#import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import ST7789 as TFT
import time
from PIL import Image, ImageDraw, ImageFont, ImageColor

RST = 27
DC  = 25
LED = 24
SPI_PORT = 0
SPI_DEVICE = 0
SPI_MODE = 0b11
SPI_SPEED_HZ = 40000000


fontH = ImageFont.truetype('./fonts/Hack-Regular.ttf', 22, encoding='unic')
fontG = ImageFont.truetype('./fonts/Gugi-Regular.ttf', 22, encoding='unic')
fontC = ImageFont.truetype('./fonts/Gugi-Regular.ttf', 18, encoding='unic')

disp = TFT.ST7789(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=SPI_SPEED_HZ),
       mode=SPI_MODE, rst=RST, dc=DC, led=LED)

def expand2square(pil_img, background_color):
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result

def clearDsp():
    image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    #draw = ImageDraw.Draw(image)
    #draw.rectangle((0,0, 240, 240), outline=0, fill=(0,0,0))
    disp.display(image)
    disp.clear()

def changeImage(filename):
    disp.clear()
    image = Image.open(filename)
    image.thumbnail((240, 240), Image.ANTIALIAS)
    image = expand2square(image, (0, 0, 0))
    disp.display(image)

'''
def pasteFile(image_main, filename):
    fileimg = Image.open(filename)
    fileimg.thumbnail((240, 240), Image.ANTIALIAS)
    fileimg = expand2square(fileimg, (0, 0, 0))
    image_main.paste(fileimg, (0, 0), fileimg)
    return image_main
'''
def textIt(image, text, position = (0,0), txtColor=(255,255,255)):
    #disp.clear()
    #image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    position = position[0], position[1]
    font = fontG
    angle = 0
    draw = ImageDraw.Draw(image)
    width, height = draw.textsize(text, font=font)
    textimage = Image.new('RGBA', (width, height), (0,0,0,0))
    textdraw = ImageDraw.Draw(textimage)
    textdraw.text((0, 0), text, font=font, fill=txtColor)
    rotated = textimage.rotate(angle, expand=1)
    image.paste(rotated, position, rotated)
    #draw.text((startX, startY), text, "orange", font=font)
    #disp.display(image)

def textOverImage(filename, text, txtPos=(0,0), txtColor=((255,255,255))):
    disp.clear()
    image = Image.open(filename)
    image.thumbnail((240, 240), Image.ANTIALIAS)
    image = expand2square(image, (0, 0, 0))
    disp.display(image)

    position = txtPos[0], txtPos[1]
    font = fontG
    angle = 0
    draw = ImageDraw.Draw(image)
    width, height = draw.textsize(text, font=font)
    textimage = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    textdraw = ImageDraw.Draw(textimage)
    textdraw.text((0, 0), text, font=font, fill=txtColor)
    rotated = textimage.rotate(angle, expand=1)
    image.paste(rotated, position, rotated)
    disp.display(image)

def drawData(datac):
    disp.clear()
    image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    #image = Image.new('RGBA', (disp.width, disp.height), (0, 0, 0, 0)) #this is a transparent background
    posX = [35, 20, 10, 10, 20, 35]
    posY = [40, 70, 100, 130, 160, 190]
    colrs = ["orange", "skyblue", "pink", "pink", "red", "green"]
    for i in range(len(datac)):
        textIt(image, datac[i], (posX[i], posY[i]), txtColor=colrs[i])

    disp.display(image)

def crcData(datac, backgr_file):
    #1. normalizing the data in %, from 0 to 100
    #datac[2] = -1.34
    normlz = [0.0, 0, 0.0, 0.0]
    colrs = ["green", "skyblue", "orange", "red"]

    #battery voltage min=3.2; max = 4.0 -> difference = 0.8 ||--> % = ((current - min) * 100 )/0.8
    if datac[0]>4: normlz[0] = 100
    else: normlz[0] = int(((datac[0] - 3.2)*100)/0.8)
    batxt = f"{datac[0]}V"

    #energy consumption: min=0A, max = 4A ||--> % =
    if datac[3] > 0:
        normlz[3] = int((datac[3] / 4) * 100)
        enrgtxt = f"-{datac[3]}A"
        colrs[3] = "red"
    else:
        normlz[3] = -int((datac[3]/4)*100)
        enrgtxt = f"+{-datac[3]}A"
        colrs[3] = "yellow"


    #the rest inputs are in % already
    normlz[1] = datac[1]
    cputxt = f"{int(datac[1])}%"
    if datac[2] < 0: normlz[2] = -(datac[2]) #if somehow the temperature drops below 0, temperature bar stay 0
    else: normlz[2] = datac[2]
    tmptxt = f"{round(datac[2], 1)}C"

    disp.clear()
    image = Image.open(backgr_file)
    image.thumbnail((240, 240), Image.ANTIALIAS)
    image = expand2square(image, (0, 0, 0))

    '''#clearing the ring:
    draw.arc((0,0, disp.width, disp.height), start=0, end = 360, width = 20, fill="black")
    draw.rectange((0, 0, 239, 40), fill="black")
    draw.rectange((0, 200, 239, 239), fill="black")'''

    textimage = Image.new('RGBA', (disp.width, disp.height), (0, 0, 0, 0))
    textdraw = ImageDraw.Draw(textimage)
    textdraw.text((100, 0), "CPU", font=fontC, fill="white")

    ofst = 55
    textdraw.text((0 + ofst, 20), cputxt, font=fontC, fill=colrs[1])
    w, h = textdraw.textsize(tmptxt, font=fontC)
    textdraw.text((disp.width - w - ofst, 20), tmptxt, font=fontC, fill=colrs[2])

    textdraw.text((100, 224), "BAT", font=fontC, fill="white")
    ofst1 = 50
    textdraw.text((ofst1, 202), batxt, font=fontC, fill=colrs[0])
    w, h = textdraw.textsize(enrgtxt, font=fontC)
    textdraw.text((disp.width - w - ofst1, 202), enrgtxt, font=fontC, fill=colrs[3])
    # rotated = textimage.rotate(0, expand=1)
    image.paste(textimage, (0, 0), textimage)

    shape = Image.new('RGBA', (disp.width, disp.height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shape)
    for i in range(0,4):
        shape = Image.new('RGBA', (disp.width, disp.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(shape)
        y = 200 - int(normlz[i] * 1.6) #the percentage values are converted to pixels from 0 to 160

        if i<2:
            start = 90
            end = 270
        else:
            start = 270
            end = 90

        if i ==0 or i==3:
            draw.arc((0,0, 239,239), start=start, end=end, width=7, fill=colrs[i])
        else:
            draw.arc((11,11, 229,229), start=start, end=end, width=7, fill=colrs[i])

        cropped = shape.crop((0, y, 239, 200))
        image.paste(cropped, (0,y), cropped)


    '''
    disp.clear()
    
    textimage = Image.new('RGBA', (disp.width, disp.height), (0, 0, 0, 0))
    textdraw = ImageDraw.Draw(textimage)
    textdraw.text((100, 0), "CPU", font=fontC, fill="white")

    ofst = 55
    textdraw.text((0+ofst, 20), cputxt, font=fontC, fill=colrs[1])
    w, h = textdraw.textsize(tmptxt, font=fontC)
    textdraw.text((disp.width-w-ofst, 20), tmptxt, font=fontC, fill=colrs[2])

    textdraw.text((100, 224), "BAT", font=fontC, fill="white")
    ofst1 = 50
    textdraw.text((ofst1, 202), batxt, font=fontC, fill=colrs[0])
    w,h = textdraw.textsize(enrgtxt, font=fontC)
    textdraw.text((disp.width - w - ofst1, 202), enrgtxt, font=fontC, fill=colrs[3])
    #rotated = textimage.rotate(0, expand=1)
    image.paste(textimage, (0,0), textimage)

    for i in range(0, 4):
        if i == 2: i =3
        elif i ==3: i=2
        shape = Image.new('RGBA', (disp.width, disp.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(shape)
        if i == 0 or i == 3:
            draw.ellipse((0, 0, 239, 239), fill=colrs[i], outline=(0, 0, 0))
            draw.ellipse((7, 7, 232, 232), fill=(0, 0, 0), outline=(0, 0, 0))
        else:
            draw.ellipse((11, 11, 229, 229), fill=colrs[i], outline=(0, 0, 0))
            draw.ellipse((18, 18, 222, 222), fill=(0, 0, 0), outline=(0, 0, 0))
        y = 200 - int(normlz[i] * 1.6)
        #print(f"i = {i}, y = {y}")
        if i < 2:
            cut_area = (0, y, 100, 200)
            cropped = shape.crop(cut_area)
            image.paste(cropped, (0,y), cropped)
        else:
            cut_area = (disp.width - 100, y, 239, 200)
            cropped = shape.crop(cut_area)
            image.paste(cropped, (disp.width - 100, y), cropped)
    '''
    disp.display(image)



# Initialize  and clear the display.
disp.begin()
disp.clear()


'''
datac = [4.14, 0, 0.0, 3.23] #battery %, CPU load %, CPU temp C, battery load A

#import os
from gpiozero import LoadAverage
from gpiozero import CPUTemperature

ico_lst = ['./ico/nn1s.jpg','./ico/nn2s.jpg','./ico/nn3s.jpg']
i=0
while True:
    #usage = os.popen("awk '{print $1}' /proc/loading").readline()
    usage = LoadAverage(min_load_average=0, max_load_average=1)
    cpu = CPUTemperature()
    datac[2] = round(cpu.temperature, 1)
    datac[1] = int(usage.load_average * 100)
    crcData(datac, ico_lst[i])

    if i>=2: i=0
    else: i+=1
    time.sleep(1)

while True:
    changeImage('./ico/load1s.jpg')
    time.sleep(0.1)
    changeImage('./ico/load2s.jpg')
    time.sleep(0.1)
    changeImage('./ico/load3s.jpg')
    time.sleep(0.1)


print("changing the image...")
changeImage('./ico/radioactive1.jpg')
time.sleep(3)
print("Display clear...")
time.sleep(1)
clearDsp()
print("done")
time.sleep(1)
print("Drawing text...")
time.sleep(2)
#txt = "CORE: 0.546'C"
#image = Image.new("RGB", (disp.width, disp.height), "BLACK")
#textIt(image, "CORE: 45.54 'C", (20, 80), txtColor="RED")
#textIt(image, "PWR: 0.546 mA", (20, 110), txtColor="ORANGE")
#textIt(image, "BAT: 4.01 V", (20, 140), txtColor="GREEN")

#clearDsp()
#textOverImage('./ico/radioactive1.jpg', txt, (30, 100), txtColor="RED")
'''