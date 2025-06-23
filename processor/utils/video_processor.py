import os
import cv2
import numpy as np
from datetime import datetime
from .yolo_utils import detect_and_save


def build_stitched_image(frames, line_y):
    if not frames:
        return None
    original_width = frames[0].shape[1]
    target_width = original_width // 2
    stitched_lines = []
    for frame in frames:
        line = frame[line_y:line_y + 1, :, :]
        resized_line = cv2.resize(line, (target_width, 1), interpolation=cv2.INTER_AREA)
        stitched_lines.append(resized_line)
    return np.vstack(stitched_lines)


def process_video_file(video_path, output_folder, model_path, segment_length_sec, log_callback=None, stop_callback=lambda: False):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        if log_callback:
            log_callback(f"❌ Не вдалося відкрити відео: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 120:
        fps = 20

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    line_y = height // 4
    segment_frames = int(segment_length_sec * fps)

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    video_name_base = f"{video_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    segment_dir = os.path.join(output_folder, video_name_base)
    os.makedirs(segment_dir, exist_ok=True)

    buffer = []
    segment_idx = 1
    all_results = []
    fourcc = cv2.VideoWriter_fourcc(*"XVID")

    while True:
        if stop_callback():
            if log_callback:
                log_callback("🛑 Обробка відео зупинена.")
            break

        ret, frame = cap.read()
        if not ret:
            break

        buffer.append(frame)

        if len(buffer) == segment_frames:
            segment_path = os.path.join(segment_dir, f"{video_name}_segment{segment_idx}.avi")
            out = cv2.VideoWriter(segment_path, fourcc, fps, (width, height))
            for f in buffer:
                out.write(f)
            out.release()

            if log_callback:
                log_callback(f"🧪 Обробка сегмента {segment_idx}")

            stitched_img = build_stitched_image(buffer, line_y)
            class_counts = detect_and_save(model_path, stitched_img, segment_dir, segment_path, segment_idx)
            all_results.append((segment_idx, class_counts))

            segment_idx += 1
            buffer.clear()

    if buffer:
        segment_path = os.path.join(segment_dir, f"{video_name}_segment{segment_idx}.avi")
        out = cv2.VideoWriter(segment_path, fourcc, fps, (width, height))
        for f in buffer:
            out.write(f)
        out.release()

        if log_callback:
            log_callback(f"🧪 Обробка останнього сегмента {segment_idx}")

        stitched_img = build_stitched_image(buffer, line_y)
        class_counts = detect_and_save(model_path, stitched_img, segment_dir, segment_path, segment_idx)
        all_results.append((segment_idx, class_counts))

    cap.release()
    return all_results
