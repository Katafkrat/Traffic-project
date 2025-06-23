import sys
import time
import traceback
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QFileDialog, QVBoxLayout, QSpinBox, QLineEdit, QMessageBox,
    QTextEdit, QComboBox, QSizePolicy
)
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from processor.traffic_processor import TrafficProcessor
from config_manager import load_config, save_config


def run_ui():
    app = QApplication(sys.argv)
    window = TrafficApp()
    window.show()
    sys.exit(app.exec_())


class Worker(QObject):
    finished = pyqtSignal()
    log = pyqtSignal(str)
    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, processor):
        super().__init__()
        self.processor = processor

    def run(self):
        try:
            summary = self.processor.process()
            self.result.emit(summary)
        except Exception:
            error_text = traceback.format_exc()
            self.error.emit(error_text)
        finally:
            self.finished.emit()


class TrafficApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Traffic Detection UI')
        self.setMinimumWidth(500)
        self.config = load_config()
        self.stop_requested = False
        self.thread = None
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("🔌 Джерело відео:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Файл", "RTSP", "Екран"])
        self.source_combo.setCurrentText(self.config.get("source", "Файл"))
        self.source_combo.currentTextChanged.connect(self.on_source_change)
        layout.addWidget(self.source_combo)

        self.video_path = QLineEdit(self.config.get("video_path", ""))
        self.video_path_label = QLabel("🎥 Відеофайл:")
        self.video_btn = QPushButton("Обрати відео")
        self.video_btn.clicked.connect(self.select_video)
        layout.addWidget(self.video_path_label)
        layout.addWidget(self.video_path)
        layout.addWidget(self.video_btn)

        self.rtsp_url = QLineEdit(self.config.get("rtsp_url", ""))
        self.rtsp_label = QLabel("🌐 RTSP URL:")
        layout.addWidget(self.rtsp_label)
        layout.addWidget(self.rtsp_url)

        self.rtsp_username = QLineEdit(self.config.get("rtsp_username", ""))
        self.rtsp_username_label = QLabel("👤 Логін RTSP:")
        layout.addWidget(self.rtsp_username_label)
        layout.addWidget(self.rtsp_username)

        self.rtsp_password = QLineEdit(self.config.get("rtsp_password", ""))
        self.rtsp_password.setEchoMode(QLineEdit.Password)
        self.rtsp_password_label = QLabel("🔑 Пароль RTSP:")
        layout.addWidget(self.rtsp_password_label)
        layout.addWidget(self.rtsp_password)

        self.rtsp_duration = QSpinBox()
        self.rtsp_duration.setValue(self.config.get("rtsp_duration_sec", 30))
        self.rtsp_duration.setMinimum(0)
        self.rtsp_duration.setMaximum(3600)
        self.rtsp_duration_label = QLabel("🕒 Тривалість запису RTSP (сек):")
        layout.addWidget(self.rtsp_duration_label)
        layout.addWidget(self.rtsp_duration)

        self.screen_duration = QSpinBox()
        self.screen_duration.setValue(self.config.get("screen_duration_sec", 15))
        self.screen_duration.setMinimum(0)
        self.screen_duration.setMaximum(3600)
        self.screen_duration_label = QLabel("🖥️ Тривалість запису екрану (сек):")
        layout.addWidget(self.screen_duration_label)
        layout.addWidget(self.screen_duration)

        self.model_path = QLineEdit(self.config.get("yolo_model_path", ""))
        layout.addWidget(QLabel("🧠 Модель YOLO:"))
        layout.addWidget(self.model_path)
        model_btn = QPushButton("Обрати модель")
        model_btn.clicked.connect(self.select_model)
        layout.addWidget(model_btn)

        self.output_path = QLineEdit(self.config.get("output_folder", ""))
        layout.addWidget(QLabel("📂 Вихідна папка:"))
        layout.addWidget(self.output_path)
        output_btn = QPushButton("Обрати папку")
        output_btn.clicked.connect(self.select_output)
        layout.addWidget(output_btn)

        layout.addWidget(QLabel("⏱ Довжина сегмента (сек):"))
        self.segment_spin = QSpinBox()
        self.segment_spin.setValue(self.config.get("segment_length_sec", 30))
        self.segment_spin.setMinimum(5)
        layout.addWidget(self.segment_spin)

        self.run_btn = QPushButton("▶ Старт обробки")
        self.run_btn.clicked.connect(self.run_processing)
        layout.addWidget(self.run_btn)

        self.stop_btn = QPushButton("⛔ Зупинити")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
        layout.addWidget(self.stop_btn)

        self.status = QLabel("🟢 Готово до роботи")
        layout.addWidget(self.status)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.log_box, stretch=1)

        self.setLayout(layout)
        self.on_source_change(self.source_combo.currentText())

    def on_source_change(self, source):
        is_file = source == "Файл"
        is_rtsp = source == "RTSP"
        is_screen = source == "Екран"

        self.video_path.setVisible(is_file)
        self.video_path_label.setVisible(is_file)
        self.video_btn.setVisible(is_file)

        self.rtsp_url.setVisible(is_rtsp)
        self.rtsp_label.setVisible(is_rtsp)
        self.rtsp_duration.setVisible(is_rtsp)
        self.rtsp_duration_label.setVisible(is_rtsp)
        self.rtsp_username.setVisible(is_rtsp)
        self.rtsp_username_label.setVisible(is_rtsp)
        self.rtsp_password.setVisible(is_rtsp)
        self.rtsp_password_label.setVisible(is_rtsp)

        self.screen_duration.setVisible(is_screen)
        self.screen_duration_label.setVisible(is_screen)

        
        if not self.isMaximized():
            self.adjustSize()

    def select_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Обрати відео", "", "Відео (*.mp4 *.avi *.mkv)")
        if path:
            self.video_path.setText(path)

    def select_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "Обрати модель", "", "*.onnx *.pt")
        if path:
            self.model_path.setText(path)

    def select_output(self):
        path = QFileDialog.getExistingDirectory(self, "Обрати папку")
        if path:
            self.output_path.setText(path)

    def append_log(self, message):
        self.log_box.append(message)
        QApplication.processEvents()

    def stop_processing(self):
        self.stop_requested = True
        self.append_log("⛔ Запит на зупинку...")
        self.status.setText("🛑 Зупиняється...")

    def run_processing(self):
        source = self.source_combo.currentText()
        model = self.model_path.text().strip()
        output = self.output_path.text().strip()
        segment = self.segment_spin.value()
        screen_duration = self.screen_duration.value()
        rtsp_duration = self.rtsp_duration.value()

        if source == "Файл":
            input_path = self.video_path.text().strip()
        elif source == "RTSP":
            url = self.rtsp_url.text().strip()
            username = self.rtsp_username.text().strip()
            password = self.rtsp_password.text().strip()

            if not url:
                QMessageBox.warning(self, "⚠️ Помилка", "Введіть RTSP URL!")
                return

            if username and password and "://" in url:
                protocol, rest = url.split("://", 1)
                input_path = f"{protocol}://{username}:{password}@{rest}"
            else:
                input_path = url
        elif source == "screen":
            input_path = "screen"
        else:
            input_path = ""

        if source == "file" and not input_path:
            QMessageBox.warning(self, "⚠️ Помилка", "Обирайте відеофайл!")
            return
        if not model:
            QMessageBox.warning(self, "⚠️ Помилка", "Обирайте модель YOLO!")
            return
        if not output:
            QMessageBox.warning(self, "⚠️ Помилка", "Обирайте вихідну папку!")
            return

        self.status.setText("🔄 Обробка...")
        self.log_box.clear()
        self.stop_requested = False
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        QApplication.processEvents()

        self.config.update({
            "video_path": self.video_path.text(),
            "rtsp_url": self.rtsp_url.text(),
            "yolo_model_path": model,
            "output_folder": output,
            "segment_length_sec": segment,
            "screen_duration_sec": screen_duration,
            "rtsp_duration_sec": rtsp_duration,
            "source": source
        })
        save_config(self.config)

        duration = screen_duration if source == "screen" else rtsp_duration

        self.processor = TrafficProcessor(
            video_path=input_path,
            output_folder=output,
            yolo_model_path=model,
            segment_length_sec=segment,
            screen_duration_sec=duration,
            source=source,
            log_callback=self.append_log,
            stop_callback=lambda: self.stop_requested
        )

        self.thread = QThread()
        self.worker = Worker(self.processor)
        self.worker.moveToThread(self.thread)

        self.worker.result.connect(self.on_processing_result)
        self.worker.log.connect(self.append_log)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def on_processing_result(self, summary):
        result_lines = []
        for segment_idx, class_counts in summary:
            parts = [f"{cls}: {cnt}" for cls, cnt in class_counts.items()]
            line = f"📦 Сегмент {segment_idx}: " + ", ".join(parts)
            result_lines.append(line)

        self.log_box.append("\n--- Результати ---\n")
        self.log_box.append("\n".join(result_lines))
        self.status.setText("✅ Завершено")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def on_error(self, error_text):
        self.status.setText("❌ Помилка")
        self.log_box.append(error_text)
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- Error at {time.ctime()} ---\n{error_text}\n")
        QMessageBox.critical(self, "❌ Помилка", "Помилка під час обробки.")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
