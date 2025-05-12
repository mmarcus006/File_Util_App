import sys
import os
from typing import Dict, Optional, List, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton, QLabel,
    QFormLayout, QLineEdit, QMessageBox, QScrollArea, QSplitter,
    QStatusBar, QToolBar, QFileDialog
)
from PyQt6.QtGui import QAction, QIcon, QColor, QPalette
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument

# Application specific imports
from .config_dialog import ConfigDialog, SETTINGS_INPUT_SECTIONS_DIR, \
    SETTINGS_SOURCE_PDFS_DIR, SETTINGS_APPROVED_FILES_DIR, SETTINGS_DATABASE_PATH
from database import db_handler
from database.models import Item1Detail, Item1Data # For field names & type checking
from data_processing import file_handler, json_parser

class MainWindow(QMainWindow):
    # Define the order and labels for Item 1 data fields in the form
    # (db_field_name, display_label)
    ITEM1_DB_FIELD_TO_LABEL = {
        'item1_brand_name': 'Brand Name:',
        'item1_legal_name': 'Legal Name:',
        'item1_parent_company': 'Parent Company:',
        'item1_address': 'Address:',
        'item1_city': 'City:',
        'item1_state': 'State:',
        'item1_zip_code': 'Zip Code:',
        'item1_website': 'Website:',
        'item1_phone': 'Phone:',
        'item1_email': 'Email:',
        'item1_founded_year': 'Founded Year:',
        'item1_franchising_since': 'Franchising Since:',
        'item1_business_description': 'Business Description:',
        'item1_fdd_issue_date': 'FDD Issue Date:',
        'item1_fdd_amendment_date': 'FDD Amendment Date:',
        # Read-only fields displayed for info
        'uuid': 'UUID:',
        'review_status': 'Review Status:',
        'original_json_path': 'Original JSON Path:',
        'last_modified_timestamp': 'Last Modified:'
    }
    # Fields that will have QLineEdit editors
    EDITABLE_DB_FIELDS = [
        'item1_brand_name', 'item1_legal_name', 'item1_parent_company', 
        'item1_address', 'item1_city', 'item1_state', 'item1_zip_code',
        'item1_website', 'item1_phone', 'item1_email', 'item1_founded_year',
        'item1_franchising_since', 'item1_business_description', 
        'item1_fdd_issue_date', 'item1_fdd_amendment_date'
    ]


    def __init__(self):
        super().__init__()
        self.current_selected_uuid: Optional[str] = None
        self.settings: Dict[str, Any] = {}
        self.data_editors: Dict[str, QLineEdit] = {} # Stores QLineEdit widgets for data fields

        self.setWindowTitle("FDD QC Lite - Item 1 Processor")
        self.setGeometry(100, 100, 1200, 800)

        # Setup main layout structure first
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # Main layout for the central widget will be QVBoxLayout
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create menu, actions, and toolbar (they don't depend on log_text_edit)
        self._create_menu_bar()
        self._create_actions() 
        self._create_toolbar()
        
        # Create the splitter and its panes
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._create_record_list_pane() # self.record_list_widget
        left_pane_widget = QWidget()
        left_layout = QVBoxLayout(left_pane_widget)
        left_layout.addWidget(QLabel("Processed Records (UUID - Status):"))
        left_layout.addWidget(self.record_list_widget)
        splitter.addWidget(left_pane_widget)

        self._create_data_display_pane() # self.data_display_scroll_area
        splitter.addWidget(self.data_display_scroll_area)

        self._create_pdf_viewer_pane() # self.pdf_view
        splitter.addWidget(self.pdf_view)
        
        splitter.setSizes([250, 400, 550]) # Initial sizes for panes

        # Add splitter to the main QVBoxLayout
        self.main_layout.addWidget(splitter)
        
        # Now create action buttons and log area, which initializes self.log_text_edit and self.status_bar
        self._create_action_buttons_and_log_area() 

        # Load settings and initialize DB *after* log/status UI elements are created
        self._load_app_settings()
        self._init_db()
        
        self._connect_signals()
        self._load_record_list() # Initial load of records

        self._log_message("Application started. Configure paths via File > Configure if needed.")

    def _load_app_settings(self):
        self.settings = ConfigDialog.get_all_settings()
        # Normalize paths right after loading
        for key, value in self.settings.items():
            if isinstance(value, str) and value: # Check if it's a non-empty string
                 if "dir" in key or "path" in key: # Heuristic for path keys
                    self.settings[key] = os.path.normpath(value)
        # self._log_message(f"Loaded settings: {self.settings}")


    def _init_db(self):
        db_path = self.settings.get(SETTINGS_DATABASE_PATH)
        if not db_path:
            self._log_message("Database path not configured. Please configure via File > Configure.", is_error=True)
            QMessageBox.critical(self, "Database Error", "Database path not configured. Please set it in the configuration.")
            # Optionally, disable features until DB is configured
            return 
        try:
            db_handler.init_db(db_path)
            self._log_message(f"Database initialized at {db_path}")
        except Exception as e:
            self._log_message(f"Error initializing database: {e}", is_error=True)
            QMessageBox.critical(self, "Database Error", f"Could not initialize database at {db_path}:\n{e}")

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        self.process_dir_action = QAction("&Process Directory...", self)
        file_menu.addAction(self.process_dir_action)
        
        self.configure_action = QAction("&Configure Paths...", self)
        file_menu.addAction(self.configure_action)

        file_menu.addSeparator()
        self.exit_action = QAction("&Exit", self)
        file_menu.addAction(self.exit_action)
        
    def _create_actions(self):
        # Placeholder if more actions are needed, menu actions created in _create_menu_bar for now
        pass

    def _create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24,24)) # Example icon size
        self.addToolBar(toolbar)
        toolbar.addAction(self.process_dir_action)
        toolbar.addAction(self.configure_action)
        # Add more actions with icons if desired
        # e.g. refresh_action = QAction(QIcon("path/to/refresh_icon.png"), "Refresh List", self)
        # toolbar.addAction(refresh_action)


    def _create_record_list_pane(self):
        self.record_list_widget = QListWidget()
        self.record_list_widget.setMinimumWidth(200)

    def _create_data_display_pane(self):
        self.data_display_scroll_area = QScrollArea()
        self.data_display_scroll_area.setWidgetResizable(True)
        
        self.data_form_widget = QWidget()
        self.data_form_layout = QFormLayout(self.data_form_widget)
        self.data_form_layout.setContentsMargins(10, 10, 10, 10)
        self.data_form_layout.setSpacing(10)

        # Create QLineEdit widgets for each editable field
        for db_field, label_text in self.ITEM1_DB_FIELD_TO_LABEL.items():
            if db_field in self.EDITABLE_DB_FIELDS:
                editor = QLineEdit()
                editor.setObjectName(db_field) # For easier identification if needed
                self.data_editors[db_field] = editor
                self.data_form_layout.addRow(label_text, editor)
            else: # For read-only fields, use a QLabel for display
                display_label = QLabel("-") # Placeholder
                display_label.setObjectName(db_field + "_display")
                self.data_editors[db_field + "_display"] = display_label # Store label to update its text
                self.data_form_layout.addRow(label_text, display_label)


        self.data_display_scroll_area.setWidget(self.data_form_widget)

    def _create_pdf_viewer_pane(self):
        self.pdf_view = QPdfView()
        self.pdf_document = QPdfDocument(self) # Parent it to manage lifecycle
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)

    def _create_action_buttons_and_log_area(self):
        # Action buttons will be placed below the central splitter
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)

        action_buttons_layout = QHBoxLayout()
        self.save_changes_button = QPushButton("Save Changes")
        self.approve_button = QPushButton("Approve & Copy File")
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.save_changes_button)
        action_buttons_layout.addWidget(self.approve_button)
        action_buttons_layout.addStretch()
        
        bottom_layout.addLayout(action_buttons_layout)

        # Log Area
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMaximumHeight(150) # Limit log area height
        bottom_layout.addWidget(QLabel("Log Messages:"))
        bottom_layout.addWidget(self.log_text_edit)
        
        # Add bottom_widget to the main_layout (which is QVBoxLayout)
        self.main_layout.addWidget(bottom_widget)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _connect_signals(self):
        self.configure_action.triggered.connect(self._open_config_dialog)
        self.process_dir_action.triggered.connect(self._process_input_directory_triggered)
        self.exit_action.triggered.connect(self.close)

        self.record_list_widget.currentItemChanged.connect(self._display_selected_record)
        self.save_changes_button.clicked.connect(self._save_changes)
        self.approve_button.clicked.connect(self._approve_and_copy_file)

    def _log_message(self, message: str, is_error: bool = False, to_statusbar: bool = True):
        if is_error:
            if not hasattr(self, 'log_text_edit'): # Graceful degradation if called too early
                print(f"LOG (early): {message}")
                return
            self.log_text_edit.append(f"<font color='red'>ERROR: {message}</font>")
        else:
            if not hasattr(self, 'log_text_edit'): # Graceful degradation if called too early
                print(f"LOG (early): {message}")
                return
            self.log_text_edit.append(message)
        if to_statusbar:
            if not hasattr(self, 'status_bar'): # Graceful degradation
                print(f"STATUS (early): {message}")
                return
            self.status_bar.showMessage(message, 5000 if not is_error else 10000) # Longer for errors

    def _open_config_dialog(self):
        dialog = ConfigDialog(self)
        if dialog.exec():
            self._log_message("Configuration saved. Reloading settings and re-initializing database...")
            self._load_app_settings()
            self._init_db() # Re-initialize DB in case path changed
            self._load_record_list() # Refresh list as DB might have changed or new paths are relevant
        else:
            self._log_message("Configuration cancelled.")

    def _process_input_directory_triggered(self):
        input_dir = self.settings.get(SETTINGS_INPUT_SECTIONS_DIR)
        pdf_dir = self.settings.get(SETTINGS_SOURCE_PDFS_DIR)

        if not input_dir or not pdf_dir or not os.path.isdir(input_dir) or not os.path.isdir(pdf_dir):
            QMessageBox.warning(self, "Paths Not Configured", 
                                "Input sections directory or Source PDFs directory is not configured or invalid. Please check File > Configure.")
            self._log_message("Directory processing aborted: Paths not configured or invalid.", is_error=True)
            return
        
        self._log_message(f"Starting processing of directory: {input_dir}")
        try:
            with db_handler.get_db_session() as session:
                files_to_process, scan_errors = file_handler.scan_input_directory(input_dir, pdf_dir)
                for err in scan_errors:
                    self._log_message(f"Scan warning: {err}", is_error=True)

                if not files_to_process:
                    self._log_message("No new Item 1 JSON files found to process.")
                    return

                processed_count = 0
                error_count = 0
                for file_info in files_to_process:
                    uuid = file_info["uuid"]
                    json_path = file_info["json_path"]
                    pdf_path = file_info.get("pdf_path") # Might be None

                    self._log_message(f"Processing {json_path}...")
                    parsed_data, parse_error = json_parser.parse_item1_json_file(json_path)

                    if parse_error:
                        self._log_message(f"Failed to parse {json_path}: {parse_error}", is_error=True)
                        db_handler.log_processing_error(session, json_path, parse_error)
                        error_count += 1
                        continue
                    
                    if parsed_data:
                        # Pydantic model_dump() gets dict from the model
                        data_dict = parsed_data.model_dump() 
                        db_handler.add_item1_data(session, uuid, data_dict, json_path, pdf_path)
                        processed_count += 1
                
                session.commit() # Commit all changes from this batch
                self._log_message(f"Directory processing complete. Processed {processed_count} files. Encountered {error_count} errors during parsing/validation.")

        except Exception as e:
            self._log_message(f"Critical error during directory processing: {e}", is_error=True)
            QMessageBox.critical(self, "Processing Error", f"An unexpected error occurred: {e}")
        finally:
            self._load_record_list() # Refresh the list

    def _load_record_list(self):
        self.record_list_widget.clear()
        self.current_selected_uuid = None # Clear selection
        self._clear_data_form()
        self.pdf_document.load("") # Clear PDF view

        try:
            with db_handler.get_db_session() as session:
                records = db_handler.get_all_item1_records_summary(session)
                if not records:
                    self._log_message("No records found in the database.")
                    return
                
                for record in records:
                    item_text = f"{record['uuid']} - {record['status'].upper()}"
                    list_item = QListWidgetItem(item_text)
                    list_item.setData(Qt.ItemDataRole.UserRole, record['uuid']) # Store UUID with item
                    
                    # Basic color coding for status
                    if record['status'] == 'approved':
                        list_item.setForeground(QColor("green"))
                    elif record['status'] == 'error':
                        list_item.setForeground(QColor("red"))
                    elif record['status'] == 'pending':
                        list_item.setForeground(QColor("orange"))
                    self.record_list_widget.addItem(list_item)
                self._log_message(f"Loaded {len(records)} records.")
        except Exception as e:
            self._log_message(f"Error loading record list: {e}", is_error=True)
            QMessageBox.critical(self, "Database Error", f"Could not load records: {e}")

    def _clear_data_form(self):
        for field_name, editor in self.data_editors.items():
            if isinstance(editor, QLineEdit):
                editor.clear()
                editor.setReadOnly(True) # Default to read-only until a record is loaded
            elif isinstance(editor, QLabel): # For read-only display fields
                editor.setText("-")
        self.save_changes_button.setEnabled(False)
        self.approve_button.setEnabled(False)


    def _display_selected_record(self, current_item: QListWidgetItem, previous_item: Optional[QListWidgetItem] = None):
        if not current_item:
            self.current_selected_uuid = None
            self._clear_data_form()
            self.pdf_document.load("") # Clear PDF view
            return

        uuid = current_item.data(Qt.ItemDataRole.UserRole)
        self.current_selected_uuid = uuid
        self._log_message(f"Selected record UUID: {uuid}")

        try:
            with db_handler.get_db_session() as session:
                item_data_db = db_handler.get_item1_data_by_uuid(session, uuid)
                pdf_path_from_db = db_handler.get_pdf_path_by_uuid(session, uuid)

                if not item_data_db:
                    self._log_message(f"No data found in DB for UUID: {uuid}", is_error=True)
                    self._clear_data_form()
                    return

                # Populate form fields
                for db_field, editor_widget in self.data_editors.items():
                    is_display_label = db_field.endswith("_display")
                    actual_db_field = db_field.replace("_display", "")
                    
                    value = getattr(item_data_db, actual_db_field, None)
                    if value is None: value = "" # Display empty string for None
                    if isinstance(value, (int, float)): value = str(value)
                    
                    if isinstance(editor_widget, QLineEdit):
                        editor_widget.setText(value)
                        editor_widget.setReadOnly(False) # Enable editing
                    elif isinstance(editor_widget, QLabel): # For display fields
                        editor_widget.setText(value)
                
                self.save_changes_button.setEnabled(True)
                self.approve_button.setEnabled(item_data_db.review_status != 'approved')


                # Load PDF
                if pdf_path_from_db and os.path.exists(pdf_path_from_db):
                    self.pdf_document.load(pdf_path_from_db)
                    if self.pdf_document.status() == QPdfDocument.Status.Error:
                         self._log_message(f"Error loading PDF {pdf_path_from_db}: {self.pdf_document.error()}", is_error=True)
                    else:
                        self._log_message(f"Loaded PDF: {pdf_path_from_db}")
                        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth) # Reset zoom
                else:
                    self.pdf_document.load("") # Clear if no path or file not found
                    if pdf_path_from_db:
                        self._log_message(f"PDF file not found at path from DB: {pdf_path_from_db}", is_error=True)
                    else:
                        self._log_message(f"No PDF path associated with UUID: {uuid}")
                        
        except Exception as e:
            self._log_message(f"Error displaying record {uuid}: {e}", is_error=True)
            QMessageBox.critical(self, "Error", f"Could not display record details: {e}")

    def _save_changes(self):
        if not self.current_selected_uuid:
            self._log_message("No record selected to save.", is_error=True)
            return

        data_to_update: Dict[str, Any] = {}
        for db_field_name, editor in self.data_editors.items():
            if db_field_name in self.EDITABLE_DB_FIELDS: # Only consider editable fields
                value = editor.text().strip()
                # Basic type conversion attempt - more robust would be needed for production
                # For now, rely on DB schema or Pydantic model if re-validating
                item1_data_column = getattr(Item1Data, db_field_name, None)
                if item1_data_column is not None:
                    column_type = item1_data_column.type.python_type
                    if column_type == int:
                        try:
                            value = int(value) if value else None
                        except ValueError:
                            self._log_message(f"Invalid integer value for {db_field_name}: '{editor.text()}'", is_error=True)
                            QMessageBox.warning(self, "Validation Error", f"Field '{self.ITEM1_DB_FIELD_TO_LABEL.get(db_field_name, db_field_name)}' must be an integer.")
                            return
                    # Add more type conversions if needed (e.g., date)
                    # For dates, they are stored as strings (ISO format)
                
                data_to_update[db_field_name] = value if value else None # Store empty as None

        if not data_to_update:
            self._log_message("No changes detected to save.")
            return

        try:
            with db_handler.get_db_session() as session:
                db_handler.update_item1_data_fields(session, self.current_selected_uuid, data_to_update)
                session.commit()
            self._log_message(f"Changes saved for UUID: {self.current_selected_uuid}")
            # Refresh the displayed data for this item, including last_modified and potentially status if it were editable
            self._refresh_current_list_item_display()
            # Re-load the data in the form to show persisted values (e.g. formatted dates, timestamps)
            current_list_item = self.record_list_widget.currentItem()
            if current_list_item:
                self._display_selected_record(current_list_item)


        except Exception as e:
            self._log_message(f"Error saving changes for {self.current_selected_uuid}: {e}", is_error=True)
            QMessageBox.critical(self, "Save Error", f"Could not save changes: {e}")

    def _approve_and_copy_file(self):
        if not self.current_selected_uuid:
            self._log_message("No record selected to approve.", is_error=True)
            return

        approved_files_dir = self.settings.get(SETTINGS_APPROVED_FILES_DIR)
        if not approved_files_dir or not os.path.isdir(os.path.dirname(approved_files_dir)): # Check parent of where approved_files_dir itself might be created
             # A better check: if os.path.normpath(approved_files_dir) itself is a valid place to create item_1 subdir
            if not os.path.exists(approved_files_dir):
                try:
                    os.makedirs(approved_files_dir, exist_ok=True) # Try to create it
                except Exception as e:
                    QMessageBox.warning(self, "Path Error", f"Approved files directory ('{approved_files_dir}') is not configured properly or cannot be created: {e}")
                    self._log_message(f"Approval aborted: Approved files directory ('{approved_files_dir}') issue.", is_error=True)
                    return
            elif not os.path.isdir(approved_files_dir): # It exists but is not a directory
                 QMessageBox.warning(self, "Path Error", f"Approved files path ('{approved_files_dir}') exists but is not a directory.")
                 self._log_message(f"Approval aborted: Approved files path ('{approved_files_dir}') is not a directory.", is_error=True)
                 return


        uuid_to_approve = self.current_selected_uuid
        try:
            with db_handler.get_db_session() as session:
                # First, update status in DB
                db_handler.update_item1_review_status(session, uuid_to_approve, "approved")
                
                # Then, attempt to copy the file
                dest_path, error = file_handler.copy_approved_file(session, uuid_to_approve, approved_files_dir)
                
                if error:
                    self._log_message(f"Error copying file for UUID {uuid_to_approve}: {error}", is_error=True)
                    # Optionally, revert status if copy fails? PRD doesn't specify. For now, status remains approved.
                    QMessageBox.warning(self, "File Copy Error", f"Record status updated to 'approved', but file copy failed: {error}")
                else:
                    self._log_message(f"Record UUID {uuid_to_approve} approved and file copied to {dest_path}.")
                
                session.commit() # Commit status change
            
            self._refresh_current_list_item_display(new_status="approved")
            self.approve_button.setEnabled(False) # Disable after successful approval

        except Exception as e:
            self._log_message(f"Error during approval for {uuid_to_approve}: {e}", is_error=True)
            QMessageBox.critical(self, "Approval Error", f"Could not approve record: {e}")


    def _refresh_current_list_item_display(self, new_status: Optional[str] = None):
        current_list_item = self.record_list_widget.currentItem()
        if current_list_item and self.current_selected_uuid:
            status_to_display = new_status
            if not status_to_display: # Fetch current status if not provided
                try:
                    with db_handler.get_db_session() as session:
                        item_data = db_handler.get_item1_data_by_uuid(session, self.current_selected_uuid)
                        if item_data:
                            status_to_display = item_data.review_status
                except Exception as e:
                    self._log_message(f"Could not refresh item status from DB: {e}", is_error=True)
                    return # Don't update display if status fetch fails

            if status_to_display:
                current_list_item.setText(f"{self.current_selected_uuid} - {status_to_display.upper()}")
                if status_to_display == 'approved':
                    current_list_item.setForeground(QColor("green"))
                elif status_to_display == 'error': # Should not happen here, but for completeness
                    current_list_item.setForeground(QColor("red"))
                elif status_to_display == 'pending':
                    current_list_item.setForeground(QColor("orange"))
            
            # Also refresh the data form to show updated last_modified_timestamp etc.
            self._display_selected_record(current_list_item)


    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Exit Application',
                                     "Are you sure you want to exit?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
            self._log_message("Application closing.")
        else:
            event.ignore()

if __name__ == '__main__':
    # Ensure QSettings has a chance to pick up app/org names
    QApplication.setOrganizationName("MyCompany")
    QApplication.setApplicationName("FDD_QC_Lite")
    
    app = QApplication(sys.argv)
    # Apply a basic style (optional)
    # app.setStyle("Fusion") 
    
    # Basic Dark Theme (Optional - requires more for full consistency)
    # dark_palette = QPalette()
    # dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    # dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    # ... set other colors ...
    # app.setPalette(dark_palette)

    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec()) 