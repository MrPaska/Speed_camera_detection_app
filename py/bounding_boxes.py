from ultralytics import YOLO
import cvzone
import math
from datetime import datetime, timedelta
import play_voice
from snackbar import alert_window
import cv2
from image_processing import process_img
from statistics import post_statistics


classes = ["momentinis", "vidutinis", "zona"]
model = YOLO("../model/best2.pt")
new_datetime = datetime.now()
vidutinis = False
stored_img = None
saved_photos = []
i = 0


def recognition(frame, user_id, bounding_box, zona_layout, video_play):
    global new_datetime, i, vidutinis, stored_img
    current_datetime = datetime.now()
    if current_datetime >= new_datetime:
        results = model(frame)
        frame_copy = frame.copy()
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]  # x1, y2 top left corner, x2, y2 bottom right corner
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                w, h = x2 - x1, y2 - y1
                conf = math.ceil(box.conf * 100) / 100  # because it rounds to 1 without (*100)/100
                cls = int(box.cls[0])
                if conf >= 0.5:
                    if conf >= 0.8 and classes[cls] == "momentinis":
                        new_datetime = current_datetime + timedelta(seconds=5)
                        play_voice.play_voice(0)
                        stored_img = frame_copy[y1:y2, x1:x2]  # x columns y rows
                        if video_play is None:
                            post_statistics("momentinis", 0, user_id, stored_img)
                        alert_window("Aptiktas momentinio greičio matuoklis!", None, zona_layout, video_play)
                        stored_img = None
                        break
                    if conf >= 0.8 and classes[cls] == "vidutinis":
                        vidutinis = True
                        stored_img = frame_copy[y1:y2, x1:x2]
                    if conf >= 0.8 and classes[cls] == "zona" and vidutinis is True:
                        i += 1
                        print(f"Vidutinis: {vidutinis}")
                        get_zona_box(frame, x1, x2, y1, y2, i)
                        new_datetime = current_datetime + timedelta(seconds=.15)
                        print(i)
                        if i == 10:
                            shutdown(user_id, stored_img, zona_layout, video_play)
                            break
                    if bounding_box:
                        cvzone.cornerRect(frame, (x1, y1, w, h), l=30, t=5, rt=1, colorR=(255, 0, 255), colorC=(0, 255, 0))  # l line length, t thickness, rt type (bold corners)
                        cvzone.putTextRect(frame, f'{cls} {conf}', (max(0, x1), max(35, y1)), scale=0.7, thickness=1)  # max for non negative values, for text to be visable in image

            if len(boxes) == 0 and vidutinis:
                shutdown(user_id, stored_img, zona_layout, video_play)
                break
    return frame


def get_zona_box(frame, x1, x2, y1, y2, n):
    photo = f"zone_cropped_{n}.jpg"
    zona_box = frame[y1:y2, x1:x2]
    try:
        cv2.imwrite(photo, zona_box)
        saved_photos.append(photo)
        print("foto saved")
    except Exception as e:
        print(f"failed to save photo {e}")


def shutdown(user_id, image, zona_layout, video_play):
    global new_datetime, i, vidutinis, stored_img
    new_datetime = datetime.now() + timedelta(seconds=5)
    process_img(saved_photos, user_id, image, zona_layout, video_play)
    saved_photos.clear()
    play_voice.play_voice(1)
    i = 0
    vidutinis = False
    stored_img = None


