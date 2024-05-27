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

		# print(f"Start: {startPoint:4} | End: {endPoint:4}")
		if (startPoint != endPoint):
			filteredTransitions.append(log)
		# 
	# 

	return filteredTransitions
# 

def AverageResults(listOfExperimentLogs):
	"""
	Goes through all the logs generated from the experiments and averages the results
	into one log
	"""

	numberOfLogs = len(listOfExperimentLogs[0])
	numberOfLists = len(listOfExperimentLogs)

	print(f"Number of Logs: {numberOfLogs} | Number of Lists: {numberOfLists}")

	listOfAverages: List[dict] = []

	for i in range(0, numberOfLogs):
	# for i in range(0, 20):
		# Access every index that the logs should be in

		# Reset currentAverageDictionary
		currentAverageDictionary = dict()
		currentAverageDictionary["channel"] = ""
		currentAverageDictionary["startSetpoint"] = ""
		currentAverageDictionary["endSetpoint"] = ""
		currentAverageDictionary["time"] = ""
		currentAverageDictionary["overshoot"] = ""

		# Reset Current Information
		currentStartSetpoint = None
		currentEndSetpoint = None
		timeValues = []
		overshootValues = []

		for experimentNum in range(0, numberOfLists):
			# Access the log at i for each experiment list
			
			currentList = listOfExperimentLogs[experimentNum]
			# print(f"There are {len(currentList)} entries")
			# print(f"First Entry: {currentList[0]}")

			currentLog = currentList[i]
			print(f"Current Log: {currentLog}")

			
			# Verify that all experiments have the same starting point
			if (currentStartSetpoint is None):
				currentStartSetpoint = currentLog["startSetpoint"]
				print(f"Started at {currentStartSetpoint}")
				startSetpointMatches = True
			elif (currentLog["startSetpoint"] == currentStartSetpoint):
				# Does this match the other logs at this index?
				startSetpointMatches = True
			else:
				print(f"SOMETHING ISN'T LINING UP")
				startSetpointMatches = False
			# 

			# Verify that all experiments have the same ending point
			if (currentEndSetpoint is None):
				currentEndSetpoint = currentLog["endSetpoint"]
				print(f"Ended at {currentEndSetpoint}")
				endSetpointMatches = True
			elif (currentLog["endSetpoint"] == currentEndSetpoint):
				# Does this match the other logs at this index?
				endSetpointMatches = True
			else:
				print(f"SOMETHING ISN'T LINING UP")
				endSetpointMatches = False
			#
			
			# Vetting Complete, save values
			timeValues.append(currentLog["time"])
			overshootValues.append(currentLog["overshoot"])
		# 
		
		# Data has been collected, compute the average
		
		if startSetpointMatches and endSetpointMatches:
			# Average the data
			print(f"Time: {timeValues}")
			print(f"Overshoot: {overshootValues}")

			averageTime = np.mean(timeValues)
			averageOvershoot = np.mean(overshootValues)

			print(f"Average Time: {averageTime: 6.2f} | Average Overshoot: {averageOvershoot: 6.2f}")

			# Create and Save Dictonary Entry
			currentAverageDictionary["channel"] = currentLog["channel"]
			currentAverageDictionary["startSetpoint"] = currentLog["startSetpoint"]
			currentAverageDictionary["endSetpoint"] = currentLog["endSetpoint"]
			currentAverageDictionary["time"] = averageTime
			currentAverageDictionary["overshoot"] = averageOvershoot
			
			print(f"Averaged Entry: {currentAverageDictionary}")

			listOfAverages.append(currentAverageDictionary)
			
			# print(f"Current List: {listOfAverages}")
		else:
			print(f"I GIVE UP!!!")
		# 
	# 

	# print(f"Returning: {listOfAverages}")

	return listOfAverages
# 

def ConvertLogsToLists(listOfLogs: List[dict]):
	"""
	Converts the list of logs into 4 arrays where all entires from the same log have the same
	index in the array
	"""

	# print(f"List o Logs: {listOfLogs}")

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
	toyDefaultFolder = "ToyExperiments/Clamped/"

	# --- Loading Results ---
	# Experimenting
	folder = defaultFolderPath
	title = "No I Term Clamping"
	# title = "I Term Clamping Upon Initialization"

	experimentResults: List[dict] = []

	for name in os.listdir(folder):
		with open(os.path.join(folder, name)) as currentFile:
			print(f"Filename: '{name}'")

			currentDictionary = dict()
			currentDictionary:dict = json.load(currentFile)
			currentFile.close()

			print(f"Dictionary: {currentDictionary.keys()}")

			experimentResults.append(currentDictionary)
		# 
	# 

	# --- Filtering Results ---

	# knob0Logs = currentDictionary["knob0"]
	# print(f"There are {len(knob0Logs)} logs")
	# knob0Logs = RemoveStationaryMovements(knob0Logs)
	# print(f"There are {len(knob0Logs)} logs")

	# Pooling Results
	knob0Logs = []
	knob1Logs = []
	for i in range(0, len(experimentResults)):
		knob0Logs.append(experimentResults[i]["knob0"])
		knob1Logs.append(experimentResults[i]["knob1"])
		print(f"Knob0 List Length: {len(knob0Logs)}")
		print(f"Knob1 List Length: {len(knob1Logs)}")
	# 

	# Removing Identities
	for i in range(0, len(experimentResults)):
		knob0Logs[i] = RemoveStationaryMovements(knob0Logs[i])
		knob1Logs[i] = RemoveStationaryMovements(knob1Logs[i])
	# 

	# Averaging Results
	knob0Averages = AverageResults(knob0Logs)

	# --- Converting To Lists ---
	startList, endList, settlingTimeList, overshootList = ConvertLogsToLists(knob0Averages)

	for i in range(0, len(startList)):
		print(f"S: {startList[i]:3} | E: {endList[i]:3} | t: {settlingTimeList[i]:5.2f} | O: {overshootList[i]:5.2f}")
	# 
		
	# --- Plotting Results ---	
	
	# Create the figure and plot (this command can also do nested plots)
	fig, ax = plt.subplots()

	# Plot the data
	print(f"Lengths: S: {len(startList)} | E: {len(endList)} | t: {len(settlingTimeList)} | O: {len(overshootList)}")

	# ax.pcolormesh(startList, endList, settlingTimeList, alpha = 0.5)
	# ax.pcolormesh([startList, endList], settlingTimeList, alpha=0.5)

	# Coloring the background
	trpColor = ax.tripcolor(startList, endList, settlingTimeList,\
						shading='gouraud', alpha=0.5)
	fig.colorbar(trpColor) # Adding the color-bar to the figure
	
	# ax.scatter(startList, endList, c=settlingTimeList, s=overshootList)
	ax.scatter(startList, endList, c=settlingTimeList)

	figureName = "experimentResults"
	# plt.show()
	plt.savefig(figureName)
# 