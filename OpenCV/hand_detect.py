import cv2
import numpy as np
import socket
# import json
import time

UDP_IP = "127.0.0.1"
UDP_PORT = 5065

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

cap = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")

hsv = None
hh, ww = None, None

s = time.time()
while time.time() - s < 5:
    frame = cap.read()[1]
    frame = cv2.flip(frame, 1)

    ww, hh = frame.shape[:2]

    cv2.rectangle(frame, (ww // 2 - 50, hh // 2 - 250), (ww // 2, hh // 2 - 200), 255, 3)
    cv2.rectangle(frame, (ww // 2 + 250, hh // 2 - 250), (ww // 2 + 290, hh // 2 - 200), 255, 3)

    cv2.putText(
        frame,
        "Put your palms inside the boxes for calibration",
        (150, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255)
    )

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    cv2.imshow("calibration", frame)
    cv2.waitKey(1)

cv2.destroyAllWindows()

left_hsv = hsv[hh // 2 - 50:hh // 2, ww // 2 - 150:ww // 2 - 110]
right_hsv = hsv[hh // 2 - 50:hh // 2, ww // 2 + 150:ww // 2 + 190]

prob = [{}, {}, {}]

for j in range(3):
    for i in range(50):
        for k in range(40):
            try:
                prob[j][left_hsv[:, :, j][i][k]] += 1
            except:
                prob[j].update({left_hsv[:, :, j][i][k]: 1})
            try:
                prob[j][right_hsv[:, :, j][i][k]] += 1
            except:
                prob[j].update({right_hsv[:, :, j][i][k]: 1})

lower_range = []
upper_range = []

for j in range(3):
    lower_range.append(min(prob[j], key=prob[j].get))
    upper_range.append(max(prob[j], key=prob[j].get))

lower_range[0] = min(lower_range[0], 2)
lower_range[1] = min(lower_range[1], 50)
lower_range[2] = min(lower_range[2], 150)

upper_range[0] = min(upper_range[0], 20)
upper_range[1] = min(upper_range[1], 100)
upper_range[2] = min(upper_range[2], 255)

# print(lower_range)
# print(upper_range)

while True:
    frame = cap.read()[1]
    frame = cv2.flip(frame, 1)

    dup = frame.copy()

    faces = face_cascade.detectMultiScale(
        cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
        scaleFactor=1.3,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    for face in faces:
        x, y, w, h = face
        frame[y:y + h + 120, x:x + w] = 0

    blur = cv2.blur(frame, (3, 3))
    hsv_frame = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_frame, np.array([2, 50, 150]), np.array([20, 100, 255]))
    # mask = cv2.inRange(hsv_frame, np.array(lower_range), np.array(upper_range))

    kernel_square = np.ones((11, 11), np.uint8)
    kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilation1 = cv2.dilate(mask, kernel_ellipse, iterations=1)
    erosion1 = cv2.erode(dilation1, kernel_square, iterations=1)

    dilation2 = cv2.dilate(erosion1, kernel_ellipse, iterations=1)
    filtered = cv2.medianBlur(dilation2, 5)

    kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
    dilation2 = cv2.dilate(filtered, kernel_ellipse, iterations=1)

    kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilation3 = cv2.dilate(filtered, kernel_ellipse, iterations=1)

    median = cv2.medianBlur(dilation3, 5)
    thresh = cv2.threshold(median, 127, 255, 0)[1]

    # cv2.imshow('test', thresh)

    junk, contours, hierarchy = cv2.findContours(
        thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    if len(contours) >= 2:
        cnts = sorted(contours, key=cv2.contourArea, reverse=True)
        # while cv2.contourArea(cnts[0]) > 9000:
        #     cnts.pop(0)
        #     if len(cnts) == 0:
        #         break

        # if len(cnts) < 2:
        #     continue

        # print(cv2.contourArea(cnts[0]), cv2.contourArea(cnts[1]))

        y_coords = []
        x_coords = []

        for i in range(min(2, len(cnts))):
            cnt = cnts[i]
            moments = cv2.moments(cnt)

            if moments['m00'] != 0:
                cx = int(moments['m10'] / moments['m00'])
                cy = int(moments['m01'] / moments['m00'])

                y_coord = (frame.shape[1] - cy) / float(frame.shape[1])
                y_coords.append(y_coord)
                x_coords.append(cx)

                centerMass = (cx, cy)

                cv2.circle(dup, centerMass, 7, [100, 0, 255], 2)
                font = cv2.FONT_HERSHEY_SIMPLEX

        if x_coords[0] > x_coords[1]:
            y_coords = y_coords[::-1]
        print("%f,%f" % (y_coords[0], y_coords[1]))
        sock.sendto(
            (("%f,%f" % (y_coords[0], y_coords[1])).encode()),
            (UDP_IP, UDP_PORT)
        )

    cv2.imshow('test', dup)
    if cv2.waitKey(1) & 255 == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
