# ----- Imports -----
# Utility
import numpy as np

# Reability
from typing import List

# For Control
import time

# My Code
from KnobController import KnobController

# ----- Class -----
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
				# Get Knob Controller and Setpoint
				knobController = self.knobs[number]
				setpoint = setpointList[number]
				
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

	def GetLogs(self):
		"""
		Get the logs from each controller in the list of controllers
		"""

		logs = []

		for number in range(0, self.numberOfKnobs):
			knobController = self.knobs[number]
			
			# Get the log
			logs.append(knobController.log)
		# 

		return logs

	# 
# 

# ----- Methods and Functions -----

# ----- Utility Classes -----

# ----- Begin Program -----
if __name__ == "__main__":
    print("Program Completed")
# 
