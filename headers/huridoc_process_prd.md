📄 Product Requirements Document (PRD)

Project: FDD Section Header Extraction using Huridocs Layout

Component: Python-native script to identify the 23 standard FDD Item headersAuthor: milleVersion: v1.0Last Updated: 2025-04-09

🧩 Background & Purpose

The goal is to extract the 23 standard "Item" headers from Franchise Disclosure Documents (FDDs) that have already been processed through Huridocs layout analysis. These headers serve as anchors to divide each FDD into structured sections for downstream data extraction and analysis.

The system must:

Accurately identify the headers despite formatting inconsistencies and OCR noise.

Use a clean, modular, explainable scoring system.

Provide structured section metadata including start and end markers.

Operate purely within a Python environment (no CLI interface).

🎯 Goals

Ingest Huridocs JSON layout output and extract all 23 standard FDD Item headers.

Use a transparent and tunable 3-layer scoring system.

Return structured metadata for each header including fuzzy match scores.

Use fallback logic with data validation rules for missing items.

🧱 Functional Requirements

1. Input

A Huridocs layout JSON object (a list of node dictionaries).

Each node includes: text, type, page_number, top, left, width, height.

2. Filtering Phase

Pre-filter nodes where type includes "section header" (case-insensitive).

Optionally include "title" nodes.

3. Fuzzy Matching Phase

For each candidate node:

Tier 1: Full Line Match

Fuzzy match the full node text against a canonical list of Item headers (e.g., "Item 7: Estimated Initial Investment").

Tier 2: "Item X" Label Match

Use regex to extract Item X (Arabic or Roman numerals only).

Match against all normalized item labels.

Tier 3: Post-label Phrase Match

Extract text after Item X: and fuzzy match it against a keyword list for each Item (e.g., Item 7: investment-related terms).

Fuzzy Score Calculation

Use a named scoring system like fuzz.token_set_ratio for all matches.

Include raw fuzzy match scores for each tier in the output.

Final score formula (customizable):

final_score = 0.5 * full_match_score + 0.3 * label_score + 0.2 * keyword_score

Text Alignment Heuristic

Add a bonus to the final score if the text is horizontally centered on the page.

Use page width and left + width to assess center proximity.

4. Best Match Selection

For each Item 1–23:

Select the candidate with the highest final score.

Only include matches above a score threshold (e.g., 60).

Break ties using:

Higher fuzzy full-match score.

More centered layout.



5. Fallback Phase for Missing Items

Re-run the matching logic over all nodes, not just section headers.

Apply the same scoring method.

Data Validation Logic:

If item N is missing:

Only accept fallback candidates where:

Page number is greater than N-1 and less than N+1 (based on expected item order).

Score exceeds fallback threshold.

6. Output Schema

A list of 23 dictionaries:

{
  "item_number": 7,
  "text": "Item 7: Estimated Initial Investment",
  "match_scores": {
    "full": 92,
    "label": 100,
    "keywords": 85,
    "final": 91.1
  },
  "page_number": 5,
  "node_index": 156,
  "start_node_index": 156,
  "end_node_index": 178,
  "start_page": 5,
  "end_page": 6,
  "alignment_score": 0.9
}

If an item is not found, mark:

"text": "Item X - Not Found"

All scores = 0

node_index and pages = null

⚠️ Non-Functional Requirements

Transparency: Scores for each phase must be retained in the output.

Pure Python: No command-line interface; all functionality must be callable from Python.

✅ Validation Rules

Output must contain exactly 23 entries.

Each item_number must be unique and between 1–23.

Section order must follow ascending item_number and node_index.

Page ranges must follow increasing order (Item 7 cannot start after Item 8).

Fallback matches must obey page-window validation (N-1 < fallback page < N+1).

🔭Other Requirements

Split-header detection (e.g., "Item" on one line, number on next).