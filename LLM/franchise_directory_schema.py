#!/usr/bin/env python3
"""
Create the complete SQLite schema + SQLAlchemy ORM for the Franchise Directory
project (franchise profiles, FDDs, Item‑20 tables, website metadata, analytics).

• Python ≥3.11, SQLAlchemy ≥2.0 required
• Produces a file `franchise_directory.sqlite`
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from sqlalchemy import (
    Date, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, CheckConstraint, create_engine, event, MetaData, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

# ---------------------------------------------------------------------#
# 0.  Helpers
# ---------------------------------------------------------------------#

def _uuid() -> str:
    return str(uuid.uuid4())

def _enable_sqlite_fk(dbapi_con, _con_record):
    """SQLite disables FKs by default – switch them on."""
    dbapi_con.execute("PRAGMA foreign_keys = ON")

# ---------------------------------------------------------------------#
# 1.  Base declarative class
# ---------------------------------------------------------------------#

class Base(DeclarativeBase):
    metadata = MetaData()

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid, unique=True
    )

# ---------------------------------------------------------------------#
# 2.  Dimension / reference tables
# ---------------------------------------------------------------------#

class State(Base):
    __tablename__ = "states"

    code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

# ---------------------------------------------------------------------#
# 3.  Core entities
# ---------------------------------------------------------------------#

class Franchisor(Base):
    """
    One row per franchise brand.  Most category tables have a 1‑to‑1 FK to this
    table (ON DELETE CASCADE) so you get a 'wide' conceptual entity without an
    unwieldy single table.
    """
    __tablename__ = "franchisors"
    __table_args__ = (UniqueConstraint("brand_name", name="uq_brand"),)

    # ---- identity & contact ----
    brand_name:            Mapped[str] = mapped_column(String, nullable=False)
    legal_name:            Mapped[Optional[str]]
    parent_company:        Mapped[Optional[str]]
    phone_number:          Mapped[Optional[str]]
    website_url:           Mapped[Optional[str]]
    email_contact:         Mapped[Optional[str]]
    headquarters_address:  Mapped[Optional[str]]
    headquarters_city:     Mapped[Optional[str]]
    headquarters_state:    Mapped[Optional[str]]
    headquarters_zip:      Mapped[Optional[str]]
    headquarters_country:  Mapped[Optional[str]]
    year_founded:          Mapped[Optional[int]]
    year_franchising_began:Mapped[Optional[int]]
    business_description:  Mapped[Optional[str]]
    company_history:       Mapped[Optional[str]]
    logo_url:              Mapped[Optional[str]]

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # ---- relationships (1‑to‑1) ----
    fees:            Mapped["FeeStructure"]          = relationship(uselist=False, cascade="all, delete-orphan")
    investment:      Mapped["InvestmentDetails"]     = relationship(uselist=False, cascade="all, delete-orphan")
    units:           Mapped["UnitHistory"]           = relationship(uselist=False, cascade="all, delete-orphan")
    territory:       Mapped["TerritoryInfo"]         = relationship(uselist=False, cascade="all, delete-orphan")
    ops:             Mapped["OperationsInfo"]        = relationship(uselist=False, cascade="all, delete-orphan")
    legal:           Mapped["LegalInfo"]             = relationship(uselist=False, cascade="all, delete-orphan")
    contact:         Mapped["ContactInfo"]           = relationship(uselist=False, cascade="all, delete-orphan")
    site_meta:       Mapped["WebsiteMetadata"]       = relationship(uselist=False, cascade="all, delete-orphan")
    media:           Mapped["MediaAssets"]           = relationship(uselist=False, cascade="all, delete-orphan")
    metrics:         Mapped["ComparisonMetrics"]     = relationship(uselist=False, cascade="all, delete-orphan")
    interaction:     Mapped["UserInteraction"]       = relationship(uselist=False, cascade="all, delete-orphan")

    # ---- one‑to‑many relationships ----
    fdds:            Mapped[List["FDDDocument"]]     = relationship(cascade="all, delete-orphan")
    #  Item‑20 tables hang off FDDDocument rows

# ---------------------------------------------------------------------#
# 4.  Category tables (1‑to‑1 with franchisor)
# ---------------------------------------------------------------------#

Money  = lambda: Numeric(12, 2)
Pct    = lambda: Numeric(5, 4)   #   0.0750 == 7.50 %

class FeeStructure(Base):
    __tablename__ = "fee_structure"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    initial_franchise_fee_min: Mapped[Optional[Decimal]] = mapped_column(Money())
    initial_franchise_fee_max: Mapped[Optional[Decimal]] = mapped_column(Money())
    initial_franchise_fee_notes: Mapped[Optional[str]]

    royalty_fee_percentage:     Mapped[Optional[Decimal]] = mapped_column(Pct())
    royalty_fee_fixed:          Mapped[Optional[Decimal]] = mapped_column(Money())
    royalty_fee_structure:      Mapped[Optional[str]]

    marketing_fee_percentage:   Mapped[Optional[Decimal]] = mapped_column(Pct())
    marketing_fee_fixed:        Mapped[Optional[Decimal]] = mapped_column(Money())
    marketing_fee_structure:    Mapped[Optional[str]]

    technology_fee:             Mapped[Optional[Decimal]] = mapped_column(Money())
    transfer_fee:               Mapped[Optional[Decimal]] = mapped_column(Money())
    renewal_fee:                Mapped[Optional[Decimal]] = mapped_column(Money())
    other_recurring_fees:       Mapped[Optional[str]]

    veteran_discount:           Mapped[Optional[Decimal]]     = mapped_column(Pct())
    minority_discount:          Mapped[Optional[Decimal]]     = mapped_column(Pct())
    multi_unit_discount:        Mapped[Optional[Decimal]]     = mapped_column(Pct())

class InvestmentDetails(Base):
    __tablename__ = "investment_details"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    total_investment_min:  Mapped[Optional[Decimal]] = mapped_column(Money())
    total_investment_max:  Mapped[Optional[Decimal]] = mapped_column(Money())
    cash_required_min:     Mapped[Optional[Decimal]] = mapped_column(Money())
    net_worth_required_min:Mapped[Optional[Decimal]] = mapped_column(Money())

    real_estate_costs_min: Mapped[Optional[Decimal]] = mapped_column(Money())
    real_estate_costs_max: Mapped[Optional[Decimal]] = mapped_column(Money())
    equipment_costs_min:   Mapped[Optional[Decimal]] = mapped_column(Money())
    equipment_costs_max:   Mapped[Optional[Decimal]] = mapped_column(Money())
    inventory_costs_min:   Mapped[Optional[Decimal]] = mapped_column(Money())
    inventory_costs_max:   Mapped[Optional[Decimal]] = mapped_column(Money())
    working_capital_min:   Mapped[Optional[Decimal]] = mapped_column(Money())
    working_capital_max:   Mapped[Optional[Decimal]] = mapped_column(Money())
    build_out_costs_min:   Mapped[Optional[Decimal]] = mapped_column(Money())
    build_out_costs_max:   Mapped[Optional[Decimal]] = mapped_column(Money())

    franchise_fee_included: Mapped[Optional[bool]]
    investment_breakdown:   Mapped[Optional[str]]

    financing_available:    Mapped[Optional[bool]]
    financing_description:  Mapped[Optional[str]]
    sba_approved:           Mapped[Optional[bool]]
    third_party_financing:  Mapped[Optional[str]]

class UnitHistory(Base):
    __tablename__ = "unit_history"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    total_units:                  Mapped[Optional[int]]
    franchised_units:             Mapped[Optional[int]]
    company_owned_units:          Mapped[Optional[int]]
    units_opened_last_year:       Mapped[Optional[int]]
    units_closed_last_year:       Mapped[Optional[int]]
    units_transferred_last_year:  Mapped[Optional[int]]
    units_3yr_growth_rate:        Mapped[Optional[Decimal]] = mapped_column(Pct())
    international_units:          Mapped[Optional[int]]
    international_countries:      Mapped[Optional[str]]
    projected_new_units:          Mapped[Optional[int]]
    termination_rate:             Mapped[Optional[Decimal]] = mapped_column(Pct())

    average_unit_revenue:         Mapped[Optional[Decimal]] = mapped_column(Money())
    median_unit_revenue:          Mapped[Optional[Decimal]] = mapped_column(Money())
    top_quartile_revenue:         Mapped[Optional[Decimal]] = mapped_column(Money())
    bottom_quartile_revenue:      Mapped[Optional[Decimal]] = mapped_column(Money())
    average_unit_profit:          Mapped[Optional[Decimal]] = mapped_column(Money())

    has_item_19:                  Mapped[Optional[bool]]
    item_19_details:              Mapped[Optional[str]]
    franchisee_satisfaction_score:Mapped[Optional[Decimal]] = mapped_column(Pct())
    franchisee_association_exists:Mapped[Optional[bool]]

class TerritoryInfo(Base):
    __tablename__ = "territory_info"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    exclusive_territory:      Mapped[Optional[bool]]
    territory_size:           Mapped[Optional[str]]
    territory_population:     Mapped[Optional[str]]
    territory_protection:     Mapped[Optional[str]]
    territory_expansion:      Mapped[Optional[str]]
    relocation_rights:        Mapped[Optional[str]]
    online_competition_protection:Mapped[Optional[str]]
    area_development_options: Mapped[Optional[str]]
    territory_selection_process:  Mapped[Optional[str]]

class OperationsInfo(Base):
    __tablename__ = "operations_info"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    business_type:          Mapped[Optional[str]]
    industry_category:      Mapped[Optional[str]]
    industry_subcategory:   Mapped[Optional[str]]
    business_model:         Mapped[Optional[str]]

    square_footage_min:     Mapped[Optional[int]]
    square_footage_max:     Mapped[Optional[int]]
    location_type:          Mapped[Optional[str]]
    home_based:             Mapped[Optional[bool]]

    owner_operator:         Mapped[Optional[bool]]
    absentee_ownership:     Mapped[Optional[bool]]

    hours_of_operation:     Mapped[Optional[str]]
    seasonality:            Mapped[Optional[str]]
    staffing_requirements:  Mapped[Optional[str]]
    experience_required:    Mapped[Optional[str]]

    training_initial_duration: Mapped[Optional[str]]
    training_location:      Mapped[Optional[str]]
    ongoing_training:       Mapped[Optional[str]]
    field_support_frequency:Mapped[Optional[str]]
    marketing_support:      Mapped[Optional[str]]
    technology_systems:     Mapped[Optional[str]]
    proprietary_systems:    Mapped[Optional[str]]
    supplier_restrictions:  Mapped[Optional[str]]
    product_restrictions:   Mapped[Optional[str]]

class LegalInfo(Base):
    __tablename__ = "legal_info"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    agreement_term:        Mapped[Optional[int]]
    renewal_terms:         Mapped[Optional[str]]
    renewal_conditions:    Mapped[Optional[str]]
    transfer_conditions:   Mapped[Optional[str]]
    termination_conditions:Mapped[Optional[str]]
    dispute_resolution:    Mapped[Optional[str]]

    litigation_history:    Mapped[Optional[str]]
    bankruptcy_history:    Mapped[Optional[str]]
    trademark_info:        Mapped[Optional[str]]
    patent_info:           Mapped[Optional[str]]
    copyright_info:        Mapped[Optional[str]]

    fdd_year:              Mapped[Optional[int]]
    fdd_effective_date:    Mapped[Optional[date]]
    states_registered:     Mapped[Optional[str]]
    fdd_link:              Mapped[Optional[str]]
    franchise_agreement_link:Mapped[Optional[str]]

class ContactInfo(Base):
    __tablename__ = "contact_info"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    sales_contact_name:   Mapped[Optional[str]]
    sales_contact_title:  Mapped[Optional[str]]
    sales_contact_phone:  Mapped[Optional[str]]
    sales_contact_email:  Mapped[Optional[str]]
    key_executives:       Mapped[Optional[str]]

    franchisee_contact_list: Mapped[Optional[str]]
    discovery_day_offered:   Mapped[Optional[bool]]
    application_process:     Mapped[Optional[str]]
    typical_approval_timeline:Mapped[Optional[str]]

class WebsiteMetadata(Base):
    __tablename__ = "website_metadata"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    profile_creation_date: Mapped[Optional[date]]
    profile_last_updated:  Mapped[Optional[date]]
    profile_verified:      Mapped[Optional[bool]]
    profile_claimed:       Mapped[Optional[bool]]
    profile_views:         Mapped[Optional[int]]
    inquiry_count:         Mapped[Optional[int]]
    featured_status:       Mapped[Optional[bool]]
    search_keywords:       Mapped[Optional[str]]
    profile_completeness:  Mapped[Optional[Decimal]] = mapped_column(Pct())
    data_sources:          Mapped[Optional[str]]
    profile_url_slug:      Mapped[Optional[str]]

class MediaAssets(Base):
    __tablename__ = "media_assets"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    hero_image_url:       Mapped[Optional[str]]
    logo_image_url:       Mapped[Optional[str]]
    gallery_image_urls:   Mapped[Optional[str]]
    video_url:            Mapped[Optional[str]]
    virtual_tour_url:     Mapped[Optional[str]]
    brochure_pdf_url:     Mapped[Optional[str]]
    press_releases:       Mapped[Optional[str]]
    testimonial_quotes:   Mapped[Optional[str]]
    awards_recognition:   Mapped[Optional[str]]

class ComparisonMetrics(Base):
    __tablename__ = "comparison_metrics"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    investment_to_sales_ratio: Mapped[Optional[Decimal]] = mapped_column(Pct())
    cost_per_square_foot:      Mapped[Optional[Decimal]] = mapped_column(Money())
    roi_estimate:              Mapped[Optional[Decimal]] = mapped_column(Pct())
    breakeven_estimate:        Mapped[Optional[str]]
    industry_rank:            Mapped[Optional[int]]
    growth_rank:              Mapped[Optional[int]]
    investment_tier:          Mapped[Optional[str]]
    success_score:            Mapped[Optional[Decimal]] = mapped_column(Pct())
    competitive_saturation:   Mapped[Optional[Decimal]] = mapped_column(Pct())
    industry_growth_trend:    Mapped[Optional[Decimal]] = mapped_column(Pct())

class UserInteraction(Base):
    __tablename__ = "user_interaction"
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), unique=True
    )

    user_ratings:             Mapped[Optional[Decimal]] = mapped_column(Pct())
    user_reviews:             Mapped[Optional[str]]
    user_questions:           Mapped[Optional[str]]
    franchisor_responses:     Mapped[Optional[str]]
    save_count:               Mapped[Optional[int]]
    comparison_count:         Mapped[Optional[int]]
    inquiry_conversion_rate:  Mapped[Optional[Decimal]] = mapped_column(Pct())
    frequently_compared_with: Mapped[Optional[str]]

# ---------------------------------------------------------------------#
# 5.  FDDs + Item‑20 detail tables (carry‑over from earlier version)
# ---------------------------------------------------------------------#

class FDDDocument(Base):
    __tablename__ = "fdd_documents"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_uuid, unique=True
    )
    franchisor_id: Mapped[str] = mapped_column(
        ForeignKey("franchisors.id", ondelete="CASCADE"), nullable=False
    )
    fiscal_year:  Mapped[int]
    issue_date:   Mapped[Optional[date]]
    source_file:  Mapped[Optional[str]]
    created_at:   Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    franchisor: Mapped["Franchisor"] = relationship(back_populates="fdds")
    t1_rows:    Mapped[List["T1SystemwideSummary"]]  = relationship(cascade="all, delete-orphan")
    t2_rows:    Mapped[List["T2Transfers"]]          = relationship(cascade="all, delete-orphan")
    t3_rows:    Mapped[List["T3FranchisedStatus"]]   = relationship(cascade="all, delete-orphan")
    t4_rows:    Mapped[List["T4CompanyOwnedStatus"]] = relationship(cascade="all, delete-orphan")
    t5_rows:    Mapped[List["T5ProjectedOpenings"]]  = relationship(cascade="all, delete-orphan")

# ---- Item‑20 tables (unchanged) ------------------------------------------------

class T1SystemwideSummary(Base):
    __tablename__ = "t1_systemwide_outlet_summary"
    __table_args__ = (
        UniqueConstraint("fdd_id", "outlet_type", "year", name="uq_t1"),
        CheckConstraint(
            "outlet_type in ('Franchised','Company-Owned','Total Outlets')",
            name="ck_t1_outlet_type"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    fdd_id: Mapped[str] = mapped_column(
        ForeignKey("fdd_documents.id", ondelete="CASCADE"), nullable=False
    )

    outlet_type:        Mapped[str]
    year:               Mapped[int]
    outlets_start_year: Mapped[Optional[int]]
    outlets_end_year:   Mapped[Optional[int]]
    net_change:         Mapped[Optional[int]]

class T2Transfers(Base):
    __tablename__ = "t2_transfers"
    __table_args__ = (UniqueConstraint("fdd_id", "state_code", "year", name="uq_t2"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    fdd_id: Mapped[str] = mapped_column(
        ForeignKey("fdd_documents.id", ondelete="CASCADE"), nullable=False
    )
    state_code: Mapped[str] = mapped_column(ForeignKey("states.code"))
    year:       Mapped[int]
    number_of_transfers: Mapped[Optional[int]]

class T3FranchisedStatus(Base):
    __tablename__ = "t3_franchised_status"
    __table_args__ = (UniqueConstraint("fdd_id", "state_code", "year", name="uq_t3"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    fdd_id: Mapped[str] = mapped_column(
        ForeignKey("fdd_documents.id", ondelete="CASCADE"), nullable=False
    )
    state_code: Mapped[str] = mapped_column(ForeignKey("states.code"))
    year:       Mapped[int]

    outlets_start_year:        Mapped[Optional[int]]
    outlets_opened:            Mapped[Optional[int]]
    terminations:              Mapped[Optional[int]]
    non_renewals:              Mapped[Optional[int]]
    reacquired_by_franchisor:  Mapped[Optional[int]]
    ceased_operations_other:   Mapped[Optional[int]]
    outlets_end_year:          Mapped[Optional[int]]

class T4CompanyOwnedStatus(Base):
    __tablename__ = "t4_company_owned_status"
    __table_args__ = (UniqueConstraint("fdd_id", "state_code", "year", name="uq_t4"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    fdd_id: Mapped[str] = mapped_column(
        ForeignKey("fdd_documents.id", ondelete="CASCADE"), nullable=False
    )
    state_code: Mapped[str] = mapped_column(ForeignKey("states.code"))
    year:       Mapped[int]

    outlets_start_year:         Mapped[Optional[int]]
    outlets_opened:             Mapped[Optional[int]]
    outlets_reacquired:         Mapped[Optional[int]]
    outlets_closed:             Mapped[Optional[int]]
    outlets_sold_to_franchisee: Mapped[Optional[int]]
    outlets_end_year:           Mapped[Optional[int]]

class T5ProjectedOpenings(Base):
    __tablename__ = "t5_projected_openings"
    __table_args__ = (UniqueConstraint("fdd_id", "state_code", name="uq_t5"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    fdd_id: Mapped[str] = mapped_column(
        ForeignKey("fdd_documents.id", ondelete="CASCADE"), nullable=False
    )
    state_code: Mapped[str] = mapped_column(ForeignKey("states.code"))

    franchise_agreements_signed_not_opened: Mapped[Optional[int]]
    projected_new_franchised:               Mapped[Optional[int]]
    projected_new_company_owned:            Mapped[Optional[int]]

# ---------------------------------------------------------------------#
# 6.  FDD File Index Table
# ---------------------------------------------------------------------#

class FDDFileIndex(Base):
    """Stores index information for individual files created by splitting FDD PDFs."""
    __tablename__ = "fdd_file_index"
    __table_args__ = (
        # Indexing filing_id for faster lookups when processing a specific FDD
        Index("ix_fdd_file_index_filing_id", "filing_id"),
        # Ensure file paths are unique per filing if needed, though full paths might suffice
        # UniqueConstraint("filing_id", "file_path", name="uq_fdd_file_path"),
    )

    # Not linking directly to FDDDocument PK via FK for now, using the folder name as ID
    filing_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True) # Assuming full path is unique
    section_identifier: Mapped[Optional[str]] # e.g., "ITEM_1", "intro", "exhibit_a"
    section_type: Mapped[Optional[str]]       # e.g., "ITEM", "INTRO", "EXHIBIT", "OTHER"
    extracted_item_number: Mapped[Optional[int]]  # e.g., 1, 20

# ---------------------------------------------------------------------#
# 7.  State seeding utility
# ---------------------------------------------------------------------#

_US_STATES = [
    ("AL","Alabama"),("AK","Alaska"),("AZ","Arizona"),("AR","Arkansas"),
    ("CA","California"),("CO","Colorado"),("CT","Connecticut"),("DE","Delaware"),
    ("FL","Florida"),("GA","Georgia"),("HI","Hawaii"),("ID","Idaho"),
    ("IL","Illinois"),("IN","Indiana"),("IA","Iowa"),("KS","Kansas"),
    ("KY","Kentucky"),("LA","Louisiana"),("ME","Maine"),("MD","Maryland"),
    ("MA","Massachusetts"),("MI","Michigan"),("MN","Minnesota"),("MS","Mississippi"),
    ("MO","Missouri"),("MT","Montana"),("NE","Nebraska"),("NV","Nevada"),
    ("NH","New Hampshire"),("NJ","New Jersey"),("NM","New Mexico"),("NY","New York"),
    ("NC","North Carolina"),("ND","North Dakota"),("OH","Ohio"),("OK","Oklahoma"),
    ("OR","Oregon"),("PA","Pennsylvania"),("RI","Rhode Island"),("SC","South Carolina"),
    ("SD","South Dakota"),("TN","Tennessee"),("TX","Texas"),("UT","Utah"),
    ("VT","Vermont"),("VA","Virginia"),("WA","Washington"),("WV","West Virginia"),
    ("WI","Wisconsin"),("WY","Wyoming"),("DC","District of Columbia")
]

def seed_states(session: Session):
    if session.query(State).count() == 0:
        session.bulk_save_objects([State(code=c, name=n) for c, n in _US_STATES])
        session.commit()

# ---------------------------------------------------------------------#
# 8.  Entrypoint
# ---------------------------------------------------------------------#

def main(db_path: str = "franchise_directory.sqlite"):
    db_url = f"sqlite:///{Path(db_path).resolve()}"
    engine = create_engine(db_url, echo=False, future=True)
    event.listen(engine, "connect", _enable_sqlite_fk)

    Base.metadata.create_all(engine, checkfirst=True)

    with Session(engine) as s:
        seed_states(s)

    print(f"✅ Schema ready at {db_path} (states pre‑loaded)")

if __name__ == "__main__":
    main()