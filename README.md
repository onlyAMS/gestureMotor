# Gesture Conrolled Servo Motor

## Overview 
This project aims to demonstrate live hand detection using the mediapipe hand landmarker implementation

## Tool stack
- MediaPipe
- Cv2 
- A random forest model trained on set hand gestures

## Notes:
Normalization function:

    def normalize_landmarks(landmarks):
        wrist = landmarks[0]
        data = []

        for landmark in landmarks:
            x = landmark.x - wrist.x
            y = landmark.y - wrist.y
            z = landmark.z - wrist.z

            data.extend([x, y, z])

        return data


### Operation flow

