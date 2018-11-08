"""https://github.com/keras-rl/keras-rl/blob/master/examples/dqn_cartpole.py"""
"""https://github.com/Kjell-K/AirGym/blob/master/DQN-Train.py"""


import numpy as np
import random

from keras.models import Sequential
from keras.layers import Dense, MaxPooling2D, Flatten, Conv2D, BatchNormalization, Conv3D,MaxPooling3D
from keras.optimizers import Adam

from rl.agents.dqn import DQNAgent
from rl.policy import LinearAnnealedPolicy, EpsGreedyQPolicy
from rl.memory import SequentialMemory
from rl.callbacks import ModelIntervalCheckpoint  # https://github.com/keras-rl/keras-rl/blob/171667dce2a39993705b12fdf0b3cc3bb7bf26d2/rl/callbacks.py


from airsim_env import AirSimEnv

env = AirSimEnv()
num_steering_angles = env.action_space.n


random.seed(33333)
np.random.seed(33333)

INPUT_SHAPE = (260-int(3*260/7), 770) # H x W (no channels because assume DepthPlanner)
WINDOW_LENGTH = 5
input_shape = (WINDOW_LENGTH,) + INPUT_SHAPE

model = Sequential()
model.add(Conv2D(96, kernel_size=5, strides=4 ,activation='relu',
                 input_shape=input_shape, data_format = 'channels_first'))
model.add(Conv2D(128, kernel_size=5, strides=4,  activation='relu'))

model.add(Flatten())
model.add(Dense(96, activation='sigmoid'))
model.add(Dense(128, activation='sigmoid'))
model.add(Dense(num_steering_angles, activation='linear'))
print(model.summary())


replay_memory = SequentialMemory(limit=10**4, window_length=WINDOW_LENGTH)

# something like: w/ probability epsilon (which decays through training),
# select a random action; otherwise, consult the agent
policy = LinearAnnealedPolicy(EpsGreedyQPolicy(),
                              attr='eps',
                              value_max=1.0,
                              value_min=-1.0, # clip rewards just like in dqn paper
                              value_test=0.025,
                              nb_steps=10**5) # of steps until eps is value_test?


ddqn_agent = DQNAgent(model=model, nb_actions=num_steering_angles,
                     memory=replay_memory, enable_double_dqn=True,
                     enable_dueling_network=False, target_model_update=1e-1, # soft update parameter?
                     policy=policy, gamma=0.99, train_interval=4)

ddqn_agent.compile(Adam(lr=1e-4), metrics=['mae']) # not use mse since |reward| <= 1.0

weights_filename = 'ddqn_collision_avoidance_1107.h5'
want_to_train = True

if want_to_train is True:
  num_total_training_steps = 10**5

  # note: interval's units are episode_steps
  callbacks_list = [ModelIntervalCheckpoint(filepath=weights_filename, verbose=5, interval=1000)]
  ddqn_agent.fit(env, callbacks=callbacks_list, nb_steps=num_total_training_steps,
                visualize=False, verbose=2)

  ddqn_agent.save_weights(weights_filename)
else: # else want to test
    ddqn_agent.load_weights(weights_filename)
    ddqn_agent.test(env, nb_episodes=10, visualize=True)
