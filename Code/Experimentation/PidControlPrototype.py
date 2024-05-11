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
	# pid = PID(1, 0.1, 0.05)
	# pid = PID(0.75, 0.1, 0.025)
	# pid = PID(0.75, 0.025, 0.025)
	
	# pid = PID(0.5, 0.05, 0.01)
	pid = PID(0.5, 0.075, 0.0)
	# pid = PID(0.5, 0.075, 0.001)
	# pid.proportional_on_measurement = True

	# Setting the sampling time
	# samplingTime = 0.01
	# samplingTime = 0.001
	samplingTime = 0.01
	pid.sample_time = samplingTime

	# - Creating Control Range -
	# Set the outputs
	# pid.output_limits = (20, 220) # Just random guesses
	# pid.output_limits = (25, 65) # Pre-scaled to account for deadzone skipping
	# pid.output_limits = (35, 55) # Pre-scaled to account for deadzone skipping
	# pid.output_limits = (40, 50) # Pre-scaled to account for deadzone skipping
	pid.output_limits = (44, 46) # Pre-scaled to account for deadzone skipping

	# Setting the setpoint
	tolerance = 7
	setpoint = 200
	pid.setpoint = setpoint

	while True:
		# Read the current value of the knob
		potentiometerValue = ReadPotentiometer(0)

		# Read the current value of the other knob
		onOffValue = ReadPotentiometer(1)

		# If we are close enough then falsify the value sent to the PID controller
		# Tell the servo to scoot if it's too far away
		if ((setpoint + tolerance > potentiometerValue) and \
			 (potentiometerValue > setpoint - tolerance)):
			# Stop, close enough
			filteredValue = setpoint

			servoStopped = True
		else:
			# Keep trying
			filteredValue = potentiometerValue

			servoStopped = False
		#

		# Get a new reading from the potentiometer
		pidRecommendation = pid(filteredValue)

		# Bypassing the deadspot in the middle
		if (pidRecommendation > 45):
			# Skipping the deadspot in the middle
			newSpeed = pidRecommendation + 8
		else:
			newSpeed = pidRecommendation

		# Move the servo the correct mout
		servoHat.move_servo_position(0, newSpeed)

		
		prevP, prevI, prevD = pid.components
		print(f"Position: {potentiometerValue:3} | F:{filteredValue:3} | Speed: {newSpeed:.2f} |"+\
			f" On Off: {onOffValue:3} | S: {servoStopped*100:3} |"\
			+ f"P: {float(prevP):5.5} I: {float(prevI):5.5} D: {float(prevD):5.5}")
		
		# So the pi doesn't over-work itself
		time.sleep(samplingTime/1)

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
