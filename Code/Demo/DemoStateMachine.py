# ----- Imports -----
# Utility
import time

# Qwiic
import qwiic_serlcd
import qwiic_tmp102

# My Code
from JoystickInterface import JoystickInterface
from SlidingNumberSelector import SlidingNumberSelector
from KnobSuite import KnobSuite

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

        # Which knob is currently selected in the move state
        self.selectedKnob = 0

        # --- Objects ---
        # - KnobSuite -
        self.knobSuite = KnobSuite(2)

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

        # - Setpoint Selectors -
        minimumSetpoint = 5
        maximumSetpoint = 250
        self.setpointSelector0 = SlidingNumberSelector(min = minimumSetpoint, max = maximumSetpoint)
        self.setpointSelector1 = SlidingNumberSelector(min = minimumSetpoint, max = maximumSetpoint)

        # 

    def Start(self):
        """
        Command that begins the state machine, which also takes over program control because
        the class is not multi-threadded
        """
        print("Starting State Machine")

        while True:
            # Process Current State
            try:
                # Iterate through the states
                if self.state == "display":
                    self.DisplayState()
                elif self.state == "move":
                    self.MoveState()
                # 
            except OSError:
                print("An OSError occured, ignoring it and moving on")
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
        # 

        print("Exiting Display State")
    # 

    def MoveState(self):
        """
        Function for the state that allows the user to adjust the position of the knobs
        """
        print("Entered Move State")

        # --- Update Display ---
        # - Initilize Selection Indicators -
        # Create Custom Characters
        selected = [ 
            0b00000,
            0b00000,
            0b00110,
            0b01111,
            0b01111,
            0b00110,
            0b00000,
            0b00000,
        ]
        notSelected = [ 
            0b00000,
            0b00000,
            0b00110,
            0b01001,
            0b01001,
            0b00110,
            0b00000,
            0b00000,
        ]
        self.lcd.createChar(0, notSelected)
        self.lcd.createChar(1, selected)
        
        # - Initialize State Screen -
        # Reset the screen
        self.lcd.clearScreen()
        
        # Print Title
        self.lcd.print("Adjust Position")

        # Move Cursor to Second Row
        self.lcd.setCursor(0, 1)

        # --- Prepare to Enter Loop ---
        setpoint0 = self.setpointSelector0.UpdateValue()
        setpoint1 = self.setpointSelector1.UpdateValue()

        # --- Processing Loop ---
        while self.state == "move":            
            # - Get User Input -
            # Query Joystick
            joystickInput = self.joystick()

            # Update State
            if joystickInput == "left" and self.selectedKnob == 0:
                self.state = "display"
            # 

            # Update Selected Knob
            if joystickInput == "right" and self.selectedKnob == 0:
                self.selectedKnob = 1
                print("! - Selected Knob 1")
            elif joystickInput == "left" and self.selectedKnob == 1:
                self.selectedKnob = 0
                print("! - Selected Knob 0")
            # 

            # - Update Setpoint -
            # Convert Joystick Input to Movement Command
            incrementDirection = 0
            
            if joystickInput == "up":
                incrementDirection = 1
            elif joystickInput == "down":
                incrementDirection = -1
            # 
            
            # Determine Current Setpoints
            if self.selectedKnob == 0:
                setpoint0 = self.setpointSelector0.UpdateValue(incrementDirection)
            elif self.selectedKnob == 1:
                setpoint1 = self.setpointSelector1.UpdateValue(incrementDirection)
            # 

            # - Update Display -
            if self.selectedKnob == 0:
                # Update Knob 0
                self.lcd.setCursor(0,1)
                self.lcd.writeChar(1)
                self.lcd.print(f"{setpoint0:3}")
                
                # Update Knob 1
                self.lcd.setCursor(10,1)
                self.lcd.writeChar(0)
                self.lcd.print(f"{setpoint1:3}")
            elif self.selectedKnob == 1:
                # Update Knob 0
                self.lcd.setCursor(0,1)
                self.lcd.writeChar(0)
                self.lcd.print(f"{setpoint0:3}")
                
                # Update Knob 1
                self.lcd.setCursor(10,1)
                self.lcd.writeChar(1)
                self.lcd.print(f"{setpoint1:3}")
            # 
            
            # - Process Movement-
            if joystickInput == "select":                
                # Display That the System is Moving
                self.lcd.setCursor(0,2)
                self.lcd.print(f"Moving")

                # Move the Knobs
                setpoints = [setpoint0, setpoint1]
                print(f"Moving to {setpoints}")
                
                self.knobSuite(setpoints)
                
                # Clearing Bottom Line (By Writing to a Whole Row)
                self.lcd.setCursor(0,2)
                self.lcd.print(f"{'':20}")

                print(f"Move Complete")
            # 
            
            # - Reset for Next Loop -
            # Small Delay (Partial)
            time.sleep(self.updateTime/2)
            
            # Reset Cursor
            self.lcd.setCursor(0,1)

            # Small Delay (Partial)
            time.sleep(self.updateTime/2)
            # 
        # 

        print("Exiting Move State")
    # 
# 

# ----- Begin Program -----
if __name__ == "__main__":
    print("Program Completed")
# 
