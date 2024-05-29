# ----- Imports -----

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

        """
        State the system should currently be in
        """
        self.state = "display"
    # 

    def Start(self):
        """
        Command that begins the state machine, which also takes over program control because
        the class is not multi-threadded
        """
        print("Starting State Machine")
    # 


    def DisplayState():
        """
        Function for the state that displays the temperature the sensor is currently
        reading
        """
        print("Entered Display State")
        print("Exiting Display State")
    # 

    def MoveState():
        """
        Function for the state that allows the user to adjust the position of the knobs
        """
        print("Entered Move State")
        print("State not currently functional")
        print("Exiting Move State")
    # 


# 

# ----- Begin Program -----
if __name__ == "__main__":
    print("Program Completed")
# 
