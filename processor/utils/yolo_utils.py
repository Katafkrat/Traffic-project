from ultralytics import YOLO
import cv2
import os
from collections import Counter

def detect_and_save(yolo_model_path, image, output_folder, video_file_name, segment_idx):
    folder_name = f"{os.path.splitext(video_file_name)[0]}_part{segment_idx}"
    save_dir = os.path.join(output_folder, folder_name)
    os.makedirs(save_dir, exist_ok=True)

    model = YOLO(yolo_model_path)
    results = model.predict(source=image, save=False, conf=0.3)[0]

    original_path = os.path.join(save_dir, "original.jpg")
    cv2.imwrite(original_path, image)

    annotated_image = results.plot()
    detected_path = os.path.join(save_dir, "detected.jpg")
    cv2.imwrite(detected_path, annotated_image)

    # 🔢 Підрахунок класів
    class_names = model.names
    classes = results.boxes.cls.tolist()
    class_counts = Counter([class_names[int(cls)] for cls in classes])

    print(f"📁 Збережено результати у {save_dir} | 🔍 Виявлено: {dict(class_counts)}")
    return dict(class_counts)
