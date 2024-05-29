# ----- Imports -----
# Utility
import numpy as np

# My Code
from InputFilters import MovingAverage

# ----- Class -----
class SlidingNumberSelector:
    """
    Class that manages the selection of numbers in discrete time steps.
    Supports fast scrolling if the same increment command has been sent 
    multiple times in a row
    """

    def __init__(self, min, max, speedRampInterval = 5):
        """
        Initializes an instance of the class
        """
        # Setting Limits
        self.minValue = min
        self.maxValue = max

        # Speed Ramping
        self.speedRampInterval = 10
        self.speedRampIndicator = MovingAverage(self.speedRampInterval)
        self.speedRampCount = 0 # Counts how many times the speed ramp has been incremented
        
        self.lastIncrementDirection = 0

        # Setting Internal Values
        self.value = np.mean([min,max], dtype = int)
    # 

    def UpdateValue(self, incrementDirection):
        """
        Updates the currently stored value

        incrementDirection: +1, positive increment, -1, negativeIncrement
        """

        # Applying Speed Ramping
        currentRampingTendency = self.speedRampIndicator(incrementDirection)
        shouldIncrementSpeedRamp = abs(currentRampingTendency) == 1
        
        noDirectionChange = self.lastIncrementDirection == incrementDirection
        shouldContinueRamping = noDirectionChange and not (incrementDirection == 0)
        
        # if shouldIncrementSpeedRamp or shouldContinueRamping:
        if shouldIncrementSpeedRamp:
            # Add 1 to the speed ramp count
            self.speedRampCount += 1

            # Reset Ramp Indicator
            self.speedRampIndicator(0)
        elif not shouldContinueRamping:
            # Stop and Reset Ramp Count
            self.speedRampCount = 0
        # 

        # Determining how much to increment by
        currentIncrement = pow(2, self.speedRampCount)

        print(f"Dir: {incrementDirection:2}" \
                + f" | Tendency: {currentRampingTendency:5.2f}" \
                + f" | Count: {self.speedRampCount:3}" \
                + f" | Increment: {currentIncrement:3}" \
                + f" | Continue: {shouldContinueRamping:5.2f}" \
            )

        # Updaing Increment Value
        if (incrementDirection > 0):
            self.value += currentIncrement
        elif (incrementDirection < 0):
            self.value -= currentIncrement
        #

        # Save Last Increment Value
        self.lastIncrementDirection = incrementDirection

        # Clamp the Bounds of the Value
        self.value = self.ClampValue(self.value)
        
        return self.value

            
    
    def ClampValue(self, number):
        """
        Clamps a number between the allowed minimum and maximum values
        """

        if (number < self.minValue):
            number = self.minValue
        elif (number > self.maxValue):
            number = self.maxValue
        # 

        return number
    #

# ----- Begin Program -----
if __name__ == "__main__":
    print("Program Completed")
# 
