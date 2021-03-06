#import the necessary packages
import argparse
import datetime
import imutils
import time
import cv2
import RPi.GPIO as GPIO
import time
import threading
import requests

status_l = 'false'
status_light = 'false'
def foo():
	global status_l
	print('sending request '+status_l)
	r = requests.post("https://ltfxwxflbe.localtunnel.me/camera/motion", data={'enabled': status_l})
	print(r.text)
	threading.Timer(5, foo).start()

def bar():
        global status_light
	print('sending light status '+status_light)
	r = requests.post("https://ltfxwxflbe.localtunnel.me/camera/light", data={'enabled': status_light})
	print(r.text)
	threading.Timer(5, bar).start()



GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)
GPIO.output(7, GPIO.HIGH)

camera = cv2.VideoCapture(0)
time.sleep(0.25)

print(camera.isOpened())
camera.open(0)

# initialize the first frame in the video stream
firstFrame = None


#call periodic post  function
foo()
bar()

print('testing ')
# loop over the frames of the video
while True:
	# grab the current frame and initialize the occupied/unoccupied
	# text
	(grabbed, frame) = camera.read()
	text = "Unoccupied"

	# if the frame could not be grabbed, then we have reached the end
	# of the video
	if not grabbed:
		print('frame failed')
		break

	# resize the frame, convert it to grayscale, and blur it
	frame = imutils.resize(frame, width=500)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)

	global status_light
        print(gray.mean())
	if gray.mean() > 50:
		status_light = 'true'
	else:
		status_light = 'false'
        #print gray.mean()

	# if the first frame is None, initialize it
	if firstFrame is None:
		firstFrame = gray
		continue

	# compute the absolute difference between the current frame and
	# first frame
	frameDelta = cv2.absdiff(firstFrame, gray)
	thresh = cv2.threshold(frameDelta, 125, 255, cv2.THRESH_BINARY)[1]

	# dilate the thresholded image to fill in holes, then find contours
	# on thresholded image
	thresh = cv2.dilate(thresh, None, iterations=2)
	(_,cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)

	# loop over the contours
	for c in cnts:
		# if the contour is too small, ignore it
		if cv2.contourArea(c) < 450:
			continue

		# compute the bounding box for the contour, draw it on the frame,
		# and update the text
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
		text = "Occupied"
	global status_l
	if(text == 'Occupied'):
		#print('LOW')
		status_l = 'true'
		#GPIO.output(7, GPIO.LOW)
	else:
		#GPIO.output(7, GPIO.HIGH)
		#print('HIGH')
		status_l = 'false'
	
	# draw the text and timestamp on the frame
	cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
		(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

	# show the frame and record if the user presses a key
	cv2.imshow("Security Feed", frame)
	cv2.imshow("Thresh", thresh)
	cv2.imshow("Frame Delta", frameDelta)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key is pressed, break from the lop
	if key == ord("q"):
		break

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
GPIO.cleanup()

