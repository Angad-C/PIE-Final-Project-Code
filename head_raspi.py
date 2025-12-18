import pygame
import time
import os
import cv2
from picamera2 import Picamera2
from ultralytics import YOLO


pygame.mixer.init()
picam2 = Picamera2()
picam2.preview_configuration.main.size = (780, 780)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()


file_path = "talk_louder.mp3"
model = YOLO("yolov8n.pt")

def playaudio(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.set_volume(0.8)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    print("Playback finished.")

while True:
    frame = picam2.capture_array()
    results = model(frame)

    annotated_frame = results[0].plot()
    
    inference_time = results[0].speed['inference']
    fps = 1000 / inference_time  # Convert to milliseconds
    text = f'FPS: {fps:.1f}'

    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, 1, 2)[0]
    text_x = annotated_frame.shape[1] - text_size[0] - 10  # 10 pixels from the right
    text_y = text_size[1] + 10  # 10 pixels from the top

    cv2.putText(annotated_frame, text, (text_x, text_y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
    for result in results:
        for cls_idx in result.boxes.cls:   # each class index
            label = model.names[int(cls_idx)]
            if label == "person":
                playaudio(file_path)

    if cv2.waitKey(1) == ord("q"):
        break

