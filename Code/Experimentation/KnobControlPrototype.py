# ----- Imports -----
# Utility
from collections import deque
import math
import numpy as np
import random

# For Control
import time

# For I2C
import pi_servo_hat
import smbus

# For control systems
from simple_pid import PID

# ----- Global Values ----
ADC_ADDRESS = 0x4a
POT_0_CONTROL_BYTE = 0x40
POT_1_CONTROL_BYTE = 0X42
POT_2_CONTROL_BYTE = 0x41

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
	This function assumes the ADC is the PCF8591: https://www.nxp.com/docs/en/data-sheet/PCF8591.pdf
	"""
	controlByte = 0x20 # This value should get overwritten so it doesn't matter much what it is

	if (potentiometerNumber == 0):
		controlByte = POT_0_CONTROL_BYTE
	elif (potentiometerNumber == 1):
		controlByte = POT_1_CONTROL_BYTE
	elif (potentiometerNumber == 2):
		controlByte = POT_2_CONTROL_BYTE
	# 

	# Read the value from the ADC
	i2cBus.write_byte(ADC_ADDRESS, controlByte)
	
	# The PCF8591 sends the previously converted value while calculating the new one
	previousValue = i2cBus.read_byte(ADC_ADDRESS)
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

class KnobController:
	"""
	This class is responsible for moving adjusting the knob controller to the correct
	position.
	"""
	
	def __init__(self, knobNumber,
			  minimumPotentiometerValue = 0, maximumPotentiometerValue = 255,
			  speedMagnitude = 30, boundarySpeedMagnitude = 3,
			  boundaryOuterThreshold = 20, boundaryInnerThreshold = 40,
			  errorMagnitude = 1, settledErrorMagnitude = 5, settlingTime = 0.25):
		"""
		Creates an instance of the class

		knobNumber : number associated with the servo - potentiometer pair for this controller
		minimumPotentiometerValue : minimum value that the potentiometer can read
		maximumPotentiometerValue : maximum value that the potentiometer can read
		speedMagnitude : maximum velocity command sent to servo under normal operation
		boundarySpeedMagnitude : maximum velocity command sent to servo when near the
			boundaries of what the potentiometer can read
		boundaryOuterThreshold : distance away from the min and max potentiometer values
			where the servo must move no faster than boundarySpeedMagnitude
		boundaryInnerThreshold : distance away from the min and max potentiometer values
			where the servo commands begin blending between speedMagnitude and
			boundarySpeedMagnitude
		errorMagnitude : magnitude of sensor deviation allowed from the setpoint for intial
			stopping condition
		settledErrorMagnitude : magnitude of sensor deviation allowed from the setpoint after
			the system has satisfiedErrorMagnitude for settlingTime (makes the system less
			susceptible to random sensor deviations)
		settlingTime : time (in seconds) the system must stay within errorMagnitude before
			tolerances can be relaxed to settledErrorMagnitude
		"""
		
		# - Initializing -
		# Defining the number associated with this motor and potentiometer combo
		self.knobNumber = knobNumber
		self.hasSettled = False

		# --- Creating Control Range ---
		# - Defining Operational Range -
		self.deadzoneSize = 4
		self.deadzoneCenter = 49
		self.speedMagnitude = speedMagnitude

		# Set the output bounds
		deadzoneLowerBound = self.deadzoneCenter - self.deadzoneSize/2
		self.pidLowerBound = deadzoneLowerBound - self.speedMagnitude
		self.pidUpperBound = deadzoneLowerBound + self.speedMagnitude

		# - Defining PID Controller -
		# Create the pid controller
		startingValue = np.mean([self.pidLowerBound, self.pidUpperBound])
		self.pid = PID(0.4, 0.33, 0.05, starting_output=startingValue)

		# Setting the sampling time
		self.samplingTime = 0.005
		self.pid.sample_time = self.samplingTime

		# Set output limits
		self.pid.output_limits = (self.pidLowerBound, self.pidUpperBound)
		print(f"PID Limits: {self.pid.output_limits}")

		# - Defining Padding near Boundaires -
		# Define the outer "padding"
		self.minimumPotentiometerValue = minimumPotentiometerValue
		self.maximumPotentiometerValue = maximumPotentiometerValue
		
		self.paddingOuterThreshold = boundaryOuterThreshold
		self.paddingInnerThreshold = boundaryInnerThreshold
		self.paddingSpeedMagnitude = boundarySpeedMagnitude

		# Calculating Padding Constants
		self.paddingLowerBound = deadzoneLowerBound - self.paddingSpeedMagnitude
		self.paddingUpperBound = deadzoneLowerBound + self.paddingSpeedMagnitude
		print(f"Padded Limits: {(self.paddingLowerBound, self.paddingUpperBound)}")

		self.speedBlendingRange = (self.paddingLowerBound - self.pidLowerBound)
		print(f"Difference Between Bounds: {self.speedBlendingRange}")

		# --- Defining Initial Setpoint ---
		medianValue = np.mean([self.minimumPotentiometerValue, self.maximumPotentiometerValue], dtype = int)
		# Setting the setpoint
		self.pid.setpoint = medianValue
		self.lastSetpoint = self.pid.setpoint

		# --- Defining Settling Characteristics ---
		self.errorMagnitude = errorMagnitude
		self.settledErrorMagnitude = settledErrorMagnitude
		self.currentErrorMagnitude = self.errorMagnitude
		
		# --- Creating Filters ---
		filterSize = 15

		# Potentiometer Filter
		self.potentiometerFilter = MovingAverage(filterSize)
		
		# On-off Filter
		self.onOffFilter = MovingAverage(filterSize)
		
		# Settling Filter
		self.settlingTime = settlingTime
		settlingWindowSize = self.settlingTime//self.samplingTime
		self.settlingFilter = MovingAverage(settlingWindowSize)

		# Populate filters
		for i in range(0, min(filterSize, settlingWindowSize)):
			value = self.ReadPotentiometerValue(self.knobNumber)
			self.SetHasSettled(value)
		# 

		# --- Stats ---
		# Recording min and max speeds
		self.minSpeed = 300 # Set way above the fastest possible speed
		self.maxSpeed = 0 # Set way below the slowest possible speed

		# Set using the same strategy as the other bounds were set
		self.deadzoneLowerBound = self.maxSpeed
		self.deadzoneUpperBound = self.minSpeed	
	# 

	def ReadRawPotentiometerValue(self, potentiometerNumber):
		"""
		Gets the unfiltered value for the appropriate analog input
		This function assumes the ADC is the PCF8591: https://www.nxp.com/docs/en/data-sheet/PCF8591.pdf
		"""
		controlByte = 0x20 # This value should get overwritten so it doesn't matter much what it is

		if (potentiometerNumber == 0):
			controlByte = POT_0_CONTROL_BYTE
		elif (potentiometerNumber == 1):
			controlByte = POT_1_CONTROL_BYTE
		elif (potentiometerNumber == 2):
			controlByte = POT_2_CONTROL_BYTE
		# 

		# Read the value from the ADC
		i2cBus.write_byte(ADC_ADDRESS, controlByte)
		
		# The PCF8591 sends the previously converted value while calculating the new one
		previousValue = i2cBus.read_byte(ADC_ADDRESS)
		value = i2cBus.read_byte(ADC_ADDRESS)

		return value
	#

	def ReadPotentiometerValue(self, potentiometerNumber):
		"""
		Reads and filters the potentiometer value
		"""
		rawValue = self.ReadRawPotentiometerValue(potentiometerNumber)
		return self.potentiometerFilter(rawValue)
	# 

	def ApplyDeadzone(self, pidRecommendation):
		"""
		By default the PID class does not know about the deadzone, this function
		introduces the deadzone to the speed recommended by the PID controller so the
		motor will spin at the proper speed
		"""
		if (pidRecommendation > (self.deadzoneCenter - 0.5*self.deadzoneSize)):
			# Skipping the deadspot in the middle
			recommendedSpeed = pidRecommendation + self.deadzoneSize
		else:
			recommendedSpeed = pidRecommendation
		#
		return recommendedSpeed
	# 

	def ReducePidBoundsAtExtremes(self, recommendedSpeed, potentiometerValue):
		"""
		Limits the values that the PID controller is allowed to access if the system is
		within the boundary limits

		This is to prevent drastic overshoot which may damage some components
		"""
		if (potentiometerValue < self.minimumPotentiometerValue + self.paddingInnerThreshold):
			# Determine the percentage of padding used
			if (potentiometerValue < self.minimumPotentiometerValue + self.paddingOuterThreshold):
				# To close to edge, no padding left
				percentageOfPaddingRemaining = 0
			else:
				# In padding zone, determine amount of padding region left
				percentageOfPaddingRemaining = \
					(self.minimumPotentiometerValue + potentiometerValue \
						- self.paddingOuterThreshold) \
					/ (self.paddingInnerThreshold - self.paddingOuterThreshold)
			#

			# Determine amount to reduce speed by
			percentageUsed = 1 - percentageOfPaddingRemaining
			speedReduction = (percentageUsed)*(self.speedBlendingRange)

			# Determine the fastest allowable speed
			speedLimit = self.pidLowerBound + speedReduction

			# Update PID integral bounds
			self.pid.output_limits = (speedLimit, self.pidUpperBound)
		elif (potentiometerValue > self.maximumPotentiometerValue - self.paddingInnerThreshold):
			# Determine the percentage of padding used
			if (potentiometerValue > self.maximumPotentiometerValue - self.paddingOuterThreshold):
				# To close to edge, no padding left
				percentageOfPaddingRemaining = 0
			else:
				# In padding zone, determine amount of padding region left

				percentageOfPaddingRemaining = (self.maximumPotentiometerValue - potentiometerValue \
						- self.paddingOuterThreshold) / (self.paddingInnerThreshold - self.paddingOuterThreshold)

			# 
			
			# Determine how far the system is from the outer edge
			percentageUsed = 1 - percentageOfPaddingRemaining
			
			# Determine amount to reduce speed by
			speedReduction = (percentageUsed)*(self.speedBlendingRange)

			# Determine the fastest allowable speed
			speedLimit = self.pidUpperBound - speedReduction

			# Update PID integral bounds
			self.pid.output_limits = (self.pidLowerBound, speedLimit)
		else:
			# Reset the bounds to normal
			self.pid.output_limits = (self.pidLowerBound, self.pidUpperBound)
		# 
	# 

	def SetHasSettled(self, potentiometerValue):
		"""
		Returns 1 if the system has settled, updates the float that indicates
		if the system has settled or not
		"""

		self.errorDelta = self.pid.setpoint - potentiometerValue
		isWithinTolerance = (abs(self.errorDelta) < self.currentErrorMagnitude)
		self.hasSettled = self.settlingFilter(isWithinTolerance)

		return self.hasSettled
	# 

	def GetHasSettled(self):
		"""
		Returns self.hasSettled as a bool
		"""
		return bool(math.floor(self.hasSettled))
	# 
	
	def __call__(self, setpoint):
		"""
		Move knob to next location
		"""
		self.pid.setpoint = setpoint
		
		# --- Update Settling State ---
		potentiometerValue = self.ReadPotentiometerValue(self.knobNumber)
		self.SetHasSettled(potentiometerValue)

		print(f"Moving to: {self.pid.setpoint} from {potentiometerValue}")
		
		# Debugging Settings
		secondsBetweenToggle = 5
		secondsBetweenUpdates = 0.05

		# setpoints = deque([50, 205, 30, 225, 100, 155, 10, 245])
		# setpoints = deque([15, 240, 10, 245, 8, 247, 5, 250])
		
		updateMod = secondsBetweenUpdates//self.samplingTime
		
		count = 0
		resetCountAt = secondsBetweenToggle*(1//self.samplingTime)
		print(f"Set? {self.hasSettled}")
		while (not self.GetHasSettled()):
			# --- Rotate through Setpoints ---
			# Iterating through setpoints
			if (count > resetCountAt):
				# self.pid.setpoint = random.randint(self.minimumPotentiometerValue + 5, self.maximumPotentiometerValue - 5)
				
				# self.pid.setpoint = setpoints[0]
				# setpoints.rotate(-1)
				count = 0
			else:
				count += 1
			#
			
			# --- Read Knob Position ---
			# Read the current value of the knob
			potentiometerValue = self.ReadPotentiometerValue(self.knobNumber)

			# Read the current value of the other knob
			rawOnOffValue = self.ReadRawPotentiometerValue(2)
			self.onOffValue = self.onOffFilter(rawOnOffValue)

			# --- Calculate New Motor Speed ---
			# Calculate new output speed
			pidRecommendation = self.pid(potentiometerValue)

			# # Bypassing the deadspot in the middle
			recommendedSpeed = self.ApplyDeadzone(pidRecommendation)

			# - Account for outer padding -
			self.ReducePidBoundsAtExtremes(recommendedSpeed, potentiometerValue)

			# - Has Settled? -
			# Udate currentErrorMagnitude if the setpoint has changed
			if (self.pid.setpoint != self.lastSetpoint):
				self.currentErrorMagnitude = self.errorMagnitude
			#
			
			# Process Error
			hasSettled = self.SetHasSettled(potentiometerValue)
			
			# - Update Servo Speed -
			if ((hasSettled < int(True))):
				# servoHat.move_servo_position(self.knobNumber, newSpeed)
				servoHat.move_servo_position(self.knobNumber, recommendedSpeed)
				servoStopped = False
			else:
				servoHat.move_servo_position(self.knobNumber, 180)
				servoStopped = True
				
				# Relax error bounds
				self.currentErrorMagnitude = self.settledErrorMagnitude
			# 
			
			# --- Stats and Record Keeping - --

			# - Update recorded stats -
			newSpeed = recommendedSpeed
			# Overall Speed Values
			self.minSpeed = min(newSpeed, self.minSpeed)
			self.maxSpeed = max(newSpeed, self.maxSpeed)

			# Speeds closest to deadzone
			if (newSpeed < self.deadzoneCenter):
				self.deadzoneLowerBound = max(newSpeed, self.deadzoneLowerBound)
			else:
				self.deadzoneUpperBound = min(newSpeed, self.deadzoneUpperBound)
			# 

			# No need to update every single cycle
			if (count % updateMod == 0):
				prevP, prevI, prevD = self.pid.components
				print(f"Pos: {potentiometerValue:5.1f} | Tgt: {self.pid.setpoint:3} |" \
					# + f" L Tgt: {self.lastSetpoint:3} |" \
					+ f" Err: {self.currentErrorMagnitude:2} |" \
					+ f" Δ: {self.errorDelta:6.1f} | Set?: {hasSettled:6.4f} |" \
					+ f" Lim: ({self.pid.output_limits[0]:5.2f}, {self.pid.output_limits[1]:5.2f}) |" \
					# + f" R Spd: {recommendedSpeed:.2f} |" \
					# + f" %:{percentageOfPaddingRemaining:4.2f} |" \
					# + f" Red:{speedReduction:4.1f} |" \
					# + f" L:{speedLimit:5.2f} |" \
					+ f" Spd:{newSpeed:5.2f} |" \
					+ f" On Off:{self.onOffValue:5.1f} |"\
					+ f" S:{servoStopped*100:3} |"\
					+ f" P: {float(prevP):7.1f} I: {float(prevI):5.3f} D: {float(prevD):5.2f}")
				# 
			# 
			
			# --- Delay ---
			# So the pi doesn't over-work itself
			time.sleep(self.samplingTime)

			if (self.onOffValue > 127):
				print("I'm done!")
				break

			# --- Record for Next Iteration ---
			# Track Setpoints
			self.lastSetpoint = self.pid.setpoint
		# 

		# Time to stop
		servoHat.move_servo_position(self.knobNumber, 180)
		
		print("")
		print(f"Min Speed: {self.minSpeed} | Max Speed: {self.maxSpeed} | Avg: {np.mean([self.minSpeed, self.maxSpeed])}")
		print(f"Magnitude: {self.speedMagnitude}")
		print(f"PID Bounds: {(self.pidLowerBound, self.pidUpperBound)} | Center: {np.mean([self.pidLowerBound, self.pidUpperBound])}")
		print(f"PID Min Output: {self.minSpeed} | PID Max Output: {self.maxSpeed - self.deadzoneSize} | Max Commanded: {self.maxSpeed}")
		print("")
		print(f"Current Bounds: {self.pid.output_limits}")
		print(f"Deadzone Lower Bound: {self.deadzoneLowerBound} | Deadzone Upper Bound: {self.deadzoneUpperBound}")
		print(f"Padded Limits: {(self.paddingLowerBound, self.paddingUpperBound)} | Magnitude: {self.paddingSpeedMagnitude}")
		print(f"Difference Between Bounds: {self.speedBlendingRange}")
	# 
# 

# ----- Begin Program -----
if __name__ == "__main__":
	knob = KnobController(0)
	knob(127)
	time.sleep(2)

	while True:
		randomSetpoint = random.randint(0 + 5, 255 - 5)
		print(f"# Go To: {randomSetpoint} | on? {knob.onOffValue}")
		
		knob(randomSetpoint)

		if (knob.onOffValue > 127):
			break
		time.sleep(10)
	# 
# 
