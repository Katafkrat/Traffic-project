import cv2
import numpy as np
import os
import time
from datetime import datetime
from .yolo_utils import detect_and_save


def build_stitched_image(frames, line_y):
    if not frames:
        return None
    original_width = frames[0].shape[1]
    target_width = original_width // 16
    stitched_lines = []
    for frame in frames:
        line = frame[line_y:line_y + 1, :, :]
        resized_line = cv2.resize(line, (target_width, 1), interpolation=cv2.INTER_AREA)
        stitched_lines.append(resized_line)
    return np.vstack(stitched_lines)


def record_and_process_rtsp(
    rtsp_url,
    output_folder,
    duration,
    segment_length_sec,
    model_path,
    video_name="rtsp_capture",
    log_callback=None,
    stop_callback=lambda: False
):
    if not rtsp_url:
        if log_callback:
            log_callback("❌ RTSP URL не задано!")
        return []

    cap = cv2.VideoCapture()
    if not cap.open(rtsp_url, cv2.CAP_FFMPEG):
        if log_callback:
            log_callback(f"❌ Не вдалося відкрити RTSP потік: {rtsp_url}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 120:
        fps = 20

    segment_frames = int(segment_length_sec * fps)
    video_name_base = f"{video_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    segment_dir = os.path.join(output_folder, video_name_base)
    full_video_path = os.path.join(segment_dir, f"{video_name_base}.avi")
    os.makedirs(segment_dir, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_writer = cv2.VideoWriter(full_video_path, fourcc, fps, (width, height))

    buffer = []
    segment_idx = 1
    line_y = height // 4
    all_results = []

    if log_callback:
        msg = f"⏺ Безперервний запис RTSP..." if duration == 0 else f"⏺ Запис RTSP потоку на {duration} сек..."
        log_callback(msg)

    start_time = time.time()

    while True:
        if stop_callback():
            if log_callback:
                log_callback("🛑 Запис RTSP перервано.")
            break

        if duration > 0 and (time.time() - start_time >= duration):
            break

        ret, frame = cap.read()
        if not ret:
            if log_callback:
                log_callback("⚠️ Не вдалося прочитати кадр з RTSP")
            break

        video_writer.write(frame)
        buffer.append(frame)

        if len(buffer) == segment_frames:
            if log_callback:
                log_callback(f"🧪 Обробка сегмента {segment_idx}")
            stitched_img = build_stitched_image(buffer, line_y)
            class_counts = detect_and_save(model_path, stitched_img, segment_dir, video_name_base + ".avi", segment_idx)
            all_results.append((segment_idx, class_counts))
            buffer.clear()
            segment_idx += 1

    if buffer:
        if log_callback:
            log_callback(f"🧪 Обробка останнього сегмента {segment_idx}")
        stitched_img = build_stitched_image(buffer, line_y)
        class_counts = detect_and_save(model_path, stitched_img, segment_dir, video_name_base + ".avi", segment_idx)
        all_results.append((segment_idx, class_counts))

    cap.release()
    video_writer.release()

    if log_callback:
        log_callback(f"✅ RTSP запис завершено: {full_video_path}")

    return all_results
