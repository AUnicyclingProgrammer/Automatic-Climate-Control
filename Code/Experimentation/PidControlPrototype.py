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

class WeightedMovingAverage:
	"""
	Uses a moving average to filter input data
	"""

	def __init__(self, windowSize = 10):
		"""
		Creating a MovingAverage filter instance
		
		windowSize : number of items to include in the moving filter
		"""

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
	
	# Best with size = 7.5, center = 57, mag = 30, time = 0.01
	# pid = PID(0.6, 0, 0)
	# pid = PID(0.6, 0.7, 0)
	# pid = PID(0.6, 0.7, 0.08)

	# Best with size = 7.5, center = 57, mag = 30, time = 0.005
	# pid = PID(1.0, 0, 0)
	# pid = PID(0.9, 0.8, 0)
	pid = PID(0.9, 0.8, 0.02)

	# Setting the sampling time
	# samplingTime = 0.01
	# samplingTime = 0.001
	samplingTime = 0.005
	pid.sample_time = samplingTime

	# - Creating Control Range -
	# deadzoneSize = 8
	# deadzoneSize = 6
	deadzoneSize = 7.5
	deadzoneCenter = 57
	speedMagnitude = 30

	# Set the outputs
	pid.output_limits = (deadzoneCenter - deadzoneSize/2 - speedMagnitude, \
					deadzoneCenter - deadzoneSize/2 + speedMagnitude)
	print(f"Limits: {pid.output_limits}")

	# Setting the setpoint
	tolerance = 0
	setpoints = deque([50, 200])
	# setpoints = deque([50, 200, 25, 225])
	pid.setpoint = 120
	
	# Creating filters
	filterSize = 10
	potentiometerFilter = WeightedMovingAverage(filterSize)
	onOffFilter = MovingAverage(filterSize)

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
		# Manage toggling the setpoints
		setpoint = setpoints[0]

		# Toggling
		if (count > resetCountAt):
			pid.setpoint = setpoints[0]
			setpoints.rotate(1)
			count = 0
		#

		count += 1
		
		# Read the current value of the knob
		rawPotentiometerValue = ReadPotentiometer(0)
		potentiometerValue = potentiometerFilter(rawPotentiometerValue)

		# Read the current value of the other knob
		rawOnOffValue = ReadPotentiometer(1)
		onOffValue = onOffFilter(rawOnOffValue)

		# If we are close enough then falsify the value sent to the PID controller
		# Tell the servo to scoot if it's too far away
		if ((setpoint + tolerance > potentiometerValue) and \
			 (potentiometerValue > setpoint - tolerance)):
			# Stop, close enough
			filteredValue = setpoint

			servoStopped = True
		else:
			# Keep trying
			filteredValue = potentiometerValue

			servoStopped = False
		#

		# Get a new reading from the potentiometer
		pidRecommendation = pid(filteredValue)

		# Bypassing the deadspot in the middle
		# if (pidRecommendation > 45):
		if (pidRecommendation > (deadzoneCenter - 0.5*deadzoneSize)):
			# Skipping the deadspot in the middle
			newSpeed = pidRecommendation + deadzoneSize
		else:
			newSpeed = pidRecommendation

		# Move the servo the correct mout
		servoHat.move_servo_position(0, newSpeed)
		minSpeed = min(newSpeed, minSpeed)
		maxSpeed = max(newSpeed, maxSpeed)

		# No need to update every single cycle
		if (count % updateMod == 0):
			prevP, prevI, prevD = pid.components
			print(f"Pos: {potentiometerValue:5.1f} | Tgt: {pid.setpoint:5.1f} |" \
				+ f" Δ: {pid.setpoint - potentiometerValue:6.1f} | " \
				+ f" F:{filteredValue:5.1f} | Spd: {newSpeed:.2f} |" \
				+ f" On Off: {onOffValue:5.1f} | S: {servoStopped*100:3} |"\
				+ f" P: {float(prevP):7.1f} I: {float(prevI):5.3f} D: {float(prevD):5.2f}")
			# 
		# 
		
		# So the pi doesn't over-work itself
		time.sleep(samplingTime/1)

		if (onOffValue > 127):
			break
	# 

	# Time to stop
	servoHat.move_servo_position(0, 180)
	print(f"Min Speed: {minSpeed} | Max Speed: {maxSpeed} | Avg: {np.mean([minSpeed, maxSpeed])}")
	print(f"Bounds: {pid.output_limits}")
	print(f"Lower Bound: {minSpeed} | Upper Bound: {maxSpeed - deadzoneSize}")
# 
