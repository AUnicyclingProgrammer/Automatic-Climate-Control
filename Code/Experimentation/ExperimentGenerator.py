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

# implementation of traveling Salesman Problem 
def travellingSalesmanProblem(graph, startVertex, numVerticies): 
	"""
	This solver was originally taken from here: https://www.geeksforgeeks.org/traveling-salesman-problem-tsp-implementation/

	I have modified it a bit
	"""

	# Python3 program to implement traveling salesman 
	# problem using naive approach. 
	from sys import maxsize 

	# Store all verticies apart from source vertex
	vertex = [] 
	for i in range(numVerticies):
		if i != startVertex: 
			vertex.append(i) 

	# Store minimum weight Hamiltonian Cycle 
	# Set the minimum path weight to the largest number we can store
	minimumPathWeight = maxsize
	minimumPath = []
	
	nextPermutation=itertools.permutations(vertex)
	for i in nextPermutation:

		# Store Current Path Weight (cost) and Current Path
		currentPathWeight = 0
		currentPath = []

		# Compute Current Path Weight
		k = startVertex
		currentPath.append(k)
		for j in i: 
			# Test the next node in the graph
			currentPathWeight += graph[k][j]
			k = j 
			currentPath.append(k)

			# Give up if this path is more expensive
			worseThanCurrentBest = (currentPathWeight > minimumPathWeight)
			if worseThanCurrentBest:
				print("This is a terrible option")
				print(f"Cost: {currentPathWeight} | Path: {currentPath}")
				break
		#
		currentPathWeight += graph[k][s]
		currentPath.append(s)

		# Update Best Path
		# Update Weight
		minimumPathWeight = min(minimumPathWeight, currentPathWeight)

		# Update Path
		if (currentPathWeight == minimumPathWeight):
			minimumPath = currentPath
		# 
		
	return minimumPathWeight, minimumPath


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
	transitions = list(itertools.permutations(experimentList, 2))
	print(f"There are {len(transitions)} transitions: {transitions}")

	# --- Creating TSP Problem ---
	# Computing Weight Matrix
	graph = list()

	# for pair in transitions:
	# 	x, y = pair
		
	# 

	# matrix representation of graph 
	V = 4
	graph = [[0, 10, 15, 20], [10, 0, 35, 25], 
			[15, 35, 0, 30], [20, 25, 30, 0]] 
	s = 0
	print(travellingSalesmanProblem(graph, s, V))
# 
