"""
FDD QC App UI Components module for the FDD Header Quality Control System.
Contains UI-related classes and components.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import json
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io

class FlaggedPairSelector(tk.Toplevel):
    """Dialog to select a flagged file pair."""
    def __init__(self, parent, flagged_pairs_dict):
        super().__init__(parent)
        self.title("Select Flagged Pair")
        self.geometry("400x300")
        self.transient(parent) # Stay on top of parent
        self.grab_set() # Modal behavior

        self.flagged_pairs = flagged_pairs_dict
        self.selected_id = None

        label = ttk.Label(self, text="Select a file ID to review:")
        label.pack(pady=10)

        self.listbox = tk.Listbox(self, selectmode=tk.SINGLE)
        self.listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        for file_id in sorted(self.flagged_pairs.keys()):
            # Display the ID and maybe part of the filename for context
            pdf_name = os.path.basename(self.flagged_pairs[file_id]['pdf'])
            self.listbox.insert(tk.END, f"{file_id} ({pdf_name})")

        self.listbox.bind("<Double-Button-1>", self._on_load)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        load_button = ttk.Button(button_frame, text="Load", command=self._on_load)
        load_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        self.wait_window() # Wait until the window is closed

    def _on_load(self, event=None):
        selection_index = self.listbox.curselection()
        if selection_index:
            full_text = self.listbox.get(selection_index[0])
            # Extract the ID (first part before the space)
            self.selected_id = full_text.split(" (", 1)[0]
            self.destroy() # Close the dialog

class PDFViewer:
    """PDF viewing component for the FDD QC App"""
    
    def __init__(self, parent_frame):
        """
        Initialize the PDF viewer component
        
        Args:
            parent_frame: Parent frame to contain the PDF viewer
        """
        self.parent_frame = parent_frame
        self.pdf_document = None
        self.current_page = 1
        self.zoom_factor = 1.0
        self.current_photo = None
        
        self.create_pdf_viewer()
    
    def create_pdf_viewer(self):
        """Create the PDF viewer UI components"""
        # PDF canvas with scrollbars
        pdf_canvas_frame = ttk.Frame(self.parent_frame)
        pdf_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add vertical scrollbar
        self.pdf_vscrollbar = ttk.Scrollbar(pdf_canvas_frame, orient=tk.VERTICAL)
        self.pdf_vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add horizontal scrollbar
        self.pdf_hscrollbar = ttk.Scrollbar(pdf_canvas_frame, orient=tk.HORIZONTAL)
        self.pdf_hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # PDF canvas
        self.pdf_canvas = tk.Canvas(
            pdf_canvas_frame, 
            bg="white",
            xscrollcommand=self.pdf_hscrollbar.set,
            yscrollcommand=self.pdf_vscrollbar.set
        )
        self.pdf_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        self.pdf_vscrollbar.config(command=self.pdf_canvas.yview)
        self.pdf_hscrollbar.config(command=self.pdf_canvas.xview)
        
        # Bind mouse wheel events
        self.pdf_canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        self.pdf_canvas.bind("<Button-4>", self._on_mousewheel)    # Linux scroll up
        self.pdf_canvas.bind("<Button-5>", self._on_mousewheel)    # Linux scroll down
        
        # PDF navigation frame
        pdf_nav_frame = ttk.Frame(self.parent_frame)
        pdf_nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(pdf_nav_frame, text="Previous", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(pdf_nav_frame, text="Next", command=self.next_page).pack(side=tk.LEFT, padx=5)
        
        self.page_var = tk.StringVar(value="Page: 0 / 0")
        ttk.Label(pdf_nav_frame, textvariable=self.page_var).pack(side=tk.LEFT, padx=20)
        
        ttk.Button(pdf_nav_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.RIGHT, padx=5)
        ttk.Button(pdf_nav_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.RIGHT, padx=5)
    
    def load_pdf(self, pdf_path):
        """
        Load a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.pdf_document = fitz.open(pdf_path)
            self.current_page = 1
            self.update_page_display()
            return True
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            return False
    
    def update_page_display(self):
        """Update the PDF page display"""
        if not self.pdf_document:
            return
        
        # Clear canvas
        self.pdf_canvas.delete("all")
        
        # Get the page
        page = self.pdf_document[self.current_page - 1]
        
        # Render page to an image
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_factor, self.zoom_factor))
        img_data = pix.tobytes("ppm")
        
        # Convert to PhotoImage
        img = Image.open(io.BytesIO(img_data))
        photo = ImageTk.PhotoImage(img)
        
        # Store reference to prevent garbage collection
        self.current_photo = photo
        
        # Display image on canvas
        self.pdf_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        
        # Configure canvas scrollregion to match the image size
        self.pdf_canvas.config(scrollregion=self.pdf_canvas.bbox(tk.ALL))
        
        # Update page counter
        self.page_var.set(f"Page: {self.current_page} / {self.pdf_document.page_count}")
    
    def prev_page(self):
        """Go to the previous page"""
        if self.pdf_document and self.current_page > 1:
            self.current_page -= 1
            self.update_page_display()
    
    def next_page(self):
        """Go to the next page"""
        if self.pdf_document and self.current_page < self.pdf_document.page_count:
            self.current_page += 1
            self.update_page_display()
    
    def zoom_in(self):
        """Zoom in the PDF display"""
        self.zoom_factor *= 1.2
        self.update_page_display()
    
    def zoom_out(self):
        """Zoom out the PDF display"""
        self.zoom_factor /= 1.2
        self.update_page_display()
    
    def go_to_page(self, page_num):
        """
        Go to a specific page
        
        Args:
            page_num: Page number to go to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.pdf_document:
            return False
        
        if page_num > 0 and page_num <= self.pdf_document.page_count:
            self.current_page = page_num
            self.update_page_display()
            return True
        
        return False
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel events for scrolling"""
        # Windows mouse wheel
        if event.num == 5 or event.delta < 0:
            self.pdf_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.pdf_canvas.yview_scroll(-1, "units")

class HeadersTable:
    """Headers table component for the FDD QC App"""
    
    def __init__(self, parent_frame):
        """
        Initialize the headers table component
        
        Args:
            parent_frame: Parent frame to contain the headers table
        """
        self.parent_frame = parent_frame
        self.headers_table = None
        self.verification_results = {}
        
        self.create_headers_table()
    
    def create_headers_table(self):
        """Create the headers table for displaying verification results"""
        # Create a frame for the table
        table_frame = ttk.Frame(self.parent_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create Treeview widget
        columns = ("item", "header", "expected_page", "found_page", "status")
        self.headers_table = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=y_scrollbar.set)
        
        # Configure scrollbars
        y_scrollbar.config(command=self.headers_table.yview)
        
        # Define column headings
        self.headers_table.heading("item", text="Item #")
        self.headers_table.heading("header", text="Header Text")
        self.headers_table.heading("expected_page", text="Expected Page")
        self.headers_table.heading("found_page", text="Found Page")
        self.headers_table.heading("status", text="Status")
        
        # Define column widths
        self.headers_table.column("item", width=50, anchor=tk.CENTER)
        self.headers_table.column("header", width=250)
        self.headers_table.column("expected_page", width=100, anchor=tk.CENTER)
        self.headers_table.column("found_page", width=100, anchor=tk.CENTER)
        self.headers_table.column("status", width=100, anchor=tk.CENTER)
        
        # Pack the table
        self.headers_table.pack(fill=tk.BOTH, expand=True)
        
        # Configure tag colors
        self.headers_table.tag_configure("verified", background="#c8e6c9")
        self.headers_table.tag_configure("likely_correct", background="#dcedc8")
        self.headers_table.tag_configure("needs_review", background="#fff9c4")
        self.headers_table.tag_configure("likely_incorrect", background="#ffccbc")
        self.headers_table.tag_configure("not_found", background="#cfd8dc")
        self.headers_table.tag_configure("unknown", background="#ffffff") # Default white
    
    def clear_table(self):
        """Clears all items from the headers table."""
        for item in self.headers_table.get_children():
            self.headers_table.delete(item)
    
    def load_headers(self, headers):
        """
        Load headers into the table
        
        Args:
            headers: List of header dictionaries
        """
        self.clear_table()
        
        for header in headers:
            item_number = header.get('item_number')
            header_text = header.get('text', '')
            page_number = header.get('page_number') # Original page number
            self.headers_table.insert("", "end", values=(
                item_number,
                header_text,
                page_number,
                "",  # Found page (will be filled by update_headers_table)
                "Loading..."  # Initial status (will be updated)
            ))
    
    def update_with_results(self, verification_results):
        """
        Update the table with verification results
        
        Args:
            verification_results: Dictionary of verification results
        """
        self.verification_results = verification_results
        
        if not verification_results:
            # Set all statuses to 'N/A' or 'Error'
            for item in self.headers_table.get_children():
                values = list(self.headers_table.item(item, "values"))
                values[4] = "Results N/A" # Update status column
                self.headers_table.item(item, values=tuple(values))
            return
        
        # Update each row with verification results
        items_in_table = {int(self.headers_table.item(item, "values")[0]): item for item in self.headers_table.get_children()}

        for item_number, result in verification_results.items():
            item_id = items_in_table.get(item_number)
            if not item_id:
                print(f"Warning: Result found for item {item_number}, but not in table.")
                continue

            # Update values in the existing row
            self.headers_table.item(item_id, values=(
                item_number,
                result.get('header_text', 'N/A'), # Use result data if available
                result.get('expected_page', 'N/A'),
                result.get('best_match_page', "Not found") if result.get('best_match_page') is not None else "Not found",
                result.get('status', 'unknown').replace("_", " ").title()
            ))
            
            # Set row color based on status
            status = result.get('status', 'unknown')
            tag = status # Use status directly as tag
            if status in ["verified", "likely_correct", "needs_review", "likely_incorrect", "not_found"]:
                self.headers_table.item(item_id, tags=(tag,))
            else:
                self.headers_table.item(item_id, tags=("unknown",)) # Fallback tag
    
    def update_header_status(self, item_number, status):
        """
        Update the status of a header in the table
        
        Args:
            item_number: Item number of the header
            status: New status
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Find the item in the table
        for item in self.headers_table.get_children():
            values = self.headers_table.item(item, "values")
            if int(values[0]) == item_number:
                # Update the status column
                new_values = list(values)
                new_values[4] = status.replace("_", " ").title()
                self.headers_table.item(item, values=tuple(new_values))
                self.headers_table.item(item, tags=(status,))
                return True
        
        return False
