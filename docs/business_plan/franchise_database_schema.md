# Comprehensive Franchise Database Schema

## Overview
This document outlines a comprehensive database schema for a franchise directory website, categorizing all required data fields logically and indicating their FDD source locations and priority levels.

## Data Field Categories

### 1. Franchisor_Info
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| franchisor_id | Unique identifier for the franchisor | N/A | High |
| brand_name | Brand/trade name of the franchise | Item 1 | High |
| legal_name | Legal name of the franchisor entity | Item 1 | High |
| parent_company | Parent company or corporate owner | Item 1 | Medium |
| headquarters_address | Street address of headquarters | Item 1 | High |
| headquarters_city | City of headquarters | Item 1 | High |
| headquarters_state | State/province of headquarters | Item 1 | High |
| headquarters_zip | Postal/ZIP code of headquarters | Item 1 | High |
| headquarters_country | Country of headquarters | Item 1 | High |
| phone_number | Main contact phone number | Item 1 | High |
| website_url | Corporate website URL | Item 1 | High |
| email_contact | Primary contact email | Item 1 | High |
| year_founded | Year the company was founded | Item 1 | High |
| year_franchising_began | Year the company began franchising | Item 1 | High |
| business_description | Description of the franchise business | Item 1 | High |
| company_history | Narrative history of the company | Item 1 | Medium |
| logo_url | URL to franchise logo image | N/A | High |
| social_media_facebook | Facebook page URL | N/A | Low |
| social_media_twitter | Twitter/X profile URL | N/A | Low |
| social_media_instagram | Instagram profile URL | N/A | Low |
| social_media_linkedin | LinkedIn company page URL | N/A | Low |
| franchise_500_rank | Current Entrepreneur Franchise 500 rank | N/A | Medium |
| franchise_500_history | Historical ranking data | N/A | Low |

### 2. Fee_Structure
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| initial_franchise_fee_min | Minimum initial franchise fee | Item 5 | High |
| initial_franchise_fee_max | Maximum initial franchise fee | Item 5 | High |
| initial_franchise_fee_notes | Notes about fee variations | Item 5 | Medium |
| royalty_fee_percentage | Royalty fee as percentage of sales | Item 6 | High |
| royalty_fee_fixed | Fixed royalty fee amount (if applicable) | Item 6 | High |
| royalty_fee_structure | Description of royalty structure | Item 6 | High |
| marketing_fee_percentage | Marketing/advertising fee percentage | Item 6 | High |
| marketing_fee_fixed | Fixed marketing fee amount (if applicable) | Item 6 | High |
| marketing_fee_structure | Description of marketing fee structure | Item 6 | High |
| technology_fee | Technology/software fees | Item 6 | Medium |
| transfer_fee | Fee for transferring franchise ownership | Item 6 | Medium |
| renewal_fee | Fee for renewing franchise agreement | Item 6 | Medium |
| other_recurring_fees | Description of other ongoing fees | Item 6 | Medium |
| veteran_discount | Discount offered to veterans (if any) | Item 5 | Medium |
| minority_discount | Discount offered to minority groups | Item 5 | Medium |
| multi_unit_discount | Discount for multi-unit development | Item 5 | Medium |

### 3. Investment_Details
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| total_investment_min | Minimum total investment required | Item 7 | High |
| total_investment_max | Maximum total investment required | Item 7 | High |
| cash_required_min | Minimum liquid capital required | Item 7 | High |
| net_worth_required_min | Minimum net worth required | Item 7 | High |
| real_estate_costs_min | Minimum real estate costs | Item 7 | High |
| real_estate_costs_max | Maximum real estate costs | Item 7 | High |
| equipment_costs_min | Minimum equipment costs | Item 7 | High |
| equipment_costs_max | Maximum equipment costs | Item 7 | High |
| inventory_costs_min | Minimum initial inventory costs | Item 7 | Medium |
| inventory_costs_max | Maximum initial inventory costs | Item 7 | Medium |
| working_capital_min | Minimum working capital needed | Item 7 | High |
| working_capital_max | Maximum working capital needed | Item 7 | High |
| build_out_costs_min | Minimum build-out/construction costs | Item 7 | Medium |
| build_out_costs_max | Maximum build-out/construction costs | Item 7 | Medium |
| franchise_fee_included | Whether franchise fee is included in total investment | Item 7 | Medium |
| investment_breakdown | Detailed breakdown of investment components | Item 7 | Medium |
| financing_available | Whether franchisor offers financing | Item 10 | High |
| financing_description | Description of financing options | Item 10 | Medium |
| sba_approved | Whether SBA financing is available/approved | Item 10 | Medium |
| third_party_financing | Available third-party financing relationships | Item 10 | Medium |

### 4. Unit_History
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| total_units | Total number of operating units | Item 20 | High |
| franchised_units | Number of franchised units | Item 20 | High |
| company_owned_units | Number of company-owned units | Item 20 | High |
| units_opened_last_year | Units opened in the last year | Item 20 | High |
| units_closed_last_year | Units closed in the last year | Item 20 | High |
| units_transferred_last_year | Units transferred in the last year | Item 20 | Medium |
| units_3yr_growth_rate | 3-year unit growth rate percentage | Item 20 | High |
| international_units | Number of international units | Item 20 | Medium |
| international_countries | List of countries with units | Item 20 | Low |
| projected_new_units | Projected new units for coming year | Item 20 | Medium |
| termination_rate | Percentage of units terminated | Item 20 | High |
| average_unit_revenue | Average revenue per unit | Item 19 | High |
| median_unit_revenue | Median revenue per unit | Item 19 | High |
| top_quartile_revenue | Top quartile unit revenue | Item 19 | Medium |
| bottom_quartile_revenue | Bottom quartile unit revenue | Item 19 | Medium |
| average_unit_profit | Average profit per unit | Item 19 | High |
| has_item_19 | Whether FDD includes Item 19 financial data | Item 19 | High |
| item_19_details | Summary of financial performance data | Item 19 | High |
| franchisee_satisfaction_score | Satisfaction rating (if available) | N/A | Medium |
| franchisee_association_exists | Whether a franchisee association exists | N/A | Medium |

### 5. Territory_Info
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| exclusive_territory | Whether exclusive territories are offered | Item 12 | High |
| territory_size | Typical territory size description | Item 12 | High |
| territory_population | Typical population in territory | Item 12 | Medium |
| territory_protection | Details of territory protection | Item 12 | Medium |
| territory_expansion | Rights to develop additional territories | Item 12 | Medium |
| relocation_rights | Rights to relocate the franchise | Item 12 | Low |
| online_competition_protection | Protection from franchisor online sales | Item 12 | Medium |
| area_development_options | Multi-unit development options | Item 12 | Medium |
| territory_selection_process | How territories are selected/assigned | Item 12 | Low |

### 6. Operations_Info
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| business_type | Type of business (retail, service, etc.) | Item 1 | High |
| industry_category | Primary industry category | Item 1 | High |
| industry_subcategory | Industry subcategory | Item 1 | High |
| business_model | Business model (brick-and-mortar, mobile, etc.) | Item 1 | High |
| square_footage_min | Minimum square footage required | Item 7, 11 | High |
| square_footage_max | Maximum square footage required | Item 7, 11 | High |
| location_type | Typical location types (mall, strip center, etc.) | Item 11 | High |
| home_based | Whether business can be home-based | Item 11 | High |
| owner_operator | Whether owner must operate the business | Item 15 | High |
| absentee_ownership | Whether absentee ownership is allowed | Item 15 | High |
| hours_of_operation | Typical hours of operation | Item 11 | Medium |
| seasonality | Seasonality factors of the business | Item 1 | Medium |
| staffing_requirements | Typical staffing needs | Item 11 | Medium |
| experience_required | Prior experience requirements | Item 15 | Medium |
| training_initial_duration | Duration of initial training | Item 11 | High |
| training_location | Location of initial training | Item 11 | Medium |
| ongoing_training | Description of ongoing training programs | Item 11 | Medium |
| field_support_frequency | Frequency of field support visits | Item 11 | Medium |
| marketing_support | Description of marketing support | Item 11 | Medium |
| technology_systems | Required technology/software systems | Item 11 | Medium |
| proprietary_systems | Proprietary systems/processes | Item 11 | Medium |
| supplier_restrictions | Required or approved suppliers | Item 8 | Medium |
| product_restrictions | Restrictions on products/services offered | Item 16 | Medium |

### 7. Legal_Info
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| agreement_term | Length of initial franchise agreement | Item 17 | High |
| renewal_terms | Terms for renewal | Item 17 | Medium |
| renewal_conditions | Conditions that must be met for renewal | Item 17 | Medium |
| transfer_conditions | Conditions for transferring ownership | Item 17 | Medium |
| termination_conditions | Conditions for termination | Item 17 | Medium |
| dispute_resolution | Method of dispute resolution | Item 17 | Low |
| litigation_history | Summary of litigation history | Item 3 | Medium |
| bankruptcy_history | Bankruptcy disclosures | Item 4 | Medium |
| trademark_info | Primary trademarks | Item 13 | Medium |
| patent_info | Relevant patents | Item 13 | Low |
| copyright_info | Relevant copyrights | Item 13 | Low |
| fdd_year | Year of most recent FDD | N/A | High |
| fdd_effective_date | Effective date of current FDD | N/A | High |
| states_registered | States where FDD is registered | Item 23 | Medium |
| fdd_link | Link to FDD if available | N/A | High |
| franchise_agreement_link | Link to sample franchise agreement | Item 22 | Medium |

### 8. Contact_Info
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| sales_contact_name | Name of franchise sales contact | Item 2 | High |
| sales_contact_title | Title of franchise sales contact | Item 2 | Medium |
| sales_contact_phone | Phone number for franchise sales | Item 2 | High |
| sales_contact_email | Email for franchise sales | Item 2 | High |
| key_executives | List of key executives and titles | Item 2 | Medium |
| franchisee_contact_list | Available list of franchisee contacts | Item 20 | Medium |
| discovery_day_offered | Whether discovery days are offered | N/A | Medium |
| application_process | Description of application process | N/A | Medium |
| typical_approval_timeline | Typical timeline from inquiry to approval | N/A | Medium |

### 9. Website_Metadata
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| profile_creation_date | Date profile was created in system | N/A | Medium |
| profile_last_updated | Date profile was last updated | N/A | High |
| profile_verified | Whether profile is verified by franchisor | N/A | High |
| profile_claimed | Whether profile is claimed by franchisor | N/A | High |
| profile_views | Number of profile views | N/A | Low |
| inquiry_count | Number of inquiries received | N/A | Medium |
| featured_status | Whether listing has featured status | N/A | Medium |
| search_keywords | Keywords for search optimization | N/A | Medium |
| profile_completeness | Percentage of profile fields completed | N/A | Medium |
| data_sources | Sources of profile data | N/A | Medium |
| profile_url_slug | URL-friendly version of brand name | N/A | High |

### 10. Media_Assets
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| hero_image_url | URL to main profile image | N/A | High |
| logo_image_url | URL to logo image | N/A | High |
| gallery_image_urls | Array of additional image URLs | N/A | Medium |
| video_url | URL to promotional video | N/A | Medium |
| virtual_tour_url | URL to virtual tour (if available) | N/A | Low |
| brochure_pdf_url | URL to downloadable brochure | N/A | Medium |
| press_releases | Recent press releases | N/A | Low |
| testimonial_quotes | Franchisee testimonial quotes | N/A | Medium |
| awards_recognition | Industry awards and recognition | N/A | Medium |

### 11. Comparison_Metrics
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| investment_to_sales_ratio | Ratio of investment to average sales | Calculated | High |
| cost_per_square_foot | Average cost per square foot | Calculated | Medium |
| roi_estimate | Estimated return on investment | Calculated | High |
| breakeven_estimate | Estimated time to breakeven | Calculated | High |
| industry_rank | Ranking within industry category | Calculated | Medium |
| growth_rank | Ranking based on unit growth | Calculated | Medium |
| investment_tier | Investment tier category | Calculated | High |
| success_score | Proprietary success likelihood score | Calculated | Medium |
| competitive_saturation | Market saturation assessment | Calculated | Medium |
| industry_growth_trend | Growth trend for the industry | N/A | Medium |

### 12. User_Interaction
| Field Name | Description | FDD Source | Priority |
|------------|-------------|------------|----------|
| user_ratings | Average user rating | N/A | Medium |
| user_reviews | User-submitted reviews | N/A | Medium |
| user_questions | User-submitted questions | N/A | Medium |
| franchisor_responses | Franchisor responses to questions | N/A | Medium |
| save_count | Number of users who saved this franchise | N/A | Low |
| comparison_count | Number of times included in comparisons | N/A | Low |
| inquiry_conversion_rate | Rate of profile views to inquiries | N/A | Medium |
| frequently_compared_with | Franchises often compared with this one | N/A | Medium |

## Implementation Notes

1. **Primary Keys and Relationships**:
   - `franchisor_id` serves as the primary key for the main franchise entity
   - Foreign key relationships should be established between related tables
   - Consider using UUID format for IDs to facilitate data migration

2. **Data Types and Validation**:
   - Monetary values should be stored in decimal/numeric format with appropriate precision
   - Percentage values should be stored as decimals (0.05 for 5%)
   - Text fields should have appropriate length constraints
   - URLs should be validated for format and accessibility

3. **Internationalization Considerations**:
   - Currency fields should include currency code
   - Address fields should accommodate international formats
   - Text fields should support Unicode for international characters

4. **Search Optimization**:
   - Create appropriate indexes on frequently searched fields
   - Consider full-text search capabilities for description fields
   - Implement efficient filtering on high-priority fields

5. **Data Maintenance**:
   - Implement versioning for tracking changes over time
   - Create audit trails for data updates
   - Establish regular data validation and cleaning processes

6. **API Considerations**:
   - Design RESTful endpoints for accessing franchise data
   - Implement appropriate caching strate
(Content truncated due to size limit. Use line ranges to read in chunks)