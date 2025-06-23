import cv2
import numpy as np
import pyautogui
import time
import os
from datetime import datetime
from .yolo_utils import detect_and_save


def build_stitched_image(frames, line_y):
    if not frames:
        return None
    original_width = frames[0].shape[1]
    target_width = original_width // 8
    stitched_lines = []
    for frame in frames:
        line = frame[line_y:line_y + 1, :, :]
        resized_line = cv2.resize(line, (target_width, 1), interpolation=cv2.INTER_AREA)
        stitched_lines.append(resized_line)
    return np.vstack(stitched_lines)


def record_and_process_screen(
    output_folder,
    duration,
    segment_length_sec,
    model_path,
    video_name="screen_capture",
    log_callback=None,
    stop_callback=lambda: False
):
    screen_size = pyautogui.size()
    fps = 20
    segment_frames = int(segment_length_sec * fps)
    video_name_base = f"{video_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    segment_dir = os.path.join(output_folder, video_name_base)
    full_video_path = os.path.join(segment_dir, f"{video_name_base}.avi")
    os.makedirs(segment_dir, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    video_writer = cv2.VideoWriter(full_video_path, fourcc, fps, screen_size)

    buffer = []
    segment_idx = 1
    line_y = screen_size.height // 4
    all_results = []

    if log_callback:
        msg = f"⏺ Безперервний запис екрану..." if duration == 0 else f"⏺ Запис екрану розпочато на {duration} сек..."
        log_callback(msg)

    frame_time = 1.0 / fps
    start_time = time.time()
    frame_idx = 0

    while True:
        if stop_callback():
            if log_callback:
                log_callback("🛑 Запис екрану перервано.")
            break

        if duration > 0 and (time.time() - start_time >= duration):
            break

        img = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        video_writer.write(frame)
        buffer.append(frame)
        frame_idx += 1

        if len(buffer) == segment_frames:
            if log_callback:
                log_callback(f"🧪 Обробка сегмента {segment_idx}")
            stitched_img = build_stitched_image(buffer, line_y)
            class_counts = detect_and_save(model_path, stitched_img, segment_dir, video_name_base + ".avi", segment_idx)
            all_results.append((segment_idx, class_counts))
            buffer.clear()
            segment_idx += 1

        elapsed = time.time() - (start_time + frame_idx * frame_time)
        if elapsed < 0:
            time.sleep(-elapsed)

    if buffer:
        if log_callback:
            log_callback(f"🧪 Обробка останнього сегмента {segment_idx}")
        stitched_img = build_stitched_image(buffer, line_y)
        class_counts = detect_and_save(model_path, stitched_img, segment_dir, video_name_base + ".avi", segment_idx)
        all_results.append((segment_idx, class_counts))

    video_writer.release()

    if log_callback:
        log_callback(f"✅ Запис завершено: {full_video_path}")

    return all_results
