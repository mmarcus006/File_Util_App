import sys
from PyQt6.QtWidgets import QApplication

# Relative imports for application modules
from ui.main_window import MainWindow
# Ensure QSettings can find the organization and application name
from ui.config_dialog import ConfigDialog # To set org/app name via QSettings constructor call if not already done

APP_NAME = "FDD_QC_Lite"
ORG_NAME = "MyCompany"

def main():
    """Main function to initialize and run the FDD QC Lite application."""
    
    # It's good practice to set these for QSettings if not already set by a constructor
    # The ConfigDialog constructor and MainWindow test already do this, but being explicit here is fine.
    QApplication.setOrganizationName(ORG_NAME)
    QApplication.setApplicationName(APP_NAME)
    
    app = QApplication(sys.argv)
    
    # Optional: Apply a style. PyQt6 comes with a few built-in styles.
    # Styles available: "Fusion", "Windows", "WindowsVista" (on Windows), "macOS" (on macOS)
    # app.setStyle("Fusion")

    main_window = MainWindow()
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 