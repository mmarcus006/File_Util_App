"""                                                            # ← Module-level docstring: explains the purpose of this test file.
End-to-end and unit tests for header_extraction.py
Run with:  pytest -q
"""

from pathlib import Path                                        # ← Standard library import for filesystem paths (OS-agnostic).
import json                                                     # ← Built-in JSON parser; we need it to load the Huridocs nodes.
import pytest                                                   # ← The testing framework we’re using.
from header_extraction.exceptions import HeaderExtractionError

import fdd_pipeline.header_extraction as he                                  # ← The module under test, imported with a short alias.

# ---------- Fixtures ---------------------------------------------------------  # ← Comment block visually separates sections.

@pytest.fixture(scope="session")                                 # ← Pytest decorator: create a fixture once per test session.
def sample_nodes():                                              # ← Fixture function name. Tests can depend on it by param name.
    data_path = Path(__file__).parent / "data" / "sample_huridocs.json"  # ← Build path to bundled JSON test file.
    return json.loads(data_path.read_text(encoding="utf-8"))     # ← Load and return parsed JSON list of page nodes.
    
# ---------- Pure helper tests -----------------------------------------------

@pytest.mark.parametrize(   # ← Run this test 4 times with different (text, expected) pairs.
"text,expected",          # ← Names of the parameters injected into the test function.
[
("Item 3", 3),                      # ← Case 1: simple Arabic numeral.
("ITEM VII", 7),                    # ← Case 2: Roman numeral uppercase.
("Item 17: Renewal", 17),           # ← Case 3: label plus extra text.
("Completely unrelated", None),     # ← Case 4: not a header → expect None.
],
)
def test_extract_item_number(text, expected): # ← Test function executes once per param set.
    assert he.extract_item_number(text) == expected # ← Assertion: helper returns correct number.

def test_alignment_score_bounds(): # ← Second unit test for calculate_alignment_score().
    node = {"left": 0, "width": 100, "page_width": 612}          # ← Minimal fake node dict with geometry fields.
    assert 0.0 <= he.calculate_alignment_score(node) <= 1.0      # ← Output should always be in [0,1].

# ---------- End-to-end happy path -------------------------------------------  # ← Section for higher-level “works as a whole” test.

def test_extract_fdd_headers_happy(sample_nodes):                # ← Uses the fixture; pytest injects parsed JSON.
    headers = he.extract_fdd_headers(sample_nodes, score_threshold=60)  # ← Run the real extraction pipeline.
    # 1. exactly 23 items
    assert len(headers) == 23                                    # ← Invariant: an FDD must have Items 1-23 inclusive.
    # 2. all item numbers unique & in order
    nums = [h.item_number for h in headers]                      # ← Pull out just the item numbers.
    assert nums == sorted(nums) == list(range(1, 24))            # ← They must be 1-23 in ascending order.
    # 3. sanity anchor checks
    item1 = headers[0]                                           # ← First header in list is Item 1.
    assert item1.item_number == 1                                # ← Confirm again.
    assert item1.start_page == 8            # anchor             # ← We know from fixture the first header is on page 1.
    assert "Item 1" in item1.header_text                         # ← Header text should literally contain “Item 1”.
    # 4. every header above threshold
    assert all(h.confidence_score >= 60 for h in headers)        # ← None of them should drop below our scoring threshold.

def test_validation_no_errors(sample_nodes):                     # ← Checks the separate structural validator helper.
    headers = he.extract_fdd_headers(sample_nodes)               # ← Extract first.
    errors = he.validate_section_headers(headers)                # ← Validate.
    assert errors == []                                          # ← Expect zero validation errors.

# ---------- Edge cases -------------------------------------------------------

def test_missing_headers_fallback(sample_nodes, monkeypatch):    # ← monkeypatch fixture allows temporary changes.
    """
    Remove all occurrences of 'Item 5' to force fallback logic.
    """
    hacked = [n for n in sample_nodes if "Item 5" not in n.get("text", "")]  # ← Filter nodes so Item 5 is absent.
    headers = he.extract_fdd_headers(hacked, score_threshold=60, fallback_threshold=40)  # ← Run extractor with looser fallback.
    # Item 5 should still exist but with low confidence
    
    item5 = next(h for h in headers if h.item_number == 5)       # ← Find the reconstructed Item 5 header.
    assert item5.confidence_score < 60    # ← It should fall below primary threshold...
    assert item5.header_text.upper().startswith(("ITEM 5", "INITIAL FEES")) # ← ...but still capture the correct label.

def test_error_on_garbage_input():        # ← Ensures predictable exception handling.
    with pytest.raises(HeaderExtractionError):     # ← Context mgr: test passes only if exception is raised.
        he.extract_fdd_headers("not a path and not a list")      # ← Pass nonsense input → should raise our custom error.
