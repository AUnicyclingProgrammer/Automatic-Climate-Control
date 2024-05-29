# ----- Imports -----
# Utility
import time

# My Code
from JoystickInterface import JoystickInterface

# ----- Global Values ----

# ----- Global Classes -----

# ----- Class -----
class DemoStateMachine:
    """
    Class defining the state machine used for the project demo
    """

    def __init__(self):
        """
        Creates an instance of the demo state machine
        """

        # --- Internal Paramters ---
        # State the system should currently be in
        self.state = "display"

        # Time to wait between updates
        self.updateTime = 0.25

        # --- Objects ---
        self.joystick = JoystickInterface()
    # 

    def Start(self):
        """
        Command that begins the state machine, which also takes over program control because
        the class is not multi-threadded
        """
        print("Starting State Machine")

        while True:
            # Iterate through the states
            if self.state == "display":
                self.DisplayState()
            elif self.state == "move":
                self.MoveState()
            # 

            # Wait a little bit between updates
            time.sleep(self.updateTime)
        # 
    # 


    def DisplayState(self):
        """
        Function for the state that displays the temperature the sensor is currently
        reading
        """
        print("Entered Display State")

        # --- Processing Loop ---
        while self.state == "display":
            # - Get User Input -
            # Query Joystick
            joystickInput = self.joystick()

            # Update State
            if joystickInput == "right" or joystickInput == "left":
                self.state = "move"
            # 
            
            # Small Delay
            time.sleep(self.updateTime)
        # 

        print("Exiting Display State")
    # 

    def MoveState(self):
        """
        Function for the state that allows the user to adjust the position of the knobs
        """
        print("Entered Move State")

        # --- Processing Loop ---
        while self.state == "move":
            print("State not currently functional")
            
            # - Get User Input -
            # Query Joystick
            joystickInput = self.joystick()

            # Update State
            if joystickInput == "right" or joystickInput == "left":
                self.state = "display"
            # 
            
            # Small Delay
            time.sleep(self.updateTime)
        # 

        print("Exiting Move State")
    # 
# 

# ----- Begin Program -----
if __name__ == "__main__":
    print("Program Completed")
# 
