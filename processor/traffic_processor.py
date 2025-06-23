from .utils.video_processor import process_video_file
from .utils.screen_recorder import record_and_process_screen
from .utils.rtsp_recorder import record_and_process_rtsp


class TrafficProcessor:
    def __init__(
        self,
        video_path,
        output_folder,
        yolo_model_path,
        segment_length_sec,
        screen_duration_sec=None,
        source="file",
        log_callback=None,
        stop_callback=None
    ):
        self.video_path = video_path
        self.output_folder = output_folder
        self.yolo_model_path = yolo_model_path
        self.segment_length_sec = segment_length_sec
        self.screen_duration_sec = screen_duration_sec
        self.source = source
        self.log_callback = log_callback
        self.stop_callback = stop_callback or (lambda: False)

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def process(self):
        if self.source == "screen":
            return self.process_screen()
        elif self.source == "rtsp":
            return self.process_rtsp()
        else:  # "file" or others
            return self.process_video(self.video_path)

    def process_screen(self):
        results = record_and_process_screen(
            output_folder=self.output_folder,
            duration=self.screen_duration_sec,
            segment_length_sec=self.segment_length_sec,
            model_path=self.yolo_model_path,
            log_callback=self.log,
            stop_callback=self.stop_callback
        )
        return results

    def process_rtsp(self):
        results = record_and_process_rtsp(
            rtsp_url=self.video_path,
            output_folder=self.output_folder,
            duration=self.screen_duration_sec,
            segment_length_sec=self.segment_length_sec,
            model_path=self.yolo_model_path,
            log_callback=self.log,
            stop_callback=self.stop_callback
        )
        return results

    def process_video(self, video_path):
        return process_video_file(
            video_path=video_path,
            output_folder=self.output_folder,
            model_path=self.yolo_model_path,
            segment_length_sec=self.segment_length_sec,
            log_callback=self.log,
            stop_callback=self.stop_callback
        )
