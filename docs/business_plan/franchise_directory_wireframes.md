# Franchise Directory Website Wireframes

## Overview
These wireframes outline the UI/UX design for a franchise directory website focused on helping users find, analyze, and compare franchise opportunities. The design prioritizes clarity, data presentation, and intuitive user journeys.

## 1. Homepage (/)

```
+------------------------------------------------------+
|  LOGO                              SIGN IN | SIGN UP |
+------------------------------------------------------+
|                                                      |
|  HEADLINE: "Find Your Perfect Franchise Opportunity" |
|  Subheadline: "Compare data from 2,000+ franchises"  |
|                                                      |
|  +------------------------------------------+        |
|  |     SEARCH BAR: "Search by name..."      |        |
|  +------------------------------------------+        |
|                                                      |
|  BROWSE BY:                                          |
|  +--------+  +--------+  +--------+  +--------+     |
|  |Industry|  |Investment|  |Business|  |Location|    |
|  +--------+  +--------+  +--------+  +--------+     |
|                                                      |
+------------------------------------------------------+
|                                                      |
|  FEATURED FRANCHISES                                 |
|  +--------+  +--------+  +--------+  +--------+     |
|  |        |  |        |  |        |  |        |     |
|  | Card 1 |  | Card 2 |  | Card 3 |  | Card 4 |     |
|  |        |  |        |  |        |  |        |     |
|  +--------+  +--------+  +--------+  +--------+     |
|                                         VIEW ALL >   |
|                                                      |
+------------------------------------------------------+
|                                                      |
|  LOW-COST FRANCHISES                                 |
|  +--------+  +--------+  +--------+  +--------+     |
|  |        |  |        |  |        |  |        |     |
|  | Card 1 |  | Card 2 |  | Card 3 |  | Card 4 |     |
|  |        |  |        |  |        |  |        |     |
|  +--------+  +--------+  +--------+  +--------+     |
|                                         VIEW ALL >   |
|                                                      |
+------------------------------------------------------+
|                                                      |
|  WHY USE OUR SITE?                                   |
|  +--------+  +--------+  +--------+                 |
|  |        |  |        |  |        |                 |
|  |Complete|  |Side-by-|  |Free    |                 |
|  |  Data  |  | Side   |  |Access  |                 |
|  |        |  |Compare |  |        |                 |
|  +--------+  +--------+  +--------+                 |
|                                                      |
+------------------------------------------------------+
|                                                      |
|  LATEST INSIGHTS                                     |
|  +-------------------+  +-------------------+        |
|  |                   |  |                   |        |
|  | Blog Post 1       |  | Blog Post 2       |        |
|  |                   |  |                   |        |
|  +-------------------+  +-------------------+        |
|                                         VIEW ALL >   |
|                                                      |
+------------------------------------------------------+
|                                                      |
|  CALL TO ACTION                                      |
|  "Start Your Franchise Journey Today"                |
|  [EXPLORE FRANCHISES]                                |
|                                                      |
+------------------------------------------------------+
|                                                      |
|  FOOTER: About | Contact | Terms | Privacy           |
|                                                      |
+------------------------------------------------------+
```

### Key Elements:

1. **Header**
   - Logo (left-aligned)
   - Sign In/Sign Up buttons (right-aligned)

2. **Hero Section**
   - Bold headline emphasizing value proposition
   - Prominent search bar with placeholder text
   - Quick browse options with icon buttons for Industry, Investment Range, Business Type, and Location

3. **Featured Franchises Section**
   - Horizontal scrolling cards or grid layout
   - Each card shows: Logo, Name, Industry, Investment Range
   - "View All" link to directory

4. **Low-Cost Franchises Section**
   - Similar layout to Featured Franchises
   - Focuses on franchises with lower investment requirements
   - "View All" link to filtered directory view

5. **Value Proposition Section**
   - Three key benefits with icons
   - Brief explanations of site advantages

6. **Latest Insights Section**
   - Recent blog posts with images and headlines
   - "View All" link to blog section

7. **Call to Action**
   - Clear button encouraging exploration
   - Positioned prominently before footer

8. **Footer**
   - Standard navigation links
   - Copyright information

## 2. Directory Page (/directory)

```
+------------------------------------------------------+
|  LOGO                              SIGN IN | SIGN UP |
+------------------------------------------------------+
|  +------------------------------------------+        |
|  |     SEARCH BAR: "Search by name..."      |        |
|  +------------------------------------------+        |
|                                                      |
+------------------------------------------------------+
|                                                      |
|  FILTERS                |  RESULTS (245 franchises)  |
|  ----------------       |                            |
|  Industry:              |  SORT BY: [Dropdown]       |
|  □ Food                 |                            |
|  □ Retail               |  +------------------------+|
|  □ Service              |  |                        ||
|  □ More...              |  |  FRANCHISE CARD 1      ||
|                         |  |  Logo  Name  Industry   ||
|  Investment Range:      |  |  $XXk-$XXXk investment ||
|  [Slider: $0-$1M+]      |  |  X% royalty  XXX units ||
|                         |  |                        ||
|  Business Type:         |  |  □ Compare             ||
|  □ Brick & Mortar       |  +------------------------+|
|  □ Mobile               |                            |
|  □ Home-based           |  +------------------------+|
|  □ More...              |  |                        ||
|                         |  |  FRANCHISE CARD 2      ||
|  Special Programs:      |  |  Logo  Name  Industry   ||
|  □ Veteran Discounts    |  |  $XXk-$XXXk investment ||
|  □ Minority Incentives  |  |  X% royalty  XXX units ||
|                         |  |                        ||
|  Financial Data:        |  |  □ Compare             ||
|  □ Has Item 19          |  +------------------------+|
|                         |                            |
|  Units Count:           |  +------------------------+|
|  [Slider: 0-1000+]      |  |                        ||
|                         |  |  FRANCHISE CARD 3      ||
|  More Filters [+]       |  |  Logo  Name  Industry   ||
|                         |  |  $XXk-$XXXk investment ||
|                         |  |  X% royalty  XXX units ||
|                         |  |                        ||
|  [APPLY FILTERS]        |  |  □ Compare             ||
|  [CLEAR ALL]            |  +------------------------+|
|                         |                            |
|                         |  PAGINATION: < 1 2 3 ... >|
|                         |                            |
|                         |  [COMPARE SELECTED (0)]    |
|                         |                            |
+------------------------------------------------------+
```

### Key Elements:

1. **Header**
   - Consistent with homepage
   - Persistent search bar

2. **Filter Panel (Left Sidebar)**
   - Industry checkboxes with popular options and "More..." expansion
   - Investment Range slider with min/max values
   - Business Type checkboxes
   - Special Programs filters (Veteran Discounts, Minority Incentives)
   - Financial Data filter (Has Item 19)
   - Units Count slider
   - Expandable additional filters
   - Apply/Clear buttons

3. **Results Area (Main Content)**
   - Results count indicator
   - Sort dropdown (Investment Low-High, Units Count, Alphabetical)
   - Grid of Franchise Cards

4. **Franchise Card Component**
   - Logo (top left)
   - Franchise Name (prominent)
   - Industry Category (smaller text)
   - Investment Range (formatted as "$XXk-$XXXk")
   - Royalty Fee (percentage)
   - Total Units Count
   - Compare checkbox (bottom right)
   - Entire card is clickable to franchise profile

5. **Pagination Controls**
   - Page numbers with previous/next buttons
   - Positioned at bottom of results

6. **Compare Button**
   - Fixed position at bottom of results
   - Shows count of selected franchises
   - Disabled until at least 2 franchises are selected

## 3. Franchise Profile Page (/franchise/[slug])

```
+------------------------------------------------------+
|  LOGO                              SIGN IN | SIGN UP |
+------------------------------------------------------+
|  < Back to Results                                   |
+------------------------------------------------------+
|                                                      |
|  FRANCHISE NAME                      [ADD TO COMPARE]|
|  Logo                                                |
|  Industry Category | Established YYYY | Franchising Since YYYY |
|                                                      |
+------------------------------------------------------+
|                                                      |
|  KEY METRICS                                         |
|  +--------+  +--------+  +--------+  +--------+     |
|  |Initial |  |Net Worth|  |Liquid  |  |Total   |    |
|  |Investment|  |Required|  |Capital |  |Units   |    |
|  |$XXk-$XXXk|  |$XXXk   |  |$XXk    |  |XXX     |    |
|  +--------+  +--------+  +--------+  +--------+     |
|                                                      |
|  +--------+  +--------+  +--------+  +--------+     |
|  |Franchise|  |Royalty |  |Ad Fund |  |Term    |    |
|  |Fee      |  |Fee     |  |Fee     |  |Length  |    |
|  |$XXk     |  |X%      |  |X%      |  |XX years|    |
|  +--------+  +--------+  +--------+  +--------+     |
|                                                      |
+------------------------------------------------------+
|                                                      |
|  [OVERVIEW] [COSTS & FEES] [GROWTH] [FDDs] [REVIEWS]|
|                                                      |
+------------------------------------------------------+
|                                                      |
|  OVERVIEW TAB CONTENT                                |
|                                                      |
|  Business Description:                               |
|  Lorem ipsum dolor sit amet, consectetur adipiscing  |
|  elit. Sed do eiusmod tempor incididunt ut labore   |
|  et dolore magna aliqua.                            |
|                                                      |
|  Quick Facts:                                        |
|  • Headquarters: City, State                         |
|  • Business Model: Brick & Mortar                    |
|  • Territories Available: List of states             |
|  • Exclusive Territory: Yes/No                       |
|  • Home-Based Option: Yes/No                         |
|  • Owner-Operator Required: Yes/No                   |
|                                                      |
|  Contact Information:                                |
|  • Website: www.franchisewebsite.com                 |
|  • Phone: (XXX) XXX-XXXX                            |
|  • Email: franchise@example.com                      |
|                                                      |
|  [REQUEST INFORMATION]                               |
|                                                      |
+------------------------------------------------------+
```

### COSTS & FEES Tab Content:

```
+------------------------------------------------------+
|                                                      |
|  INITIAL INVESTMENT BREAKDOWN                        |
|  +---------------------------+----------+----------+ |
|  | Category                  | Low      | High     | |
|  +---------------------------+----------+----------+ |
|  | Franchise Fee             | $XX,XXX  | $XX,XXX  | |
|  | Real Estate/Leasehold     | $XX,XXX  | $XXX,XXX | |
|  | Equipment                 | $XX,XXX  | $XX,XXX  | |
|  | Inventory                 | $XX,XXX  | $XX,XXX  | |
|  | Signs                     | $X,XXX   | $XX,XXX  | |
|  | Training Expenses         | $X,XXX   | $XX,XXX  | |
|  | Additional Funds (3 mo.)  | $XX,XXX  | $XX,XXX  | |
|  +---------------------------+----------+----------+ |
|  | TOTAL                     | $XXX,XXX | $XXX,XXX | |
|  +---------------------------+----------+----------+ |
|                                                      |
|  ONGOING FEES                                        |
|  +---------------------------+--------------------+  |
|  | Fee Type                  | Amount             |  |
|  +---------------------------+--------------------+  |
|  | Royalty                   | X% of gross sales  |  |
|  | Marketing/Ad Fund         | X% of gross sales  |  |
|  | Technology Fee            | $XXX/month         |  |
|  | Transfer Fee              | $XX,XXX            |  |
|  | Renewal Fee               | $XX,XXX            |  |
|  +---------------------------+--------------------+  |
|                                                      |
|  FINANCING OPTIONS                                   |
|  • In-house financing available: Yes/No              |
|  • Covers: Franchise fee, equipment, etc.            |
|  • SBA approved: Yes/No                              |
|  • Veteran discount: X% off franchise fee            |
|                                                      |
+------------------------------------------------------+
```

### GROWTH Tab Content:

```
+------------------------------------------------------+
|                                                      |
|  UNIT GROWTH CHART                                   |
|  [Bar or line chart showing unit growth over time]   |
|                                                      |
|  UNIT STATISTICS                                     |
|  +---------------+--------+--------+--------+------+ |
|  | Year          | 2022   | 2021   | 2020   | 2019 | |
|  +---------------+--------+--------+--------+------+ |
|  | Franchised    | XXX    | XXX    | XXX    | XXX  | |
|  | Company-Owned | XX     | XX     | XX     | XX   | |
|  | Total Units   | XXX    | XXX    | XXX    | XXX  | |
|  | New Openings  | XX     | XX     | XX     | XX   | |
|  | Terminations  | X      | X      | X      | X    | |
|  | Reacquisitions| X      | X      | X      | X    | |
|  +---------------+--------+--------+--------+------+ |
|                                                      |
|  FINANCIAL PERFORMANCE (If Item 19 available)        |
|  • Average Unit Revenue: $XXX,XXX                    |
|  • Median Unit Revenue: $XXX,XXX                     |
|  • Top Quartile Revenue: $XXX,XXX                    |
|  • Bottom Quartile Revenue: $XXX,XXX                 |
|  • Average Profit Margin: XX% (if disclosed)         |
|                                                      |
|  Note: Financial performance data from Item 19 of    |
|  FDD. Past performance is not a guarantee of future  |
|  results.                                            |
|                                                      |
+------------------------------------------------------+
```

### FDDs Tab Content:

```
+------------------------------------------------------+
|                                                      |
|  AVAILABLE FDDs                                      |
|  +------+-------------+---------------------------+  |
|  | Year | States      | Actions                   |  |
|  +------+-------------+---------------------------+  |
|  | 2023 | CA, FL, IL  | [VIEW SUMMARY] [DOWNLOAD] |  |
|  | 2022 | CA, FL, IL  | [VIEW SUMMARY] [DOWNLOAD] |  |
|  | 2021 | CA, FL, IL  | [VIEW SUMMARY] [DOWNLOAD] |  |
|  +------+-------------+---------------------------+  |
|                                                      |
|  FDD HIGHLIGHTS                                      |
|  • Item 19 Financial Performance: Available/Not Available |
|  • Litigation History: None/Summary                  |
|  • Bankruptcy History: None/Summary                  |
|  • Franchisee Association: Yes/No                    |
|                                                      |
|  Note: Full FDD access may require registration      |
|  or subscription.                                    |
|                                                      |
+------------------------------------------------------+
```

### REVIEWS Tab Content:

```
+------------------------------------------------------+
|                                                      |
|  FRANCHISEE SATISFACTION                             |
|  [Star Rating: X.X/5] based on XX reviews            |
|                                                      |
|  REVIEW HIGHLIGHTS                                   |
|  +--------------------------------------------------+|
|  | ★★★★★ John D. - Franchisee since 2019           ||
|  | "Lorem ipsum dolor sit amet, consectetur..."     ||
|  +--------------------------------------------------+|
|                                                      |
|  +--------------------------------------------------+|
|  | ★★★★☆ Sarah M. - Franchisee since 2020          ||
|  | "Lorem ipsum dolor sit amet, consectetur..."     ||
|  +--------------------------------------------------+|
|                                                      |
|  QUESTIONS & ANSWERS                                 |
|  +--------------------------------------------------+|
|  | Q: "What is the typical breakeven period?"       ||
|  | A: "Most of our franchisees achieve breakeven... ||
|  +--------------------------------------------------+|
|                                                      |
|  [ASK A QUESTION]                                    |
|                                                      |
+------------------------------------------------------+
```

## 4. Comparison Page (/compare)

```
+------------------------------------------------------+
|  LOGO                              SIGN IN | SIGN UP |
+------------------------------------------------------+
|  < Back to Results                                   |
+------------------------------------------------------+
|                                                      |
|  COMPARING 3 FRANCHISES                 [PRINT] [PDF]|
|                                                      |
+------------------------------------------------------+
|                                                      |
|  +----------+----------+----------+----------+       |
|  | METRICS  | FRANCHISE| FRANCHISE| FRANCHISE|       |
|  |          |    1     |    2     |    3     |       |
|  +----------+----------+----------+----------+       |
|  | Logo     | [Logo 1] | [Logo 2] | [Logo 3] |       |
|  +----------+----------+----------+----------+       |
|  | Industry | Category1| Category2| Category1|       |
|  +----------+----------+----------+----------+       |
|  |                  INVESTMENT                |       |
|  +----------+----------+----------+----------+       |
|  | Initial  | $XXk-    | $XXk-    | $XXk-    |       |
|  | Investment| $XXXk    | $XXXk    | $XXXk    |       |
|  +----------+----------+----------+----------+       |
|  | Franchise| $XX,XXX  | $XX,XXX  | $XX,XXX  |       |
|  | Fee      |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  | Net Worth| $XXX,XXX | $XXX,XXX | $XXX,XXX |       |
|  | Required |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  | Liquid   | $XX,XXX  | $XX,XXX  | $XX,XXX  |       |
|  | Capital  |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  |                  ONGOING FEES                |       |
|  +----------+----------+----------+----------+       |
|  | Royalty  | X%       | X%       | X%       |       |
|  | Fee      |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  | Ad Fund  | X%       | X%       | X%       |       |
|  | Fee      |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  |                  PERFORMANCE                |       |
|  +----------+----------+----------+----------+       |
|  | Total    | XXX      | XXX      | XXX      |       |
|  | Units    |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  | Growth   | +XX%     | +XX%     | +XX%     |       |
|  | Rate     |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  | Has Item | Yes/No   | Yes/No   | Yes/No   |       |
|  | 19       |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  | Avg Unit | $XXX,XXX | $XXX,XXX | $XXX,XXX |       |
|  | Revenue  |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  |                  OPERATIONS                 |       |
|  +----------+----------+----------+----------+       |
|  | Business | Type 1   | Type 2   | Type 1   |       |
|  | Type     |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  | Term     | XX years | XX years | XX years |       |
|  | Length   |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  | Founded  | YYYY     | YYYY     | YYYY     |       |
|  +----------+----------+----------+----------+       |
|  | Franchising| YYYY   | YYYY     | YYYY     |       |
|  | Since    |          |          |          |       |
|  +----------+----------+----------+----------+       |
|  |                                            |       |
|  | [VIEW PROFILE] [VIEW PROFILE] [VIEW PROFILE]       |
|  |                                            |       |
+------------------------------------------------------+
|                                                      |
|  [ADD ANOTHER FRANCHISE TO COMPARE]                  |
|                                                      |
+------------------------------------------------------+
```

### Key Elements:

1. **Header**
   - Consistent with other pages
   - Back to Results link
   - Print and PDF export options

2. **Comparison Table**
   - Fixed first column with metric names
   - One column per franchise being compared
   - Franchises represented by logo and name at top
   - Metrics organized into logical sections:
     - Investment (Initial Investment, Franchise Fee, Net Worth, Liquid Capital)
     - Ongoing Fees (Royalty, Ad Fund)
     - Performance (Total Units, Growth Rate, Item 19 availability, Average Revenue)
     - Operations (Business Type, Term Length, Founded, Franchising Since)
   - View Profile buttons at bottom of each column

3. **Add More Option**
   - Button to add additional franchises to comparison
   - Limited to a reasonable number (e.g., 5 max)

4. **Visual Differentiation**
   - Color coding to highlight significant differences
   - Visual indicators for best values (lowest fees, highest growth)

## Mobile Adaptations

### Mobile Homepage
- Stacked layout with hamburger menu
- Full-width search bar
- Scrollable category buttons
- Vertical card layout (2 columns)

### Mobile Directory
- Filters accessible via expandable drawer or modal
- Single column card layout
- Fixed compare button at bottom of screen

### Mobile Profile Page
- Stacked layout with all sections vertical
- Horizontally scrollable tabs
- Tables reformatted for narrow screens
- Key metrics in 2x2 grid

### Mobile Comparison
- Horizontal scrolling for franchise columns
- Fixed metrics column on left
- Swipeable franchise columns

## Interactive Elements

1. **Search Functionality**
   - Autocomplete suggestions
   - Recent searches saved
   - Search results highlight matching terms

2. **Filtering System**
   - Real-time results update (no page reload)
   - Filter tags showing active filters
   - Save filter combinations

3. **Comparison Tool**
   - Add/remove franchises with visual feedback
   - Highlight differences between compared franchises
   - Export comparison as PDF

4. **Profile Navigation**
   - Sticky tabs when scrolling
   - Back-to-top button on long sections
   - Breadcrumb navigation
