from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

from photo_explorer import __version__


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Explorer")
        self.setFixedSize(400, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        version_label = QLabel(f"Version: {__version__}")
        message_label = QLabel("Application foundation is running")

        layout.addWidget(version_label)
        layout.addWidget(message_label)


def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
