from imagesearch.centroidtracker import CentroidTracker
from imutils.video import VideoStream
import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib
import numpy as np
import imutils
import time
import cv2
import threading
from flask import Response
from flask import Flask
from flask import render_template
# import keyboard

# stepper X variables
GpioPinsX = [4, 17, 27, 22]
XAxis = RpiMotorLib.BYJMotor("Bottom", "28BYJ")
# stepper y variables
GpioPinsY = [18, 23, 24, 25]
YAxis = RpiMotorLib.BYJMotor("Top", "28BYJ")
# mechanics constants
StepsPerFrame = 10
deadzoneThreshold = 25
frameWidth = 400
frameHeight = 300
# flask variables
outputFrame = None
lock = threading.Lock()
flask = Flask(__name__)


@flask.route("/")
def index():
    return render_template("index.html")


def prep():
    global outputFrame, lock

    while True:
        with lock:
            if outputFrame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

        if not flag:
            continue
        yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n'


def x_move():
    if centroid[0] <= frameWidth/2 - deadzoneThreshold:
        XAxis.motor_run(GpioPinsX, .002, StepsPerFrame, True, False, "full", 0)

    if centroid[0] >= frameWidth/2 + deadzoneThreshold:
        XAxis.motor_run(GpioPinsX, .002, StepsPerFrame, False, False, "full", 0)


def y_move():
    if centroid[1] <= frameHeight/2 - deadzoneThreshold/2:
        YAxis.motor_run(GpioPinsY, .002, StepsPerFrame, True, False, "full", 0)

    if centroid[1] >= frameHeight/2 + deadzoneThreshold/2:
        YAxis.motor_run(GpioPinsY, .002, StepsPerFrame, False, False, "full", 0)


ct = CentroidTracker()
(H, W) = (None, None)
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe("deploy.prototxt", "caffe.caffemodel")
print("[INFO] starting video stream...")
vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)


@flask.route("/html")
def html():
    return Response(prep(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == '__main__':
    flask.run(host='0.0.0.0', port=80, debug=True, use_reloader=False)

GPIO.cleanup()

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=frameWidth)

    if W is None or H is None:
        (H, W) = frame.shape[:2]

    blob = cv2.dnn.blobFromImage(frame, 1, (W, H), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()
    rects = []

    for i in range(0, detections.shape[2]):
        if detections[0, 0, i, 2] > 0.5:
            box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
            rects.append(box.astype("int"))

            (startX, startY, endX, endY) = box.astype("int")
            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)

    objects = ct.update(rects)
    for (objectID, centroid) in objects.items():
        text = "ID {}".format(objectID)
        cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)
        print(objectID, centroid[0], centroid[1])

        if __name__ == '__main__':
            moveX = threading.Thread(name='moveX', target=x_move)
            moveY = threading.Thread(name='moveY', target=y_move)
            moveX.start()
            moveY.start()
        break

    outputFrame = frame.copy()

    print('main running.' "threads running:", threading.active_count())

#     if keyboard.is_pressed('q'):
#         break
# GPIO.cleanup()
# vs.stop()
