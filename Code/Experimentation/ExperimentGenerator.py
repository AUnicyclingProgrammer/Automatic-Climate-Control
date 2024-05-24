# ----- Imports -----
# Utility
from collections import deque
import math
import numpy as np
import random
import itertools

# Reability
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

def OptimizationPass(distance_matrix, x0 = None, option = 1):

	print("")
	if option == 1:
		permutation, distance = solve_tsp_simulated_annealing(distance_matrix, x0=x0)
		
		print("$ : Simulated Annnealing Solution:")
		print(f"Dist: {distance} | Permutation: {permutation}")

		permutation, distance = solve_tsp_local_search(
			distance_matrix, x0=permutation, perturbation_scheme="ps3"
		)

		print("Ξ Local Search Solution:")
		print(f"Dist: {distance} | Permutation: {permutation}")
	elif option ==2:
		permutation, distance = solve_tsp_lin_kernighan(distance_matrix, x0=x0)
		
		print("LK : Lin Kernighan Solution:")
		print(f"Dist: {distance} | Permutation: {permutation}")
	else:
		permutation, distance = solve_tsp_record_to_record(distance_matrix, x0=x0)
		
		print("R2R : Record to Record Solution:")
		print(f"Dist: {distance} | Permutation: {permutation}")
	
	# 
	print("")
	return permutation, distance
# 

# ----- Utility Classes -----

# ----- Begin Program -----
if __name__ == "__main__":

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

	# --- Experiment Parameters ---
	minValue = 0
	maxValue = 255

	closestToEdge = 5
	outerThreshold = 20
	innerThreshold = 40
	centerPoint = 127

	# 240 Permutations
	# outerNumber = 3
	# paddedNumber = 3
	# centerNumber = 4
	
	# Prefered for Experiment
	# 182 Transitions Required
	# outerNumber = 2
	# paddedNumber = 3
	# centerNumber = 4

	# For Testing TSP Solver
	# 56 Transitions Required
	outerNumber = 1
	paddedNumber = 2
	centerNumber = 2
	
	# For fast results
	# Only 20 Transitions
	# outerNumber = 1
	# paddedNumber = 1
	# centerNumber = 1
	
	
	# --- Complining Testing Points ---
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
	identityCost = 1

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
	permutation = None
	lastPermutation = "tempValue"

	permutation, distance = OptimizationPass(distance_matrix, x0=permutation, option = 1)
	
	for i in range(0, 5):
		print(f"\t\t Pass # {i}")
		
		permutation, distance = OptimizationPass(distance_matrix, x0=permutation, option = 2)

		if (distance > bestDistance) or (permutation == lastPermutation):
			break
		# 

		bestDistance = min(distance, bestDistance)
		lastPermutation == permutation
	# 

	# --- Converting Back to Point List ---
	optimalTransitions = [transitionList[index] for index in permutation]

	print(f"~~~ Optimal Transition Pairs: {optimalTransitions}")
	
	listOfPoints = ConvertPairsIntoPoints(optimalTransitions)

	print(f"~~~ Order to Traverse {len(listOfPoints)} Points: {listOfPoints}")
# 