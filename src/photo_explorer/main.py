import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QFileDialog,
    QListWidget,
    QHBoxLayout,
    QMessageBox,
)

from photo_explorer import __version__
from photo_explorer import scanner, catalog


MAX_DISPLAYED = 1000
MAX_REPORTED_PROBLEMS = 10


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Explorer")
        self.setMinimumSize(500, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        version_label = QLabel(f"Version: {__version__}")
        message_label = QLabel("Application foundation is running")

        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("No folder selected")
        self.select_btn = QPushButton("Select Photo Folder...")
        self.select_btn.clicked.connect(self.select_folder)
        self.scan_btn = QPushButton("Scan Selected Folder")
        self.scan_btn.clicked.connect(self.scan_folder)
        self.scan_btn.setEnabled(False)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.select_btn)
        folder_layout.addWidget(self.scan_btn)

        # Results
        self.count_label = QLabel("Images found: 0")
        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(150)

        layout.addWidget(version_label)
        layout.addWidget(message_label)
        layout.addLayout(folder_layout)
        layout.addWidget(self.count_label)
        layout.addWidget(self.list_widget)

        self.selected_folder = None

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Photo Folder", str(Path.home()))
        if folder:
            self.selected_folder = Path(folder).resolve()
            self.folder_label.setText(str(self.selected_folder))
            self.scan_btn.setEnabled(True)
            self.list_widget.clear()
            self.count_label.setText("Images found: 0")

    def scan_folder(self):
        if not self.selected_folder or not self.selected_folder.exists():
            QMessageBox.warning(self, "Error", "Please select a valid folder")
            return

        outcome = scanner.scan_folder(self.selected_folder, recursive=True)

        stats = None
        try:
            with catalog.connect() as conn:
                stats = catalog.ingest_files(conn, outcome.files, scanner.get_file_metadata)
        except (sqlite3.Error, catalog.SchemaVersionError, OSError) as e:
            self.list_widget.clear()
            self.count_label.setText("Cataloging failed; see error dialog")
            QMessageBox.critical(self, "Scan Error", f"Cataloging failed: {e}")
            return

        # Show discovered files
        self.list_widget.clear()
        for img in outcome.files[:MAX_DISPLAYED]:
            self.list_widget.addItem(str(img))
        if len(outcome.files) > MAX_DISPLAYED:
            self.list_widget.addItem(f"... and {len(outcome.files) - MAX_DISPLAYED} more")

        cataloged = stats.inserted + stats.updated
        self.count_label.setText(
            f"Cataloged: {cataloged} (new: {stats.inserted}, "
            f"updated: {stats.updated}, failed: {stats.failed})"
        )

        problems = outcome.errors + stats.errors
        if problems:
            shown = "\n".join(problems[:MAX_REPORTED_PROBLEMS])
            extra = (
                ""
                if len(problems) <= MAX_REPORTED_PROBLEMS
                else f"\n... and {len(problems) - MAX_REPORTED_PROBLEMS} more"
            )
            QMessageBox.warning(
                self,
                "Scan completed with problems",
                f"{len(problems)} problem(s) encountered:\n{shown}{extra}",
            )


def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
