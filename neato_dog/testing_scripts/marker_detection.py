from ultralytics import YOLO
import cv2

model = YOLO("neato_dog/YOLO_model/best.pt")
cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("Error: no camera found")
    exit()

print("Webcam accessed successfully. Press 'q' to quit.")

while True:
    ret,frame = cam.read()

    if not ret:
        print("Error: failed to grab frame")
        break

    results = model(frame, stream=True)

    for result in results:
        # Copied from Yolo documentation
        # xywh = result.boxes.xywh  # center-x, center-y, width, height
        # xywhn = result.boxes.xywhn  # normalized
        # xyxy = result.boxes.xyxy  # top-left-x, top-left-y, bottom-right-x, bottom-right-y
        # xyxyn = result.boxes.xyxyn  # normalized
        # names = [result.names[cls.item()] for cls in result.boxes.cls.int()]  # class name of each box
        # confs = result.boxes.conf  # confidence score of each box
        annotated_frame = result.plot()

    cv2.imshow('Webcam Feed', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break



cam.release()
cv2.destroyAllWindows()

