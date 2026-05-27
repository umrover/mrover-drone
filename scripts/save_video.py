import numpy as np
import cv2 as cv
import time
from datetime import datetime
import sys
import os

if len(sys.argv) > 1:
    arg = sys.argv[1]
    
    if arg.startswith("/dev/video"):
        device = arg
    else:
        device = int(arg)
else:
    device = 0  # default

print(f"Using device: {device}")


cap = cv.VideoCapture(device)

if not cap.isOpened():
    raise RuntimeError("Cannot open /dev/video4")

# Force settings 
width = 640
height = 480
fps = 30

cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
cap.set(cv.CAP_PROP_FPS, fps)



# Define the codec and create VideoWriter object
fourcc = cv.VideoWriter_fourcc(*'mp4v')
def create_writer():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}.mp4"
    print(f"Recording: {filename}")
    return cv.VideoWriter(filename, fourcc, fps, (width, height))


out = create_writer()
start_time = time.time()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Can't receive frame (stream end?). Exiting...")
        break

    out.write(frame)

    if time.time() - start_time >= 30:
        out.release()
        out = create_writer()
        start_time = time.time()
        

    #write the flipped frame
    cv.imshow('frame', frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
out.release()
cv.destroyAllWindows()