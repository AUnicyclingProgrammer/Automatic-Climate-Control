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
		
		# Settling Filter
		self.settlingTime = settlingTime
		settlingWindowSize = self.settlingTime//self.samplingTime
		self.settlingFilter = MovingAverage(settlingWindowSize)

		# Populate filters
		for i in range(0, min(filterSize, settlingWindowSize)):
			value = self.ReadPotentiometerValue(self.knobNumber)
			self.UpdateHasSettled(value)
		# 

		# --- Stats ---
		# Recording min and max speeds
		self.minSpeed = 300 # Set way above the fastest possible speed
		self.maxSpeed = 0 # Set way below the slowest possible speed

		# Set using the same strategy as the other bounds were set
		self.deadzoneLowerBound = self.maxSpeed
		self.deadzoneUpperBound = self.minSpeed

		# --- Indicating that the System has Intialized ---
		self.updated = False
		self.terminatedCleanly = False
		self.newInstance = True
		
		# --- Creating First Log ---
		self.startSetpoint = self.lastSetpoint
		self.startTime = time.monotonic()
		self.endTime = time.monotonic()
		
		self.GenerateLog()
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

	def GetHasSettled(self):
		"""
		Returns self.hasSettled as a bool
		"""
		
		return self.hasSettled == 1
	# 

	def UpdateHasSettled(self, potentiometerValue = None):
		"""
		Returns 1 if the system has settled.
		Also the settling filter used to indicate if the system has settled or not
		based on the current error bounds and current system position (which can be
		updated with potentiometerValue)

		potentiometerValue (optional) : last value read from potentiometer
		"""
		
		# The filter should be updated if there is a new value, otherwise this is a query
		usePreviousValue = potentiometerValue is not None

		# Was a new value provided
		if not usePreviousValue:
			currentValue = self.lastPotentiometerValue
		else:
			currentValue = potentiometerValue
			self.lastPotentiometerValue = currentValue
		# 
		
		# - Determine Current Settling State -
		# Is the value within the tolrances
		self.errorDelta = currentValue - self.pid.setpoint
		isWithinTolerance = (abs(self.errorDelta) < self.currentErrorMagnitude)

		# Was the system previously stable but now considered unstable?
		previouslySettled = self.hasSettled == 1
		failureCausedByTolranceChange = previouslySettled and not isWithinTolerance
		
		# - Update Filter -
		# Filter should always be updated if the system is not within the current tolerance
		if usePreviousValue or failureCausedByTolranceChange:
			self.hasSettled = self.settlingFilter(isWithinTolerance)
		# 

		# Update overshoot if a new value was provided
		if not usePreviousValue:
			if ((self.rising) and (self.errorDelta > 0)):
				# If the error is initially negative but becomes positive
				self.overshoot = max(self.overshoot, abs(self.errorDelta))
			elif ((not self.rising) and (self.errorDelta < 0)):
				# If the error is initially positive but becomes negative
				self.overshoot = max(self.overshoot, abs(self.errorDelta))
			#
		# 

		return self.hasSettled == 1
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

	def GetLastSetpoint(self):
		"""
		Retreives the previous setpoint from the log
		"""

		return self.log["endSetpoint"]
	# 

	def UpdateSetpoint(self, setpoint):
		"""
		Updates the setpoint without moving to the new location
		"""

		self.pid.setpoint = setpoint
		
		# If the setpoint has been manually changed then the class needs re-initialized
		self.updated = False
		self.terminatedCleanly = False
	# 
	
	def __call__(self, setpoint, sequential = True, printDebugValues = True):
		"""
		Move knob to next location

		setpoint : next location to move to
		sequential : if true, call will not exit until system has settled
		printDebugValues : if true, prints debug values during operation
		"""
		# --- Determining State ---
		# Does the system need re-initialized?
		if (not self.updated):
			print(f"Updating {self.knobNumber}")
			# --- Preparing for Logging ---
			self.startTime = time.monotonic()
			self.startSetpoint = self.GetLastSetpoint()

			# --- Updating Controller Setpoint ---
			self.pid.setpoint = setpoint
			
			# --- Update Settling State ---
			# Make sure to update the error bounds if the setpoint has changed
			if (self.pid.setpoint != self.GetLastSetpoint()):
				# Different setpoint, reset error bounds
				self.currentErrorMagnitude = self.errorMagnitude
			# 

			# Error mangitude is now correct, it is safe to update
			self.UpdateHasSettled()
			
			# --- Preparing to Calculate Overshoot ---
			# Reset last known overshoot
			self.overshoot = 0

			# Recording starting position so overshoot can be calculated
			self.startingPosition = self.lastPotentiometerValue
			
			# System is rising if it is currently at a value below the setpoint
			self.rising = (self.startingPosition < self.pid.setpoint)
			
			# --- Update Complete, Peparing to Move ---
			# System has been updated, but that also means it hasn't officially exited yet
			self.updated = True
			self.terminatedCleanly = False

			if printDebugValues:
				print(f"Moving {self.knobNumber} to: {self.pid.setpoint} from {self.startingPosition}. Rising?: {self.rising}")
			# 

			# --- Initialize Timer ---
			secondsBetweenUpdates = 0.05
			updateMod = secondsBetweenUpdates//self.samplingTime
			
			self.count = 0
			self.resetCountAt = updateMod
		# 

		# --- Moving to New Location ---
		if (sequential):
			# For sequential operation
			while (not self.GetHasSettled()):
				self.Update()
				time.sleep(self.samplingTime)
			# 
		else:
			# Performing Parallel Operation
			# Reasons why the system should update:
			# * it is not in the right position
			# * it has not properly exited
			if (not self.GetHasSettled or not self.terminatedCleanly):
				# Increment by one time step
				self.Update()
			# 
		# 
		
		# Is the system settled and has it officially exited yet?
		if (self.GetHasSettled() and not self.terminatedCleanly):
			# Time to stop
			servoHat.move_servo_position(self.knobNumber, 180)
			
			# Log Data
			self.endTime = time.monotonic()
			self.lastSetpoint = self.pid.setpoint
			self.log = self.GenerateLog()
			
			if printDebugValues:
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
				print(f"Current Error: {self.errorDelta:6.2f}")
				print(f"Log: {self.log}")
			# 

			# System has officially exited, but this means it is not longer updated
			self.updated = False
			self.terminatedCleanly = True
			self.newInstance = False
		# 
	# 

	def Update(self, printDebugValues = True):
		"""
		Updates the controller by one time step
		"""
		# --- Manage Looping Count ---
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
		newSpeed = self.ApplyDeadzone(pidRecommendation)

		# - Account for outer padding -
		self.ReducePidBoundsAtExtremes(newSpeed, potentiometerValue)

		# - Has Settled? -
		hasSettled = self.UpdateHasSettled(potentiometerValue)
		
		# - Update Servo Speed -
		if (not hasSettled):
			# Update Speed
			servoHat.move_servo_position(self.knobNumber, newSpeed)
		else:
			# Turn off Servo
			servoHat.move_servo_position(self.knobNumber, 180)
			
			# Relax error bounds
			self.currentErrorMagnitude = self.settledErrorMagnitude
		# 
		
		# --- Stats and Record Keeping - --

		# - Update recorded stats -
		# Overall Speed Values
		self.minSpeed = min(newSpeed, self.minSpeed)
		self.maxSpeed = max(newSpeed, self.maxSpeed)

		# Record speeds closest to deadzone
		if (newSpeed < self.deadzoneCenter):
			self.deadzoneLowerBound = max(newSpeed, self.deadzoneLowerBound)
		else:
			self.deadzoneUpperBound = min(newSpeed, self.deadzoneUpperBound)
		# 

		# Print Out Debugging Information
		if ((self.count % self.resetCountAt == 0) and printDebugValues):
			prevP, prevI, prevD = self.pid.components
			print(f"#: {self.knobNumber} | " \
				+ f"Pos: {potentiometerValue:5.1f} | Tgt: {self.pid.setpoint:3} |" \
				# + f" L Tgt: {self.GetLastSetpoint():3} |" \
				+ f" Err: {self.currentErrorMagnitude:4.2f} |" \
				+ f" Δ: {self.errorDelta:6.1f} |" \
				+ f" O: {self.overshoot:4.1f}" \
				+ f" Set?: {self.hasSettled:6.4f} |" \
				+ f" Lim: ({self.pid.output_limits[0]:5.2f}, {self.pid.output_limits[1]:5.2f}) |" \
				# + f" %:{percentageOfPaddingRemaining:4.2f} |" \
				# + f" Red:{speedReduction:4.1f} |" \
				# + f" L:{speedLimit:5.2f} |" \
				+ f" Spd:{newSpeed:5.2f} |" \
				# + f" S:{servoStopped*100:3} |"\
				+ f" S:{self.UpdateHasSettled()*100:3} |"\
				+ f" P: {float(prevP):7.1f} I: {float(prevI):5.3f} D: {float(prevD):5.2f} |" \
				# + f" Count: {int(self.count)}" \
			)
			# 
		# 
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

		# - "Private" Variables -
		self.numberOfKnobs = numberOfKnobs
		self.knobs: List[KnobController] = []
		self.settledKnobs: List[bool] = []
				
		# - Creating Suite of Knobs -
		for number in range(0, numberOfKnobs):
			knobController = KnobController(number, **kwargs)
			self.knobs.append(knobController) 
			
			# Assume all knobs are not in the correct place to begin with
			self.settledKnobs.append(False)
		# 

		# - Other useful variables -
		# All controllers have the same sampling time
		self.samplingTime = knobController.samplingTime
	# 

	def HasControllerSettled(self, knobController: KnobController):
		"""
		Returns True if the knobController reports that the knob is in the correct
		position
		"""

		hasSettled = knobController.UpdateHasSettled()
		hasTerminatedCleanly = knobController.terminatedCleanly
		condition = hasTerminatedCleanly and hasSettled

		return condition
	# 

	def __call__(self, setpointList, sequential = True, printDebugValues = True):
		"""
		Updates all knobs in the suite at the same time

		setpointList: list of setpoints to pass to knobs. The index the value is at
			corresponds to the knob channel the command will be sent to. No channels will be
			skipped
		sequential : if True, adjusts knobs one after the other
		"""

		if printDebugValues:
			for number in range(0, self.numberOfKnobs):
				setpoint = setpointList[number]
				knobController = self.knobs[number]
				print(f"Num: {number} | Setpoint: {setpoint} | Sequential? : {sequential} |" \
					+ f" Settled: {knobController.UpdateHasSettled()} |" \
					+ f" Terminated?: {knobController.terminatedCleanly} |" \
					+ f" Last Setpoint: {knobController.lastSetpoint}"
				)
			# 
		# 

		# --- Update All Setpoints and Settling States ---
		# But don't command the system to move yet
		for number in range(0, self.numberOfKnobs):
			# Get Knob and Next Setpoint
			knobController = self.knobs[number]
			setpoint = setpointList[number]

			# Update the Target Setpoint Only (No Movmement Commanded)
			knobController.UpdateSetpoint(setpoint)

			# Update Settled Status
			self.settledKnobs[number] = self.HasControllerSettled(knobController)

			# Save Knob Instance (Technically Unecessary)
			self.knobs[number] = knobController
		# 
		
		
		# --- Move to Setpoints ---
		while (not np.all(self.settledKnobs)):
			for number in range(0, self.numberOfKnobs):
				# Get Knob Controller
				knobController = self.knobs[number]
				
				# Update Knob (if not settled)
				if (not self.settledKnobs[number]):
					knobController(setpoint, sequential=sequential)
				# 

				# Has it settled
				self.settledKnobs[number] = self.HasControllerSettled(knobController)

				# Add delay if processing all knobs in parallel
				if not sequential:
					time.sleep(self.samplingTime)	
				# 

				# Save Knob Instance (Technically Unecessary)
				self.knobs[number] = knobController
			# 
		# 
	# 
# 


# ----- Begin Program -----
if __name__ == "__main__":
	# knobSuite = KnobSuite(2, speedMagnitude=15)
	knobSuite = KnobSuite(2)
	
	# knobSuite([127, 127], sequential = True)
	knobSuite([127, 127], sequential = False)
	
	if (ReadPotentiometer(2) > 127):
		exit()
	# 
	time.sleep(2)

	while True:
		randomSetpoint = random.randint(0 + 5, 255 - 5)

		setpoints = list(randomSetpoint*np.ones(knobSuite.numberOfKnobs, dtype = float))
		# setpoints = [randomSetpoint, 255 - randomSetpoint]
		# print(f"# Go To: {setpoints}")

		# knobSuite(setpoints, sequential = True)
		knobSuite(setpoints, sequential = False)

		if (ReadPotentiometer(2) > 127):
			break
		time.sleep(2)
	# 
# 
