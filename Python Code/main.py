import random
import time
import numpy as np
import csv

import threading

# --> custom libraries
import SDL_Pi_INA3221
import senzi
import dispi
import soundi
import braini

# -------- 1. Take care of the battery and consumption ---------
from gpiozero import CPUTemperature
from gpiozero import LoadAverage
from smbus2 import SMBus

ina3221 = SDL_Pi_INA3221.SDL_Pi_INA3221(addr=0x40)

# -------- 2. Taking care of the sensors data ------------------
compass = senzi.COMPASS()
acceler = senzi.ACCELEROMETER()
head = senzi.HEAD()
head_pos = 2 #the initial head position is pointing ahead (position index 2). Positions are [0,1,2,3,4]
botm = senzi.BOTM()

# -------------- 3. Creating the brain -------------------------
brain = braini.BRAIN(10, 6, 6, 3, 3)
#the brain has 10 inputs and 2 outputs [left=0..1, right=0..1], while 0.0=full_backward, 0.5=stop, 1.0=full_forward
'''
observations = []
#This will collect the sensors list, after every step, until 10 episodes are reached. This will become hudge, so I will record the data in csv

actions_taken1 = []
actions_taken2 = []
#these will collect a list of the chosen action indexes (0,1 or 2), for both layerOut's

rewards_out1 = []
rewards_out2 = []
cumulative_rewards1 = []
cumulative_rewards2 = []
#these witll record the rewards over all the 10 episodes, for both LayerOut's. Cumulative_rewards are calculated after every episode
'''
# --------------------------------------------------------------
# ------------------- START ------------------------------------

ico_i=0
'''
#Thread to show everything on the display, periodicaly
def showOnDisplay(dataToShow, datatoshow, datatoshow....):
    while True:

def selfCheck_thread():
    datac = [0.00, 0, 0.0, 0.00]
    ico_lst = ['./ico/nn1s.jpg', './ico/nn2s.jpg', './ico/nn3s.jpg']
    i = 0

    while True:
        cpu = CPUTemperature()
        usage = LoadAverage(min_load_average=0, max_load_average=2)
        datac[1] = int(usage.load_average * 100)

        datac[2] = round(cpu.temperature, 2)
        datac[0] = round(ina3221.getBusVoltage_V(3), 2)
        pwrl1 = ina3221.getCurrent_mA(1)   #current/power consumption from Line 1
        pwrl2 = ina3221.getCurrent_mA(2)  #currentpower consumption from Line 2
        pwrin = ina3221.getCurrent_mA(3)  #current from the Charging line

        datac[3] = round((pwrl1 + pwrl2 + pwrin) / 1000, 2)

        #print(f"{pwrl1} + {pwrl2} + {pwrin} = {datac[3]*1000}")
        dispi.crcData(datac, ico_lst[i])

        if i >= 2: i = 0
        else: i += 1
        time.sleep(1)
'''
def selfCheck():
    datac = [0.00, 0, 0.0, 0.00]
    ico_lst = ['./ico/nn1s.jpg', './ico/nn2s.jpg', './ico/nn3s.jpg']
    global ico_i
    cpu = CPUTemperature()
    usage = LoadAverage(min_load_average=0, max_load_average=2)
    datac[1] = int(usage.load_average * 100)
    datac[2] = round(cpu.temperature, 2)
    time.sleep(0.05)
    datac[0] = round(ina3221.getBusVoltage_V(3), 2)
    time.sleep(0.05)
    pwrl1 = ina3221.getCurrent_mA(1)  # current/power consumption from Line 1
    time.sleep(0.05)
    pwrl2 = ina3221.getCurrent_mA(2)  # currentpower consumption from Line 2
    time.sleep(0.05)
    pwrin = ina3221.getCurrent_mA(3)  # current from the Charging line
    time.sleep(0.05)
    datac[3] = round((pwrl1 + pwrl2 + pwrin) / 1000, 2)

    # print(f"{pwrl1} + {pwrl2} + {pwrin} = {datac[3]*1000}")
    dispi.crcData(datac, ico_lst[ico_i])

    if ico_i >= 2: ico_i=0
    else: ico_i += 1


def setup(): #this function starts in the first powering-up the robot.

    soundi.initialize()


def main():
    episodes = 5  # this is the number of episodes that will be run before go to sleep
    # counter for the episodes. if they become == "n_episodes", I take a break and optimize the policy (learn the brain):

    step_size = 3 #this is a time to run the motors (or how big step to take) for the next move.
    # It will be calculated on every end of episode
    # if the reward was small, it will take a smaller step, and vice versa. (this is the robot PRECAUTION)

    # note: "<---" means this value will be feed to NN for backpropagation

    # --------- START OF THE PROCESS ----------
    while True:
        # Start of a new learning season. The robot will perform several steps in episodes and learn to do better.
        # Choose a new target direction and turn the robot to it.
        # whatever the robot turn during the season, it always try to find a way to this target direction
        target_direction = random.randrange(360)
        rotate_to_target(target_direction)

        #action_probs1 = np.zeros((0))  # <---
        #action_probs2 = np.zeros((0))  # <---
        action_probs1 = np.zeros((0, 3))  # <---
        action_probs2 = np.zeros((0, 3))  # <---
        episode_rewards1 = []   #both will store the reward of every step. After the end of the episodes, cumulative rewards will be calculated
        episode_rewards2 = []
        cumulative_rewards1 = np.zeros((0))  # <---
        cumulative_rewards2 = np.zeros((0))  # <---

        # observation list. It will store all the observations during the episode
        #observations = np.zeros((0, OSens.size))  # <--- I actually don't need that for backprop.

        step = 0

        # for episode in range(episodes, 0, -1): #loop (start, stop, step) -> (10, stop when 0, increment = -1)
        for episode in range(episodes):
            # 1. Take a measurements, fire-up the brain and take a step, measuring the rewards.
            #OSens_q, chosen_prob1, chosen_prob2, reward_out1, reward_out2, ep_end = step_in(target_direction, step_size)
            prob_distr1, prob_distr2, reward_out1, reward_out2, ep_end = step_in(target_direction, step_size)

            # 2. Recording the observations before taking this move.
            #observations = np.concatenate((observations, OSens_q.reshape((1, OSens_q.size))), axis=0)

            # 3. recording the probabilities of the action taked. We record the probs for all the discrete otputs
            # note: No matter which of the 3 actions. we only need the probability of receiving the reward of this action.
            #action_probs1 = np.append(action_probs1, chosen_prob1)
            #action_probs2 = np.append(action_probs2, chosen_prob2)
            action_probs1 = np.concatenate((action_probs1, prob_distr1), axis=0)
            action_probs2 = np.concatenate((action_probs2, prob_distr2), axis=0)

            # 4. recording the rewards for this episode:
            episode_rewards1.append(reward_out1)
            episode_rewards2.append(reward_out2)

            #5. if we reach the final step, we calculate the cumulative reward and start a new episode.
            if ep_end:
                for i in range(step+1):
                    total_reward1 = 0
                    total_reward2 = 0
                    for j in range(i, step+1):
                        total_reward1 = total_reward1 + episode_rewards1[j]
                        total_reward2 = total_reward2 + episode_rewards2[j]
                    cumulative_rewards1 = np.append(cumulative_rewards1, total_reward1)
                    cumulative_rewards2 = np.append(cumulative_rewards2, total_reward2)

                step = 0
                episode_rewards1.clear() #note: .clear is included from python 3.3+
                episode_rewards2.clear()

                # TODO: after the end of every episode, record the collected data into a csv file, for bkp

            else: step += 1
        else:
            # Go to sleep and learn a new policy with the collected samples.

            # 1. Do some reaction, showing that the robot will go to sleep.
            soundi.going_sleep()
            # todo: using a function in lion.py, turn the middle LED's on, telling the robot is learning.

            # 2. Sending all the collected data from this 10 episodes, to the BRAIN object, to learn.
            brain.log_loss(action_probs1, action_probs2, cumulative_rewards1, cumulative_rewards2)
            brain.learn(learning_rate=0.01)
            brain.clear_batch()
            # TODO: ---->
            # TODO: save the neural network after the training was complete.
            # TODO: wake-up the robot and start a new season.


'''
def go_to_sleep():

    loop2.start()
'''

def step_in(target_direction, step_size):
    OSens = np.zeros((10))
    # this is the obstacle sensors data list, including [compass, head1-5, botm1-4]

    # 1. Observing the environment
    # note: the environment is observed initially, before fire-up.
    OSens[0] = compass.readCompass()
    heads = head.readAll()
    OSens[1:6] = heads
    btms = botm.readAll()
    OSens[6:10] = btms
    OSens_q = braini.input_eqalizeing(OSens)

    # 2. Fire-UP the brain and take the probabilities for the two motors
    brainOUT1, brainOUT2 = brain.fireUp(OSens_q)

    # 3. prepare the motor commands and run the motors
    #left, right, chosen_prob1, chosen_prob2, speed_rw1, speed_rw2, ontrack_rw = braini.motors_calculate(brainOUT1[0], brainOUT2[0])
    left, right, speed_rw1, speed_rw2, ontrack_rw = braini.motors_calculate(brainOUT1[0],brainOUT2[0])
    motoRun(left=left, right=right, dur=step_size*10) # send an instruction for the motors to move for 3 seconds / for 3 seconds if observe after run

    # during this time, the i2c buss is free to perform a self-check and display the data on the display
    selfCheck() # by the time of moving, we take a self check and update the display.
    time.sleep(step_size)
    # the robot is now moved to the new state.

    # 4. check for impact and for danger of fall
    ep_end, impact_power, danger_power = check_for_impact()

    # 5. calculating the total return of this move:
    compass_reward = braini.compass_Reward(OSens[0], target_direction)

    reward_out1 = speed_rw1 + ontrack_rw + compass_reward - impact_power - danger_power
    reward_out2 = speed_rw2 + ontrack_rw + compass_reward - impact_power - danger_power
    print(f"--- TOTAL REWARD LEFT = {reward_out1} || RIGHT = {reward_out2} ---")

    #if is_impact, the episode is over. We return the collected information
    if ep_end:
        impactReaction(OSens[0])

    #return OSens_q, chosen_prob1, chosen_prob2, reward_out1, reward_out2, ep_end
    #return chosen_prob1, chosen_prob2, reward_out1, reward_out2, ep_end
    return brainOUT1, brainOUT2, reward_out1, reward_out2, ep_end

def check_for_impact():
    #it will return a value,
    impact_power = 0    #this stores the power of the impact with things on the way. As close the object is, as large is the power
    is_impact = False   #it will become true only if a min_thresshold is passed.

    btmIn_Threshold = 100  # it means 100mm
    btmIn_Threshold_min = 50 #ti means 50mm, or 5 cm
    btmOut_Threshold_max = 400 # threshold for measuring a cliff (danger of fall)
    btmOut_Threshold = 150
    head_Threshold = 20 #this is the head sensor threshold
    head_Threshold_min = 5

    head_front = head.readOn(2)
    btms = botm.readAll()

    #1. check for impact / something on the way of the robot
    if head_front < head_Threshold:
        power = 100 - (head_front * 5)
        if power > impact_power: impact_power = power
        if power < head_Threshold_min:
            is_impact = True
            impact_power = 100
    if is_impact == False:  #it wont check the botom sensors for impact, if the front sensor registers impact.
        for btm in btms:
            if btm < btmIn_Threshold:
                power = 100 - btm
                if power > impact_power: impact_power = power
                if power < btmIn_Threshold_min:
                    is_impact = True
                    impact_power = 100
                    break

    #2. check the btms sensors for cliff detection, and calculate the danger of fall...
    #it works opposit to the impact detection. As far as the distance, as bigger the danger
    danger_front = 0
    danger_back = 0
    for i in range(2):
        if btms[i] > btmOut_Threshold:
            if btms[i] < btmOut_Threshold_max:
                danger_front = danger_front + (btms[i] * 0.3)
            else: danger_front = danger_front + 150

    for i in range(2, 4):
        if btms[i] > btmOut_Threshold:
            if btms[i] < btmOut_Threshold_max:
                danger_back = danger_back + (btms[i] * 0.3)
            else: danger_back = danger_back + 150
    #take the largest danger:
    danger_power = danger_front if danger_front > danger_back else danger_back

    return is_impact, impact_power, danger_power

# --------------------------------------------------------------
# ------------------------- INTERACT ---------------------------
# the functions below make the robot move and interact with the environment.
def motoRun(left = 0, right = 0, dur=40): # 1 step is 4 seconds long. During it, a measure will be taken
    addr = 0x04  # address of the motor controlling arduino
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

# -> def moveBack and wander. + sound
def impactReaction(cur_ang):
    '''# 1. Stop the motors
    with SMBus(1) as bus:
        bus.write_byte_data(0x04, 0x00, 0)
    time.sleep(0.05)  # wait for the controller to perform the instruction'''

    # 2. Turn back a step:
    motoRun(-200, -200, 10)
    soundi.tapRespond1()
    head.surPrised()
    soundi.tapRespond2()
    time.sleep(2)

    # 3. Randomly choose an ange, far enought from currnet
    rotate_to = random.randrange(360)
    calc = abs(cur_ang-rotate_to)
    diff = calc if calc <= 180 else abs(calc-360)
    while diff < 90:
        rotate_to = random.randrange(360)
        calc = abs(cur_ang - rotate_to)
        diff = calc if calc <= 180 else abs(calc - 360)
        #randomly choose an angle, far enough from the current angle (>=90 degrees offset)

    # 4. Rotate to the new angle:
    while True:
        if abs(rotate_to - cur_ang) < 20:
            # print(f"{OSens[0]} --> {target_direction}")
            break
        else:
            # print(f"{OSens[0]} --> {target_direction}")
            motoRun(left=200, right=-200, dur=5)
            cur_ang = compass.readCompass()
            time.sleep(0.4)

def rotate_to_target(target_direction):
    # 1. measure the compass data
    cs = compass.readCompass()

    while True:
        if abs(target_direction - cs) < 20:
            # print(f"{OSens[0]} --> {target_direction}")
            break
        else:
            # print(f"{OSens[0]} --> {target_direction}")
            motoRun(left=200, right=-200, dur=5)
            cs = compass.readCompass()
            time.sleep(0.4)
'''
def sleeping_thread(end_it):
    while True:
        soundi.sleeping_sound()
        if end_it:
            break

    soundi.initialize()
'''
setup()
#loop1 = threading.Thread(name = 'selfCheck_thread', target=selfCheck_thread)
#end_it = False
#loop2 = threading.Thread(name = 'sleeping_thread', target=sleeping_thread, args=(lambda: end_it, ))
#loop3 = threading.Thread(name = 're_move', target=re_move)

#loop1.start()
#loop2.start()
#loop3.start()
