# ----- Imports -----
# Utility
from collections import deque
import math
import numpy as np
import random
import itertools

# Readability
import time
from typing import List


# ----- Methods and Functions -----

def ConvertPairsIntoPoints(transitionParis):
	"""
	Converts a list of transition pairs into a list of points
	"""

	flatList = []
	for pair in transitionParis:
		for point in pair:
			flatList.append(point)
		# 
	#

	# Always take the first value
	pointList = []
	pointList.append(flatList[0])
	
	# Remove duplicates
	for i in range(1, len(flatList)):
		currentPoint = flatList[i]
		lastPoint = flatList[i-1]
		
		# print(f"i:{i:3} | Current: {currentPoint:3} Last: {lastPoint:3}")
		
		# Only add points that are different from the ones before them
		if (currentPoint != lastPoint):
			pointList.append(currentPoint)
		# 
	# 

	return pointList
# 

def OptimizationPass(distance_matrix, x0 = None, exact = False):

	print("")
	# print(f"X0: {x0}")

	if not exact:
		permutation, distance = solve_tsp_simulated_annealing(distance_matrix, x0=x0)
		
		print("$ : Simulated Annealing Solution:")
		print(f"Dist: {distance} | Permutation: {permutation}")

		permutation, distance = solve_tsp_local_search(
			distance_matrix, x0=permutation, perturbation_scheme="ps4"
		)
		# permutation, distance = solve_tsp_local_search(
		# 	distance_matrix, x0=permutation, perturbation_scheme="ps6"
		# )

		print("Ξ : Local Search Solution:")
		print(f"Dist: {distance} | Permutation: {permutation}")
	else:
		# The pi isn't able to compute the exact solution, this needs to be done on a much
		# more powerful machine.
		from python_tsp.exact import solve_tsp_branch_and_bound, solve_tsp_dynamic_programming

		# permutation, distance = solve_tsp_branch_and_bound(distance_matrix)
		permutation, distance = solve_tsp_dynamic_programming(distance_matrix)

		print("B&B : Branch and Bound Solution:")
		print(f"Dist: {distance} | Permutation: {permutation}")
	# 

	print("")
	return permutation, distance
# 

# ----- Utility Classes -----

# ----- Begin Program -----
if __name__ == "__main__":

	currentTime = time.localtime()
	currentTimeString = time.strftime("%H:%M:%S", currentTime)
	print(currentTimeString)

	startTime = time.monotonic()

	# --- Experiment Parameters ---
	minValue = 0
	maxValue = 255

	closestToEdge = 5
	outerThreshold = 20
	innerThreshold = 40
	centerPoint = 127

	# 240 Transitions Required
	# outerNumber = 3
	# paddedNumber = 3
	# centerNumber = 4
	
	# Preferred for Experiment
	# 182 Transitions Required
	outerNumber = 2
	paddedNumber = 3
	centerNumber = 4

	# For Testing TSP Solver
	# 56 Transitions Required
	# outerNumber = 1
	# paddedNumber = 2
	# centerNumber = 2
	
	# For fast results
	# Only 20 Transitions
	# outerNumber = 1
	# paddedNumber = 1
	# centerNumber = 1
	
	
	# --- Compiling Testing Points ---
	outerRegion = list(np.linspace(closestToEdge, outerThreshold, outerNumber, endpoint = False))
	paddingRegion = list(np.linspace(outerThreshold, innerThreshold, paddedNumber, endpoint = False))
	centralRegion = list(np.linspace(innerThreshold, maxValue - innerThreshold, centerNumber))

	firstPart = [round(point) for point in outerRegion + paddingRegion]
	centerPart = [round(point) for point in centralRegion]
	lastPart = [255 - point for point in firstPart]
	lastPart.reverse()
	experimentList = firstPart + centerPart + lastPart

	
	print("Points to Visit")
	print(f"#:{len(experimentList)} - {experimentList}")

	print("All Required Transitions")
	transitionList = list(itertools.permutations(experimentList, 2))
	numberOfTransitions = len(transitionList)
	print(f"A minimum of {numberOfTransitions} transitions is required: {transitionList}")

	# --- Creating TSP Problem ---
	# Graph costs
	idealTransitionCost = 0
	extraTransitionCost = 5
	identityCost = 10

	# Computing Weight Matrix
	transitionGraph =np.zeros((numberOfTransitions, numberOfTransitions)).tolist()

	permutationCount = 0
	for i in range(0, numberOfTransitions):
		x1, y1 = transitionList[i]
		
		for j in range(0, numberOfTransitions):
			x2, y2 = transitionList[j]

			isIdentity = (x1 == x2) and (y1 == y2)
			isIdealTransition = (y1 == x2)

			if isIdentity:
				transitionCost = identityCost
			elif isIdealTransition:
				transitionCost = idealTransitionCost
			else:
				transitionCost = extraTransitionCost
			# 

			# print(f"Transition: {permutationCount:5} | From ({x1:3},{y1:3}) to ({x2:3},{y2:3})", end = "")
			# print(f" | Cost: {transitionCost}")
			
			permutationCount += 1

			transitionGraph[i][j] = transitionCost
		# 
	# 

	print(f"There are {permutationCount} elements in the cost graph.")

	# print("Cost Graph:")
	# print(transitionGraph)

	# --- Example Problem ---
	from python_tsp.heuristics import solve_tsp_local_search, solve_tsp_simulated_annealing, solve_tsp_lin_kernighan, solve_tsp_record_to_record

	# distance_matrix = np.array([
	# 	[0,  5, 4, 10],
	# 	[5,  0, 8,  5],
	# 	[4,  8, 0,  3],
	# 	[10, 5, 3,  0]
	# ])
	# permutation, distance = solve_tsp_local_search(distance_matrix)

	# --- My Problem ---
	# Converting the graph into a numpy array
	distance_matrix = np.array(transitionGraph)

	bestDistance = maxValue
	previousBestDistance = maxValue
	permutation = None
	bestPermutation = None
	
	numberOfCycles = 1
	for i in range(0, numberOfCycles):
		print(f"\t\t Pass # {i}")
		
		permutation, distance = OptimizationPass(distance_matrix)

		if (distance > bestDistance):
			break
		# 

		bestDistance = min(distance, bestDistance)

		# If a better result was found save the new permutation
		if bestDistance < previousBestDistance:
			bestPermutation = permutation
			bestResult = (bestDistance, bestPermutation)
		# 
		
		previousBestDistance = bestDistance
	# 

	distance, permutation = bestResult

	print("!!!\\")
	print(f"Best Result with Cost of {distance}: {permutation}")
	print("!!!/")
	print("")

	# --- Converting Back to Point List ---
	optimalTransitions = [transitionList[index] for index in permutation]

	print(f"~~~ Optimal Transition Pairs: {optimalTransitions}")
	
	listOfPoints = ConvertPairsIntoPoints(optimalTransitions)

	print(f"~~~ Order to Traverse {len(listOfPoints)} Points: {listOfPoints}")

	# --- Saving Results ---
	# Converting to default python datatypes (only if necessary)
	distance = int(distance)

	# Saving Results as a Dictionary
	experimentDict = dict()
	experimentDict["numberOfPoints"] = len(listOfPoints)
	experimentDict["pointList"] = listOfPoints
	experimentDict["distance"] = distance
	
	print(f"Dictionary Before Saving and Loading: {experimentDict}")

	# Exporting the dictionary to a JSON
	import json

	fileName = "ServoExperimentPoints_"+str(distance)+".json"

	# Opening JSON File
	with open(fileName, 'w') as jsonFile:
		json.dump(experimentDict, jsonFile)
	# 
	jsonFile.close()

	# Loading the file to make sure it worked
	jsonFile = "dud"

	jsonFile = open(fileName)
	loadedDictionary = json.load(jsonFile)
	jsonFile.close()
	
	print(f"Dictionary After Saving and Loading : {loadedDictionary}")

	# Just because I want to know how long everything took
	endTime = time.monotonic()
	
	currentTime = time.localtime()
	currentTimeString = time.strftime("%H:%M:%S", currentTime)
	print(currentTimeString)

	secondsElapsed = endTime - startTime
	minutesElapsed = secondsElapsed / 60
	print(f"Execution Time (s) : {secondsElapsed}")
	print(f"Execution Time (m) : {minutesElapsed}")
# 