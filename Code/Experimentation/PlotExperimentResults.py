# ----- Imports -----
# Utility
from collections import deque
import math
import matplotlib.axes
import matplotlib.figure
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

	# Extract values into variables so the code is more legible
	numberOfLogs = len(listOfExperimentLogs[0])
	numberOfLists = len(listOfExperimentLogs)

	# print(f"Number of Logs: {numberOfLogs} | Number of Lists: {numberOfLists}")

	listOfAverages: List[dict] = []

	for i in range(0, numberOfLogs):
		# For each log index

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

		# Average all logs at i
		for experimentNum in range(0, numberOfLists):
			# For each log at i from each experiment
			currentList = listOfExperimentLogs[experimentNum]
			currentLog = currentList[i]
			
			# Verify that all experiments have the same starting point
			if (currentStartSetpoint is None):
				currentStartSetpoint = currentLog["startSetpoint"]
				# print(f"Started at {currentStartSetpoint}")
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
				# print(f"Ended at {currentEndSetpoint}")
				endSetpointMatches = True
			elif (currentLog["endSetpoint"] == currentEndSetpoint):
				# Does this match the other logs at this index?
				endSetpointMatches = True
			else:
				print(f"SOMETHING ISN'T LINING UP")
				endSetpointMatches = False
			#
			
			# Save the values from the current log
			timeValues.append(currentLog["time"])
			overshootValues.append(currentLog["overshoot"])
		# 
		
		# Data has been collected, compute the average
		if startSetpointMatches and endSetpointMatches:
			# If all logs start and end at the same spot
			
			# Average the data
			averageTime = np.mean(timeValues)
			averageOvershoot = np.mean(overshootValues)

			# print(f"Time: {timeValues}")
			# print(f"Overshoot: {overshootValues}")
			# print(f"Average Time: {averageTime: 6.2f} | Average Overshoot: {averageOvershoot: 6.2f}")

			# Save Results to currentAverageDictionary
			currentAverageDictionary["channel"] = currentLog["channel"]
			currentAverageDictionary["startSetpoint"] = currentLog["startSetpoint"]
			currentAverageDictionary["endSetpoint"] = currentLog["endSetpoint"]
			currentAverageDictionary["time"] = averageTime
			currentAverageDictionary["overshoot"] = averageOvershoot
			
			listOfAverages.append(currentAverageDictionary)
			
			# print(f"Averaged Entry: {currentAverageDictionary}")
		else:
			# Something went wrong, complain
			print(f"I GIVE UP!!!")
			break
		# 
	# 

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

# ----- Plotting Functions -----
def CreateAlphaBlendedCmap(alpha):
	# Code from here: https://stackoverflow.com/questions/53565797/how-to-remove-edge-lines-from-tripcolor-plot-with-alpha-0
	cls = plt.get_cmap()(np.linspace(0,1,256))
	cls = (1-alpha) + alpha*cls
	cmap = matplotlib.colors.ListedColormap(cls)

	return cmap
# 

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
	title = "Without Term Clamping"
	
	# folder = clampedFolderPath
	# title = "With I Term Clamping"

	experimentResults: List[dict] = []

	# Loading each file and extracting the results
	for name in os.listdir(folder):
		with open(os.path.join(folder, name)) as currentFile:
			currentDictionary = dict()
			currentDictionary:dict = json.load(currentFile)
			currentFile.close()

			# print(f"Filename: '{name}'")
			# print(f"Dictionary: {currentDictionary.keys()}")

			experimentResults.append(currentDictionary)
		# 
	# 

	# --- Filtering Results ---
	# Sorting Results by Knob
	knob0Logs = []
	knob1Logs = []
	for i in range(0, len(experimentResults)):
		knob0Logs.append(experimentResults[i]["knob0"])
		knob1Logs.append(experimentResults[i]["knob1"])
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

	# Printing out the contents of the list
	# for i in range(0, len(startList)):
	# 	# print(f"S: {startList[i]:3} | E: {endList[i]:3} | t: {settlingTimeList[i]:5.2f} | O: {overshootList[i]:5.2f}")
	# # 
		
	# --- Plotting Results ---	
	# - Creating Figure and Applying Lables -
	# Create the figure and plot (this command can also do nested plots)
	fig, ax = plt.subplots()

	ax.set_title(title)
	ax.set_xlabel("Starting Position")
	ax.set_ylabel("Ending Position")

	# - Plotting the Data -
	# Blending the alpha values so there isn't such nasty overlap
	cmap = CreateAlphaBlendedCmap(0.75)

	# Applying Background Shading
	trpColor = ax.tripcolor(startList, endList, settlingTimeList,\
						shading='gouraud')
	fig.colorbar(trpColor, label = "Settling Time (s)") # Adding the color-bar to the figure
	
	# Plotting Data Points
	# ax.scatter(startList, endList, c=settlingTimeList, marker=".")
	# ax.scatter(startList, endList, marker="o")
	ax.plot(startList, endList, linewidth=0, marker="o", color="k", fillstyle="none")

	# - Saving the Figure -
	figureName = "experimentResults"
	plt.savefig(figureName)
# 