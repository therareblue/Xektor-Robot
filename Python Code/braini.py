import numpy as np

# ========================DATA PREPARE=============================
'''
1. when start, the robot choose a desired direction.
2. the robot runs for 10 episodes. Every episode starts with randomly rotating to an angle, and finish when an impact ocure.
3. each episode collect data for the observations (of the state), actions taken (log of probability for the chosen action), rewards and future rewards.
4. future rewards (total cumulative rewards) are calculating after the end of every episode. the  final vector is long the same as rewards vector. 
#for calculating future rewards, later I can use belman equation, with adding a discount. 
-->. After 10 episodes, the robot stops for "sleeping" and make the bacpropagation and optimization::
5. future rewards are normalized, to decrease the probability of over-flowing the neural network
6. calculating the loss function
7. backpropagating the loss function to calculate the dW and dB for the network
8. adjusting the parameters. 

9. wake-up the robot choose a desired direction and start again.

'''

# --> ACTIONS: speed = -1, 0, +1; turn = -1 (left) / 0 (no turn) / +1(right)

# --> STATES: these are all the inputs from the sensors (10 inputs), 0 is the compass; 1-5 is the head in every angle, 6-9 are the bottom sensors
sensors = 10
#sensor_inputs = [degrees, cm, cm, cm, cm, cm, mm, mm, mm, mm]

def input_eqalizeing(sensor_inputs):
    #this function puts all the inputs into a range from 0.0 to 1.0
    inputs_array = np.zeros((10))
    inputs_array[0] = round((sensor_inputs[0])/360.0, 5)
    for i in range(1, 6):
        #this is the head sensor, turned in 5 directions from left to right
        #I need to be sure that the maximum value of the head senzor do not exceed 200cm
        val = 200.0 if sensor_inputs[i] > 200.0 else sensor_inputs[i]
        inputs_array[i] = round(val/200.0, 5)
    for i in range(6, 10):
        #this are the bottom sensors. they measure in mm. max is from 0 to 2000
        val = 2000.0 if sensor_inputs[i] > 2000.0 else sensor_inputs[i]
        inputs_array[i] = round(val/2000.0, 5)
    return inputs_array

#inpuths should be the states (sensors) and rewards.

def motors_calculate(nn_out1, nn_out2):
    #nn_out1 coresponds to motor-Left, nn_out2 -> motor-Right
    #the idea is to have neural network output layer for every motor
    #I get the speed, coresponded to the biggest value in left and right

    if nn_out1[0] > nn_out1[2]:
        left = int(nn_out1[0]*255.0)
        chosen_left = 0
    elif nn_out1[2] > nn_out1[0]:
        left = int(-nn_out1[2]*255.0)
        chosen_left = 2
    else:
        left = 0
        chosen_left = 1

    if nn_out2[0] > nn_out2[2]:
        right = int(nn_out2[0]*255.0)
        chosen_right = 0
    elif nn_out2[2] > nn_out2[0]:
        right = int(-nn_out2[2]*255.0)
        chosen_right = 2
    else:
        right = 0
        chosen_right = 1

    chosen_prob1 = nn_out1[chosen_left]
    chosen_prob2 = nn_out2[chosen_right]

    #calculating the error in the motors:
    #1. speed Err
    if nn_out1[0] > nn_out1[1] and nn_out1[0] > nn_out1[2]: speed_rw1 = nn_out1[0]*25.5
    elif nn_out1[1] > nn_out1[0] and nn_out1[1] >= nn_out1[2]: speed_rw1 = -nn_out1[1]*25.5
    elif nn_out1[2] > nn_out1[0] and nn_out1[2] >= nn_out1[1]: speed_rw1 = -nn_out1[2] * 25.5
    else: speed_rw1 = 0
    if nn_out2[0] > nn_out2[1] and nn_out2[0] > nn_out2[2]: speed_rw2 = nn_out2[0]*25.5
    elif nn_out2[1] > nn_out2[0] and nn_out2[1] >= nn_out2[2]: speed_rw2 = -nn_out2[1]*25.5
    elif nn_out2[2] > nn_out1[0] and nn_out2[2] >= nn_out2[1]: speed_rw2 = -nn_out2[2] * 25.5
    else: speed_rw2 = 0

    #2. Off track Err
    ontrack_rw = ontrack_Reward(left, right)

    #return left, right, chosen_prob1, chosen_prob2, speed_rw1, speed_rw2, ontrack_rw
    return left, right, speed_rw1, speed_rw2, ontrack_rw

# ===================CREATING THE BRAIN:============================

# LAYER_IN ->> LAYER_H1 --> ACTIVATION_H1 ->> LAYER_H2 --> ACTIVATION_H2 ->> LAYER_OUT --> SOFTMAX =>> calculating losses =>> backpropagation and optimization
class Layer:
    def __init__(self, n_inputs, n_neurons):
        self.neurons = n_neurons
        self.weights = np.random.uniform(low=-1, high=1, size=(n_inputs, n_neurons))
        self.biases = np.zeros((1, n_neurons))
        self.rawOut_badge = np.zeros((0, n_neurons)) #this stores all the fire-up raw outputs, until it's cleared

    def forward(self, inputs):
        self.inputs = inputs
        self.output_raw = np.dot(inputs, self.weights) + self.biases
        self.rawOut_badge = np.concatenate((self.rawOut_badge, self.output_raw), axis=0)

    #def activate(self, inputs, f = "lkrelu"):
    def activate(self, f="lkrelu"):
        if f == "lkrelu":
            #self.output = np.where(inputs > 0, inputs, inputs * 0.01)
            self.output = np.where(self.output_raw > 0, self.output_raw, self.output_raw * 0.01)
        elif f == "softmax":
            exp_values = np.exp(self.output_raw - np.max(self.output_raw, axis=1, keepdims=True))
            self.output = exp_values / np.sum(exp_values, axis=1, keepdims=True)

    def rawout_badge_clear(self):
        self.rawOut_badge = self.rawOut_badge = np.zeros((0, self.neurons))
        #clearing the layer badge of reccords for the fire-up outputs

def lkReLU_deriv(inputs):
    #return 0.01 if inputs < 0 else 1
    return np.where(inputs < 0, 0.01, 1)

def lkReLU(inputs): #used only for the gradiend calculation of backprop
    return np.where(inputs > 0, inputs, inputs * 0.01)

class BRAIN:
    #creating a brain with 1 input layer, 2 hidden layers and 2 output layers (for left and right motor)
    def __init__(self, n_in, n_h1, n_h2, n_out1, n_out2):
        self.n_inputs = n_in
        self.LayerIn = [0] * n_in #creating list of zeroes with n_in number of values
        self.Layer1 = Layer(n_in, n_h1)
        self.Layer2 = Layer(n_h1, n_h2)
        self.LayerOut1 = Layer(n_h2, n_out1)
        self.LayerOut2 = Layer(n_h2, n_out2)
        self.Output1 = np.zeros((1,n_out1))
        self.Output2 = np.zeros((1, n_out2))

        #this one stores all the inputs of the fire-up steps, before its cleaned.
        self.inputs_badge = np.zeros((0, n_in))

    def fireUp(self, inputs):
        self.LayerIn = inputs
        self.inputs_badge = np.concatenate((self.inputs_badge, inputs.reshape((1, inputs.size))), axis=0)
        self.Layer1.forward(self.LayerIn)
        #self.Layer1.activate(self.Layer1.output_raw)
        self.Layer1.activate()  # by default activation function is set to "leaky ReLU"

        self.Layer2.forward(self.Layer1.output)
        #self.Layer2.activate(self.Layer2.output_raw)
        self.Layer2.activate() #with "leaky ReLU, by default

        self.LayerOut1.forward(self.Layer2.output)
        #self.LayerOut1.activate(self.LayerOut1.output_raw, f="softmax")
        self.LayerOut1.activate(f="softmax")
        self.LayerOut2.forward(self.Layer2.output)
        #self.LayerOut2.activate(self.LayerOut2.output_raw, f="softmax")
        self.LayerOut2.activate(f="softmax")

        self.Output1 = self.LayerOut1.output
        self.Output2 = self.LayerOut2.output
        return self.Output1, self.Output2 #this is an np array with snape [[y1 y2 y3]]

    def log_loss(self, action_probs1, action_probs2, cumulative_rewards1, cumulative_rewards2):
        # 1. calculating the log probabilities of the probability vector
        log_probs1 = -np.log(action_probs1.T)
        log_probs2 = -np.log(action_probs2.T)
        # note: action_probs are a matricies with shapes (n_steps, 3), n_steps rows, 3 elements (for each discrete action).
        # We need to transpose them in order to have 3 rows (3 outputs), with n_steps in every row. And then take the log()
        # here we use natural log (ln), I search the whole net for it and it logicaly seams to be the ln, and not log10

        # 2. calculate a normalized cumulative_reward (not to take to big steps in optimization)
        rw1_mean = np.mean(cumulative_rewards1)
        rw1_std = np.std(cumulative_rewards1)
        if rw1_std == 0: rewards1_norm = (cumulative_rewards1 - rw1_mean) / 1e-7
        else: rewards1_norm = (cumulative_rewards1 - rw1_mean) / rw1_std

        rw2_mean = np.mean(cumulative_rewards2)
        rw2_std = np.std(cumulative_rewards2)
        if rw2_std == 0: rewards2_norm = (cumulative_rewards2 - rw2_mean) / 1e-7
        else: rewards2_norm = (cumulative_rewards2 - rw2_mean) / rw2_std

        # 3. calculating the loss (vector), using the new normalized cumulative rewards

        loss1 = np.mean((log_probs1 * rewards1_norm), axis=1)
        loss2 = np.mean((log_probs2 * rewards2_norm), axis=1)
        # note: both loss now are arrays with the means of the log_prob*rewards for every discrete output.
        # making the loss a vectors:
        self.Loss1 = loss1.reshape(1, loss1.size).T
        self.Loss2 = loss2.reshape(1, loss2.size).T

        #print(f"LOSS Out1 = {self.Loss1}")
        #print(f"LOSS Out2 = {self.Loss2}")

        # NOT USED
        #loss_arr = np.concatenate((loss1, loss2))
        #self.Loss = loss_arr.reshape(1, loss_arr.size).T
        # note: Loss VECTOR of the output is now ready to be used to calculate the hidden loss
        # and then calculate the gradients of every node
        # NOT USED

    def learn(self, learning_rate=0.05):
        # Note:
        # in order to do that, we calculate the DOT product of layer weights times layer loss
        # note: the weight matrix usualy should be transposed to match the size of the loss vector.
        # Here we don't need that because it is already transposed when created (on the INIT process).

        # 1. Calculating the gradients of the w and b of every node.
        # note: we use the badge data of inputs and layer_raw_outputs stored during the fire-up proccesses
        # we do caclulation and optimization for every step stored into the badge of inputs and outputs
        for i in range(np.size(self.inputs_badge, axis=0)):
            # for each step, caclulate gradients and optimize
            # n = self.LayerOut2.neurons
            # usually we divide the gradient by number of neurons, but as we have a "learning_rate" part, we don't need to do that.
            L2_out = lkReLU(self.Layer2.rawOut_badge[i])
            L2_out = L2_out.reshape((1, L2_out.size))
            #print("Loss1: ")
            #print(self.Loss1)
            #print("Loss2: ")
            #print(self.Loss2)
            dW_out1 = np.dot(self.Loss1, L2_out).T
            dW_out2 = np.dot(self.Loss2, L2_out).T
            db_out1 = self.Loss1.T
            db_out2 = self.Loss2.T
            '''
            print("---------------------------------------------------")
            print(dW_out1)
            print(learning_rate * dW_out1)
            sw1 = self.LayerOut1.weights - (learning_rate * dW_out1)
            print(sw1)
            print("---------------------------------------------------")
            '''
            # calculating the loss vector of Hidden Layer2 and then the gradients for layer2 w and b

            #loss_L2 = (self.LayerOut1.weights.dot(self.Loss1) + self.LayerOut2.weights.dot(self.Loss2))
            lkrl_drv2 = lkReLU_deriv(self.Layer2.rawOut_badge[i].reshape((1, self.Layer2.rawOut_badge[i].size))).T
            loss_L2 = (np.dot(self.LayerOut1.weights, self.Loss1) + np.dot(self.LayerOut2.weights, self.Loss2)) * lkrl_drv2

            #print("LossL2:")
            #print(loss_L2)

            L1_out = lkReLU(self.Layer1.rawOut_badge[i])
            L1_out = L1_out.reshape((1, L1_out.size))
            dW_L2 = np.dot(loss_L2, L1_out).T
            db_L2 = loss_L2.T

            #1. input_badge[i] vector must be reshaped; 2. layer1.rawout[i] too and T, same as above
            # calculating the loss vector of Hidden Layer1 and then the gradients  for layer1 w and b
            lkrl_drv1 = lkReLU_deriv(self.Layer1.rawOut_badge[i].reshape((1, self.Layer1.rawOut_badge[i].size))).T
            loss_L1 = np.dot(self.Layer2.weights, loss_L2) * lkrl_drv1

            #print("LossL1:")
            #print(loss_L1)
            dW_L1 = np.dot(loss_L1, self.inputs_badge[i].reshape((1, self.inputs_badge[i].size))).T
            db_L1 = loss_L1.T

            #2. Update the parameters:
            #todo: BIASES updating error,.. with shape..
            self.Layer1.weights = self.Layer1.weights - (learning_rate * dW_L1)

            self.Layer1.biases = self.Layer1.biases - (learning_rate * db_L1)
            self.Layer2.weights = self.Layer2.weights - (learning_rate * dW_L2)
            self.Layer2.biases = self.Layer2.biases - (learning_rate * db_L2)
            self.LayerOut1.weights = self.LayerOut1.weights - (learning_rate * dW_out1)
            self.LayerOut1.biases = self.LayerOut1.biases - (learning_rate * db_out1)
            self.LayerOut2.weights = self.LayerOut2.weights - (learning_rate * dW_out2)
            self.LayerOut2.biases = self.LayerOut2.biases - (learning_rate * db_out2)

    def clear_batch(self):
        # clearing the batches of inputs and outputs to free the memory for the next learning season
        self.inputs_badge = np.zeros((0, self.n_inputs))
        self.Layer2.rawOut_badge = np.zeros((0, self.Layer2.neurons))
        self.Layer1.rawOut_badge = np.zeros((0, self.Layer1.neurons))

    def save(self):
        np.savetxt('brain/lw1.csv', self.Layer1.weights, delimiter=',')
        np.savetxt('brain/lb1.csv', self.Layer1.biases, delimiter=',')
        np.savetxt('brain/lw2.csv', self.Layer2.weights, delimiter=',')
        np.savetxt('brain/lb2.csv', self.Layer2.biases, delimiter=',')
        #np.savetxt('brain/lwo.csv', self.LayerOut.weights, delimiter=',')
        #np.savetxt('brain/lbo.csv', self.LayerOut.biases, delimiter=',')
        np.savetxt('brain/lwo1.csv', self.LayerOut1.weights, delimiter=',')
        np.savetxt('brain/lbo1.csv', self.LayerOut1.biases, delimiter=',')
        np.savetxt('brain/lwo2.csv', self.LayerOut2.weights, delimiter=',')
        np.savetxt('brain/lbo2.csv', self.LayerOut2.biases, delimiter=',')

    def load(self):
        self.Layer1.weights = np.loadtxt('brain/lw1.csv', delimiter=',')
        bs = np.loadtxt('brain/lb1.csv', delimiter=',')
        self.Layer1.biases = bs.reshape(-1, len(bs))
        self.Layer2.weights = np.loadtxt('brain/lw2.csv', delimiter=',')
        bs = np.loadtxt('brain/lb2.csv', delimiter=',')
        self.Layer2.biases = bs.reshape(-1, len(bs))
        #self.LayerOut.weights = np.loadtxt('brain/lwo.csv', delimiter=',')
        #bs = np.loadtxt('brain/lbo.csv', delimiter=',')
        #self.LayerOut.biases = bs.reshape(-1, len(bs))
        self.LayerOut1.weights = np.loadtxt('brain/lwo1.csv', delimiter=',')
        bs = np.loadtxt('brain/lbo1.csv', delimiter=',')
        self.LayerOut1.biases = bs.reshape(-1, len(bs))
        self.LayerOut2.weights = np.loadtxt('brain/lwo2.csv', delimiter=',')
        bs = np.loadtxt('brain/lbo2.csv', delimiter=',')
        self.LayerOut2.biases = bs.reshape(-1, len(bs))

    def print(self):
        print("---------INPUTS---------")
        print(self.LayerIn)
        print("")
        print("---------HIDDEN 1---------")
        print(self.Layer1.weights)
        print(self.Layer1.biases)
        print("")
        print(self.Layer1.output)
        print("")
        print("---------HIDDEN 2---------")
        print(self.Layer2.weights)
        print(self.Layer2.biases)
        print("")
        print(self.Layer2.output)
        print("")
        print("---------OUTPUT LAYER---------")
        print(self.LayerOut1.weights)
        print(self.LayerOut1.biases)
        print("")
        print(self.LayerOut2.weights)
        print(self.LayerOut2.biases)
        print("")
        print("---------ACTIONS DISTR---------")
        print("RAW1 = {} --> {}".format(self.LayerOut1.output_raw, self.Output1))
        print("RAW2 = {} --> {}".format(self.LayerOut2.output_raw, self.Output2))
        #print(self.Output1)
        #print(self.Output2)



#===================================================================
'''
def impact_Reward(sensor_inputs):
    #it takes the sensor inputs and detects if any of the inputs are below an IMPACT THRESHOLD
    impact_power = 0
    btm_Threshold = 100 #it means 100mm
    head_Threshold = 10
    for i in range(2, 5): #For calculating the reward, it takes only the front 3 head states, because it moves in their direction
        if sensor_inputs[i] < head_Threshold:
            power = 100 - (sensor_inputs[i])*10
            if power > impact_power: impact_power = power

    for i in range(6, 10):
        if sensor_inputs[i] < btm_Threshold:
            power = 100 - (sensor_inputs[i])*10
            if power > impact_power: impact_power = power

    return -impact_power
'''

def compass_Reward(compass_input, target):
    compass_reward = 10 - round((180 - abs(180 - abs(target - compass_input))) / 180.0, 4) * 20
    return compass_reward

def ontrack_Reward(left, right):
    if abs(left-right) > 20:
        offtrack_reward = -abs(left - right) * 0.1
    else: offtrack_reward = 20 - abs(left-right)
    return offtrack_reward

#===============================================================================
#===============================================================================
'''
sensor_inputs = [5, 200, 130, 43, 73, 63, 120, 120, 170, 128]
STATES = input_eqalizeing(sensor_inputs)
#brain = BRAIN(len(STATES), 6, 6, 4)
brain = BRAIN(len(STATES), 6, 6, 3, 3)
#brain.load()
target_direction = random.randrange(360)
for i in range(0, 50):
    probabilities1, probabilities2 = brain.fireUp(STATES)
    brain.draw()
    #brain.save()
    print("========================================")
    #print("raw NN out: {}".format(raw_output))
    print("LayerOut-LEFT: {}".format(probabilities1))
    print("LayerOut-RIGHT: {}".format(probabilities2))

    left, right, speed_reward1, speed_reward2 = motors_output(probabilities1, probabilities2)

    print("----------------------------------------")
    #get a random direction

    print("DIRECTION current: {} --> target: {}".format(sensor_inputs[0], target_direction))
    print("--------------REWARDS:-------------------")
    print("Speed Reward: Left = {} || Right = {}".format(speed_reward1, speed_reward2))
    ontrack_reward = ontrack_Reward(left, right)
    print("onTrack Reward: {}".format(ontrack_reward))
    compass_reward = compass_Reward(sensor_inputs, target_direction)
    print("compass Reward = {}".format(compass_reward))
    impact_reward = impact_Reward(sensor_inputs)
    print("impact Reward = {}".format(impact_reward))
    fall_danger_reward = fall_Danger_Reward(sensor_inputs)
    print("fall danger Reward = {}".format(fall_danger_reward))
    out1_reward = speed_reward1+ontrack_reward+compass_reward+impact_reward+fall_danger_reward
    out2_reward = speed_reward2+ontrack_reward+compass_reward+impact_reward+fall_danger_reward
    #right_reward = left_reward - speed_reward1 + speed_reward2
    print("")
    print("--- TOTAL REWARD LEFT = {} || RIGHT = {} ---".format(out1_reward, out2_reward))
    print("----------------------------------------")
    brain.getLoss(out1_reward, out2_reward)
    print("----------------------------------------")
    learning_rate = 0.05
    brain.calcDelta()
    brain.learn(learning_rate)
    print("========================================")

'''