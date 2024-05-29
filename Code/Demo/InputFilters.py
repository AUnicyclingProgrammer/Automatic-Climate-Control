# ----- Imports -----
# Utility
from collections import deque
import math
import numpy as np
import random

# Reability
from typing import List

# For Control
import time

# For I2C
import pi_servo_hat
import smbus

# For control systems
from simple_pid import PID

class MovingAverage:
	"""
	Uses a moving average to filter input data
	"""

	def __init__(self, windowSize = 10):
		"""
		Creating a MovingAverage filter instance
		
		windowSize : number of items to include in the moving filter
		"""

		# Instantiate the window
		self.window = np.zeros(int(windowSize))
	#

	def __call__(self, inputValue):
		"""
		Increments the filter by one timestep

		inputValue : raw value to be filtered
		"""
		
		# Rotate the window by one place
		self.window = np.roll(self.window, 1)
		
		# Add the new element
		self.window[0] = inputValue

		# Get the mean and return it
		return np.mean(self.window)
	# 
# 

class WeightedMovingAverage:
	"""
	Uses a moving average to filter input data
	"""

	def __init__(self, windowSize = 10):
		"""
		Creating a MovingAverage filter instance
		
		windowSize : number of items to include in the moving filter
		"""

		# Filter input
		windowSize = int(windowSize)
		
		# Instantiate the weights
		rawWeights = np.linspace(0, 1, num = windowSize)
		self.weights = rawWeights/sum(rawWeights)
		
		# Instantiate the window
		self.window = np.zeros(windowSize)
	#

	def __call__(self, inputValue):
		"""
		Increments the filter by one timestep

		inputValue : raw value to be filtered
		"""
		
		# Rotate the window by one place
		self.window = np.roll(self.window, 1)
		
		# Add the new element
		self.window[0] = inputValue

		# Get the mean and return it
		return np.mean(self.window)
	# 
# 