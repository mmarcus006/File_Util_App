import json
import re
import os
from typing import List, Dict, Any, Tuple, Optional, Union
from rapidfuzz import fuzz, process

def load_huridocs_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Load and parse the Huridocs layout JSON file.
    
    Args:
        file_path: Path to the Huridocs JSON file
        
    Returns:
        List of node dictionaries from the JSON file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_candidate_nodes(nodes: List[Dict[str, Any]], 
                          include_titles: bool = True) -> List[Dict[str, Any]]:
    """
    Filter nodes to only include potential section headers.
    
    Args:
        nodes: List of all nodes from the Huridocs JSON
        include_titles: Whether to include nodes with type "title"
        
    Returns:
        Filtered list of candidate nodes
    """
    candidates = []
    
    for i, node in enumerate(nodes):
        node_type = node.get('type', '').lower()
        
        # Include if type contains "section header" (case-insensitive)
        if 'section header' in node_type:
            node_with_index = node.copy()
            node_with_index['node_index'] = i
            candidates.append(node_with_index)
        # Optionally include title nodes
        elif include_titles and 'title' in node_type:
            node_with_index = node.copy()
            node_with_index['node_index'] = i
            candidates.append(node_with_index)
    
    return candidates

# Define canonical item headers and keywords for each item
CANONICAL_ITEM_HEADERS = {
    1: "Item 1: The Franchisor and any Parents, Predecessors, and Affiliates",
    2: "Item 2: Business Experience",
    3: "Item 3: Litigation",
    4: "Item 4: Bankruptcy",
    5: "Item 5: Initial Fees",
    6: "Item 6: Other Fees",
    7: "Item 7: Estimated Initial Investment",
    8: "Item 8: Restrictions on Sources of Products and Services",
    9: "Item 9: Franchisee's Obligations",
    10: "Item 10: Financing",
    11: "Item 11: Franchisor's Assistance, Advertising, Computer Systems, and Training",
    12: "Item 12: Territory",
    13: "Item 13: Trademarks",
    14: "Item 14: Patents, Copyrights, and Proprietary Information",
    15: "Item 15: Obligation to Participate in the Actual Operation of the Franchise Business",
    16: "Item 16: Restrictions on What the Franchisee May Sell",
    17: "Item 17: Renewal, Termination, Transfer, and Dispute Resolution",
    18: "Item 18: Public Figures",
    19: "Item 19: Financial Performance Representations",
    20: "Item 20: Outlets and Franchisee Information",
    21: "Item 21: Financial Statements",
    22: "Item 22: Contracts",
    23: "Item 23: Receipts"
}

# Define keywords for each item
ITEM_KEYWORDS = {
    1: ["franchisor", "parent", "predecessor", "affiliate"],
    2: ["business", "experience", "background"],
    3: ["litigation", "legal", "lawsuit", "court"],
    4: ["bankruptcy", "insolvency", "financial", "reorganization"],
    5: ["initial", "fee", "franchise fee", "payment"],
    6: ["other", "fee", "royalty", "advertising", "ongoing"],
    7: ["initial", "investment", "cost", "expense", "estimated"],
    8: ["restriction", "source", "product", "service", "supplier", "approved"],
    9: ["obligation", "franchisee", "responsibility", "duty"],
    10: ["financing", "loan", "finance", "arrangement"],
    11: ["assistance", "advertising", "computer", "system", "training", "support"],
    12: ["territory", "area", "market", "location", "exclusive"],
    13: ["trademark", "mark", "logo", "brand", "service mark"],
    14: ["patent", "copyright", "proprietary", "information", "intellectual"],
    15: ["participate", "operation", "manage", "involvement", "active"],
    16: ["restriction", "product", "service", "sell", "offer"],
    17: ["renewal", "termination", "transfer", "dispute", "resolution"],
    18: ["public", "figure", "celebrity", "endorsement"],
    19: ["financial", "performance", "representation", "earning", "claim"],
    20: ["outlet", "franchisee", "information", "location", "statistic"],
    21: ["financial", "statement", "balance", "income", "audit"],
    22: ["contract", "agreement", "document", "legal", "sign"],
    23: ["receipt", "acknowledge", "acknowledgment", "received"]
}

def calculate_alignment_score(node: Dict[str, Any]) -> float:
    """
    Calculate how centered a node is on the page.
    
    Args:
        node: The node dictionary with layout information
        
    Returns:
        Alignment score between 0-1 where 1 is perfectly centered
    """
    page_width = node.get('page_width', 612)  # Default to standard letter width
    node_left = node.get('left', 0)
    node_width = node.get('width', 0)
    
    # Calculate the center position of the node
    node_center = node_left + (node_width / 2)
    page_center = page_width / 2
    
    # Calculate how far (as a percentage of page width) the node is from center
    distance_from_center = abs(node_center - page_center) / page_width
    
    # Convert to a 0-1 score where 1 is perfectly centered
    return max(0, 1 - (distance_from_center * 2))

def extract_item_number(text: str) -> Optional[int]:
    """
    Extract item number from text using regex.
    
    Args:
        text: The text to extract item number from
        
    Returns:
        Item number as an integer or None if not found
    """
    # Match "Item X" or "ITEM X" where X is a number 1-23
    arabic_match = re.search(r'item\s+(\d+)', text.lower())
    if arabic_match and 1 <= int(arabic_match.group(1)) <= 23:
        return int(arabic_match.group(1))
    
    # Convert Roman numerals if present (e.g. "Item VII")
    roman_match = re.search(r'item\s+([ivxlcdm]+)', text.lower())
    if roman_match:
        roman = roman_match.group(1).upper()
        try:
            # Simple Roman numeral conversion
            roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
            result = 0
            prev_value = 0
            
            for char in reversed(roman):
                value = roman_values.get(char, 0)
                if value >= prev_value:
                    result += value
                else:
                    result -= value
                prev_value = value
                
            if 1 <= result <= 23:
                return result
        except (KeyError, ValueError):
            pass
    
    return None

def extract_post_label_text(text: str) -> str:
    """
    Extract text after "Item X:" pattern.
    
    Args:
        text: The full text string
        
    Returns:
        Text portion after the item label or empty string
    """
    match = re.search(r'item\s+\d+\s*:(.+)', text.lower())
    if match:
        return match.group(1).strip()
    
    # Try with Roman numerals
    roman_match = re.search(r'item\s+[ivxlcdm]+\s*:(.+)', text.lower())
    if roman_match:
        return roman_match.group(1).strip()
    
    return ""

def score_candidate(node: Dict[str, Any], 
                   canonical_items: Dict[int, str], 
                   item_keywords: Dict[int, List[str]]) -> Dict[int, Dict[str, float]]:
    """
    Calculate match scores for a node against all items.
    
    Args:
        node: The candidate node dictionary
        canonical_items: Dictionary of canonical item header texts
        item_keywords: Dictionary of keywords for each item
        
    Returns:
        Dictionary mapping item numbers to their scoring details
    """
    text = node.get('text', '').strip()
    
    if not text:
        return {}
    
    scores = {}
    
    # Try to extract item number first to narrow down matching
    item_number = extract_item_number(text)
    item_range = [item_number] if item_number else range(1, 24)
    
    for item_num in item_range:
        # Tier 1: Full line match
        canonical = canonical_items[item_num]
        full_match_score = fuzz.token_set_ratio(text.lower(), canonical.lower())
        
        # Tier 2: Item label match
        extracted_item_num = extract_item_number(text)
        label_score = 100 if extracted_item_num == item_num else 0
        
        # Tier 3: Keywords match
        post_label_text = extract_post_label_text(text)
        keyword_scores = [fuzz.token_set_ratio(post_label_text.lower(), kw.lower()) 
                          for kw in item_keywords[item_num]]
        keyword_score = max(keyword_scores) if keyword_scores else 0
        
        # Calculate final score with customizable weights
        final_score = (0.5 * full_match_score) + (0.3 * label_score) + (0.2 * keyword_score)
        
        # Add alignment bonus (up to 5% of final score)
        alignment_score = calculate_alignment_score(node)
        final_score += (alignment_score * 5)
        
        scores[item_num] = {
            "full": full_match_score,
            "label": label_score,
            "keywords": keyword_score,
            "final": final_score,
            "alignment": alignment_score
        }
    
    return scores

def find_best_matches(candidates: List[Dict[str, Any]], 
                     canonical_items: Dict[int, str],
                     item_keywords: Dict[int, List[str]], 
                     score_threshold: float = 60.0) -> Dict[int, Dict[str, Any]]:
    """
    Find the best match for each item among the candidates.
    
    Args:
        candidates: List of candidate nodes
        canonical_items: Dictionary of canonical item header texts
        item_keywords: Dictionary of keywords for each item
        score_threshold: Minimum score to consider a valid match
        
    Returns:
        Dictionary mapping item numbers to their best match details
    """
    best_matches = {}
    
    # Score all candidates
    for candidate in candidates:
        scores = score_candidate(candidate, canonical_items, item_keywords)
        
        for item_num, score_details in scores.items():
            if score_details["final"] >= score_threshold:
                if (item_num not in best_matches or 
                    score_details["final"] > best_matches[item_num]["match_scores"]["final"]):
                    
                    # On tie, prefer the one with higher full match score
                    if (item_num in best_matches and 
                        abs(score_details["final"] - best_matches[item_num]["match_scores"]["final"]) < 0.5):
                        if score_details["full"] <= best_matches[item_num]["match_scores"]["full"]:
                            continue
                    
                    best_matches[item_num] = {
                        "item_number": item_num,
                        "text": candidate.get('text', ''),
                        "match_scores": {
                            "full": score_details["full"],
                            "label": score_details["label"],
                            "keywords": score_details["keywords"],
                            "final": score_details["final"]
                        },
                        "page_number": candidate.get('page_number'),
                        "node_index": candidate.get('node_index'),
                        "start_node_index": candidate.get('node_index'),
                        "end_node_index": None,  # Will be filled later
                        "start_page": candidate.get('page_number'),
                        "end_page": None,  # Will be filled later
                        "alignment_score": score_details["alignment"]
                    }
    
    return best_matches

def find_fallbacks(all_nodes: List[Dict[str, Any]], 
                 missing_items: List[int],
                 canonical_items: Dict[int, str],
                 item_keywords: Dict[int, List[str]],
                 best_matches: Dict[int, Dict[str, Any]],
                 fallback_threshold: float = 50.0) -> Dict[int, Dict[str, Any]]:
    """
    Find fallback matches for missing items using all nodes.
    
    Args:
        all_nodes: All nodes from the document
        missing_items: List of item numbers that are missing
        canonical_items: Dictionary of canonical item header texts
        item_keywords: Dictionary of keywords for each item
        best_matches: Dictionary of already found best matches
        fallback_threshold: Minimum score for fallback matches
        
    Returns:
        Dictionary mapping item numbers to their fallback match details
    """
    fallbacks = {}
    
    # Get page ranges for validation
    sorted_items = sorted([item for item in best_matches.keys()])
    
    # Add node_index to all nodes
    nodes_with_index = []
    for i, node in enumerate(all_nodes):
        node_copy = node.copy()
        node_copy['node_index'] = i
        nodes_with_index.append(node_copy)
    
    for missing_item in missing_items:
        # Determine valid page range for fallback
        if not sorted_items:  # No existing items to reference
            valid_page_range = (1, float('inf'))
        else:
            prev_item = max([i for i in sorted_items if i < missing_item], default=None)
            next_item = min([i for i in sorted_items if i > missing_item], default=None)
            
            min_page = 1
            max_page = float('inf')
            
            if prev_item and prev_item in best_matches:
                min_page = best_matches[prev_item]["page_number"]
            
            if next_item and next_item in best_matches:
                max_page = best_matches[next_item]["page_number"]
                
            valid_page_range = (min_page, max_page)
        
        # Look for fallbacks within the valid page range
        valid_fallback_candidates = []
        
        for node in nodes_with_index:
            page_num = node.get('page_number')
            if page_num and valid_page_range[0] <= page_num <= valid_page_range[1]:
                valid_fallback_candidates.append(node)
                
        # Score the candidates
        best_fallback = None
        best_fallback_score = fallback_threshold
        
        for candidate in valid_fallback_candidates:
            scores = score_candidate(candidate, canonical_items, item_keywords)
            
            if missing_item in scores and scores[missing_item]["final"] >= best_fallback_score:
                if not best_fallback or scores[missing_item]["final"] > best_fallback_score:
                    best_fallback = candidate
                    best_fallback_score = scores[missing_item]["final"]
        
        # If fallback found, add to results
        if best_fallback:
            score_details = score_candidate(best_fallback, canonical_items, item_keywords)[missing_item]
            
            fallbacks[missing_item] = {
                "item_number": missing_item,
                "text": best_fallback.get('text', ''),
                "match_scores": {
                    "full": score_details["full"],
                    "label": score_details["label"],
                    "keywords": score_details["keywords"],
                    "final": score_details["final"]
                },
                "page_number": best_fallback.get('page_number'),
                "node_index": best_fallback.get('node_index'),
                "start_node_index": best_fallback.get('node_index'),
                "end_node_index": None,  # Will be filled later
                "start_page": best_fallback.get('page_number'),
                "end_page": None,  # Will be filled later
                "alignment_score": score_details["alignment"]
            }
    
    return fallbacks

def determine_section_boundaries(matched_items: Dict[int, Dict[str, Any]], 
                               all_nodes: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Determine the end boundaries for each section.
    
    Args:
        matched_items: Dictionary of matched items
        all_nodes: All nodes from the document
        
    Returns:
        Updated matched items with section boundaries
    """
    # Sort items by node_index
    sorted_items = sorted(matched_items.values(), key=lambda x: x["node_index"])
    
    for i, item in enumerate(sorted_items):
        # If this is the last item, end is the end of document
        if i == len(sorted_items) - 1:
            item["end_node_index"] = len(all_nodes) - 1
            last_node = all_nodes[-1]
            item["end_page"] = last_node.get("page_number", item["start_page"])
        else:
            # End is just before the next section starts
            next_item = sorted_items[i + 1]
            item["end_node_index"] = next_item["node_index"] - 1
            item["end_page"] = next_item["start_page"]
            
            # Special case: if next item is on same page, end page is same page
            if next_item["start_page"] == item["start_page"]:
                item["end_page"] = item["start_page"]
    
    # Convert back to dictionary keyed by item_number
    return {item["item_number"]: item for item in sorted_items}

def find_split_headers(candidates: List[Dict[str, Any]], 
                      all_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find headers that might be split across multiple lines.
    
    Args:
        candidates: List of candidate nodes
        all_nodes: All nodes from the document
        
    Returns:
        List of merged candidate nodes
    """
    merged_candidates = candidates.copy()
    
    # Look for nodes with just "Item" or just a number
    for i, node in enumerate(candidates):
        text = node.get('text', '').strip().lower()
        
        # If node just contains "item" or similar
        if re.match(r'^item\s*$', text):
            # Look at the next node to see if it has a number
            if node['node_index'] + 1 < len(all_nodes):
                next_node = all_nodes[node['node_index'] + 1]
                next_text = next_node.get('text', '').strip()
                
                # Check if next node contains just a number or number with colon
                if re.match(r'^\d+\s*:?', next_text) or re.match(r'^[ivxlcdm]+\s*:?', next_text.lower()):
                    # Create a merged node
                    merged_node = node.copy()
                    merged_node['text'] = f"Item {next_text}"
                    merged_candidates.append(merged_node)
                    
                    # Also check one more node for the title part
                    if node['node_index'] + 2 < len(all_nodes):
                        title_node = all_nodes[node['node_index'] + 2]
                        title_text = title_node.get('text', '').strip()
                        
                        if not re.match(r'^item', title_text.lower()):
                            # Create a more complete merged node
                            complete_node = node.copy()
                            if ':' in next_text:
                                complete_node['text'] = f"Item {next_text} {title_text}"
                            else:
                                complete_node['text'] = f"Item {next_text}: {title_text}"
                            merged_candidates.append(complete_node)
    
    return merged_candidates

def extract_fdd_headers(huridocs_json: Union[str, List[Dict[str, Any]]],
                      score_threshold: float = 60.0,
                      fallback_threshold: float = 50.0,
                      include_titles: bool = True) -> List[Dict[str, Any]]:
    """
    Main function to extract all 23 FDD item headers from Huridocs JSON.
    
    Args:
        huridocs_json: Either a file path to JSON or parsed JSON data
        score_threshold: Minimum score for primary matches
        fallback_threshold: Minimum score for fallback matches
        include_titles: Whether to include title nodes in candidates
        
    Returns:
        List of 23 dictionaries with extracted header metadata
    """
    # Load JSON if string path provided
    if isinstance(huridocs_json, str):
        nodes = load_huridocs_json(huridocs_json)
    else:
        nodes = huridocs_json
    
    # 1. Pre-filter candidate nodes
    candidates = filter_candidate_nodes(nodes, include_titles)
    
    # 2. Handle split headers
    candidates = find_split_headers(candidates, nodes)
    
    # 3. Find best matches
    best_matches = find_best_matches(
        candidates, 
        CANONICAL_ITEM_HEADERS, 
        ITEM_KEYWORDS, 
        score_threshold
    )
    
    # 4. Find fallbacks for missing items
    missing_items = [i for i in range(1, 24) if i not in best_matches]
    fallbacks = find_fallbacks(
        nodes, 
        missing_items, 
        CANONICAL_ITEM_HEADERS, 
        ITEM_KEYWORDS, 
        best_matches,
        fallback_threshold
    )
    
    # 5. Combine results
    all_matches = {**best_matches, **fallbacks}
    
    # 6. Determine section boundaries
    all_matches = determine_section_boundaries(all_matches, nodes)
    
    # 7. Create entries for any still-missing items
    final_results = []
    
    for item_num in range(1, 24):
        if item_num in all_matches:
            final_results.append(all_matches[item_num])
        else:
            # Create placeholder for missing item
            final_results.append({
                "item_number": item_num,
                "text": f"Item {item_num} - Not Found",
                "match_scores": {
                    "full": 0,
                    "label": 0,
                    "keywords": 0,
                    "final": 0
                },
                "page_number": None,
                "node_index": None,
                "start_node_index": None,
                "end_node_index": None,
                "start_page": None,
                "end_page": None,
                "alignment_score": 0
            })
    
    # Sort by item_number to ensure correct order
    final_results.sort(key=lambda x: x["item_number"])
    
    return final_results

def process_huridocs_file(file_path: str, 
                         output_path: Optional[str] = None,
                         score_threshold: float = 60.0,
                         fallback_threshold: float = 50.0) -> List[Dict[str, Any]]:
    """
    Process a Huridocs JSON file and optionally save results.
    
    Args:
        file_path: Path to Huridocs JSON file
        output_path: Optional path to save results JSON
        score_threshold: Minimum score for primary matches
        fallback_threshold: Minimum score for fallback matches
        
    Returns:
        List of extracted header metadata
    """
    results = extract_fdd_headers(
        file_path,
        score_threshold=score_threshold,
        fallback_threshold=fallback_threshold
    )
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
    
    return results

def validate_results(results: List[Dict[str, Any]]) -> List[str]:
    """
    Validate extraction results against required rules.
    
    Args:
        results: Extraction results to validate
        
    Returns:
        List of validation errors or empty list if all valid
    """
    errors = []
    
    # Check we have exactly 23 entries
    if len(results) != 23:
        errors.append(f"Expected 23 entries, found {len(results)}")
    
    # Check item_number uniqueness and range
    item_numbers = [item["item_number"] for item in results]
    if len(set(item_numbers)) != len(item_numbers):
        errors.append("Duplicate item numbers found")
    
    for num in item_numbers:
        if not 1 <= num <= 23:
            errors.append(f"Invalid item number: {num}")
    
    # Check section order follows node_index
    for i in range(len(results) - 1):
        current = results[i]
        next_item = results[i + 1]
        
        # Skip if either item has no node_index
        if current["node_index"] is None or next_item["node_index"] is None:
            continue
        
        if current["node_index"] >= next_item["node_index"]:
            errors.append(f"Item {current['item_number']} has higher node_index than Item {next_item['item_number']}")
    
    # Check page ranges
    last_end_page = None
    for item in results:
        # Skip if missing pages
        if item["start_page"] is None:
            continue
            
        # Check start_page <= end_page
        if item["end_page"] is not None and item["start_page"] > item["end_page"]:
            errors.append(f"Item {item['item_number']} has start_page > end_page")
        
        # Check item starts after previous item ended
        if last_end_page is not None and item["start_page"] < last_end_page:
            errors.append(f"Item {item['item_number']} starts before previous item ends")
            
        last_end_page = item["end_page"]
    
    return errors

def process_huridocs_directory(input_dir: str, 
                             output_dir: str = r"C:\Projects\File_Util_App\output\header_output",
                             score_threshold: float = 60.0,
                             fallback_threshold: float = 50.0) -> Dict[str, List[Dict[str, Any]]]:
    """
    Process all Huridocs JSON files in a directory and save results to output directory.
    Skip files that already have output files.
    
    Args:
        input_dir: Directory containing Huridocs JSON files
        output_dir: Directory to save output JSON files
        score_threshold: Minimum score for primary matches
        fallback_threshold: Minimum score for fallback matches
        
    Returns:
        Dictionary mapping filenames to their extraction results
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Track results for all files
    all_results = {}
    
    # Find all JSON files in the input directory
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    
    print(f"Found {len(json_files)} JSON files in {input_dir}")
    
    # Process each file
    skipped_files = 0
    processed_files = 0
    
    for i, filename in enumerate(json_files):
        input_path = os.path.join(input_dir, filename)
        
        # Create output filename
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}_extracted_headers.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Check if output file already exists
        if os.path.exists(output_path):
            print(f"[{i+1}/{len(json_files)}] Skipping: {filename} (output file already exists)")
            skipped_files += 1
            
            # Try to load existing results
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                all_results[filename] = results
            except Exception as e:
                print(f"  Error loading existing results: {str(e)}")
            
            continue
        
        print(f"[{i+1}/{len(json_files)}] Processing: {filename}")
        processed_files += 1
        
        try:
            # Process the file
            results = process_huridocs_file(
                input_path,
                output_path=output_path,
                score_threshold=score_threshold,
                fallback_threshold=fallback_threshold
            )
            
            # Validate results
            validation_errors = validate_results(results)
            if validation_errors:
                print(f"  Validation errors: {validation_errors}")
            else:
                print("  Validation passed")
                
            # Count found items
            found_items = len([item for item in results if item["node_index"] is not None])
            print(f"  Found {found_items} of 23 items")
            
            # Store results
            all_results[filename] = results
            
        except Exception as e:
            print(f"  Error processing file: {str(e)}")
    
    # Print summary
    print("\nProcessing Summary:")
    print(f"Skipped {skipped_files} files (already processed)")
    print(f"Processed {processed_files} new files")
    print(f"Total files tracked: {len(all_results)} of {len(json_files)}")
    
    return all_results

if __name__ == "__main__":
    # Process a directory of Huridocs JSON files
    input_dir = r"/Users/miller/Documents/GitHub/File_Util_App/data/huridoc_analysis_output"
    output_dir = r"/Users/miller/Documents/GitHub/File_Util_App\output\header_output"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Processing Huridocs JSON files from: {input_dir}")
    print(f"Saving results to: {output_dir}")
    
    # Process all files in the directory
    all_results = process_huridocs_directory(input_dir, output_dir)
    
    # Print final summary
    total_files = len(all_results)
    total_items = sum(len([item for item in results if item["node_index"] is not None]) 
                     for results in all_results.values())
    
    print(f"\nFinal Summary:")
    print(f"Processed {total_files} files")
    print(f"Found {total_items} items out of {total_files * 23} possible items")
    print(f"Average items per file: {total_items / total_files:.1f} (out of 23)") 