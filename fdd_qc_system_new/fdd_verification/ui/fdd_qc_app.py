"""
FDD QC App main module for the FDD Header Quality Control System.
Contains the main application class and entry point.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import sys
import json

from fdd_verification.core.pdf_processor import PDFProcessor, JSONProcessor
from fdd_verification.ui.fdd_qc_ui_components import (
    FlaggedPairSelector,
    PDFViewer,
    HeadersTable,
)
from fdd_verification.ui.fdd_qc_data_manager import FDDQCDataManager


class FDDQualityControlApp:
    """
    Main application for FDD Quality Control System (Batch Review Mode)
    """

    def __init__(self, root, flagged_for_review: dict):
        """
        Initialize the application in batch review mode.

        Args:
            root: Tkinter root window
            flagged_for_review (dict): Dictionary of pairs flagged during batch processing.
                                       Format: {file_id: {'pdf': pdf_path, 'json': json_path, 'results': results_path}}
        """
        self.root = root
        self.root.title("FDD Header QC Review")
        self.root.geometry("1400x800")

        # Bind Enter key to the root window
        self.root.bind("<Return>", self.on_header_enter)
        
        # Bind Control+Enter to save results
        self.root.bind("<Control-Return>", lambda event: self.save_results())

        # Initialize data manager
        self.data_manager = FDDQCDataManager()
        self.data_manager.load_flagged_pairs(flagged_for_review)

        # Data storage for the currently loaded pair
        self.current_pdf_path = None
        self.current_json_path = None
        self.current_results_path = None
        self.pdf_processor = None
        self.json_processor = None
        self.verification_results = {}  # Store loaded results here

        # Create UI components
        self.create_menu()
        self.create_main_layout()

        # Initialize status
        self.update_status(
            f"Ready. {len(flagged_for_review)} pairs flagged for review."
        )

        # Auto-load the first uncorrected file
        self.root.after(100, self._auto_load_next_uncorrected)

    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="Load Flagged Pair...", command=self._show_flagged_pairs_dialog
        )
        file_menu.add_command(
            label="Load Next Uncorrected", command=self._auto_load_next_uncorrected
        )
        file_menu.add_separator()
        file_menu.add_command(label="Save Corrected JSON", command=self.save_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Help", command=self.show_help_batch)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def create_main_layout(self):
        """Create the main application layout"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a PanedWindow for resizable sections
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel - PDF viewer
        self.pdf_frame = ttk.LabelFrame(paned_window, text="PDF Viewer")
        paned_window.add(self.pdf_frame, weight=2)

        # Create PDF viewer component
        self.pdf_viewer = PDFViewer(self.pdf_frame)

        # Right panel - Headers and verification
        self.headers_frame = ttk.LabelFrame(paned_window, text="FDD Headers for Review")
        paned_window.add(self.headers_frame, weight=1)

        # Create headers table component
        self.headers_table_component = HeadersTable(self.headers_frame)

        # Bind events
        self.headers_table_component.headers_table.bind(
            "<Double-1>", self.on_header_double_click
        )
        self.headers_table_component.headers_table.bind(
            "<<TreeviewSelect>>", self.on_header_select
        )
        self.headers_table_component.headers_table.bind(
            "<Return>", self.on_header_enter
        )

        # Create detail frame below the table
        self.detail_frame = ttk.LabelFrame(self.headers_frame, text="Header Details")
        self.detail_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create fields for editing
        edit_frame = ttk.Frame(self.detail_frame)
        edit_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(edit_frame, text="Item Number:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.item_number_var = tk.StringVar()
        ttk.Label(edit_frame, textvariable=self.item_number_var).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=2
        )

        ttk.Label(edit_frame, text="Header Text:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.header_text_var = tk.StringVar()
        ttk.Label(edit_frame, textvariable=self.header_text_var, wraplength=300).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=2
        )

        ttk.Label(edit_frame, text="Expected Page:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.expected_page_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.expected_page_var, width=10).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=2
        )

        ttk.Label(edit_frame, text="Found Page:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.found_page_var = tk.StringVar()
        ttk.Label(edit_frame, textvariable=self.found_page_var).grid(
            row=3, column=1, sticky=tk.W, padx=5, pady=2
        )

        ttk.Label(edit_frame, text="Confidence:").grid(
            row=4, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.confidence_var = tk.StringVar()
        ttk.Label(edit_frame, textvariable=self.confidence_var).grid(
            row=4, column=1, sticky=tk.W, padx=5, pady=2
        )

        # Action buttons
        button_frame = ttk.Frame(self.detail_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            button_frame, text="Go to Expected Page", command=self.go_to_expected_page
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            button_frame, text="Go to Found Page", command=self.go_to_found_page
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            button_frame, text="Update Page Number", command=self.update_page_number
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Approve", command=self.approve_header).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(button_frame, text="Reject", command=self.reject_header).pack(
            side=tk.RIGHT, padx=5
        )

        # Bottom panel - Status and controls
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=10)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=5)

        # Action buttons
        ttk.Button(
            bottom_frame, text="Save Corrected JSON", command=self.save_results
        ).pack(side=tk.RIGHT, padx=5)

    def _show_flagged_pairs_dialog(self):
        """Show dialog to select a flagged pair"""
        if not self.data_manager.flagged_pairs:
            messagebox.showinfo("Information", "No pairs were flagged for review.")
            return

        dialog = FlaggedPairSelector(self.root, self.data_manager.flagged_pairs)
        selected_id = dialog.selected_id

        if selected_id:
            self._load_flagged_pair(selected_id)

    def _auto_load_next_uncorrected(self):
        """Automatically load the next uncorrected file"""
        uncorrected_files = self.data_manager.get_uncorrected_files()
        if not uncorrected_files:
            messagebox.showinfo(
                "All Files Processed",
                "All flagged files have been corrected. You can reopen files manually if needed.",
            )
            return

        # Sort by ID to ensure consistent order
        next_file_id = sorted(uncorrected_files)[0]
        self._load_flagged_pair(next_file_id)

        # Update status to indicate auto-loading
        remaining = len(uncorrected_files)
        self.update_status(
            f"Auto-loaded file {next_file_id}. {remaining} uncorrected file(s) remaining."
        )

    def _load_flagged_pair(self, file_id: str):
        """
        Loads the PDF, original JSON, and results JSON for the selected flagged pair

        Args:
            file_id: ID of the flagged pair to load
        """
        pair_info = self.data_manager.get_flagged_pair_info(file_id)
        if not pair_info:
            messagebox.showerror(
                "Error", f"File ID {file_id} not found in flagged list."
            )
            return

        pdf_path = pair_info["pdf"]
        json_path = pair_info["json"]
        results_path = pair_info["results"]

        self.update_status(f"Loading flagged pair ID: {file_id}...")
        try:
            # --- Load PDF ---
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            self.pdf_viewer.load_pdf(pdf_path)
            self.current_pdf_path = pdf_path
            self.pdf_processor = PDFProcessor(pdf_path)

            # --- Load JSON ---
            if not os.path.exists(json_path):
                raise FileNotFoundError(f"JSON not found: {json_path}")

            self.json_processor = JSONProcessor(json_path)
            self.current_json_path = json_path

            # Load headers into table
            headers = self.json_processor.get_all_headers()
            self.headers_table_component.load_headers(headers)

            # --- Load Results ---
            self.current_results_path = results_path
            self.verification_results = self.data_manager.load_verification_results(
                results_path
            )

            # Update table with results
            self.headers_table_component.update_with_results(self.verification_results)

            # Store the current file ID
            self.data_manager.current_file_id = file_id

            self.update_status(f"Loaded flagged pair ID: {file_id}")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading flagged pair: {str(e)}")
            self.update_status(f"Error loading flagged pair: {str(e)}")

    def on_header_select(self, event):
        """Handle header selection in the table"""
        selection = self.headers_table_component.headers_table.selection()
        if not selection:
            return

        # Get selected item
        item = selection[0]
        values = self.headers_table_component.headers_table.item(item, "values")

        # Update detail view
        try:
            item_number = int(values[0])
            self.item_number_var.set(item_number)
            self.header_text_var.set(values[1])
            self.expected_page_var.set(
                values[2]
            )  # This is the *original* expected page from JSON/Results
            self.found_page_var.set(values[3])  # This is the page found by verification

            # Get confidence from verification results
            if self.verification_results and item_number in self.verification_results:
                result = self.verification_results[item_number]
                confidence = result.get("confidence", 0)
                self.confidence_var.set(f"{confidence:.2f}")
            else:
                self.confidence_var.set("N/A")

            # Automatically navigate to the expected page when a header is selected
            self.go_to_expected_page()

        except (ValueError, IndexError):
            # Handle cases where table might be empty or have unexpected values
            self.item_number_var.set("")
            self.header_text_var.set("")
            self.expected_page_var.set("")
            self.found_page_var.set("")
            self.confidence_var.set("")
            print("Error updating detail view from table selection.")

    def on_header_double_click(self, event):
        """Handle double-click on a header in the table"""
        self.go_to_expected_page()

    def on_header_enter(self, event):
        """Handle Enter key press on a header in the table"""
        self.approve_header()

    def go_to_expected_page(self):
        """Go to the expected page in the PDF (from original JSON/results)"""
        try:
            expected_page_str = self.expected_page_var.get()
            if not expected_page_str or expected_page_str == "N/A":
                messagebox.showwarning("Warning", "No expected page number available.")
                return

            expected_page = int(expected_page_str)
            if not self.pdf_viewer.go_to_page(expected_page):
                messagebox.showwarning(
                    "Warning", f"Invalid page number: {expected_page}"
                )
        except ValueError:
            messagebox.showwarning("Warning", "Invalid page number format.")

    def go_to_found_page(self):
        """Go to the found page in the PDF"""
        found_page = self.found_page_var.get()
        if found_page and found_page != "Not found":
            try:
                page_num = int(found_page)
                if not self.pdf_viewer.go_to_page(page_num):
                    messagebox.showwarning("Warning", "Invalid page number.")
            except ValueError:
                messagebox.showwarning("Warning", "Invalid page number.")
        else:
            messagebox.showinfo("Information", "No matching page found.")

    def update_page_number(self):
        """Update the page number for the selected header"""
        selection = self.headers_table_component.headers_table.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a header first.")
            return

        try:
            # Get the new page number
            new_page = int(self.expected_page_var.get())

            # Get the item number
            item = selection[0]
            values = self.headers_table_component.headers_table.item(item, "values")
            item_number = int(values[0])

            # Update in JSON processor
            if self.json_processor:
                self.json_processor.update_header_page_number(item_number, new_page)

            # Update in verification results if available
            if self.verification_results and item_number in self.verification_results:
                self.verification_results[item_number]["expected_page"] = new_page

            # Update table
            self.headers_table_component.headers_table.item(
                item, values=(item_number, values[1], new_page, values[3], "Updated")
            )

            self.update_status(
                f"Updated page number for Item {item_number} to {new_page}."
            )

        except ValueError:
            messagebox.showwarning("Warning", "Invalid page number.")

    def approve_header(self):
        """Approve the selected header"""
        selection = self.headers_table_component.headers_table.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a header first.")
            return

        item = selection[0]
        values = self.headers_table_component.headers_table.item(item, "values")
        try:
            item_number = int(values[0])
        except (ValueError, IndexError):
            print("Could not get item number from selected row.")
            return

        # Update in verification results (which holds the state during review)
        if item_number in self.verification_results:
            self.verification_results[item_number]["status"] = "verified"
            # Update the expected page in results if it was manually changed in the entry
            try:
                current_entry_page = int(self.expected_page_var.get())
                self.verification_results[item_number][
                    "expected_page"
                ] = current_entry_page
                # Also update the underlying json_processor if loaded
                if self.json_processor:
                    self.json_processor.update_header_page_number(
                        item_number, current_entry_page
                    )
            except ValueError:
                print(
                    f"Could not update expected page for item {item_number} from entry."
                )

        # Update table visually
        # Use data from verification_results to ensure consistency
        result = self.verification_results.get(item_number, {})
        self.headers_table_component.headers_table.item(
            item,
            values=(
                item_number,
                result.get("header_text", values[1]),
                result.get("expected_page", values[2]),
                (
                    result.get("best_match_page", values[3])
                    if result.get("best_match_page") is not None
                    else "Not found"
                ),
                "Verified",
            ),
        )
        self.headers_table_component.headers_table.item(item, tags=("verified",))

        self.update_status(f"Approved Item {item_number}.")

    def reject_header(self):
        """Reject the selected header"""
        selection = self.headers_table_component.headers_table.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a header first.")
            return

        item = selection[0]
        values = self.headers_table_component.headers_table.item(item, "values")
        try:
            item_number = int(values[0])
        except (ValueError, IndexError):
            print("Could not get item number from selected row.")
            return

        # Update in verification results (which holds the state during review)
        if item_number in self.verification_results:
            self.verification_results[item_number][
                "status"
            ] = "needs_review"  # Mark as needs review again
            # Update the expected page in results if it was manually changed in the entry
            try:
                current_entry_page = int(self.expected_page_var.get())
                self.verification_results[item_number][
                    "expected_page"
                ] = current_entry_page
                # Also update the underlying json_processor if loaded
                if self.json_processor:
                    self.json_processor.update_header_page_number(
                        item_number, current_entry_page
                    )
            except ValueError:
                print(
                    f"Could not update expected page for item {item_number} from entry."
                )

        # Update table visually
        result = self.verification_results.get(item_number, {})
        self.headers_table_component.headers_table.item(
            item,
            values=(
                item_number,
                result.get("header_text", values[1]),
                result.get("expected_page", values[2]),
                (
                    result.get("best_match_page", values[3])
                    if result.get("best_match_page") is not None
                    else "Not found"
                ),
                "Needs Review",
            ),
        )
        self.headers_table_component.headers_table.item(item, tags=("needs_review",))

        self.update_status(f"Rejected Item {item_number}. Marked for review.")

    def save_results(self):
        """Save the currently loaded, potentially corrected, header data"""
        if not self.json_processor or not self.current_json_path:
            messagebox.showwarning("Warning", "No JSON data loaded to save.")
            return

        try:
            # Save the data using the data manager
            saved_path = self.data_manager.save_corrected_json(
                self.json_processor, self.current_json_path
            )

            if saved_path:
                messagebox.showinfo(
                    "Success",
                    f"Corrected headers saved to {os.path.basename(saved_path)}",
                )
                self.update_status(
                    f"Saved corrected data to {os.path.basename(saved_path)}"
                )

                # Auto-load next file after a short delay
                self.root.after(500, self._auto_load_next_uncorrected)
            else:
                messagebox.showerror("Error", "Failed to save corrected data")
                self.update_status("Error saving corrected data")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save corrected data: {str(e)}")
            self.update_status("Error saving corrected data")

    def update_status(self, message):
        """Update the status bar message"""
        self.status_var.set(message)
        print(message)

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "FDD Header Quality Control System\nVersion 1.0\n\nA tool for verifying and correcting FDD header page numbers.",
        )

    def show_help_batch(self):
        """Show help dialog for batch mode"""
        help_text = """
        FDD Header QC Review - Batch Mode Help
        
        This application helps you review and correct FDD header page numbers that were flagged during batch processing.
        
        Key features:
        - Automatically loads flagged files for review
        - Shows verification results with confidence scores
        - Allows you to approve or reject header verifications
        - Lets you manually update page numbers if needed
        - Saves corrected JSON files
        
        Keyboard shortcuts:
        - Enter: Approve the selected header
        - Ctrl+Enter: Save corrected JSON
        """
        messagebox.showinfo("Help", help_text)


def main():
    """Main entry point for the application"""
    if len(sys.argv) > 1:
        # If a flagged pairs JSON file is provided as an argument, load it
        flagged_pairs_path = sys.argv[1]
        try:
            with open(flagged_pairs_path, "r") as f:
                flagged_pairs = json.load(f)
        except Exception as e:
            print(f"Error loading flagged pairs file: {e}")
            flagged_pairs = {}
    else:
        # Otherwise, look for the default flagged pairs file
        default_path = os.path.join(
            os.path.dirname(__file__), "output", "flagged_pairs.json"
        )
        if os.path.exists(default_path):
            try:
                with open(default_path, "r") as f:
                    flagged_pairs = json.load(f)
            except Exception as e:
                print(f"Error loading default flagged pairs file: {e}")
                flagged_pairs = {}
        else:
            print("No flagged pairs file provided and default file not found.")
            flagged_pairs = {}

    # Create and run the application
    root = tk.Tk()
    app = FDDQualityControlApp(root, flagged_pairs)
    root.mainloop()


if __name__ == "__main__":
    main()
