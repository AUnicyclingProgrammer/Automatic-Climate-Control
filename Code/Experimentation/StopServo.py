import pi_servo_hat
import time

# Default Constructor (Can't change the address)
test = pi_servo_hat.PiServoHat()

# Soft rest the system, preparing it for use
test.restart()

time.sleep(0.1)

# Stop every servo
for i in range(0, 15+1):
    test.move_servo_position(i,180)