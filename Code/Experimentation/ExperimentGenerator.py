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
	print(f"There are {numberOfTransitions} transitionList: {transitionList}")

	# --- Creating TSP Problem ---
	# Translate pairs into indicies to simplify problem formulation
	# verticies = []
	# for i in range(0, numberOfTransitions):
	# 	verticies.append(i)
	# # 

	# print("Verticies to Visit (Transitions)")
	# print(f"#:{len(verticies)} - {verticies}")

	# Graph costs
	transitionNotRequiredCost = 0
	transitionRequiredCost = 1
	identityCost = 1

	# Computing Weight Matrix
	transitionGraph =np.zeros((numberOfTransitions, numberOfTransitions)).tolist()

	permutationCount = 0
	for i in range(0, numberOfTransitions):
		x1, y1 = transitionList[i]
		
		for j in range(0, numberOfTransitions):
			x2, y2 = transitionList[j]

			# print(f"Transition: {permutationCount:5} | From ({x1:3},{y1:3}) to ({x2:3},{y2:3})", end = "")
			permutationCount += 1

			isIdentity = (x1 == x2) and (y1 == y2)
			noTransitionRequired = (x1 == x2) or (y1 == y2)

			if isIdentity:
				transitionCost = identityCost
			elif noTransitionRequired:
				transitionCost = transitionNotRequiredCost
			else:
				transitionCost = transitionRequiredCost
			# 
			# print(f" | Cost: {transitionCost}")

			transitionGraph[i][j] = transitionCost
		# 
	# 

	print(f"There are {permutationCount} elements in the cost graph.")

	# print("Cost Graph:")
	# print(transitionGraph)

	# --- Example Problem ---
	from python_tsp.heuristics import solve_tsp_local_search, solve_tsp_simulated_annealing

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

	permutation, distance = solve_tsp_simulated_annealing(distance_matrix)
	
	print("Simulated Annnealing")
	print(f"Dist: {distance} | Permutation: {permutation}")

	permutation2, distance2 = solve_tsp_local_search(
		distance_matrix, x0=permutation, perturbation_scheme="ps3"
	)

	print("Final Results")
	print(f"Dist: {distance2} | Permutation: {permutation2}")
# 
