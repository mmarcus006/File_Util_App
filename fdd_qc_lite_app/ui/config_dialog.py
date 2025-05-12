import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QFileDialog, QLabel, QMessageBox
)
from PyQt6.QtCore import QSettings, Qt
import os

# Define settings keys
SETTINGS_PROJECT_ROOT_DIR = "paths/project_root_dir"
SETTINGS_INPUT_SECTIONS_DIR = "paths/input_sections_dir"
SETTINGS_SOURCE_PDFS_DIR = "paths/source_pdfs_dir"
SETTINGS_APPROVED_FILES_DIR = "paths/approved_files_dir"
SETTINGS_DATABASE_PATH = "paths/database_path"

DEFAULT_DATABASE_NAME = "fdd_qc_lite.db"
# User-specified default PDF source path
DEFAULT_PDF_SOURCE_PATH_FALLBACK = os.path.normpath("C:/projects/File_Util_App/processed_fdds")

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Configuration")
        self.setMinimumWidth(550)

        self.settings = QSettings("MyCompany", "FDD_QC_Lite")

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Project Root Directory
        self.project_root_dir_edit = QLineEdit()
        self.project_root_dir_edit.setPlaceholderText("Optional: Select a root for automatic path suggestions")
        self.project_root_dir_edit.textChanged.connect(self._update_paths_from_project_root)
        self.project_root_dir_button = QPushButton("Browse...")
        self.project_root_dir_button.clicked.connect(lambda: self.browse_directory(self.project_root_dir_edit, "Select Project Root Directory", is_project_root=True))
        form_layout.addRow(QLabel("Project Root Directory:"), self.project_root_dir_edit)
        form_layout.addRow("", self.project_root_dir_button)
        form_layout.addRow(QLabel("--- Individual paths (can be set independently or derived from root) ---"))

        # Input Sections Directory
        self.input_sections_dir_edit = QLineEdit()
        self.input_sections_dir_button = QPushButton("Browse...")
        self.input_sections_dir_button.clicked.connect(lambda: self.browse_directory(self.input_sections_dir_edit, "Select Input Sections Directory"))
        form_layout.addRow(QLabel("Input Sections Directory:"), self.input_sections_dir_edit)
        form_layout.addRow("", self.input_sections_dir_button)

        # Source PDFs Directory
        self.source_pdfs_dir_edit = QLineEdit()
        self.source_pdfs_dir_button = QPushButton("Browse...")
        self.source_pdfs_dir_button.clicked.connect(lambda: self.browse_directory(self.source_pdfs_dir_edit, "Select Source PDFs Directory"))
        form_layout.addRow(QLabel("Source PDFs Directory:"), self.source_pdfs_dir_edit)
        form_layout.addRow("", self.source_pdfs_dir_button)

        # Approved Files Output Directory
        self.approved_files_dir_edit = QLineEdit()
        self.approved_files_dir_button = QPushButton("Browse...")
        self.approved_files_dir_button.clicked.connect(lambda: self.browse_directory(self.approved_files_dir_edit, "Select Approved Files Output Directory"))
        form_layout.addRow(QLabel("Approved Files Directory:"), self.approved_files_dir_edit)
        form_layout.addRow("", self.approved_files_dir_button)
        
        # Database File Path
        self.database_path_edit = QLineEdit()
        self.database_path_button = QPushButton("Browse/Set Location...")
        self.database_path_button.clicked.connect(self.browse_database_file)
        form_layout.addRow(QLabel("Database File Location:"), self.database_path_edit)
        form_layout.addRow("", self.database_path_button)

        main_layout.addLayout(form_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        self._loading_settings = False
        self.load_settings()

    def browse_directory(self, line_edit_widget, caption, is_project_root=False):
        current_path = line_edit_widget.text() or os.getcwd()
        directory = QFileDialog.getExistingDirectory(self, caption, current_path)
        if directory:
            norm_dir = os.path.normpath(directory)
            line_edit_widget.setText(norm_dir)

    def _update_paths_from_project_root(self, project_root_path: str):
        if self._loading_settings:
            return

        project_root_path = os.path.normpath(project_root_path.strip())

        if project_root_path and os.path.isdir(project_root_path):
            self.input_sections_dir_edit.setText(os.path.join(project_root_path, "output", "sections"))
            self.source_pdfs_dir_edit.setText(os.path.join(project_root_path, "processed_fdds"))
            self.approved_files_dir_edit.setText(os.path.join(project_root_path, "approved_files"))
            self.database_path_edit.setText(os.path.join(project_root_path, "database", DEFAULT_DATABASE_NAME))
            self.input_sections_dir_edit.setProperty("derived", True)
            self.source_pdfs_dir_edit.setProperty("derived", True)
            self.approved_files_dir_edit.setProperty("derived", True)
            self.database_path_edit.setProperty("derived", True)
        else:
            self.input_sections_dir_edit.setProperty("derived", False)
            self.source_pdfs_dir_edit.setProperty("derived", False)
            self.approved_files_dir_edit.setProperty("derived", False)
            self.database_path_edit.setProperty("derived", False)
            self._apply_placeholders_and_defaults(project_root_set=False)

    def browse_database_file(self):
        default_dir = os.path.dirname(self.database_path_edit.text()) if self.database_path_edit.text() else os.getcwd()
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Set Database File Location", 
            os.path.join(default_dir, DEFAULT_DATABASE_NAME),
            "SQLite Database Files (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        if file_path:
            self.database_path_edit.setText(os.path.normpath(file_path))
            self.database_path_edit.setProperty("derived", False)

    def load_settings(self):
        self._loading_settings = True
        
        project_root = self.settings.value(SETTINGS_PROJECT_ROOT_DIR, "")
        self.project_root_dir_edit.setText(project_root)
        
        self.input_sections_dir_edit.setText(self.settings.value(SETTINGS_INPUT_SECTIONS_DIR, ""))
        self.input_sections_dir_edit.setProperty("derived", False)

        self.source_pdfs_dir_edit.setText(self.settings.value(SETTINGS_SOURCE_PDFS_DIR, ""))
        self.source_pdfs_dir_edit.setProperty("derived", False)
        
        self.approved_files_dir_edit.setText(self.settings.value(SETTINGS_APPROVED_FILES_DIR, ""))
        self.approved_files_dir_edit.setProperty("derived", False)
        
        self.database_path_edit.setText(self.settings.value(SETTINGS_DATABASE_PATH, ""))
        self.database_path_edit.setProperty("derived", False)

        if project_root and os.path.isdir(project_root):
            self.input_sections_dir_edit.setText(os.path.join(project_root, "output", "sections"))
            self.source_pdfs_dir_edit.setText(os.path.join(project_root, "processed_fdds"))
            self.approved_files_dir_edit.setText(os.path.join(project_root, "approved_files"))
            self.database_path_edit.setText(os.path.join(project_root, "database", DEFAULT_DATABASE_NAME))
            self.input_sections_dir_edit.setProperty("derived", True)
            self.source_pdfs_dir_edit.setProperty("derived", True)
            self.approved_files_dir_edit.setProperty("derived", True)
            self.database_path_edit.setProperty("derived", True)
        
        self._apply_placeholders_and_defaults(project_root_set=bool(project_root and os.path.isdir(project_root)))
        self._loading_settings = False
        if self.project_root_dir_edit.text() and os.path.isdir(self.project_root_dir_edit.text()):
             self._update_paths_from_project_root(self.project_root_dir_edit.text())

    def _apply_placeholders_and_defaults(self, project_root_set: bool):
        if not self.input_sections_dir_edit.text():
            self.input_sections_dir_edit.setPlaceholderText("e.g., .../output/sections/")
        
        if not self.source_pdfs_dir_edit.text():
            if not project_root_set or not self.source_pdfs_dir_edit.property("derived"):
                 self.source_pdfs_dir_edit.setText(DEFAULT_PDF_SOURCE_PATH_FALLBACK)
                 self.source_pdfs_dir_edit.setProperty("derived", False)
            else:
                self.source_pdfs_dir_edit.setPlaceholderText("e.g., .../processed_fdds/")

        if not self.approved_files_dir_edit.text():
            self.approved_files_dir_edit.setPlaceholderText("e.g., .../approved_files/")
        
        if not self.database_path_edit.text():
            default_db_path_in_cwd = os.path.join(os.getcwd(), DEFAULT_DATABASE_NAME)
            self.database_path_edit.setText(default_db_path_in_cwd)
            current_root = self.project_root_dir_edit.text()
            if current_root and os.path.isdir(current_root):
                derived_db_path = os.path.join(current_root, "database", DEFAULT_DATABASE_NAME)
                if os.path.normpath(default_db_path_in_cwd) != os.path.normpath(derived_db_path):
                    self.database_path_edit.setProperty("derived", False)
            else:
                self.database_path_edit.setProperty("derived", False)

    def save_settings(self):
        project_root = self.project_root_dir_edit.text().strip()
        input_sections = self.input_sections_dir_edit.text().strip()
        source_pdfs = self.source_pdfs_dir_edit.text().strip()
        approved_files = self.approved_files_dir_edit.text().strip()
        db_path = self.database_path_edit.text().strip()

        if not all([input_sections, source_pdfs, approved_files, db_path]):
            QMessageBox.warning(self, "Missing Information", "All individual paths (Input Sections, Source PDFs, Approved Files, Database) must be configured, even if a project root is set.")
            return
        
        if not os.path.isdir(input_sections):
            QMessageBox.warning(self, "Invalid Path", f"Input Sections Directory is not a valid directory: {input_sections}")
            return
        if not os.path.isdir(source_pdfs):
            QMessageBox.warning(self, "Invalid Path", f"Source PDFs Directory is not a valid directory: {source_pdfs}")
            return
        
        approved_parent = os.path.dirname(approved_files)
        if not approved_parent:
            approved_parent = os.getcwd()
        if not os.path.isdir(approved_parent):
             QMessageBox.warning(self, "Invalid Path", f"Parent directory for Approved Files ('{approved_files}') does not exist: {approved_parent}")
             return

        db_parent = os.path.dirname(db_path)
        if not db_parent:
            db_parent = os.getcwd()
        if not os.path.isdir(db_parent):
            QMessageBox.warning(self, "Invalid Path", f"Parent directory for Database file ('{db_path}') does not exist: {db_parent}")
            return

        self.settings.setValue(SETTINGS_PROJECT_ROOT_DIR, project_root)
        self.settings.setValue(SETTINGS_INPUT_SECTIONS_DIR, input_sections)
        self.settings.setValue(SETTINGS_SOURCE_PDFS_DIR, source_pdfs)
        self.settings.setValue(SETTINGS_APPROVED_FILES_DIR, approved_files)
        self.settings.setValue(SETTINGS_DATABASE_PATH, db_path)
        
        QMessageBox.information(self, "Settings Saved", "Configuration has been saved successfully.")
        self.accept()

    @staticmethod
    def get_all_settings() -> dict:
        settings = QSettings("MyCompany", "FDD_QC_Lite")
        default_db_path_in_cwd = os.path.join(os.getcwd(), DEFAULT_DATABASE_NAME)
        
        project_root = settings.value(SETTINGS_PROJECT_ROOT_DIR, "")
        
        input_sections = settings.value(SETTINGS_INPUT_SECTIONS_DIR, "")
        if not input_sections and project_root and os.path.isdir(project_root):
            input_sections = os.path.join(project_root, "output", "sections")

        source_pdfs = settings.value(SETTINGS_SOURCE_PDFS_DIR, "")
        if not source_pdfs:
            if project_root and os.path.isdir(project_root):
                source_pdfs = os.path.join(project_root, "processed_fdds")
            else:
                source_pdfs = DEFAULT_PDF_SOURCE_PATH_FALLBACK
        
        approved_files = settings.value(SETTINGS_APPROVED_FILES_DIR, "")
        if not approved_files and project_root and os.path.isdir(project_root):
            approved_files = os.path.join(project_root, "approved_files")
            
        db_path = settings.value(SETTINGS_DATABASE_PATH, "")
        if not db_path:
            if project_root and os.path.isdir(project_root):
                db_path = os.path.join(project_root, "database", DEFAULT_DATABASE_NAME)
            else:
                db_path = default_db_path_in_cwd

        return {
            SETTINGS_PROJECT_ROOT_DIR: project_root,
            SETTINGS_INPUT_SECTIONS_DIR: os.path.normpath(input_sections) if input_sections else "",
            SETTINGS_SOURCE_PDFS_DIR: os.path.normpath(source_pdfs) if source_pdfs else "",
            SETTINGS_APPROVED_FILES_DIR: os.path.normpath(approved_files) if approved_files else "",
            SETTINGS_DATABASE_PATH: os.path.normpath(db_path) if db_path else ""
        }

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setOrganizationName("MyCompany")
    QApplication.setApplicationName("FDD_QC_Lite")
    
    dialog = ConfigDialog()
    if dialog.exec():
        print("Configuration saved.")
        print("Current settings from get_all_settings():")
        for key, value in ConfigDialog.get_all_settings().items():
            print(f"  {key}: {value}")
    else:
        print("Configuration cancelled.")
    if not QApplication.instance().hasMainWindow():
        sys.exit(app.exec()) 