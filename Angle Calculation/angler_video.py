import cv2
import time
import numpy as np
import math
import socket

protoFile1 = "model/testing.prototxt"
weightsFile1 = "model/pose_iter_102000.caffemodel"

nPoints = 22
POSE_PAIRS = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [0, 9], [9, 10], [10, 11], [11, 12],
              [0, 13], [13, 14], [14, 15], [15, 16], [0, 17], [17, 18], [18, 19], [19, 20]]

threshold = 0.2
embed = []
done_frames = 0

#input_source = "videos/angle_testing.avi"
input_source = 0
cap = cv2.VideoCapture(input_source)
hasFrame, frame = cap.read()

frameWidth = frame.shape[1]
frameHeight = frame.shape[0]
angle = 0
angle_degrees = 0

aspect_ratio = frameWidth / frameHeight

inHeight = 368
inWidth = int(((aspect_ratio * inHeight) * 8) // 8)

vid_writer = cv2.VideoWriter('outputs/angle_testing.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 15,
                             (frame.shape[1], frame.shape[0]))

## CLIENT CODE

host = '127.0.0.1'
port = 12345
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))

##

net = cv2.dnn.readNetFromCaffe(protoFile1, weightsFile1)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL_FP16)
k = 0
while 1:
    k += 1
    t = time.time()
    hasFrame, frame = cap.read()
    frameCopy = np.copy(frame)
    if not hasFrame:
        cv2.waitKey()
        break

    inpBlob = cv2.dnn.blobFromImage(frame, 1.0 / 255, (inWidth, inHeight),
                                    (0, 0, 0), swapRB=False, crop=False)

    net.setInput(inpBlob)

    output = net.forward()

    # print("forward = {}".format(time.time() - t))

    # Empty list to store the detected keypoints
    points = []

    for i in range(nPoints):
        # confidence map of corresponding body's part.
        probMap = output[0, i, :, :]
        probMap = cv2.resize(probMap, (frameWidth, frameHeight))

        # Find global maxima of the probMap.
        minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)

        if prob > threshold:
            # cv2.circle(frameCopy, (int(point[0]), int(point[1])), 6, (0, 255, 255), thickness=-1, lineType=cv2.FILLED)
            # cv2.putText(frameCopy, "{}".format(i), (int(point[0]), int(point[1])), cv2.FONT_HERSHEY_SIMPLEX, .8,
            #             (0, 0, 255), 2, lineType=cv2.LINE_AA)

            # Add the point to the list if the probability is greater than the threshold
            points.append((int(point[0]), int(point[1])))
        else:
            points.append(None)

    try:
        # print(points)
        x1, y1 = points[14]
        x2, y2 = points[15]
        angle = math.atan((y2 - y1) / (x1 - x2))
        angle_degrees = math.degrees(angle)
        if angle_degrees < 0:
            angle_degrees = 180 + angle_degrees
        if y2 > y1:
            angle_degrees = 0
        print("ANGLE = ", angle_degrees)
    except:
        print("Improper points recieved")

    # Draw Skeleton
    # for pair in POSE_PAIRS:
    #     partA = pair[0]
    #     partB = pair[1]
    #
    #     if points[partA] and points[partB]:
    #         cv2.line(frame, points[partA], points[partB], (0, 255, 255), 2, lineType=cv2.LINE_AA)
    #         cv2.circle(frame, points[partA], 5, (0, 0, 255), thickness=-1, lineType=cv2.FILLED)
    #         cv2.circle(frame, points[partB], 5, (0, 0, 255), thickness=-1, lineType=cv2.FILLED)

    # print("Time Taken for frame = {}".format(time.time() - t))
    done_frames += 1

    cv2.putText(frame, "Angle = {:.5f} degrees".format(angle_degrees), (50, 50), cv2.FONT_HERSHEY_COMPLEX, .8,
                (255, 50, 0), 2,
                lineType=cv2.LINE_AA)

    try:
        s.send(str(angle_degrees).encode())
    except Exception as e:
        print(e)
        s.close()
        break
    cv2.imshow('out', frame)
    # cv2.imshow('framecopy', frameCopy)
    key = cv2.waitKey(1)
    if key == 27:
        s.close()
        break

    print("Time taken = {}".format(time.time() - t))
    print("Frame :", done_frames, '\n')

    # vid_writer.write(frame)

vid_writer.release()
cap.release()
cv2.destroyAllWindows()
