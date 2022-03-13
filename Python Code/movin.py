from smbus2 import SMBus
import time

addr = 0x04 #address of the motor controlling arduino
#bus = SMBus(1)
'''
def drive(instruction):
    #drive function take the output data from NN [LFW, RFW, LBW, RBW] calculate and  send it to the motors controller via i2C, as [instruction, speed/duration]
'''
'''
class MOTORI:
    def __init__(self, device_adress=0x04):
        self.device = device_adress
        #self.movin = False  #flag that says wheither a is moving or not
    
    def step(self, left, right, dur):
        
    def ismovin(self):
        with SMBus(1) as bus:
            answer = bus.read_byte(addr)vv
'''

def move(left, right): #continuous move untill a stop function is sent
    stepup(left, right, dur=255) #when duration is set to 255, it will drive continuously, even if main computer stops
    '''with SMBus(1) as bus:
        answer = bus.read_byte(addr)
    print(f"Answer from the slave: {answer}")'''

def step(left, right, dur=10): #default duration of one step is = 10 * 0.1s = 1sec
    # left and right = -255 to 255
    # 0x00 -> duration ; 0x01 -> left forward; 0x02 -> right forward; 0x03 -> left backward; 0x04 -> right forward
    # limiting the input data:
    if left > 255: left = 255
    elif left < -255: left = -255
    if right > 255: right = 255
    elif right < -255: right = -255
    if dur > 255: dur = 255
    elif dur < 0: dur = 0

    with SMBus(1) as bus:
        if left >= 0: bus.write_byte_data(addr, 0x01, left)
        else: bus.write_byte_data(addr, 0x03, -left)
        if right >= 0: bus.write_byte_data(addr, 0x02, right)
        else: bus.write_byte_data(addr, 0x04, -right)

        bus.write_byte_data(addr, 0x00, dur)

    time.sleep(0.05)  # wait for the controller to perform the instruction

def stop():
    with SMBus(1) as bus:
        bus.write_byte_data(addr, 0x00, 0)
    time.sleep(0.05)  # wait for the controller to perform the instruction

def ismovin():
    with SMBus(1) as bus:
        answer = bus.read_byte(addr)
    return answer