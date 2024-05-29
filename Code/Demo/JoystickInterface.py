# ----- Imports -----
import qwiic_joystick
import time

# ----- Class -----
class JoystickInterface:
	"""
	Class that interfaces with a Qwiic Joystick, providing discrete, directional output
	"""

	def __init__(self):
		"""
		Creates an instance of the joystick interface
		"""
		
		# --- Key Parameters ---
		# Center of the Joystick
		self.center = 1024//2
		
		# Values must deviate this much from the center to be outside of the deadzone
		self.deadzoneMagnitude = 200

		# --- Initializing Joystick ---
		self.joystick = qwiic_joystick.QwiicJoystick()
		myJoystick.begin()
	# 

	def __call__(self):
		"""
		Returns the current state of the joystick

		States in order of precedence:
		1. select
		2. center
		3. up / down
		4. right / left
		"""

		# Reading Joystick State
		x = self.joystick.get_horizontal()
		y = self.joystick.get_vertical()
		button = not self.joystick.get_button() # Returns 0 if pressed

		# Defining Default Output
		currentState = "center"

		# Checking if Joystick is in Deadzone
		xInDeadzone = (self.center - self.deadzoneMagnitude < x) \
			and (x < self.center + self.deadzoneMagnitude)
		yInDeadzone = (self.center - self.deadzoneMagnitude < y) \
			and (y < self.center + self.deadzoneMagnitude)
		inDeadzone = xInDeadzone and yInDeadzone

		# Determining State
		if button:
			currentState = "select"
		elif inDeadzone:
			currentState = "center"
		elif y > self.center and xInDeadzone:
			currentState = "up"
		elif y < self.center and xInDeadzone:
			currentState = "down"
		elif x > self.center and yInDeadzone:
			currentState = "left"
		elif x < self.center and yInDeadzone:
			currentState = "right"
		# 

		return currentState
	# 

# 

# ----- Begin Program -----
if __name__ == "__main__":
	print("\nSparkFun qwiic Joystick   Example 1\n")
	myJoystick = qwiic_joystick.QwiicJoystick()

	myJoystick.begin()

	print("Initialized. Firmware Version: %s" % myJoystick.get_version())

	joystick = JoystickInterface()

	while True:

		print("X: %d, Y: %d, Button: %d" % ( \
					myJoystick.get_horizontal(), \
					myJoystick.get_vertical(), \
					myJoystick.get_button()))
		
		joystickState = joystick()
		print(f"State: {joystickState}")

		time.sleep(.5)
	
	print("Program Completed")
# 
