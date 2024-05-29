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

    def __init__(self, min, max, speedRampInterval = 10):
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

        # Setting Internal Values
        self.value = np.mean([min,max], dtype = int)
    # 

    def UpdateValue(self, incrementDirection):
        """
        Updates the currently stored value

        incrementDirection: +1, positive increment, -1, negativeIncrement
        """

        # Determining how much to increment by
        currentIncrement = 1

        # Updaing Increment Value
        if (incrementDirection > 0):
            self.value += currentIncrement
        elif (incrementDirection < 0):
            self.value -= currentIncrement
        #

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
