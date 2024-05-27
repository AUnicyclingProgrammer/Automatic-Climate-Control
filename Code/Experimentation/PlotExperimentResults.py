# ----- Imports -----
# Utility
from collections import deque
import math
import numpy as np
import random
import matplotlib.pyplot as plt
import json
import os

# Readability
import time
from typing import List


# ----- Methods and Functions -----
def RemoveStationaryMovements(transitionList):
	"""
	This function removes all transitions that started and ended on the same point.
	"""

	filteredTransitions = []

	for log in transitionList:
		startPoint = log["startSetpoint"]
		endPoint = log["endSetpoint"]

		print(f"Start: {startPoint:4} | End: {endPoint:4}")
		if (startPoint != endPoint):
			filteredTransitions.append(log)
		# 
	# 

	return filteredTransitions
# 

def ConvertLogsToLists(listOfLogs: List[dict]):
	"""
	Converts the list of logs into 4 arrays where all entires from the same log have the same
	index in the array
	"""

	startPoints: List[int] = []
	endPoints: List[int] = []
	settlingTime: List[float] = []
	overshoot: list[float] = []
	
	for log in listOfLogs:
		startPoints.append(log["startSetpoint"])
		endPoints.append(log["endSetpoint"])
		settlingTime.append(log["time"])
		overshoot.append(log["overshoot"])
	# 

	return startPoints, endPoints, settlingTime, overshoot
# 

# ----- Utility Classes -----

# ----- Begin Program -----
if __name__ == "__main__":
	# --- Universal Parameters ---
	defaultFolderPath = "./DefaultConfiguration/"
	clampedFolderPath = "./ClampedConfiguration/"

	toyDefaultFolder = "ToyExperiments/Default/"

	# --- Loading Results ---
	# Experimenting
	folder = toyDefaultFolder
	for name in os.listdir(folder):
		with open(os.path.join(folder, name)) as currentFile:
			print(f"Filename: '{name}'")

			currentDictionary = dict()
			currentDictionary:dict = json.load(currentFile)
			currentFile.close()

			print(f"Dictionary: {currentDictionary}")
	# 

	# --- Filtering Results ---
	knob0Logs = currentDictionary["knob0"]

	print(f"There are {len(knob0Logs)} logs")

	knob0Logs = RemoveStationaryMovements(knob0Logs)

	print(f"There are {len(knob0Logs)} logs")

	# --- Converting To Lists ---
	startList, endList, settlingTimeList, overshootList = ConvertLogsToLists(knob0Logs)

	print(len(startList))
	print(len(endList))
	print(len(settlingTimeList))
	print(len(overshootList))
	for i in range(0, len(startList)):
		print(f"S: {startList[i]:3} | E: {endList[i]:3} | t: {settlingTimeList[i]:5.2f} | O: {overshootList[i]:5.2f}")
	# 
		
	# --- Plotting Results ---
	import matplotlib
	
	# Create the figure and plot (this command can also do nested plots)
	fig, ax = plt.subplots()

	# Plot the data
	ax.scatter(startList, endList, c=settlingTimeList)

	plt.show()
# 