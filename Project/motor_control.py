import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib
import threading

GpioPins = [4, 17, 27, 22]
XAxis = RpiMotorLib.BYJMotor("Bottom", "28BYJ")
StepsPerFrame = 100
deadzoneThreshold = 15

Position = [0, 0]


def x_move():
    if Position[0] <= 200 - deadzoneThreshold:
        XAxis.motor_run(GpioPins, .002, StepsPerFrame, True, False, "full", 0)

    if Position[0] >= 200 + deadzoneThreshold:
        XAxis.motor_run(GpioPins, .002, StepsPerFrame, False, False, "full", 0)


def new_thread():
    if __name__ == '__main__':
        move = threading.Thread(name='move', target=x_move)
        move.daemon = True
        move.start()


while True:
    print('main running.' "threads running:", threading.active_count())
    if threading.active_count() == 1:
        break
print("main stopping.")
GPIO.cleanup()
