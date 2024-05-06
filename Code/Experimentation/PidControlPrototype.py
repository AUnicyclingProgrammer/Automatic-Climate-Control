# Imports
import pi_servo_hat
import smbus

import time

from simple_pid import PID

"""
	Right now my goal is get to the point where I can make the servo turn to a certain
	position, which I will know from the potentiometer feedback.

	Control Loop:
	* Read Current Position
	* Update Motor

	Things I need to be able to do:
	* query the potentiometer for it's position
	* pass the position to the PID loop
	* get a response from the PID loop
	* Convert the response into a servo speed
	* command the servo motor to go the correct speed
"""

# ----- Global Values ----
ADC_ADDRESS = 0x4a
POT_0_CHANNEL = 0x41
POT_1_CHANNEL = 0X40

# ----- Global Classes -----
# Initializing the i2c bus
i2cBus = smbus.SMBus(1)

# Initializing Servo Hat
servoHat = pi_servo_hat.PiServoHat()
# Soft rest the system, preparing it for use
servoHat.restart()

# ----- Methods and Functions -----
def ReadPotentiometer(potentiometerNumber):
	"""
	Gets the value for the appropriate analog input
	"""
	channelAddress = 0x20 # This value should get overwritten so it doesn't matter much what it is

	if (potentiometerNumber == 0):
		channelAddress = POT_0_CHANNEL
	elif (potentiometerNumber == 1):
		channelAddress = POT_1_CHANNEL

	# Read the value from the ADC
	i2cBus.write_byte(ADC_ADDRESS, channelAddress)
	value = i2cBus.read_byte(ADC_ADDRESS)
	return value
# 


# ----- Begin Program -----
if __name__ == "__main__":
	# This isn't necessary but it keeps the code tider

	# First pass, I'm just going to go with the nubmers the potentiometer
	# outputs because there is a lot of overlap.
	
	# - Initializing -
	# Create the pid controller
	pid = PID(1, 0.1, 0.05)

	# Setting the sampling time
	samplingTime = 0.05
	pid.sample_time = samplingTime

	# - Creating Control Range -
	
	# The motor will be assigned this many speeds values at which it can turn in each direction
	numberElementsPerDirection = 21
	slowestReverseValue = 47
	slowestForwardValue = 53
	for i in range(0, numberElementsPerDirection):
		print(i)


	print(f"Speed Range: {speedRange}")

	# Set the outputs (set arbitrarliy for the time being)
	# pid.output_limits = (20, 220)
	pid.output_limits = (40, 60)

	# Setting the setpoint to 120
	pid.setpoint = 50

	while True:
		# Read the current value of the knob
		potentiometerValue = ReadPotentiometer(0)

		# Read the current value of the other knob
		onOffValue = ReadPotentiometer(1)

		# Get a new reading from the potentiometer
		newSpeed = pid(potentiometerValue)

		# Tell the servo to scoot
		servoHat.move_servo_position(0, newSpeed)

		print(f"Position: {potentiometerValue} | Speed: {newSpeed} | On Off: {onOffValue}")
		
		# So the pi doesn't over-work itself
		time.sleep(samplingTime)

		if (onOffValue > 127):
			break
	# 

	# Time to stop
	servoHat.move_servo_position(0, 180)


# This runs the servo to a few known positions
if (False):
	# Moves servo position to 0 degrees (1ms), Channel 0
	servoHat.move_servo_position(0, 0)
	
	# Pause 1 sec
	time.sleep(1)
	
	# Moves servo position to 90 degrees (2ms), Channel 0
	servoHat.move_servo_position(0, 90)
	
	# Pause 1 sec
	time.sleep(1)
	
	# Telling the servo to stop 
	servoHat.move_servo_position(0,180)
	

# This is a sweep servoHat
if False:
	for i in range (0,10): # Run 10 times
		for i in range(0, 180):
			servoHat.move_servo_position(0, i)
			time.sleep(0.01)
		
		for i in range(180,0,-1):
			servoHat.move_servo_position(0, i)
			time.sleep(0.001)
			

# Trying to figure out what this little servo does.
if False:
	time.sleep(2)
	for i in range (0,1):
		# for i in range(0,180,1):
		for i in range(0,200,1):
			servoHat.move_servo_position(0,i)
			print("Current Angle: " + str(i))
			time.sleep(1)

# This command tells the servo to stop spinning
servoHat.move_servo_position(0, 180)
