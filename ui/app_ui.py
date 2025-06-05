import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QFileDialog, QVBoxLayout, QSpinBox, QLineEdit, QMessageBox, QTextEdit
)
from processor.traffic_processor import TrafficProcessor
from config_manager import load_config, save_config


def run_ui():
    app = QApplication(sys.argv)
    window = TrafficApp()
    window.show()
    sys.exit(app.exec_())


class TrafficApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Traffic Detection UI')
        self.setGeometry(100, 100, 500, 400)
        self.config = load_config()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.video_path = QLineEdit(self.config.get("video_path", ""))
        layout.addWidget(QLabel("🎥 Відео файл:"))
        layout.addWidget(self.video_path)
        video_btn = QPushButton("Обрати відео")
        video_btn.clicked.connect(self.select_video)
        layout.addWidget(video_btn)

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

        self.status = QLabel("🟢 Готово до роботи")
        layout.addWidget(self.status)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

        self.setLayout(layout)

    def select_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Обрати відео", "", "Відео (*.mp4 *.avi *.mkv)")
        if path:
            self.video_path.setText(path)

    def select_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "Обрати модель", "", "*.pt")
        if path:
            self.model_path.setText(path)

    def select_output(self):
        path = QFileDialog.getExistingDirectory(self, "Обрати папку")
        if path:
            self.output_path.setText(path)

    def run_processing(self):
        video = self.video_path.text()
        model = self.model_path.text()
        output = self.output_path.text()
        segment = self.segment_spin.value()

        if not all([video, model, output]):
            QMessageBox.warning(self, "⚠️ Помилка", "Заповніть усі поля!")
            return

        self.status.setText("🔄 Обробка...")
        QApplication.processEvents()

        self.config.update({
            "video_path": video,
            "yolo_model_path": model,
            "output_folder": output,
            "segment_length_sec": segment
        })
        save_config(self.config)

        try:
            start = time.time()
            processor = TrafficProcessor(**self.config)
            summary = processor.process()

            result_lines = []
            for segment_idx, class_counts in summary:
                parts = [f"{cls}: {cnt}" for cls, cnt in class_counts.items()]
                line = f"📦 Сегмент {segment_idx}: " + ", ".join(parts)
                result_lines.append(line)

            self.log_box.setText("\n".join(result_lines))
            end = time.time()
            self.status.setText(f"✅ Завершено за {end - start:.1f} с")
        except Exception as e:
            self.status.setText("❌ Помилка")
            QMessageBox.critical(self, "❌ Помилка", str(e))
