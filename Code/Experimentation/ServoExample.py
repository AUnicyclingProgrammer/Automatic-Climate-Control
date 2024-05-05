import pi_servo_hat
import time

# Default Constructor (Can't change the address)
test = pi_servo_hat.PiServoHat()

# Soft rest the system, preparing it for use
test.restart()

# This runs the servo to a few known positions
if (True):
	# Moves servo position to 0 degrees (1ms), Channel 0
	test.move_servo_position(0, 0)
	
	# Pause 1 sec
	time.sleep(1)
	
	# Moves servo position to 90 degrees (2ms), Channel 0
	test.move_servo_position(0, 90)
	
	# Pause 1 sec
	time.sleep(1)
	
	# Telling the servo to stop 
	test.move_servo_position(0,180)
	

# This is a sweep test
if False:
	for i in range (0,10): # Run 10 times
		for i in range(0, 180):
			test.move_servo_position(0, i)
			time.sleep(0.01)
		
		for i in range(180,0,-1):
			test.move_servo_position(0, i)
			time.sleep(0.001)
			

# Trying to figure out what this little servo does.
if True:
	for i in range (0,5):
		for i in range(0,180,1):
			test.move_servo_position(0,i)
			print("Current Angle: " + str(i))
			time.sleep(0.1)

# This command tells the servo to stop spinning			
test.move_servo_position(0, 180)
