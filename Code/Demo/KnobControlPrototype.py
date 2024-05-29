# ----- Imports -----
# Utility
from collections import deque
import random

# Reability
from typing import List

# For Control
import time

# My Code
from KnobSuite import KnobSuite
from KnobController import KnobController

# ----- Begin Program -----
if __name__ == "__main__":
	onOffController = KnobController(2)
	
	# knobSuite = KnobSuite(2, speedMagnitude=15)
	knobSuite = KnobSuite(2)

	conductExperiment = False
	experimentDictionary = None
	if not conductExperiment:
		# setpointQueue = deque([50, 200, 200, 50])
		setpointQueue = deque([50, 200, 100, 150])
		# setpointQueue = deque([25, 225])
		# setpointQueue = deque([50, 200, 25, 225])
		# setpointQueue = deque([50, 200, 40, 210, 30, 220, 25, 225, 20, 230])
		# setpointQueue = deque([30, 225, 25, 230, 20, 235, 15, 240, 10, 245])
		# setpointQueue = deque([15, 240, 10, 245])
		# setpointQueue = deque([15, 240, 10, 245, 8, 247, 5, 250])
		# setpointQueue = deque([10, 8, 5])
		# setpointQueue = deque([5, 250])
		# setpointQueue = deque([5, 250, 127])
		# setpointQueue = deque([50, 205, 30, 225, 100, 155, 10, 245])
		# setpointQueue = deque([125, 127, 130])
	else:
		import json

		# fileName = "ServoExperimentPoints.json"
		fileName = "ServoExperimentPoints_0.json"
		
		experimentDictionary = dict()

		jsonFile = open(fileName)
		experimentDictionary = json.load(jsonFile)
		jsonFile.close()
	
		print(f"Loaded Experimental Data : {experimentDictionary}")

		setpointQueue = deque(experimentDictionary["pointList"])
	# 

	print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	print("TODAY'S POINTS!!!")
	print(setpointQueue)
	print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	
	# knobSuite([127, 127], sequential = True)
	knobSuite([127, 127], sequential = False)

	
	# Move to first location in experiment
	startingLocation = setpointQueue[0]
	knobSuite([startingLocation, startingLocation], sequential = False)
	
	if (onOffController.ReadRawPotentiometerValue(2) > 127):
		exit()
	# 
	time.sleep(2)

	# Prepare for testing knobs
	knob0Logs = []
	knob1Logs = []

	setpointNumber = 0
	while True:
		randomSetpoint = random.randint(0 + 5, 255 - 5)
		setpoints = [randomSetpoint, 255 - randomSetpoint]

		# setpoint = setpointQueue[0]
		# setpointQueue.rotate(-1)
		# setpoints = [setpoint, setpoint]

		print(f"# Go To Location {setpointNumber} : {setpoints}")

		# knobSuite(setpoints, sequential = True)
		knobSuite(setpoints, sequential = False)

		# Get and save logs
		log0, log1 = knobSuite.GetLogs()
		knob0Logs.append(log0)
		knob1Logs.append(log1)

		if (onOffController.ReadRawPotentiometerValue(2) > 127):
			break
		time.sleep(2)

		setpointNumber += 1

		# Terminate if the experiment is over
		if ((experimentDictionary is not None) \
	  		and (setpointNumber == experimentDictionary["numberOfPoints"]) and conductExperiment):
			break
		# 
	# 

	# Save the results
	if conductExperiment:
		# Initialization
		currentTime = time.localtime()
		currentTimeString = time.strftime("%H_%M_%S", currentTime)

		resultsFilename = "ExperimentResults_" + currentTimeString + ".json"
		print("Filename: "+ resultsFilename)

		# Saving Results to Dictionary
		resultsDictionary = dict()
		resultsDictionary["knob0"] = knob0Logs
		resultsDictionary["knob1"] = knob1Logs

		# Saving Dictionary as JSON
		with open(resultsFilename, 'w') as jsonFile:
			json.dump(resultsDictionary, jsonFile)
		# 
		jsonFile.close()

		print(f"Experimental Results Saved To: {resultsFilename}")
	# 
# 
