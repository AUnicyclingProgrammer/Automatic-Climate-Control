# ----- Imports -----
# Utility
import time

# Qwiic
import qwiic_serlcd
import qwiic_tmp102

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
        self.updateTime = 0.5

        # --- Objects ---
        # - Joystick -
        self.joystick = JoystickInterface()

        # - LCD -
        self.lcd = qwiic_serlcd.QwiicSerlcd()

        self.lcd.setBacklight(255, 255, 255) # Set backlight to bright white
        self.lcd.setContrast(5) # set contrast. Lower to 0 for higher contrast.
        self.lcd.clearScreen() # clear the screen - this moves the cursor to the home position as well

        time.sleep(2) # give a sec for system messages to complete
        
        self.lcd.print("Hello!")

        time.sleep(1) # Wait so the user can see the greeting

        # - Temperature Sensor -
        self.tempSensor = qwiic_tmp102.QwiicTmp102Sensor()

        self.tempSensor.begin()

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

        # --- Update Display ---
        # Reset the screen
        self.lcd.clearScreen()
        
        # Print Title
        self.lcd.print("Temperature")

        # Move Cursor to Second Row
        self.lcd.setCursor(0, 1)
        
        # --- Processing Loop ---
        while self.state == "display":
            try:
                # - Get User Input -
                # Query Joystick
                joystickInput = self.joystick()

                # Update State
                if joystickInput == "right" or joystickInput == "left":
                    self.state = "move"
                # 

                # - Display Temperature -
                # Print Temperature
                temperature = self.tempSensor.read_temp_f()
                self.lcd.print(f"{temperature:4.1f} F")
                
                # - Reset for Next Loop -
                # Small Delay (Partial)
                time.sleep(self.updateTime/2)
                
                # Reset Cursor
                self.lcd.setCursor(0,1)

                # Small Delay (Partial)
                time.sleep(self.updateTime/2)
            # except (KeyboardInterrupt, SystemExit) as exErr:
            except OSError:
                print("An OSError occured, ignoring it and moving on")
                time.sleep(self.updateTime)
            # 
        # 

        print("Exiting Display State")
    # 

    def MoveState(self):
        """
        Function for the state that allows the user to adjust the position of the knobs
        """
        print("Entered Move State")

        # --- Update Display ---
        # Reset the screen
        self.lcd.clearScreen()
        
        # Print Title
        self.lcd.print("Adjust Position")

        # Move Cursor to Second Row
        self.lcd.setCursor(0, 1)

        # --- Processing Loop ---
        while self.state == "move":            
            try:
                # - Get User Input -
                # Query Joystick
                joystickInput = self.joystick()

                # Update State
                if joystickInput == "right" or joystickInput == "left":
                    self.state = "display"
                # 

                # - Process Movement -
                
                # - Reset for Next Loop -
                # Small Delay (Partial)
                time.sleep(self.updateTime/2)
                
                # Reset Cursor
                self.lcd.setCursor(0,1)

                # Small Delay (Partial)
                time.sleep(self.updateTime/2)
            except OSError:
                print("An OSError occured, ignoring it and moving on")
                time.sleep(self.updateTime)
        # 

        print("Exiting Move State")
    # 
# 

# ----- Begin Program -----
if __name__ == "__main__":
    print("Program Completed")
# 
