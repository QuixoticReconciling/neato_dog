"""This script detects a red expo marker using our custom YOLO dataset."""

from ultralytics import YOLO
import cv2

# Access the YOLO model and webcam
model = YOLO("neato_dog/YOLO_model/best.pt")
cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("Error: no camera found")
    exit()

print("Webcam accessed successfully. Press 'q' to quit.")

# While the camera is accessed
while True:

    # Read outputs a boolean whether its succeeded or not, and then the actual frame itself.
    ret,frame = cam.read()

    if not ret:
        print("Error: failed to grab frame")
        break

    results = model(frame, stream=True)

    for result in results:
        """ Useful YOLO commands to know from https://docs.ultralytics.com/tasks/detect"""
        # xywh = result.boxes.xywh  # center-x, center-y, width, height
        # xywhn = result.boxes.xywhn  # normalized
        # xyxy = result.boxes.xyxy  # top-left-x, top-left-y, bottom-right-x, bottom-right-y
        # xyxyn = result.boxes.xyxyn  # normalized
        # names = [result.names[cls.item()] for cls in result.boxes.cls.int()]  # class name of each box
        # confs = result.boxes.conf  # confidence score of each box
        
        annotated_frame = result.plot() # Plot the boxes for classes that YOLO recognizes

    cv2.imshow('Webcam Feed', annotated_frame) # Final annotated frame with bounding box

    # Kill
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break



cam.release()
cv2.destroyAllWindows()

