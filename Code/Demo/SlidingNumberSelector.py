# ----- Imports -----

# ----- Class -----
class SlidingNumberSelector:
    """
    Class that manages the selection of numbers in discrete time steps.
    Supports fast scrolling if the same increment command has been sent 
    multiple times in a row
    """

    def __init__(self, min, max):
        """
        Initializes an instance of the class
        """
        self.minValue = min
        self.maxValue = max
    # 

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
