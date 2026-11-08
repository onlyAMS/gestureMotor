import cv2
import mediapipe as mp
import time
import math
import serial
import numpy as np
import csv
import joblib
from collections import deque, Counter

last_sample = time.time()
sample_interval = 0.2  # 200 milliseconds

labels = ["closed_palm", "open_palm", "thumbs_up"]

model = joblib.load("hand_gesture_model.pkl")
new_model = joblib.load("new_gesture_model_2.pkl")

arduino = serial.Serial('COM5', 9600)
time.sleep(2)

# Prediction stabilization
prediction_history = deque(maxlen=7)
previous_gesture = None


def predict_gesture(data):

    data = normalize_landmarks(data)

    data = np.array(data).reshape(1, -1)
    probabilities = model.predict_proba(data)
    confidence = np.max(probabilities)

    if confidence < 0.65:
        return "Unknown"

    prediction = model.predict(data)

    return prediction[0], probabilities


def save_landmarks(data, label):

    data = data.tolist()
    data.append(label)

    with open("hand_data.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(data)


def normalize_landmarks(landmarks):
    wrist = landmarks[0]
    data = []

    for landmark in landmarks:
        x = landmark.x - wrist.x
        y = landmark.y - wrist.y
        z = landmark.z - wrist.z

        data.extend([x, y, z])

    return data


def collect_sample(last_sample, sample_interval, saved_samples):
    current_time = time.time()
    if current_time - last_sample >= sample_interval:
        hand = results.hand_landmarks[0]

        row = normalize_landmarks(hand)
        row = np.array(row).reshape(1, -1)
        save_landmarks(row, 'thumbs')

        last_sample = current_time

        saved_samples += 1

        print(f"{saved_samples} samples saved")


def make_prediction(landmarks):

    normalized_landmarks = normalize_landmarks(landmarks)
    data = np.array(normalized_landmarks)
    data = data.reshape(1, -1)

    probabilities = new_model.predict_proba(data)

    highest_prob = probabilities.max()
    best_index = probabilities.argmax()

    if highest_prob >= 0.85:
        gesture = new_model.classes_[best_index]
        return gesture, highest_prob * 100
    else:
        return "Uncertain", 0


def stabilize_prediction(prediction):

    prediction_history.append(prediction)

    if len(prediction_history) < 7:
        return None

    counts = Counter(
        p for p in prediction_history
        if p != "Uncertain"
    )

    if not counts:
        return None

    most_common, count = counts.most_common(1)[0]

    if count >= 5:
        return most_common

    return None


def find_distance(point1, point2):
    distance = math.sqrt(
        (point2.x - point1.x) ** 2 +
        (point2.y - point1.y) ** 2
    )
    distance = round(distance, 2)
    return distance


def send_data(data):
    arduino.write(f"{data}\n".encode('utf-8'))
    print(f"Sent: {data}")
    print(type(data))


def count_fingers(hand):

    fingers = 0

    # Index
    if hand[8].y < hand[6].y:
        fingers += 1

    # Middle
    if hand[12].y < hand[10].y:
        fingers += 1

    # Ring
    if hand[16].y < hand[14].y:
        fingers += 1

    # Pinky
    if hand[20].y < hand[18].y:
        fingers += 1

    return fingers


# Initialize MediaPipe
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

# Hand landmark connections
connections = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

# Configure detector
options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="hand_landmarker.task"
    ),
    running_mode=RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

# Initialize webcam
cap = cv2.VideoCapture(0)
saved_samples = 0
frame_count = 0
gesture = "unknown"

with HandLandmarker.create_from_options(options) as detector:

    while cap.isOpened():

        success, frame = cap.read()

        if not success:
            break

        # Mirror webcam
        frame = cv2.flip(frame, 1)

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to MediaPipe image
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        # Process frame
        timestamp = int(time.time() * 1000)

        results = detector.detect_for_video(
            mp_image,
            timestamp
        )

        # Check for detected hands
        if results.hand_landmarks:

            landmarks = results.hand_landmarks[0]

            frame_count += 1

            if frame_count % 5 == 0:

                raw_gesture, certainty = make_prediction(landmarks)

                print(f"{raw_gesture} with {certainty}% confidence")

                # Majority voting
                confirmed_gesture = stabilize_prediction(raw_gesture)

                # Only transmit when confirmed gesture changes
                if confirmed_gesture is not None:

                    if confirmed_gesture != previous_gesture:

                        gesture = confirmed_gesture

                        send_data(gesture)

                        previous_gesture = confirmed_gesture

            # sample collection...{INSERT HERE}

            height, width, _ = frame.shape

            for hand in results.hand_landmarks:

                points = []

                # Extract landmark coordinates
                for landmark in hand:

                    x = int(landmark.x * width)
                    y = int(landmark.y * height)

                    points.append((x, y))

                # Draw connecting lines
                for start, end in connections:

                    cv2.line(
                        frame,
                        points[start],
                        points[end],
                        (255, 255, 255),
                        2
                    )

                # Draw landmark points
                for point in points:

                    cv2.circle(
                        frame,
                        point,
                        5,
                        (0, 255, 0),
                        -1
                    )

        # Display webcam
        cv2.imshow("Hand Detection", frame)

        # Press Q to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


# Release resources
cap.release()
cv2.destroyAllWindows()

