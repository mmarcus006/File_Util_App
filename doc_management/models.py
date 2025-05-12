"""
SQLAlchemy ORM models for the file management database.
"""

import datetime
from typing import Optional, List, Dict

from sqlalchemy import (
    ForeignKey, String, DateTime, JSON, Integer, Float, Text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class File(Base):
    """Model representing the 'files' table."""
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    huridoc_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    processed_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    header_path: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Renaming might be good later if this path only holds JsonItem data now
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # # Relationship to Header (one-to-one) - Commented out as JsonItem replaces this
    # # Use lazy='joined' to typically load header info along with File
    # header: Mapped["Header"] = relationship(back_populates="file", cascade="all, delete-orphan", lazy="joined")

    # Relationship to JsonItem (one-to-many)
    # One File can have multiple associated JsonItem records
    items: Mapped[List["JsonItem"]] = relationship(back_populates="file", cascade="all, delete-orphan", lazy="select") # 'select' is often default/suitable for one-to-many

    def __repr__(self) -> str:
        return f"<File(file_id='{self.file_id}')>"

# # --- Commented out Header model ---
# class Header(Base):
#     """Model representing the 'headers' table with granular columns for extracted data."""
#     __tablename__ = "headers"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     # Foreign key linking back to the files table (unique ensures one-to-one)
#     file_id_fk: Mapped[int] = mapped_column(ForeignKey("files.id"), unique=True, nullable=False)

#     # --- Columns derived from JSON structure --- 

#     # source_files
#     source_original_pdf: Mapped[Optional[str]] = mapped_column(String, nullable=True)
#     source_converted_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)

#     # processing_details
#     proc_conversion_tool: Mapped[Optional[str]] = mapped_column(String, nullable=True)
#     proc_conversion_timestamp: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Store as string unless format is guaranteed
#     proc_script_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)

#     # header_fields (Storing the dict as JSON blob)
#     header_fields_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)

#     # match_results
#     match_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
#     match_total_expected: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
#     match_missing_headers: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True) # Store list as JSON
#     match_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

#     # quality_scores
#     quality_text_clarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
#     quality_format_consistency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
#     quality_completeness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

#     # timestamps
#     ts_extraction_start: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Store as string unless format is guaranteed
#     ts_extraction_end: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Store as string unless format is guaranteed

#     # --- Standard Columns --- 
#     created_at: Mapped[datetime.datetime] = mapped_column(
#         DateTime(timezone=True), server_default=func.now()
#     )

#     # Relationship back to File
#     file: Mapped["File"] = relationship(back_populates="header")

#     def __repr__(self) -> str:
#         # Use the file_id from the related File object for representation
#         # Ensure the relationship is loaded before accessing self.file
#         file_id_repr = self.file.file_id if self.file else '[Detached]'
#         return f"<Header(file_id='{file_id_repr}')>" 

class JsonItem(Base):
    """Model representing the 'json_items' table, storing data from the list-based JSON."""
    __tablename__ = "json_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Foreign key linking back to the files table
    file_id_fk: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=False)

    # --- Columns derived from the JSON list item structure ---
    item_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Use Text for potentially long strings

    # Match Scores (flattened from nested dict)
    match_score_full: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_score_label: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # Assuming label score can be float/int
    match_score_keywords: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_score_final: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    node_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_node_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_node_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    alignment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pdf_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # --- Standard Columns --- 
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship back to File
    file: Mapped["File"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        file_id_repr = self.file.file_id if self.file else '[Detached]'
        return f"<JsonItem(file_id='{file_id_repr}', item_number={self.item_number})>" 