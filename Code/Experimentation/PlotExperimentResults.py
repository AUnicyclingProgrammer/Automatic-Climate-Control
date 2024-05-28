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

def AverageFolderContents(folder):
	"""
	Averages all logs from the specified folder
	"""

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
	knob1Averages = AverageResults(knob1Logs)

	return knob0Averages, knob1Averages
# 

# ----- Plotting Functions -----
def CreateAlphaBlendedCmap(alpha):
	# Code from here: https://stackoverflow.com/questions/53565797/how-to-remove-edge-lines-from-tripcolor-plot-with-alpha-0
	cls = plt.get_cmap()(np.linspace(0,1,256))
	cls = (1-alpha) + alpha*cls
	cmap = matplotlib.colors.ListedColormap(cls)

	return cmap
# 

def PlotExperimentalResults(figureTitle, filename, knob0Data, knob1Data):
	"""
	Plots the results from an experiment
	"""
	# --- Converting To Lists ---
	knob0StartList, knob0EndList, knob0SettlingTimeList, knob0OvershootList = ConvertLogsToLists(knob0Data)
	knob1StartList, knob1EndList, knob1SettlingTimeList, knob1OvershootList = ConvertLogsToLists(knob1Data)

	# --- Knob 0 Plots ---
	# -- Creating Figure/Subplots and Apply Lables --
	fig, axs = plt.subplots(2, 2)
	plt.suptitle(figureTitle)
	
	# Changing Figure Dimensions
	figureSizeMultiplier = 1.25
	fig.set_size_inches(figureSizeMultiplier*fig.get_size_inches())

	# Applying Lables
	axs[0,0].set_title("Knob 0 Settling Time")
	axs[1,0].set_title("Knob 0 Overshoot")
	
	axs[0,1].set_title("Knob 1 Settling Time")
	axs[1,1].set_title("Knob 1 Overshoot")
	
	axs[0,0].set_xlabel("Starting Position")
	axs[0,1].set_xlabel("Starting Position")
	axs[1,0].set_xlabel("Starting Position")
	axs[1,1].set_xlabel("Starting Position")
	
	axs[0,0].set_ylabel("Ending Position")
	axs[0,1].set_ylabel("Ending Position")
	axs[1,0].set_ylabel("Ending Position")
	axs[1,1].set_ylabel("Ending Position")

	# -- Plotting the Data --
	# Creating a new color map with blended alpha values (removes ghost edges)
	cmap = CreateAlphaBlendedCmap(0.75)
	
	# - Knob 0 Settling -
	# Creating Settling Color Graident
	trpColor = axs[0,0].tripcolor(knob0StartList, knob0EndList, knob0SettlingTimeList,\
						shading='gouraud')
	fig.colorbar(trpColor, label = "Settling Time (s)") # Adding the color-bar to the figure
	
	# - Knob 0 Overshoot -
	# Creating Overshoot Color Graident
	trpColor = axs[1,0].tripcolor(knob0StartList, knob0EndList, knob0OvershootList,\
						shading='gouraud')
	fig.colorbar(trpColor, label = "Overshoot") # Adding the color-bar to the figure
	
	# - Knob 1 Settling -
	# Creating Settling Color Graident
	trpColor = axs[0,1].tripcolor(knob1StartList, knob1EndList, knob1SettlingTimeList,\
						shading='gouraud')
	fig.colorbar(trpColor, label = "Settling Time (s)") # Adding the color-bar to the figure
	
	# - Knob 1 Overshoot -
	# Creating Overshoot Color Graident
	trpColor = axs[1,1].tripcolor(knob1StartList, knob1EndList, knob1OvershootList,\
						shading='gouraud')
	fig.colorbar(trpColor, label = "Overshoot") # Adding the color-bar to the figure
	
	
	# - All Plots -
	# Plotting Transition Start and End Points on All Plots
	marker = "."
	axs[0,0].plot(knob0StartList, knob0EndList, linewidth=0, marker=marker, color="k", fillstyle="none")
	axs[0,1].plot(knob0StartList, knob0EndList, linewidth=0, marker=marker, color="k", fillstyle="none")
	axs[1,0].plot(knob0StartList, knob0EndList, linewidth=0, marker=marker, color="k", fillstyle="none")
	axs[1,1].plot(knob0StartList, knob0EndList, linewidth=0, marker=marker, color="k", fillstyle="none")


	# Change Layout
	"""
	Needs done at end of file, applies to everything if done right away
	Doing it at the end prevents fields from overlapping
	I guess it doesn't work if called right away because all the fields don't exist yet.
	"""
	fig.tight_layout()

	# - Saving the Figure -
	plt.savefig(filename)
# 

# ----- Universal Functions -----
def LoadAndPlotExperimentalData(folder, figureTitle, figureFilename):
	# --- Loading Results ---
	knob0Averages, knob1Averages = AverageFolderContents(folder)
		
	# --- Plotting Results ---
	PlotExperimentalResults(figureTitle, figureFilename, knob0Averages, knob1Averages)
# 

# ----- Begin Program -----
if __name__ == "__main__":
	# --- Universal Parameters ---
	defaultFolderPath = "./DefaultConfiguration/"
	clampedFolderPath = "./ClampedConfiguration/"

	toyDefaultFolder = "ToyExperiments/Default/"
	toyDefaultFolder = "ToyExperiments/Clamped/"

	# --- Loading and Plotting Results ---
	figureTitle = "Without I Term Clamping"
	filename = "defaultExperimentResults"
	LoadAndPlotExperimentalData(defaultFolderPath, figureTitle, filename)
	
	figureTitle = "With I Term Clamping"
	filename = "clampedExperimentResults"
	LoadAndPlotExperimentalData(clampedFolderPath, figureTitle, filename)
# 