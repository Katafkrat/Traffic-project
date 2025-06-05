import os
import cv2
import numpy as np
from .yolo_utils import detect_and_save


class TrafficProcessor:
    def __init__(self, video_path, output_folder, yolo_model_path, segment_length_sec):
        self.video_path = video_path
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
        self.video_file = os.path.basename(video_path)
        self.model_path = yolo_model_path
        self.segment_length_sec = segment_length_sec
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise ValueError(f"❌ Не вдалося відкрити відео: {self.video_file}")

        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) // 2
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.line_y = self.frame_height // 4

    def process(self):
        duration_sec = self.total_frames // self.fps
        segments = duration_sec // self.segment_length_sec
        results_summary = []
    
        for segment_idx in range(segments):
            print(f"🔹 Обробка сегменту {segment_idx + 1}/{segments}")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, segment_idx * self.segment_length_sec * self.fps)
            segment_frame_count = self.segment_length_sec * self.fps
            result_image = np.zeros((segment_frame_count, self.frame_width, 3), dtype=np.uint8)
    
            for i in range(segment_frame_count):
                ret, frame = self.cap.read()
                if not ret:
                    break
                line_image = frame[self.line_y:self.line_y + 1, :]
                line_image = cv2.resize(line_image, (self.frame_width, 1))
                result_image[i:i + 1, :, :] = line_image
    
            print(f"✅ Обробка YOLO: сегмент {segment_idx + 1}")
            class_counts = detect_and_save(self.model_path, result_image, self.output_folder, self.video_file, segment_idx + 1)
            results_summary.append((segment_idx + 1, class_counts))
    
        self.cap.release()
        return results_summary

