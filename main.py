import cv2
import numpy as np
import time
import sys
import math
import pulsectl

# Add your local hand-tracking module path
sys.path.insert(0, '/home/roman/Hand-Tracking/hand-tracking')
import hand_tracking_module as htm

# Webcam dimensions
wCam, hCam = 640, 480

# Initialize PulseAudio controller
pulse = pulsectl.Pulse('volume-control')
# Use default sink instead of hardcoded index
sink = pulse.get_sink_by_name(pulse.server_info().default_sink_name)

# Initialize camera
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

# Initialize FPS calculation
pTime = 0

# UI and volume parameters
volumeBarY = 400
volumePercent = 0
detector = htm.HandDetector(detectionCon=0.7, maxHands=1)

while True:
    success, img = cap.read()
    img = detector.findHands(img)  # Detect hands and draw landmarks
    lmList, bbox = detector.findPosition(img, draw=True)

    if len(lmList) != 0:
        # Calculate bounding box area of the hand
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) // 100

        # Only consider realistic hand area
        if 250 < area < 1200:
            # Distance between thumb tip (id 4) and index finger tip (id 8)
            length, img, lineInfo = detector.findDistance(4, 8, img)

            # Map the distance to volume level (0.0 to 1.0)
            volumeLevel = np.interp(length, [50, 250], [0, 1])
            volumeBarY = int(np.interp(length, [50, 250], [400, 150]))
            volumePercent = int(volumeLevel * 100)

            # Smooth the volume (optional)
            smoothness = 2
            volumePercent = smoothness * round(volumePercent / smoothness)

            # Detect if pinky is down before setting volume
            fingers = detector.fingersUp()
            if not fingers[-1]:  # Pinky finger
                pulse.volume_set_all_chans(sink, volumeLevel)
                # Highlight interaction point
                cv2.circle(img, (lineInfo[-2], lineInfo[-1]), 15, (255, 255, 0), cv2.FILLED)
            if fingers[2]==0:
                break
    # Draw volume bar
    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
    cv2.rectangle(img, (50, volumeBarY), (85, 400), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, f"{volumePercent} %", (40, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Show current volume
    current_volume = sink.volume.value_flat
    cv2.putText(img, f"Current: {int(current_volume * 100)}%", (400, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # FPS calculation
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f"FPS: {int(fps)}", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Show image
    cv2.imshow('Volume Control', img)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
