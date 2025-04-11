# FDD Header Extraction Module

This module extracts the 23 standard Item headers from Franchise Disclosure Documents (FDDs) using Huridocs layout analysis data.

## Features

- Accurately identifies section headers despite formatting inconsistencies and OCR noise
- Uses a transparent, tunable 3-layer scoring system for matching
- Provides structured section metadata including boundaries and match scores
- Pure Python implementation with no CLI dependencies
- Handles split headers across multiple lines
- Includes fallback logic for missing items

## Usage

### Basic Usage

```python
from headers.fdd_header_extraction import process_huridocs_file

# Process a single file
results = process_huridocs_file(
    "path/to/huridocs_analysis.json",
    output_path="path/to/output_headers.json"
)

# Access the extracted headers
for item in results:
    print(f"Item {item['item_number']}: {item['text']}")
    print(f"  Page: {item['page_number']}, Score: {item['match_scores']['final']}")
```

### Scoring System

The module uses a 3-tier scoring system:

1. **Full Line Match** (50% weight): Fuzzy matches the full node text against canonical headers
2. **Item Label Match** (30% weight): Extracts and matches just the "Item X" portion
3. **Post-Label Keywords Match** (20% weight): Matches text after "Item X:" against item-specific keywords

An additional alignment bonus is added for text that is horizontally centered on the page.

### Customizing Thresholds

You can adjust the scoring thresholds:

```python
results = process_huridocs_file(
    "path/to/huridocs_analysis.json",
    score_threshold=70.0,  # Higher threshold for primary matches
    fallback_threshold=55.0  # Higher threshold for fallback matches
)
```

### Testing and Validation

Use the provided test script to evaluate extraction quality:

```bash
python fdd_header_test.py path/to/huridocs_analysis.json path/to/output.json
```

## Output Format

The output is a list of 23 dictionaries with the following structure:

```json
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
```

For items that could not be found, the format includes:
- `"text": "Item X - Not Found"`
- All scores set to 0
- All node and page indexes set to `null`

## Dependencies

- `rapidfuzz` for fuzzy string matching
- Standard Python libraries (json, re) 