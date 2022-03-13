import numpy as np
import smbus2
import time
import math
import csv

bus = smbus2.SMBus(1)
def read_byte(device, adr):
    return bus.read_byte_data(device, adr)
    #return bus.

def write_byte(device, adr, value):
    bus.write_byte_data(device, adr, value)


class COMPASS:
    def __init__(self, device_adress = 0x1e):
        self.device = device_adress
        write_byte(self.device, 0x00, 0b01110000)  # write to conf_reg A ->> Set to 8 samples @ 15Hz /
        write_byte(self.device, 0x01, 0b10000000)  # write to conf_reg B ->> Configuration Register B - 4 gain LSb
        write_byte(self.device, 0x02, 0b00000000)  # write to mode_reg ->> Continuous sampling

    def readX(self, regList):
        MSB = regList[0]
        LSB = regList[1]
        ls = [MSB, LSB]
        bt = bytes(ls)
        xdt = int.from_bytes(bt, "big")
        if xdt > 32768:
            xdt = xdt - 65535
        # print(f"X conversion = {bt}")
        return xdt

    def readY(self, regList):
        MSB = regList[4]
        LSB = regList[5]
        ls = [MSB, LSB]
        bt = bytes(ls)
        ydt = int.from_bytes(bt, "big")
        if ydt > 32768:
            ydt = ydt - 65535
        # print(f"Y conversion = {bt}")
        return ydt

    def readCompass(self, x_offset=304.5, y_offset=49.5):
        regList = [read_byte(self.device, 0x03), read_byte(self.device, 0x04), read_byte(self.device, 0x05), read_byte(self.device, 0x06),
                 read_byte(self.device, 0x07), read_byte(self.device, 0x08)]
        x_out = self.readX(regList)
        y_out = self.readY(regList)

        x_out = x_out - x_offset
        y_out = y_out - y_offset

        bearing = math.atan2(y_out, x_out)
        if bearing < 0:
            bearing += 2 * math.pi
        # print(f"Bearing: {round(bearing, 2)} deg.")
        return int(math.degrees(bearing))

    def calibrateCompass(self):
        dataList = []
        print("Initializing... ")
        regList = [read_byte(self.device, 0x03), read_byte(self.device, 0x04), read_byte(self.device, 0x05), read_byte(self.device, 0x06),
                 read_byte(self.device, 0x07), read_byte(self.device, 0x08)]
        minx = self.readX(regList)
        maxx = self.readX(regList)
        miny = self.readY(regList)
        maxy = self.readY(regList)
        time.sleep(0.5)
        print(f"minx=maxx = {minx} | miny=maxy = {miny}")
        print("Taking 500 readings every 0.1s...")
        print("--------------------------------")
        for i in range(0, 500):
            regList = [read_byte(self.device, 0x03), read_byte(self.device, 0x04), read_byte(self.device, 0x05),
                     read_byte(self.device, 0x06), read_byte(self.device, 0x07), read_byte(self.device, 0x08)]
            x_out = self.readX(regList)
            y_out = self.readY(regList)

            if x_out < minx:
                minx = x_out
            if y_out < miny:
                miny = y_out
            if x_out > maxx:
                maxx = x_out
            if y_out > maxy:
                maxy = y_out

            readValue = {}
            readValue["Xraw"] = x_out
            readValue["Yraw"] = y_out
            readValue["X"] = 0
            readValue["Y"] = 0
            dataList.append(readValue)

            time.sleep(0.1)

        x_offset = (maxx + minx) / 2
        y_offset = (maxy + miny) / 2
        print ("Calibration Data ready: ")
        print ("minx: ", minx)  # 0
        print ("miny: ", miny)  # 0
        print ("maxx: ", maxx)  # 470.12
        print ("maxy: ", maxy)  # 204.24
        print ("x offset: ", x_offset)
        print ("y offset: ", y_offset)
        print("--------------------------------")
        print("Creating Calibration File...")
        for val in dataList:
            val["X"] = val["Xraw"] - x_offset
            val["Y"] = val["Yraw"] - y_offset
        outputFile = "Compass_Call_{0}.csv".format(int(time.time()))
        try:
            with open(outputFile, "w") as csvFile:
                dictWriter = csv.DictWriter(csvFile, ["Xraw", "Yraw", "X", "Y"])
                dictWriter.writeheader()
                dictWriter.writerows(dataList)
            print(f"Data has being saved into {outputFile}.")
        except:
            print("An error ocured while writing the file.")

class ACCELEROMETER:
    def __init__(self, device_adress = 0x53):
        self.device = device_adress
        write_byte(self.device, 0x2C, 0x0B)  # Set to 200bit/s, normal power mode
        value = read_byte(self.device, 0x31)
        value &= ~0x0F
        value |= 0x0B
        value |= 0x08
        write_byte(self.device, 0x31, value)  # rewriting stat register for +-2g / 10 bit resolution
        write_byte(self.device, 0x2D, 0x08)  # set mode to measurement mode

    def readAcceleration(self):
        bytes = bus.read_i2c_block_data(self.device, 0x32, 6)
        x = bytes[0] | (bytes[1] << 8)
        if x & (1 << 16 - 1):
            x = x - (1 << 16)
        y = bytes[2] | (bytes[3] << 8)
        if y & (1 << 16 - 1):
            y = y - (1 << 16)
        z = bytes[4] | (bytes[5] << 8)
        if z & (1 << 16 - 1):
            z = z - (1 << 16)

        #print(f"X -> {x}")
        #print(f"Y -> {y}")
        #print(f"Z -> {z}")
        x = x * 0.004
        y = y * 0.004
        z = z * 0.004
        x = x * 9.80665
        y = y * 9.80665
        z = z * 9.80665
        x = round(x, 4)
        y = round(y, 4)
        z = round(z, 4)
        #print("   x = %.3f ms2" % x)
        #print("   y = %.3f ms2" % y)
        #print("   z = %.3f ms2" % z)

        return [x, y, z]

class HEAD:
    def __init__(self, device_adress = 0x06):
        self.device = device_adress
        self.head_pos = 2 #the initial and the default position of the head is 2 (pointing front)

    def initScan(self):
        readings = np.zeros((5)) #if i do not initialize the list with values, but only with [], below will not be able to index it with readings[i]

        bus.write_byte_data(self.device, 0x00, 1)
        self.head_pos=1
        time.sleep(0.40)
        readings[1] = bus.read_byte(self.device)
        time.sleep(0.01)
        for i in range(0, 5):
            bus.write_byte_data(self.device, 0x00, i)
            self.head_pos = i
            time.sleep(0.40)
            readings[i] = bus.read_byte(self.device)
            time.sleep(0.01)
        bus.write_byte_data(self.device, 0x00, 3)
        self.head_pos = 3
        time.sleep(0.40)
        if readings[3] == 230:
            readings[3] = bus.read_byte(self.device)
            time.sleep(0.01)
        bus.write_byte_data(self.device, 0x00, 2)
        self.head_pos = 2
        time.sleep(0.40)
        if readings[2] == 230:
            readings[2] = bus.read_byte(self.device)
            time.sleep(0.01)
        return readings

    def readOn(self, position):
        try:
            write_byte(self.device, 0x00, position)
            time.sleep(0.40)  # wait for the controller to perform the instruction
            answer = bus.read_byte(self.device)
            time.sleep(0.01)
            return answer
        except OSError:
            return 255

    def readAll(self):
        readings = np.zeros((5))
        i = self.head_pos #the readAll starts from the last recorded head position (it should be the current head position)
        while i>0:
            i=i-1
            readings[i] = self.readOn(i)
        for i in range(1, 5):
            readings[i] = self.readOn(i)
        readings[3] = self.readOn(3)
        readings[2] = self.readOn(2)
        self.head_pos = 2
        return readings

    def surPrised(self):
        write_byte(self.device, 0x02, 0)
        0.5
    def dizy(self):
        write_byte(self.device, 0x03, 0)
        time.sleep(4.5)

class BOTM:
    def __init__(self): #the device is from 0 to 3, the addresses are: 0x50, 0x52, 0x54, 0x56
        self.devices = [0x50, 0x52, 0x54, 0x56]
    def readOn(self, device_index = 0):
        try:
            bus.write_byte(self.devices[device_index], 0)
            time.sleep(0.04)
            b1 = read_byte(self.devices[device_index], 0)
            b2 = read_byte(self.devices[device_index], 1)
            time.sleep(0.02)
            result = (b1 << 8) + b2
            return (result)
        except OSError:
            return 2555 #in np array I cant put string, so error will be replaced with 2555
    def readAll(self):
        btms = np.zeros((4))
        for i in range(4):
            btms[i] = self.readOn(device_index=i)
            while btms[i] == 2555:
                btms[i] = self.readOn(device_index=i)
        return btms