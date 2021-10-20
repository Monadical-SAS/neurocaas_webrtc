import cv2
import sys


DEVICE = sys.argv[1]

cap = cv2.VideoCapture(DEVICE)

if not cap.isOpened():
    print('Cannot open device')
    exit(-1)

while True:
    _, frame = cap.read()
    cv2.imshow('Stream', frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
