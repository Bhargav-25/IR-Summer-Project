#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: Daniela Ordóñez Tapia

"""

import sim
import cv2
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import colors

IMG_WIDTH = 256
IMG_HEIGHT = 256

grid_matrix = np.zeros((512, 512))


# Find the masks by color (red, green and blue)
def findColorsMasks(original):
    hsv_image = cv2.cvtColor(original, cv2.COLOR_BGR2HSV)

    # Red colour
    redMin_1 = np.array([0, 120, 20])
    redMax_1 = np.array([10, 255, 255])
    redMin_2 = np.array([170, 120, 20])
    redMax_2 = np.array([180, 255, 255])
    red_mask_1 = cv2.inRange(hsv_image, redMin_1, redMax_1)
    red_mask_2 = cv2.inRange(hsv_image, redMin_2, redMax_2)
    red_mask = cv2.bitwise_or(red_mask_1, red_mask_2)

    # Blue colour
    blueMin = np.array([85, 120, 20])
    blueMax = np.array([135, 255, 255])
    blue_mask = cv2.inRange(hsv_image, blueMin, blueMax)

    # Green colour
    greenMin = np.array([40, 0, 20])
    greenMax = np.array([80, 255, 255])
    green_mask = cv2.inRange(hsv_image, greenMin, greenMax)

    lower_white = np.array([0, 0, 0])
    upper_white = np.array([0, 0, 255])
    white_mask = cv2.inRange(hsv_image, lower_white, upper_white)

    map_mask = cv2.bitwise_or(blue_mask, red_mask)
    obstacle_mask = cv2.bitwise_or(green_mask, white_mask)

    return map_mask, obstacle_mask, white_mask


def detectCenterOfMass(given_image):
    ret, thresh = cv2.threshold(given_image, 0, 255, 0)
    contours, hierarchy = cv2.findContours(
        thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return_image = cv2.cvtColor(given_image, cv2.COLOR_GRAY2BGR)
    center_X = IMG_WIDTH/2.0

    for c in contours:
        # compute the center of the contour
        M = cv2.moments(c)
        if (M["m10"] and M["m01"] and M["m00"]) != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            # draw the contour and center of the shape on the image
            cv2.drawContours(return_image, [c], -1, (0, 255, 0), 2)
            cv2.circle(return_image, (cX, cY), 7, (0, 0, 255), -1)
            center_X = cX

    return (return_image)


def detectBlobs(given_image):
    # given_image = cv2.cvtColor(given_image, cv2.COLOR_BGR2GRAY)
    # Set up the detector with default parameters.
    params = cv2.SimpleBlobDetector_Params()

    # Change thresholds
    params.minThreshold = 10
    params.maxThreshold = 200

    # Filter by Color.
    params.filterByColor = True
    params.blobColor = 255

    # Filter by Area.
    params.filterByArea = True
    params.minArea = 10

    # Filter by Circularity
    params.filterByCircularity = True
    params.minCircularity = 0.1

    # Filter by Convexity
    params.filterByConvexity = True
    params.minConvexity = 0.87

    # Filter by Inertia
    params.filterByInertia = True
    params.minInertiaRatio = 0.01

    # Create a detector with the parameters
    ver = (cv2.__version__).split('.')
    if int(ver[0]) < 3:
        detector = cv2.SimpleBlobDetector(params)
    else:
        detector = cv2.SimpleBlobDetector_create(params)

    # Detect blobs
    keypoints = detector.detect(given_image)

    # Draw detected blobs as red circles.
    # cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
    print("------")
    im_with_keypoints = cv2.drawKeypoints(given_image, keypoints, np.array(
        []), (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    return im_with_keypoints


# -------------------------------------- START PROGRAM --------------------------------------
# Start Program and just in case, close all opened connections
print('Program started')
sim.simxFinish(-1)

# Connect to simulator running on localhost
# V-REP runs on port 19997, a script opens the API on port 19999
clientID = sim.simxStart('127.0.0.1', 19999, True, True, 5000, 5)

# Connect to the simulation
if clientID != -1:
    print('Connected to remote API server')

    # Get handles to simulation objects
    print('Obtaining handles of simulation objects')

    # Floor perspective camera for exploration
    res, camera_pers = sim.simxGetObjectHandle(
        clientID, 'Vision_sensor', sim.simx_opmode_oneshot_wait)
    if res != sim.simx_return_ok:
        print('Could not get handle to Camera')

    # Floor orthographic camera for exploration
    res, camera_orth = sim.simxGetObjectHandle(
        clientID, 'Vision_sensor0', sim.simx_opmode_oneshot_wait)
    if res != sim.simx_return_ok:
        print('Could not get handle to Camera')


# -------------------------------------- Main Control Loop --------------------------------------

    # Start main control loop
    print('Starting control loop')

    res, resolution, image_pers = sim.simxGetVisionSensorImage(
        clientID, camera_pers, 0, sim.simx_opmode_streaming)
    res, resolution, image_orth = sim.simxGetVisionSensorImage(
        clientID, camera_orth, 0, sim.simx_opmode_streaming)

    while (sim.simxGetConnectionId(clientID) != -1):
        # Get image from Camera
        res_pers, resolution, image_pers = sim.simxGetVisionSensorImage(
            clientID, camera_pers, 0, sim.simx_opmode_buffer)
        res, resolution, image_orth = sim.simxGetVisionSensorImage(
            clientID, camera_orth, 0, sim.simx_opmode_buffer)

        if res == sim.simx_return_ok:
            original = np.array(image, dtype=np.uint8)
            original.resize([resolution[0], resolution[1], 3])
            original = cv2.flip(original, 0)
            original = cv2.cvtColor(original, cv2.COLOR_RGB2BGR)
            cv2.imshow("Camera", original)

            map_mask, obstacle_mask, white_mask = findColorsMasks(original)
            output_image = cv2.bitwise_and(
                original, original, mask=map_mask)
            cv2.imshow("MapMask", output_image)
            obstacle_mask = cv2.bilateralFilter(obstacle_mask, 9, 110, 110)
            cv2.imshow("ObstacleMask", obstacle_mask)

            center_mass = detectCenterOfMass(white_mask)
            # cv2.imshow("CenterOfMass", obstacle_mask)

            im_with_keypoints = detectBlobs(obstacle_mask)
            # Show keypoints
            # cv2.imshow("Keypoints", im_with_keypoints)
            # cv2.waitKey(0)

            # for i in range(len(mask)):
            #     for j in range(len(mask)):
            #         if mask[i][j] == 255:
            #             matrix[i][j] = 1
            # grid_matrix = mask/255

            # # fig, ax = plt.subplots()
            # cmap = colors.ListedColormap(['white', 'red'])

            # bounds = [0, 1, 512]
            # norm = colors.BoundaryNorm(bounds, cmap.N)
            # img = plt.imshow(grid_matrix, interpolation='nearest', origin='lower',
            #                  cmap=cmap, norm=norm)
            # plt.show()

            # # plot it
            # ax.imshow(grid_matrix, interpolation='none', cmap=cmap, norm=norm)

            # print(grid_matrix)

            # cv2.cvtColor(output_image, cv2.COLOR_HSV2BGR)
        elif res == sim.simx_return_novalue_flag:
            # Camera has not started or is not returning images
            print("Wait, there's no image yet")
        else:
            # Something else has happened
            print("Unexpected error returned", res)

        keypress = cv2.waitKey(1) & 0xFF
        if keypress == ord('q'):
            break
else:
    print('Could not connect to remote API server')

# Close all simulation elements
sim.simxFinish(clientID)
cv2.destroyAllWindows()
print('Simulation ended')
