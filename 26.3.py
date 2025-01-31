import cv2
import numpy as np
from tracker import EuclideanDistTracker

tracker = EuclideanDistTracker()

# Path to the input video file
video_path = r"C:\Users\deoga\OneDrive\Desktop\12.mp4"

cap = cv2.VideoCapture(video_path)

input_size = 320

confThreshold = 0.2
nmsThreshold = 0.2

font_color = (255, 255, 255)
font_size = 0.7
font_thickness = 2

middle_line_position = 350

up_line_position = middle_line_position - 15
down_line_position = middle_line_position + 15

classesFile = r"C:\Users\deoga\OneDrive\Desktop\12343\coco.names"
classNames = open(classesFile).read().strip().split('\n')

required_class_index = [2, 3, 5, 7]

detected_classNames = []

modelConfiguration = r"C:\Users\deoga\OneDrive\Desktop\12343\yolov3-320.cfg"
modelWeights = r"C:\Users\deoga\OneDrive\Desktop\12343\yolov3-320.weights"

net = cv2.dnn.readNetFromDarknet(modelConfiguration, modelWeights)

net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

np.random.seed(42)
colors = np.random.randint(0, 255, size=(len(classNames), 3), dtype='uint8')

def find_center(x, y, w, h):
    x1 = int(w / 2)
    y1 = int(h / 2)
    cx = x + x1
    cy = y + y1
    return cx, cy

temp_up_list = []
temp_down_list = []
up_list = [0, 0, 0, 0]
down_list = [0, 0, 0, 0]

def count_vehicle(box_id, img):
    x, y, w, h, id, index = box_id

    center = find_center(x, y, w, h)
    ix, iy = center

    if (iy > up_line_position) and (iy < middle_line_position):
        if id not in temp_up_list:
            temp_up_list.append(id)
    elif iy < down_line_position and iy > middle_line_position:
        if id not in temp_down_list:
            temp_down_list.append(id)
    elif iy < up_line_position:
        if id in temp_down_list:
            temp_down_list.remove(id)
            down_list[index] += 1
    elif iy > down_line_position:
        if id in temp_up_list:
            temp_up_list.remove(id)
            up_list[index] += 1

    cv2.circle(img, center, 2, (0, 0, 255), -1)

def postProcess(outputs, img):
    global detected_classNames
    height, width = img.shape[:2]
    boxes = []
    classIds = []
    confidence_scores = []
    detection = []
    for output in outputs:
        for det in output:
            scores = det[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if classId in required_class_index and confidence > confThreshold:
                w, h = int(det[2] * width), int(det[3] * height)
                x, y = int((det[0] * width) - w / 2), int((det[1] * height) - h / 2)
                boxes.append([x, y, w, h])
                classIds.append(classId)
                confidence_scores.append(float(confidence))

    indices = cv2.dnn.NMSBoxes(boxes, confidence_scores, confThreshold, nmsThreshold)

    indices = np.array(indices)

    for i in indices.flatten():
        x, y, w, h = boxes[i]
        color = [int(c) for c in colors[classIds[i]]]
        name = classNames[classIds[i]]
        detected_classNames.append(name)

        cv2.putText(img, f'{name.upper()} {int(confidence_scores[i] * 100)}%', (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)
        detection.append([x, y, w, h, required_class_index.index(classIds[i])])

    boxes_ids = tracker.update(detection)
    for box_id in boxes_ids:
        count_vehicle(box_id, img)

def realTime():
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to read frame from the video source.")
            break

        img = cv2.resize(img, (1280, 720))  # Resize the image to half its original size
        ih, iw, channels = img.shape
        blob = cv2.dnn.blobFromImage(img, 1 / 255, (input_size, input_size), [0, 0, 0], 1, crop=False)

        net.setInput(blob)
        outputNames = net.getUnconnectedOutLayersNames()
        outputs = net.forward(outputNames)

        postProcess(outputs, img)

        cv2.line(img, (0, middle_line_position), (iw, middle_line_position), (255, 0, 255), 2)
        cv2.line(img, (0, up_line_position), (iw, up_line_position), (0, 0, 255), 2)
        cv2.line(img, (0, down_line_position), (iw, down_line_position), (0, 0, 255), 2)

        for i, vehicle_type in enumerate(["Car", "Motorbike", "Bus", "Truck"]):
            cv2.putText(img, f"{vehicle_type}: {up_list[i]}  {down_list[i]}", (20, 40 + 20*i),
                        cv2.FONT_HERSHEY_SIMPLEX, font_size, font_color, font_thickness)

        cv2.imshow('Output', img)

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

realTime()
