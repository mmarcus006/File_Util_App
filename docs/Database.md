Complete Database Schema (FDD-Centric)

I. Franchise & Classification Tables (Relatively Stable Data)

1. Franchise
Master table for the franchise brand itself. Contains stable identifying information.

Field Name	Data Type	Description	FDD Extractable	FDD Item
franchise_id	INT (PK)	Unique identifier for the franchise brand.	False	N/A
name	TEXT	Official name of the franchise brand.	True	1
slug	VARCHAR	URL-friendly version of the name (e.g., "mcdonalds").	False	N/A
logo_url	VARCHAR	URL path to the franchise's logo image file.	False	N/A
website_url	VARCHAR	Official website URL of the franchisor.	True	1
founded_year	INT	Year the original company associated with the brand was founded.	True	1
franchising_since	INT	Year the company began offering franchises under this brand.	True	1
hq_location	VARCHAR	Headquarters location (e.g., "Chicago, IL").	True	1
description	TEXT	Brief introductory summary of the franchise brand and its business.	True	1
overview_narrative	TEXT	Longer descriptive text covering brand essence, market position, history, etc.	True (Partially)	1
primary_industry_id	INT (FK)	Foreign key to Industry table for primary classification.	False	N/A
primary_category_id	INT (FK)	Foreign key to Category table for primary classification.	False	N/A
last_manual_update	TIMESTAMP	Timestamp of the last manual edit to this brand-level record.	False	N/A
2. Industry
Classification table for broad industry sectors.

Field Name	Data Type	Description	FDD Extractable	FDD Item
industry_id	INT (PK)	Unique identifier for the industry.	False	N/A
industry_name	VARCHAR	Name of the industry (e.g., "Food & Beverage").	False	N/A
3. Category
Classification table for specific business categories within industries.

Field Name	Data Type	Description	FDD Extractable	FDD Item
category_id	INT (PK)	Unique identifier for the category.	False	N/A
industry_id	INT (FK)	Foreign key linking to the Industry table.	False	N/A
category_name	VARCHAR	Name of the category (e.g., "Fast Food", "Senior Care").	False	N/A
4. FranchiseCategory (Join Table)
Links Franchises to one or more Categories for browsing/filtering.

Field Name	Data Type	Description	FDD Extractable	FDD Item
franchise_id	INT (FK)	Foreign key linking to the Franchise table.	False	N/A
category_id	INT (FK)	Foreign key linking to the Category table.	False	N/A
(Primary Key: (franchise_id, category_id))

II. FDD Tracking & Core FDD Data Tables

5. FDD
Central table tracking each specific Franchise Disclosure Document instance.

Field Name	Data Type	Description	FDD Extractable	FDD Item
fdd_id	INT (PK)	Unique identifier for this specific FDD record.	False	N/A
franchise_id	INT (FK)	Foreign key linking to the Franchise table.	False	N/A
publication_year	INT	The year the FDD was published or became effective (e.g., 2024).	True	Cover
document_url	VARCHAR	Optional: URL to the source FDD document file.	False	N/A
extracted_date	DATE	Date when the data from this FDD was extracted into the database.	False	N/A
state_filed_in	VARCHAR	Optional: Specific state FDD if variations exist (e.g., "CA", "MN", "Base").	True	Cover
(Unique Constraint: (franchise_id, publication_year, state_filed_in))

6. FDD_Executive (Item 2: Business Experience)
Stores information about key executives listed in a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
executive_id	INT (PK)	Unique identifier for the executive entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
name	VARCHAR	Name of the director or officer.	True	2
title	VARCHAR	Position/Title held by the executive.	True	2
experience_summary	TEXT	Summary of the executive's principal occupations in past 5 years.	True	2
7. FDD_Litigation (Item 3: Litigation)
Stores records of relevant litigation disclosed in a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
litigation_id	INT (PK)	Unique identifier for the litigation record for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
case_summary	TEXT	Description of the litigation case (parties involved, nature, status).	True	3
litigation_type	VARCHAR	Category of litigation (e.g., "Franchisor vs Franchisee", "Government").	True	3
8. FDD_Bankruptcy (Item 4: Bankruptcy)
Stores records of relevant bankruptcy history disclosed in a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
bankruptcy_id	INT (PK)	Unique identifier for the bankruptcy record for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
entity_involved	VARCHAR	Who filed bankruptcy (Franchisor, Parent, Predecessor, Affiliate, Executive).	True	4
bankruptcy_summary	TEXT	Details of the bankruptcy case (date, court, resolution).	True	4
9. FDD_InitialFee (Item 5: Initial Fees)
Stores details about the initial franchise fee for a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
initial_fee_id	INT (PK)	Unique identifier for the initial fee record for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
amount	INT / DECIMAL	The standard initial franchise fee amount.	True	5
fee_range_min	INT / DECIMAL	Minimum fee if it varies.	True	5
fee_range_max	INT / DECIMAL	Maximum fee if it varies.	True	5
notes	TEXT	Conditions, refundability, payment terms related to the initial fee.	True	5
10. FDD_OngoingFee (Item 6: Other Fees)
Stores details about recurring or miscellaneous fees for a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
fee_id	INT (PK)	Unique identifier for the ongoing fee entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
fee_type	VARCHAR	Type of fee (e.g., "Royalty", "Advertising", "Technology", "Training").	True	6
amount_formula	VARCHAR	Fee amount or calculation (e.g., "5%", "$100/month", "1% of Gross Sales").	True	6
due_date_or_frequency	VARCHAR	When the fee is due (e.g., "Monthly", "Annually", "Upon Invoice").	True	6
notes	TEXT	Additional details about the fee (e.g., purpose, calculation basis).	True	6
11. FDD_InitialInvestmentItem (Item 7: Estimated Initial Investment)
Stores detailed line items for the initial investment breakdown for a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
cost_item_id	INT (PK)	Unique identifier for the cost item entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
item_name	VARCHAR	Name of the cost item (e.g., "Real Estate Deposit", "Initial Fee").	True	7
min_cost	INT / DECIMAL	Minimum estimated cost for this item.	True	7
max_cost	INT / DECIMAL	Maximum estimated cost for this item.	True	7
method_of_payment	VARCHAR	How payment is made (e.g., "Lump Sum", "As Incurred").	True	7
due_date	VARCHAR	When payment is due (e.g., "Before Opening", "Upon Signing Lease").	True	7
paid_to	VARCHAR	To whom the payment is made (e.g., "Franchisor", "Third Party").	True	7
notes	TEXT	Footnotes or clarifications about the cost item.	True	7
12. FDD_SupplierRestriction (Item 8: Restrictions on Sources)
Stores details on required suppliers or specifications for a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
restriction_id	INT (PK)	Unique identifier for the supplier restriction entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
item_restricted	VARCHAR	Product, service, or supply subject to restriction (e.g., "POS System", "Food Ingredients").	True	8
restriction_type	VARCHAR	Nature of restriction (e.g., "Must buy from Franchisor", "Approved Supplier List", "Meets Specs").	True	8
revenue_to_franchisor	BOOLEAN	Does the franchisor derive revenue from required purchases?	True	8
notes	TEXT	Further details on the restrictions or supplier approval process.	True	8
13. FDD_FranchiseeObligation (Item 9: Franchisee's Obligations)
Summarizes key franchisee obligations from the agreement for a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
obligation_id	INT (PK)	Unique identifier for the obligation summary entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
obligation_area	VARCHAR	Area of obligation (e.g., "Site Selection", "Training", "Fees", "Operations").	True	9
summary	TEXT	Brief summary of the franchisee's main duties in this area.	True	9
agreement_reference	VARCHAR	Section number(s) in the Franchise Agreement covering this obligation.	True	9
14. FDD_FinancingOption (Item 10: Financing)
Stores details about financing arrangements offered or facilitated by the franchisor for a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
financing_id	INT (PK)	Unique identifier for the financing option entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
financing_type	VARCHAR	Type of financing (e.g., "Direct from Franchisor", "Third-Party Lender", "Lease").	True	10
summary_of_terms	TEXT	Key terms, conditions, and extent of financing offered or arranged.	True	10
notes	TEXT	Disclaimers, waivers, or intent to receive payment from sources.	True	10
15. FDD_SupportProvided (Item 11: Franchisor's Assistance, etc.)
Links a specific FDD to the support features offered during that period. Uses the master SupportFeature list.

Field Name	Data Type	Description	FDD Extractable	FDD Item
fdd_support_id	INT (PK)	Unique identifier for this support link for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
feature_id	INT (FK)	Foreign key linking to the SupportFeature catalog table.	False	N/A
detail	VARCHAR	Specific details if applicable (e.g., "120 hours", "Yes, Required", "Optional").	True	11
support_category	VARCHAR	Broad category from Item 11 (e.g., "Pre-Opening", "Ongoing", "Advertising", "Computer", "Training").	True	11
(Primary Key could be (fdd_id, feature_id) if one entry per feature per FDD is desired)

16. SupportFeature (Master Catalog - Unchanged but used by Item 11)
Catalog of potential support and training features offered by franchisors.

Field Name	Data Type	Description	FDD Extractable	FDD Item
feature_id	INT (PK)	Unique identifier for the support feature.	False	N/A
feature_name	VARCHAR	Name of the feature (e.g., "Grand Opening Support", "Field Operations Support").	True (Derived)	11
feature_type	VARCHAR	Category of support (e.g., "Training", "Marketing", "Operational", "Technology").	False	N/A
17. FDD_TrainingProgram (Item 11: Training Details)
Stores specific details about training programs described in an FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
training_id	INT (PK)	Unique identifier for the training program entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
program_name	VARCHAR	Name or type of training (e.g., "Initial Management Training", "On-the-Job").	True	11
timing	VARCHAR	When training occurs (e.g., "Before Opening", "Ongoing").	True	11
location	VARCHAR	Location of training (e.g., "Headquarters", "Online", "Franchise Location").	True	11
hours_classroom	INT	Number of hours of classroom training.	True	11
hours_on_the_job	INT	Number of hours of on-the-job training.	True	11
subjects_covered	TEXT	Key topics covered in the training.	True	11
18. FDD_Territory (Item 12: Territory)
Stores details about territory rights granted in a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
territory_id	INT (PK)	Unique identifier for the territory description for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
is_exclusive	BOOLEAN	Is an exclusive territory granted?	True	12
territory_definition	TEXT	How the territory is defined (e.g., radius, zip codes, population count).	True	12
reservations	TEXT	Rights reserved by the franchisor within the territory (e.g., alternative channels).	True	12
relocation_options	TEXT	Conditions under which franchisee or franchisor can relocate/modify territory.	True	12
19. FDD_Trademark (Item 13: Trademarks)
Stores information about principal trademarks listed in a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
trademark_id	INT (PK)	Unique identifier for the trademark entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
mark	VARCHAR	The principal trademark (e.g., "McDonald's", "Golden Arches Logo").	True	13
registration_status	VARCHAR	Status (e.g., "Registered", "Pending", "Not Registered").	True	13
usage_conditions	TEXT	Any limitations or conditions on the franchisee's use of the mark.	True	13
20. FDD_IntellectualProperty (Item 14: Patents, Copyrights, Proprietary Info)
Stores information about other IP listed in a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
ip_id	INT (PK)	Unique identifier for the IP entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
ip_type	VARCHAR	Type of IP (e.g., "Patent", "Copyright", "Trade Secret").	True	14
description	TEXT	Description of the patent, copyright, or proprietary information.	True	14
usage_conditions	TEXT	Any limitations or conditions on the franchisee's use.	True	14
21. FDD_OperationalParticipation (Item 15: Obligation to Participate)
Stores rules regarding franchisee's personal participation for a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
participation_id	INT (PK)	Unique identifier for the participation rule entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
personal_participation_required	BOOLEAN	Is the franchisee required to personally supervise the outlet?	True	15
manager_requirements	TEXT	Requirements if a manager operates the outlet (e.g., training, equity).	True	15
absentee_ownership_allowed	BOOLEAN	Is absentee ownership explicitly permitted under certain conditions?	True	15
notes	TEXT	Other conditions related to participation or management.	True	15
22. FDD_ProductServiceRestriction (Item 16: Restrictions on What Franchisee May Sell)
Stores limitations on goods/services the franchisee can offer for a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
restriction_id	INT (PK)	Unique identifier for the product/service restriction entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
restriction_summary	TEXT	Description of the limitations on goods or services offered.	True	16
customer_restrictions	TEXT	Any restrictions on the types of customers the franchisee may serve.	True	16
23. FDD_AgreementTerm (Item 17: Renewal, Termination, Transfer, Dispute Resolution)
Stores key terms related to the franchise agreement lifecycle for a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
term_id	INT (PK)	Unique identifier for the agreement term entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
term_length_years	INT	Length of the initial franchise agreement term.	True	17
renewal_term_years	INT / VARCHAR	Length of renewal term(s), or description if complex/none.	True	17
renewal_conditions	TEXT	Conditions franchisee must meet to renew.	True	17
termination_grounds_franchisor	TEXT	Summary of reasons the franchisor can terminate the agreement.	True	17
termination_grounds_franchisee	TEXT	Summary of reasons the franchisee can terminate the agreement.	True	17
post_termination_obligations	TEXT	Franchisee obligations after termination/expiration (e.g., de-identification).	True	17
transfer_conditions	TEXT	Conditions for franchisee to transfer the franchise.	True	17
dispute_resolution	TEXT	Methods specified for resolving disputes (e.g., mediation, arbitration, litigation venue).	True	17
24. FDD_PublicFigureEndorsement (Item 18: Public Figures)
Stores information about the use of public figures in promoting the franchise for a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
endorsement_id	INT (PK)	Unique identifier for the public figure entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
figure_name	VARCHAR	Name of the public figure used in advertising or promotion.	True	18
compensation	TEXT	Description of compensation paid to the public figure.	True	18
figure_investment	TEXT	Extent of the public figure's investment in the franchisor.	True	18
25. FDD_FinancialPerformanceMetric (Item 19: Financial Performance Representations)
Stores FPR data disclosed in a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
fpr_metric_id	INT (PK)	Unique identifier for the FPR metric entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table containing the disclosure.	False	N/A
performance_year	INT	The actual year(s) the financial performance data represents.	True	19
metric_name	VARCHAR	Name/description of the metric (e.g., "Average Gross Sales", "Median Net Profit", "Cost of Goods Sold %").	True	19
value	DECIMAL/FLOAT	The numeric value of the metric.	True	19
unit	VARCHAR	Unit of measure (e.g., "USD", "%", "Ratio").	True	19
subset_description	TEXT	Description of the subset of outlets included in the representation (e.g., "Top 10%", "Company-Owned").	True	19
notes	TEXT	Footnotes, assumptions, or cautionary statements accompanying the FPR.	True	19
26. FDD_OutletData (Item 20: Outlets and Franchisee Information)
Stores unit count changes and franchisee statistics for the period covered by a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
outlet_data_id	INT (PK)	Unique identifier for the outlet data entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
data_year	INT	The calendar year the outlet data represents (usually year prior to FDD pub).	True	20
state_or_region	VARCHAR	Geographic area the data pertains to (e.g., "CA", "USA", "International").	True	20
franchised_start_count	INT	Number of franchised outlets at start of year.	True	20
franchised_opened	INT	Number of franchised outlets opened during year.	True	20
franchised_terminated	INT	Number terminated during year.	True	20
franchised_non_renewed	INT	Number not renewed during year.	True	20
franchised_reacquired	INT	Number reacquired by franchisor during year.	True	20
franchised_ceased	INT	Number ceased operations for other reasons during year.	True	20
franchised_end_count	INT	Number of franchised outlets at end of year.	True	20
corporate_start_count	INT	Number of company-owned outlets at start of year.	True	20
corporate_opened	INT	Number opened during year.	True	20
corporate_closed	INT	Number closed during year.	True	20
corporate_end_count	INT	Number of company-owned outlets at end of year.	True	20
projected_openings_franchised	INT	Projected franchised openings in next year.	True	20
projected_openings_corporate	INT	Projected corporate openings in next year.	True	20
franchisee_list_available	BOOLEAN	Is a list of current franchisee contact info available (as per Item 20)?	True	20
27. FDD_ContractReference (Item 22: Contracts)
Lists the main contracts included as exhibits in a specific FDD.

Field Name	Data Type	Description	FDD Extractable	FDD Item
contract_ref_id	INT (PK)	Unique identifier for the contract reference entry for this FDD.	False	N/A
fdd_id	INT (FK)	Foreign key linking to the FDD table.	False	N/A
contract_name	VARCHAR	Name of the contract (e.g., "Franchise Agreement", "Lease Rider").	True	22
exhibit_letter	VARCHAR	The exhibit letter designation in the FDD (e.g., "Exhibit A").	True	22
III. Platform Feature & User Tables (Not Directly FDD-Sourced)

28. FranchiseRanking
Stores yearly ranks on various lists (External data, linked to Franchise).

Field Name	Data Type	Description	FDD Extractable	FDD Item
ranking_id	INT (PK)	Unique identifier for the ranking entry.	False	N/A
franchise_id	INT (FK)	Foreign key linking to the Franchise table.	False	N/A
list_name	VARCHAR	Name of the ranking list (e.g., "Entrepreneur Franchise 500").	False	N/A
year	INT	Year the ranking was published.	False	N/A
rank	INT	The rank number achieved on the list.	False	N/A
29. FranchiseFAQ
Stores curated Frequently Asked Questions and Answers specific to a franchise (Platform content, linked to Franchise).

Field Name	Data Type	Description	FDD Extractable	FDD Item
faq_id	INT (PK)	Unique identifier for the FAQ entry.	False	N/A
franchise_id	INT (FK)	Foreign key linking to the Franchise table.	False	N/A
question	TEXT	The frequently asked question text.	False	N/A
answer	TEXT	The curated answer (may draw data from FDD tables via queries).	False	N/A
30. User
Stores information about registered users of the platform.

Field Name	Data Type	Description	FDD Extractable	FDD Item
user_id	INT (PK)	Unique identifier for the user.	False	N/A
name	VARCHAR	User's name.	False	N/A
email	VARCHAR(UNIQUE)	User's email address (used for login).	False	N/A
password_hash	VARCHAR	Hashed password for security.	False	N/A
role	ENUM(...)	User role (e.g., 'Prospective', 'Franchisor', 'Admin', 'Consultant').	False	N/A
date_registered	TIMESTAMP	Date and time the user registered.	False	N/A
31. Lead
Captures inquiries (leads) submitted by users for specific franchises.

Field Name	Data Type	Description	FDD Extractable	FDD Item
lead_id	INT (PK)	Unique identifier for the lead submission.	False	N/A
franchise_id	INT (FK)	Foreign key linking to the Franchise table being inquired about.	False	N/A
user_id	INT (FK, Nullable)	Foreign key linking to the User table (if logged in).	False	N/A
name	VARCHAR	Name of the person submitting the inquiry.	False	N/A
email	VARCHAR	Email address of the inquirer.	False	N/A
phone	VARCHAR	Phone number of the inquirer.	False	N/A
city	VARCHAR	City of the inquirer.	False	N/A
state	VARCHAR	State/Region of the inquirer.	False	N/A
investment_budget	VARCHAR	Inquirer's stated investment capacity (range or amount).	False	N/A
message	TEXT	Optional message from the inquirer.	False	N/A
date_submitted	TIMESTAMP	Date and time the lead was submitted.	False	N/A
32. Favorite (Join Table)
Allows logged-in users to save or "favorite" franchises.

Field Name	Data Type	Description	FDD Extractable	FDD Item
user_id	INT (FK)	Foreign key linking to the User table.	False	N/A
franchise_id	INT (FK)	Foreign key linking to the Franchise table.	False	N/A
date_favorited	TIMESTAMP	Date and time the franchise was favorited.	False	N/A
(Primary Key: (user_id, franchise_id))

33. FranchisorAccount
Manages accounts for franchisor representatives who claim/manage their profile.

Field Name	Data Type	Description	FDD Extractable	FDD Item
franchisor_account_id	INT (PK)	Unique identifier for the franchisor account.	False	N/A
franchise_id	INT (FK, UNIQUE)	Foreign key linking to the Franchise they represent.	False	N/A
user_id	INT (FK, UNIQUE)	Foreign key linking to the User representing the franchisor.	False	N/A
contact_name	VARCHAR	Name of the primary contact person at the franchisor for this platform.	False	N/A
contact_email	VARCHAR	Email of the primary contact person.	False	N/A
verification_status	ENUM(...)	Status of the account claim (e.g., 'Pending', 'Verified', 'Rejected').	False	N/A
34. Article
Stores content for the blog or resource center.

Field Name	Data Type	Description	FDD Extractable	FDD Item
article_id	INT (PK)	Unique identifier for the article.	False	N/A
title	VARCHAR	Title of the article.	False	N/A
content	LONGTEXT	Full content of the article (HTML or Markdown).	False	N/A
author_id	INT (FK, Nullable)	Foreign key linking to the User table (if authored by platform user).	False	N/A
published_date	DATE	Date the article was published.	False	N/A
category	VARCHAR	Category of the article (e.g., "Financing", "Operations").	False	N/A
slug	VARCHAR	URL-friendly version of the title.	False	N/A
