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
			  speedMagnitude = 30, boundarySpeedMagnitude = 4,
			  boundaryOuterThreshold = 20, boundaryInnerThreshold = 40,
			  errorMagnitude = 1.1, settledErrorMagnitude = 5, settlingTime = 0.25,
			  printDebugValues = True):
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
		self.knobNumber = int(knobNumber)
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
		if printDebugValues:
			print(f"PID Limits: {self.pid.output_limits}")
		# 

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
		self.speedBlendingRange = (self.paddingLowerBound - self.pidLowerBound)
		
		if printDebugValues:
			print(f"Padded Limits: {(self.paddingLowerBound, self.paddingUpperBound)}")
			print(f"Difference Between Bounds: {self.speedBlendingRange}")
		# 

		# --- Defining Initial Setpoint ---
		medianValue = np.mean([self.minimumPotentiometerValue, self.maximumPotentiometerValue], dtype = int)
		# Setting the setpoint
		self.pid.setpoint = medianValue
		self.lastSetpoint = self.pid.setpoint

		# --- Defining Settling Characteristics ---
		self.errorMagnitude = errorMagnitude
		self.settledErrorMagnitude = settledErrorMagnitude
		self.currentErrorMagnitude = self.errorMagnitude
		
		# Log values related to settling (currently placeholders)
		self.overshoot = 0
		self.rising = 0
		
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

		# Don't know what this value is yet
		self.endTime = None
	# 

	# --- Potentiometer ---
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

	# --- PID Output Modifications ---
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

	# --- Settling ---
	def SetHasSettled(self, potentiometerValue):
		"""
		Returns 1 if the system has settled, updates the float that indicates
		if the system has settled or not
		"""

		self.errorDelta = potentiometerValue - self.pid.setpoint
		isWithinTolerance = (abs(self.errorDelta) < self.currentErrorMagnitude)
		self.hasSettled = self.settlingFilter(isWithinTolerance)

		if ((self.rising) and (self.errorDelta > 0)):
			# If the error is initially negative but becomes positive
			self.overshoot = max(self.overshoot, abs(self.errorDelta))
		elif ((not self.rising) and (self.errorDelta < 0)):
			# If the error is initially positive but becomes negative
			self.overshoot = max(self.overshoot, abs(self.errorDelta))
		# 

		return self.hasSettled
	# 

	def GetHasSettled(self):
		"""
		Returns self.hasSettled as a bool
		"""
		return bool(math.floor(self.hasSettled))
	# 

	def GenerateLog(self):
		"""
		This function is used for experiments, it tracks a few key system metrics

		Metrics tracked
		* setpoint
		* lastSetpoint
		* overshoot
		* time
		* channel
		* minSpeed
		* maxSpeed
		"""

		currentLog = dict()
		currentLog["channel"] = self.knobNumber
		currentLog["startSetpoint"] = self.startSetpoint
		currentLog["endSetpoint"] = self.pid.setpoint
		currentLog["time"] = self.endTime - self.startTime
		currentLog["overshoot"] = self.overshoot
		currentLog["minSpeed"] = self.minSpeed
		currentLog["maxSpeed"] = self.maxSpeed
		self.log = currentLog

		return currentLog
	# 
	
	def __call__(self, setpoint, sequential = True, printDebugValues = True):
		"""
		Move knob to next location

		setpoint : next location to move to
		sequential : if true, call will not exit until system has settled
		printDebugValues : if true, prints debug values during operation
		"""
		# --- Preparing for Logging ---
		self.startTime = time.monotonic()

		# --- Updating Controller Settings ---
		# Sequential Operation
		self.startSetpoint = self.lastSetpoint
		self.pid.setpoint = setpoint

		# Udate currentErrorMagnitude if the setpoint has changed
		if (self.pid.setpoint != self.lastSetpoint):
			self.currentErrorMagnitude = self.errorMagnitude
		#
		
		# --- Update Settling State ---
		potentiometerValue = self.ReadPotentiometerValue(self.knobNumber)
		self.SetHasSettled(potentiometerValue)
		
		# --- Preparing to Calculate Overshoot ---
		# Reset last known overshoot
		self.overshoot = 0

		# Recording starting position so overshoot can be calculated
		self.startingPosition = potentiometerValue
		
		# System is rising it is currently at a value below the setpoint
		self.rising = (potentiometerValue < self.pid.setpoint)
		
		# --- Moving to New Location ---
		if printDebugValues:
			print(f"Moving to: {self.pid.setpoint} from {self.startingPosition}. Rising?: {self.rising}")
		# 

		secondsBetweenUpdates = 0.05
		updateMod = secondsBetweenUpdates//self.samplingTime
		
		self.count = 0
		self.resetCountAt = updateMod

		if (sequential):
			# For sequential operation
			while (not self.GetHasSettled()):
				self.Update()
				time.sleep(self.samplingTime)
			# 
		elif (not self.GetHasSettled() and (self.endTime is not None)):
			# For parallel operation
			self.Update()
		# 
			
		# while ((not self.GetHasSettled()) and sequential):
		# 	# --- Rotate through Setpoints ---
		# 	# Iterating through setpoints
		# 	if (count > resetCountAt):
		# 		count = 0
		# 	else:
		# 		count += 1
		# 	#
			
		# 	# --- Read Knob Position ---
		# 	# Read the current value of the knob
		# 	potentiometerValue = self.ReadPotentiometerValue(self.knobNumber)

		# 	# --- Calculate New Motor Speed ---
		# 	# Calculate new output speed
		# 	pidRecommendation = self.pid(potentiometerValue)

		# 	# # Bypassing the deadspot in the middle
		# 	recommendedSpeed = self.ApplyDeadzone(pidRecommendation)

		# 	# - Account for outer padding -
		# 	self.ReducePidBoundsAtExtremes(recommendedSpeed, potentiometerValue)

		# 	# - Has Settled? -
		# 	hasSettled = self.SetHasSettled(potentiometerValue)
			
		# 	# - Update Servo Speed -
		# 	if ((hasSettled < int(True))):
		# 		# servoHat.move_servo_position(self.knobNumber, newSpeed)
		# 		servoHat.move_servo_position(self.knobNumber, recommendedSpeed)
		# 		servoStopped = False
		# 	else:
		# 		servoHat.move_servo_position(self.knobNumber, 180)
		# 		servoStopped = True
				
		# 		# Relax error bounds
		# 		self.currentErrorMagnitude = self.settledErrorMagnitude
		# 	# 
			
		# 	# --- Stats and Record Keeping - --

		# 	# - Update recorded stats -
		# 	newSpeed = recommendedSpeed
		# 	# Overall Speed Values
		# 	self.minSpeed = min(newSpeed, self.minSpeed)
		# 	self.maxSpeed = max(newSpeed, self.maxSpeed)

		# 	# Speeds closest to deadzone
		# 	if (newSpeed < self.deadzoneCenter):
		# 		self.deadzoneLowerBound = max(newSpeed, self.deadzoneLowerBound)
		# 	else:
		# 		self.deadzoneUpperBound = min(newSpeed, self.deadzoneUpperBound)
		# 	# 

		# 	# No need to update every single cycle
		# 	if ((count % updateMod == 0) and printDebugValues):
		# 		prevP, prevI, prevD = self.pid.components
		# 		print(f"#: {self.knobNumber} | " \
		# 			+ f"Pos: {potentiometerValue:5.1f} | Tgt: {self.pid.setpoint:3} |" \
		# 			# + f" L Tgt: {self.lastSetpoint:3} |" \
		# 			+ f" Err: {self.currentErrorMagnitude:4.2f} |" \
		# 			+ f" Δ: {self.errorDelta:6.1f} |" \
		# 			+ f" O: {self.overshoot:4.1f}" \
		# 			+ f" Set?: {hasSettled:6.4f} |" \
		# 			+ f" Lim: ({self.pid.output_limits[0]:5.2f}, {self.pid.output_limits[1]:5.2f}) |" \
		# 			# + f" R Spd: {recommendedSpeed:.2f} |" \
		# 			# + f" %:{percentageOfPaddingRemaining:4.2f} |" \
		# 			# + f" Red:{speedReduction:4.1f} |" \
		# 			# + f" L:{speedLimit:5.2f} |" \
		# 			+ f" Spd:{newSpeed:5.2f} |" \
		# 			# + f" On Off:{self.onOffValue:5.1f} |"\
		# 			# + f" S:{servoStopped*100:3} |"\
		# 			+ f" P: {float(prevP):7.1f} I: {float(prevI):5.3f} D: {float(prevD):5.2f}")
		# 		# 
		# 	# 
			
		# 	# --- Delay ---
		# 	# So the pi doesn't over-work itself
		# 	time.sleep(self.samplingTime)

		# 	# --- Record for Next Iteration ---
		# 	# Track Setpoints
		# 	self.lastSetpoint = self.pid.setpoint
		# # 

		# Has the system settled before?
		if (self.GetHasSettled() and (self.endTime is None)):
			# Time to stop
			servoHat.move_servo_position(self.knobNumber, 180)
			self.endTime = time.monotonic()
			self.log = self.GenerateLog()
			
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
			print("")
			print(f"Log: {self.log}")
		# 
	# 

	def Update(self, printDebugValues = True):
		"""
		Updates the controller by one time step
		"""
		# --- Rotate through Setpoints ---
		# Iterating through setpoints
		if (self.count > self.resetCountAt):
			self.count = 0
		else:
			self.count += 1
		#
		
		# --- Read Knob Position ---
		# Read the current value of the knob
		potentiometerValue = self.ReadPotentiometerValue(self.knobNumber)

		# --- Calculate New Motor Speed ---
		# Calculate new output speed
		pidRecommendation = self.pid(potentiometerValue)

		# # Bypassing the deadspot in the middle
		recommendedSpeed = self.ApplyDeadzone(pidRecommendation)

		# - Account for outer padding -
		self.ReducePidBoundsAtExtremes(recommendedSpeed, potentiometerValue)

		# - Has Settled? -
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
		if ((self.count % self.resetCountAt == 0) and printDebugValues):
			prevP, prevI, prevD = self.pid.components
			print(f"#: {self.knobNumber} | " \
				+ f"Pos: {potentiometerValue:5.1f} | Tgt: {self.pid.setpoint:3} |" \
				# + f" L Tgt: {self.lastSetpoint:3} |" \
				+ f" Err: {self.currentErrorMagnitude:4.2f} |" \
				+ f" Δ: {self.errorDelta:6.1f} |" \
				+ f" O: {self.overshoot:4.1f}" \
				+ f" Set?: {hasSettled:6.4f} |" \
				+ f" Lim: ({self.pid.output_limits[0]:5.2f}, {self.pid.output_limits[1]:5.2f}) |" \
				# + f" R Spd: {recommendedSpeed:.2f} |" \
				# + f" %:{percentageOfPaddingRemaining:4.2f} |" \
				# + f" Red:{speedReduction:4.1f} |" \
				# + f" L:{speedLimit:5.2f} |" \
				+ f" Spd:{newSpeed:5.2f} |" \
				# + f" On Off:{self.onOffValue:5.1f} |"\
				# + f" S:{servoStopped*100:3} |"\
				+ f" P: {float(prevP):7.1f} I: {float(prevI):5.3f} D: {float(prevD):5.2f}")
			# 
		# 
		
		# --- Delay ---
		# So the pi doesn't over-work itself
		# time.sleep(self.samplingTime)

		# --- Record for Next Iteration ---
		# Track Setpoints
		self.lastSetpoint = self.pid.setpoint		
	# 
# 

class KnobSuite:
	"""
	This class adjusts all the knobs in a suite simultaneously while avoiding
	conflicts on the i2c line
	"""

	def __init__(self, numberOfKnobs, **kwargs):
		"""
		Initializes the knob suite

		numberOfKnobs : number of knobs to create, channels begin at at 0 and count up to
			this number minus 1
		**kwargs : named arguments to sent to each KnobController instance
		"""

		self.numberOfKnobs = numberOfKnobs
		self.knobs = []
		
		# Creating the suite of knobs
		for number in range(0, numberOfKnobs):
			knobController = KnobController(number, **kwargs)
			self.knobs.append(knobController)
		# 

		# Other useful variables
		self.samplingTime = knobController.samplingTime

	# 

	def __call__(self, setpointList, printDebugValues = True):
		"""
		Updates all knobs in the suite at the same time

		setpointList: list of setpoints to pass to knobs. The index the value is at
			corresponds to the knob channel the command will be sent to. No channels will be
			skipped
		"""

		for number in range(0, self.numberOfKnobs):
			# Get Knob and Setpoint
			knobController = self.knobs[number]
			setpoint = setpointList[number]
			
			if printDebugValues:
				print(f"Num: {number} | Setpoint: {setpoint}")
			# 
			
			# Update Knob
			knobController(setpoint)
		# 

	# 
# 


# ----- Begin Program -----
if __name__ == "__main__":
	# knobSuite = KnobSuite(2, speedMagnitude=15)
	knobSuite = KnobSuite(2)
	
	knobSuite([127, 127])
	
	if (ReadPotentiometer(2) > 127):
		exit()
	# 
	time.sleep(2)

	while True:
		randomSetpoint = random.randint(0 + 5, 255 - 5)
		print(f"# Go To: {randomSetpoint}")

		setpoints = list(randomSetpoint*np.ones(knobSuite.numberOfKnobs, dtype = float))

		knobSuite(setpoints)
		
		# knob0(randomSetpoint)
		# print("Log0" + str(knob0.log))
		
		# knob1(randomSetpoint)
		# print("Log1" + str(knob1.log))

		if (ReadPotentiometer(2) > 127):
			break
		time.sleep(2)
	# 
# 
