import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Optional, Any
import json # Added for loading JSON from file if needed
import html # Added for potentially cleaning HTML in table captions/bodies if used

# --- Configuration ---
MODEL_NAME = 'all-MiniLM-L6-v2'
SIMILARITY_THRESHOLD = 0.45 # Adjust based on testing

# --- Reference Data and Regex Patterns ---

def get_fdd_item_references() -> Dict[int, str]:
    """
    Returns a dictionary mapping Item numbers to reference text/keywords.
    NOTE: These are simplified examples. Enhance these significantly for production.
    """
    return {
        1: "The Franchisor, and any Parents, Predecessors, and Affiliates. Company information, history, related entities.",
        2: "Business Experience. Directors, trustees, general partners, principal officers, executives.",
        3: "Litigation. Lawsuits, legal actions involving the franchisor, predecessors, affiliates, key personnel.",
        4: "Bankruptcy. History of bankruptcy for the franchisor, predecessors, affiliates, key personnel.",
        5: "Initial Fees. Initial franchise fee, deposit, commitment fee, other payments before opening.",
        6: "Other Fees. Royalty, advertising, transfer, renewal, ongoing fees, payment schedule.",
        7: "Estimated Initial Investment. Table detailing startup costs: initial fee, real estate, equipment, inventory, working capital.",
        8: "Restrictions on Sources of Products and Services. Obligations to purchase or lease from specific suppliers, specifications, revenue.",
        9: "Franchisee's Obligations. Table referencing primary obligations under the franchise agreement.",
        10: "Financing. Franchisor financing arrangements offered to franchisees.",
        11: "Franchisor's Assistance, Advertising, Computer Systems, and Training. Pre-opening and ongoing assistance, advertising programs, required technology, training details.",
        12: "Territory. Exclusive or protected territory, conditions, rights reserved by franchisor.",
        13: "Trademarks. Principal trademarks, service marks, logos, registration status, usage restrictions.",
        14: "Patents, Copyrights, and Proprietary Information. Information regarding patents, copyrights, trade secrets, confidential information.",
        15: "Obligation to Participate in the Actual Operation of the Franchise Business. Requirement for franchisee or manager direct involvement.",
        16: "Restrictions on What the Franchisee May Sell. Limits on goods or services offered.",
        17: "Renewal, Termination, Transfer, and Dispute Resolution. Terms for renewal, termination causes, transfer conditions, dispute resolution methods (arbitration, mediation, litigation).",
        18: "Public Figures. Compensation or benefits given to public figures for promoting the franchise.",
        19: "Financial Performance Representations. Earnings claims, historical financial data provided to prospective franchisees (if any). Often states none are made.",
        20: "Outlets and Franchisee Information. Statistics on franchised and company-owned outlets, projected openings, franchisee lists.",
        21: "Financial Statements. Audited financial statements of the franchisor.",
        22: "Contracts. Copies of the franchise agreement and related contracts.",
        23: "Receipts. Acknowledgment of receipt pages for the franchisee to sign."
    }

def build_regex_patterns() -> Dict[int, re.Pattern]:
    """
    Builds regex patterns to identify FDD Item titles.
    Handles variations in spacing, punctuation, case, and Roman numerals.
    Targets start of the text block primarily.
    """
    patterns = {}
    roman = {
        1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX',
        10: 'X', 11: 'XI', 12: 'XII', 13: 'XIII', 14: 'XIV', 15: 'XV', 16: 'XVI', 17: 'XVII',
        18: 'XVIII', 19: 'XIX', 20: 'XX', 21: 'XXI', 22: 'XXII', 23: 'XXIII'
    }
    # Keywords to help anchor the regex (first few words of reference text)
    keywords = {i: " ".join(get_fdd_item_references()[i].split()[:4]).split('.')[0] for i in range(1, 24)}

    for i in range(1, 24):
        # Pattern: Optional "ITEM", number (arabic or roman), optional punctuation, optional few keywords.
        # Use non-capturing groups. Prioritize start of string (^). Allow flexibility.
        # Added (?!\s*\.\.\d) negative lookahead to help avoid matching TOC entries like "ITEM 1 ... ..1"
        pattern_str = rf"^(?:ITEM\s*)?(?:{i}|{roman[i]})\s*[:.-]?\s*(?:{keywords[i].replace('.', '')})?(?!\s*\.\.\s*\d)"
        patterns[i] = re.compile(pattern_str, re.IGNORECASE)
    return patterns

def clean_text(text: str) -> str:
    """Basic text cleaning."""
    if not isinstance(text, str):
        return ""
    # Remove common LaTeX-like formatting found in example
    text = re.sub(r'\\textsuperscript\{.*?\}', '', text)
    text = re.sub(r'\\mathrm\{.*?\}', '', text)
    # Replace multiple spaces/newlines with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    # Could add HTML unescaping if needed: text = html.unescape(text)
    return text

# --- Core Logic ---

class FDDItemIdentifier:
    """
    Identifies FDD Items using a hybrid Regex and Semantic Similarity approach,
    adapted for the specific JSON structure provided.
    """
    def __init__(self, model_name: str = MODEL_NAME, similarity_threshold: float = SIMILARITY_THRESHOLD):
        print(f"Loading Sentence Transformer model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Model loaded.")
        self.similarity_threshold = similarity_threshold
        self.item_references = get_fdd_item_references()
        self.regex_patterns = build_regex_patterns()

        print("Computing reference embeddings...")
        self.reference_texts = list(self.item_references.values())
        self.reference_item_numbers = list(self.item_references.keys())
        if hasattr(self.model, 'encode'):
             self.reference_embeddings = self.model.encode(self.reference_texts)
        else:
            raise RuntimeError("SentenceTransformer model not loaded correctly.")
        print("Reference embeddings computed.")

    def _get_text_from_element(self, element: Dict[str, Any]) -> Optional[str]:
        """Extracts relevant text from a JSON element for analysis."""
        element_type = element.get("type")
        text_content = None

        if element_type == "text":
            text_content = element.get("text")
        elif element_type == "table":
            # Prioritize table caption if it exists and isn't empty
            captions = element.get("table_caption", [])
            if captions and isinstance(captions, list) and captions[0]:
                 # Check if caption looks like an ITEM heading
                 caption_text = clean_text(captions[0])
                 # Simple check: does it start with ITEM or a number followed by space/punctuation?
                 if re.match(r"^(ITEM\s*)?(\d+|[IVXLCDM]+)\s*[:.-]?\s*", caption_text, re.IGNORECASE):
                      text_content = caption_text
                 # else: Optionally analyze table body or ignore table if caption isn't item-like
                 # print(f"Ignoring table caption (doesn't look like Item): {caption_text}")

        if text_content:
            return clean_text(text_content)
        return None # Return None if no relevant text found

    def _find_regex_match(self, text: str) -> Optional[int]:
        """Checks if the text strongly matches any Item title regex."""
        if not text: # Handles None or empty string
            return None

        cleaned_text = text.strip() # Already cleaned, but strip again just in case
        if not cleaned_text:
            return None

        # Check if text is very short - less likely to be a real heading
        if len(cleaned_text.split()) < 2 and not cleaned_text.upper().startswith("ITEM"):
             return None # Avoid matching just "1." or similar in short text blocks

        for item_num, pattern in self.regex_patterns.items():
            match = pattern.search(cleaned_text)
            # Match must be near the beginning
            if match and match.start() < 5:
                 # Heuristic: Check if it's likely a real heading vs incidental match
                 # Requires "ITEM" or match length > 3 or contains significant keywords
                 match_str = match.group(0).upper()
                 if "ITEM" in match_str or len(match.group(0)) > 4:
                     # print(f"Regex match found for Item {item_num} in text: '{cleaned_text[:50]}...'") # DEBUG
                     return item_num
        return None

    def _find_semantic_match(self, text_embedding: Optional[np.ndarray]) -> Optional[int]:
        """Finds the best semantic match above the threshold."""
        if text_embedding is None or text_embedding.size == 0:
             return None

        similarities = cosine_similarity(text_embedding.reshape(1, -1), self.reference_embeddings)[0]
        best_match_idx = np.argmax(similarities)
        best_score = similarities[best_match_idx]

        if best_score >= self.similarity_threshold:
            matched_item_num = self.reference_item_numbers[best_match_idx]
            # print(f"Semantic match found: Item {matched_item_num} (Score: {best_score:.2f})") # DEBUG
            return matched_item_num
        return None

    def _is_toc_entry(self, text: Optional[str], page_idx: int) -> bool:
        """
        Detects if a text is likely a Table of Contents entry rather than a real header.
        
        Args:
            text: The text to analyze
            page_idx: The page index where this text appears
            
        Returns:
            True if this is likely a TOC entry, False otherwise
        """
        # Common TOC indicators
        if not text:
            return False
            
        # Check for page number markers like "......" or dots followed by numbers
        toc_pattern = re.compile(r'\.{3,}|…|\s+\d+$|(?:Item|Section).+\.{2,}\s*\d+|\s+Page\s+\d+|table\s+of\s+contents', re.IGNORECASE)
        if toc_pattern.search(text):
            return True
            
        # Check if this is on a known TOC page (typically early in document, pages 1-6)
        if page_idx <= 6:
            # Look for multiple Item references in succession on same page
            item_refs = re.findall(r'(?:Item|ITEM)\s+\d+', text)
            if len(item_refs) > 1:
                return True
        
        return False
    
    def _select_best_header_match(self, candidates: List[Tuple[int, Dict[str, Any], float]]) -> Optional[Tuple[int, Dict[str, Any]]]:
        """
        Selects the best match from multiple candidates for the same Item header.
        
        Args:
            candidates: List of tuples (index, element, similarity_score)
            
        Returns:
            Tuple of (index, element) for the best match, or None if no candidates
        """
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0][0], candidates[0][1]
        
        # Filter out TOC entries
        non_toc_candidates = []
        for idx, element, score in candidates:
            text = self._get_text_from_element(element)
            page_idx = element.get('page_idx', 0)
            if text and not self._is_toc_entry(text, page_idx):
                non_toc_candidates.append((idx, element, score))
        
        if not non_toc_candidates:
            # If all were TOC entries, choose the best-scoring one
            return max(candidates, key=lambda x: x[2])[0:2]
        
        # If we have non-TOC candidates, choose the one with highest similarity score
        return max(non_toc_candidates, key=lambda x: x[2])[0:2]

    def identify_items(self, document_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes document elements (from JSON) to identify FDD Items.

        Args:
            document_elements: A list of dictionaries from the JSON structure.

        Returns:
            A list of dictionaries, where each dictionary represents an identified
            Item and contains 'item_number' and 'elements' (list of original dicts).
        """
        identified_items = []
        current_item_number: Optional[int] = None
        current_item_elements: List[Dict[str, Any]] = []
        other_elements: List[Dict[str, Any]] = [] # Elements before Item 1 or unassigned

        print(f"Processing {len(document_elements)} elements...")

        # --- Step 1: Extract text and compute embeddings ---
        texts_to_embed = []
        element_indices_with_text = [] # Keep track of which elements have text to embed
        all_analyzable_texts = [] # Store the text used for analysis for each element

        for i, element in enumerate(document_elements):
            analyzable_text = self._get_text_from_element(element)
            all_analyzable_texts.append(analyzable_text) # Store text (or None)
            if analyzable_text:
                texts_to_embed.append(analyzable_text)
                element_indices_with_text.append(i)

        print(f"Found {len(texts_to_embed)} elements with analyzable text.")
        print("Computing embeddings...")
        if texts_to_embed:
             try:
                 embeddings = self.model.encode(texts_to_embed, show_progress_bar=True)
                 print("Embeddings computed.")
             except Exception as e:
                  print(f"Error computing embeddings: {e}. Proceeding without semantic matching.")
                  embeddings = [] # Fallback
        else:
             embeddings = []
             print("No text found to embed.")

        # Create a mapping from original element index to its embedding
        element_embeddings = {idx: None for idx in range(len(document_elements))}
        for i, original_idx in enumerate(element_indices_with_text):
            if i < len(embeddings):
                element_embeddings[original_idx] = embeddings[i]

        # --- Step 2: Collect potential header matches ---
        potential_headers = {i: [] for i in range(1, 24)}  # Dict to store candidates for each item number
        
        for i, element in enumerate(document_elements):
            analyzable_text = all_analyzable_texts[i]
            if not analyzable_text:
                continue
                
            # Check for Regex match (strong indicator of a header)
            regex_match_item = self._find_regex_match(analyzable_text)
            if regex_match_item is not None:
                # Get similarity score for ranking
                element_embedding = element_embeddings.get(i)
                if element_embedding is not None:
                    similarities = cosine_similarity(element_embedding.reshape(1, -1), self.reference_embeddings)[0]
                    best_score = similarities[self.reference_item_numbers.index(regex_match_item)]
                else:
                    best_score = 0.0  # Default if no embedding
                
                # Store this candidate with its index, element data, and score
                potential_headers[regex_match_item].append((i, element, best_score))
        
        # --- Step 3: Process headers in order and assign elements ---
        last_header_idx = -1  # Index of the last confirmed header element
        
        for item_num in range(1, 24):
            candidates = potential_headers[item_num]
            if not candidates:
                continue
                
            # Select the best candidate for this item
            best_match = self._select_best_header_match(candidates)
            if not best_match:
                continue
                
            header_idx, header_element = best_match
            
            # Handle all the elements between the last header and this one
            if last_header_idx == -1:  # This is the first identified header
                # All elements before this are "other" (pre-item or cover pages)
                other_elements = document_elements[:header_idx]
                if other_elements:
                    identified_items.append({
                        "item_number": 0,
                        "elements": other_elements
                    })
            else:
                # Finalize the previous item with all elements between the last header and this one
                elements_for_prev_item = document_elements[last_header_idx:header_idx]
                if elements_for_prev_item:
                    identified_items.append({
                        "item_number": current_item_number,
                        "elements": elements_for_prev_item
                    })
            
            # Update tracking variables
            current_item_number = item_num
            last_header_idx = header_idx
            
        # Handle elements after the last identified header
        if last_header_idx >= 0 and last_header_idx < len(document_elements) - 1:
            remaining_elements = document_elements[last_header_idx:]
            if remaining_elements:
                identified_items.append({
                    "item_number": current_item_number,
                    "elements": remaining_elements
                })
                
        # If no headers were found at all
        if last_header_idx == -1:
            identified_items.append({
                "item_number": 0,
                "elements": document_elements
            })

        print(f"Identification complete. Found {len(identified_items)} sections.")
        return identified_items

# --- Example Usage ---

if __name__ == "__main__":
    # Fix the UnicodeDecodeError by specifying UTF-8 encoding and using a with statement
    json_file_path = r'9Round_Franchising_LLC_FDD_2024_ID636440/bbd94cce-d087-49e0-a7b7-ba787df47de7_content_list.json'
    with open(json_file_path, 'r', encoding='utf-8') as file:
        sample_json_data = json.load(file)
        
    # Initialize the identifier
    identifier = FDDItemIdentifier()

    # Identify items in the sample data
    identified_sections = identifier.identify_items(sample_json_data)

    # Print the results
    print("\n--- Identified Sections ---")
    for section in identified_sections:
        item_num = section["item_number"]
        num_elements = len(section["elements"])
        first_elem = section["elements"][0] if section["elements"] else {}
        first_text = clean_text(identifier._get_text_from_element(first_elem) or f"Type: {first_elem.get('type', 'N/A')}")

        print(f"\nItem {item_num} ({num_elements} elements)")
        print(f"  Starts with element type: '{first_elem.get('type', 'N/A')}', page: {first_elem.get('page_idx', 'N/A')}")
        print(f"  Starts with text: '{first_text[:100]}...'")
        # Optionally print all text for debugging:
        # for element in section["elements"]:
        #     elem_text = identifier._get_text_from_element(element)
        #     print(f"    - Page {element.get('page_idx')}, Type {element.get('type')}: {elem_text[:80] if elem_text else '(No analyzable text)'}...")

    print("\n--- Analysis Summary ---")
    identified_item_numbers = {s['item_number'] for s in identified_sections if s['item_number'] != 0}
    print(f"Identified Items: {sorted(list(identified_item_numbers))}")
    missing_items = set(range(1, 24)) - identified_item_numbers
    if missing_items:
        print(f"Potentially Missing Items: {sorted(list(missing_items))}")
    if any(s['item_number'] == 0 for s in identified_sections):
        print("Found content before Item 1 (assigned to Item 0).")