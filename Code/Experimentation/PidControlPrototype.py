# ----- Imports -----
# Utility
from collections import deque
import numpy as np

# For Control
import time

# For I2C
import pi_servo_hat
import smbus

# For control systems
from simple_pid import PID

"""
	Right now my goal is get to the point where I can make the servo turn to a certain
	position, which I will know from the potentiometer feedback.

	Control Loop:
	* Read Current Position
	* Update Motor

	Things I need to be able to do:
	* query the potentiometer for it's position
	* pass the position to the PID loop
	* get a response from the PID loop
	* Convert the response into a servo speed
	* command the servo motor to go the correct speed
"""

# ----- Global Values ----
ADC_ADDRESS = 0x4a
POT_0_CHANNEL = 0x41
POT_1_CHANNEL = 0X40

# ----- Global Classes -----
# Initializing the i2c bus
i2cBus = smbus.SMBus(1)

# Initializing Servo Hat
servoHat = pi_servo_hat.PiServoHat()
# Soft rest the system, preparing it for use
servoHat.restart()

# ----- Methods and Functions -----
def ReadPotentiometer(potentiometerNumber):
	"""
	Gets the value for the appropriate analog input
	"""
	channelAddress = 0x20 # This value should get overwritten so it doesn't matter much what it is

	if (potentiometerNumber == 0):
		channelAddress = POT_0_CHANNEL
	elif (potentiometerNumber == 1):
		channelAddress = POT_1_CHANNEL

	# Read the value from the ADC
	i2cBus.write_byte(ADC_ADDRESS, channelAddress)
	value = i2cBus.read_byte(ADC_ADDRESS)
	return value
#

# ----- Utility Classes -----

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

# ----- Begin Program -----
if __name__ == "__main__":
	# This isn't necessary but it keeps the code tider

	# First pass, I'm just going to go with the nubmers the potentiometer
	# outputs because there is a lot of overlap.
	
	# - Initializing -
	# Create the pid controller
	
	# 1:1 settings
	# Best with size = 7.5, center = 57, mag = 20
	# pid = PID(0.30, 0.205, 0.04)
	
	# Best with size = 7.5, center = 57, mag = 10
	# pid = PID(0.25, 0.205, 0.04)
	
	# 2:1 Settings
	# Best with size = 7.5, center = 57, mag = 30, time = 0.01
	# pid = PID(0.6, 0, 0)
	# pid = PID(0.6, 0.7, 0)
	# pid = PID(0.6, 0.7, 0.08)

	# Best with size = 7.5, center = 57, mag = 30, time = 0.005
	# pid = PID(1.0, 0, 0)
	# pid = PID(0.9, 0.8, 0)
	# pid = PID(0.9, 0.8, 0.02)
	pid = PID(0.9, 0.8, 0.02)

	# Setting the sampling time
	# samplingTime = 0.01
	# samplingTime = 0.001
	samplingTime = 0.005
	pid.sample_time = samplingTime

	# - Creating Control Range -
	deadzoneSize = 7.5
	deadzoneCenter = 57
	speedMagnitude = 30

	# Set the output bounds
	deadzoneLowerBound = deadzoneCenter - deadzoneSize/2
	pidLowerBound = deadzoneLowerBound - speedMagnitude
	pidUpperBound = deadzoneLowerBound + speedMagnitude
	pid.output_limits = (pidLowerBound, pidUpperBound)
	print(f"Limits: {pid.output_limits}")

	# Define the outer "padding"
	minimumPotentiometerValue = 0
	maximumPotentiometerValue = 255
	
	paddingMagnitude = 40
	paddingSpeedMagnitude = 0.1*speedMagnitude

	# - Tuning System -
	# Setting the setpoint
	errorMagnitude = 1.5
	# setpoints = deque([50, 200])
	setpoints = deque([25, 225])
	# setpoints = deque([50, 200, 25, 225])
	pid.setpoint = 120
	
	# Creating filters
	filterSize = 10
	potentiometerFilter = WeightedMovingAverage(filterSize)
	onOffFilter = MovingAverage(filterSize)
	
	# Settling Filter
	# Can disable motor if average error is below acceptable limit for this long
	settlingTime = 0.2
	settlingWindowSize = settlingTime//samplingTime
	settlingFilter = MovingAverage(settlingWindowSize)

	# Just some record keeping
	minSpeed = 300 # Set way above the fastest possible speed
	maxSpeed = 0 # Set way below the slowest possible speed
	
	# Debugging Settings
	secondsBetweenToggle = 5
	secondsBetweenUpdates = 0.05

	updateMod = secondsBetweenUpdates//samplingTime
	
	count = 0
	resetCountAt = secondsBetweenToggle*(1//samplingTime)
	while True:
		# - Rotate through Setpoints -
		# Manage toggling the setpoints
		setpoint = setpoints[0]

		# Iterating through setpoints
		if (count > resetCountAt):
			pid.setpoint = setpoints[0]
			setpoints.rotate(1)
			count = 0
		else:
			count += 1
		#
		
		# - Read Potentiometers -
		# Read the current value of the knob
		rawPotentiometerValue = ReadPotentiometer(0)
		potentiometerValue = potentiometerFilter(rawPotentiometerValue)

		# Read the current value of the other knob
		rawOnOffValue = ReadPotentiometer(1)
		onOffValue = onOffFilter(rawOnOffValue)

		# - Calculate New Motor Speed -
		# Calculate new output speed
		pidRecommendation = pid(potentiometerValue)

		# Bypassing the deadspot in the middle
		if (pidRecommendation > (deadzoneCenter - 0.5*deadzoneSize)):
			# Skipping the deadspot in the middle
			recommendedSpeed = pidRecommendation + deadzoneSize
		else:
			recommendedSpeed = pidRecommendation
		#

		# Account for outer padding
		if (potentiometerValue < minimumPotentiometerValue + paddingMagnitude):
			# Determine how far the system is from the outer edge
			percentageOfPaddingRemaining = potentiometerValue / paddingMagnitude
			percentageUsed = 1 - percentageOfPaddingRemaining

			# Determine amount to reduce speed by
			speedReduction = (percentageUsed)*(paddingSpeedMagnitude)

			# Determine the fastest allowable speed
			speedLimit = pidLowerBound + speedReduction

			# Adjust speed accordingly
			newSpeed = max(speedLimit, recommendedSpeed)

		elif (potentiometerValue > maximumPotentiometerValue - paddingMagnitude):
			# Determine how far the system is from the outer edge
			percentageOfPaddingRemaining = (maximumPotentiometerValue \
								   			- potentiometerValue) / paddingMagnitude
			percentageUsed = 1 - percentageOfPaddingRemaining
			
			# Determine amount to reduce speed by
			speedReduction = (percentageUsed)*paddingSpeedMagnitude

			# Determine the fastest allowable speed
			speedLimit = pidUpperBound - speedReduction

			# Adjust speed accordingly
			newSpeed = min(speedLimit, recommendedSpeed)
		else:
			percentageOfPaddingRemaining = 1
			speedReduction = 0
			
			if (recommendedSpeed < deadzoneCenter):
				speedLimit = pidLowerBound
			else:
				speedLimit = pidUpperBound
			#

			newSpeed = recommendedSpeed
		# 

		# Determine Current Error
		errorDelta = pid.setpoint - potentiometerValue
		averageErrorDelta = settlingFilter(errorDelta)
		
		# Update Servo Speed
		if (abs(averageErrorDelta) > errorMagnitude):
			servoHat.move_servo_position(0, newSpeed)
			servoStopped = False
		else:
			# Position has settled, stop motor
			servoHat.move_servo_position(0, 180)
			servoStopped = True
		
		# - Stats and Record Keeping - 

		# Update recorded stats
		minSpeed = min(newSpeed, minSpeed)
		maxSpeed = max(newSpeed, maxSpeed)

		# No need to update every single cycle
		if (count % updateMod == 0):
			prevP, prevI, prevD = pid.components
			print(f"Pos: {potentiometerValue:5.1f} | Tgt: {pid.setpoint:5.1f} |" \
				+ f" Δ: {errorDelta:6.1f} | Avg Δ: {averageErrorDelta:7.1f} |" \
				+ f" R Spd: {recommendedSpeed:.2f} |" \
				+ f" %:{percentageOfPaddingRemaining:4.2f} |" \
				+ f" Red:{speedReduction:4.1f} |" \
				+ f" L:{speedLimit:5.2f} |" \
				+ f" Spd:{newSpeed:5.2f} |" \
				# + f" On Off:{onOffValue:5.1f} |"\
				+ f" S:{servoStopped*100:3} |"\
				+ f" P: {float(prevP):7.1f} I: {float(prevI):5.3f} D: {float(prevD):5.2f}")
			# 
		# 
		
		# - Delay -
		# So the pi doesn't over-work itself
		time.sleep(samplingTime)

		if (onOffValue > 127):
			break
	# 

	# Time to stop
	servoHat.move_servo_position(0, 180)
	print(f"Min Speed: {minSpeed} | Max Speed: {maxSpeed} | Avg: {np.mean([minSpeed, maxSpeed])}")
	print(f"Bounds: {pid.output_limits}")
	print(f"Lower Bound: {minSpeed} | Upper Bound: {maxSpeed - deadzoneSize}")
# 
