import json
import os
import sys
from typing import Dict, Any, List
from fdd_header_extraction import process_huridocs_file, validate_results

def test_fdd_header_extraction(huridocs_file_path: str, 
                             output_path: str = None,
                             score_threshold: float = 60.0,
                             fallback_threshold: float = 50.0) -> None:
    """
    Test the FDD header extraction on a Huridocs JSON file.
    
    Args:
        huridocs_file_path: Path to the Huridocs JSON file
        output_path: Optional path to save results JSON
        score_threshold: Minimum score for primary matches
        fallback_threshold: Minimum score for fallback matches
    """
    print(f"Processing file: {huridocs_file_path}")
    
    # Process the file
    try:
        results = process_huridocs_file(
            huridocs_file_path,
            output_path=output_path,
            score_threshold=score_threshold,
            fallback_threshold=fallback_threshold
        )
        
        # Validate the results
        validation_errors = validate_results(results)
        
        # Print summary statistics
        found_items = [item for item in results if item["node_index"] is not None]
        missing_items = [item for item in results if item["node_index"] is None]
        
        print(f"\nExtraction Summary:")
        print(f"- Found {len(found_items)} of 23 items")
        print(f"- Missing {len(missing_items)} items")
        
        if missing_items:
            print("\nMissing Items:")
            for item in missing_items:
                print(f"- Item {item['item_number']}")
                
        print("\nScore Distribution:")
        score_ranges = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "50-59": 0,
            "< 50": 0
        }
        
        for item in found_items:
            final_score = item["match_scores"]["final"]
            if final_score >= 90:
                score_ranges["90-100"] += 1
            elif final_score >= 80:
                score_ranges["80-89"] += 1
            elif final_score >= 70:
                score_ranges["70-79"] += 1
            elif final_score >= 60:
                score_ranges["60-69"] += 1
            elif final_score >= 50:
                score_ranges["50-59"] += 1
            else:
                score_ranges["< 50"] += 1
                
        for range_name, count in score_ranges.items():
            print(f"- {range_name}: {count} items")
        
        # Show validation errors if any
        if validation_errors:
            print("\nValidation Errors:")
            for error in validation_errors:
                print(f"- {error}")
        else:
            print("\nAll validation checks passed!")
            
        # Print a few examples of matched headers
        if found_items:
            print("\nExample Matched Headers:")
            samples = found_items[:3] if len(found_items) >= 3 else found_items
            for item in samples:
                print(f"Item {item['item_number']}: {item['text']}")
                print(f"  Page: {item['page_number']}, Score: {item['match_scores']['final']:.1f}")
                print(f"  Match details: Full={item['match_scores']['full']}, "
                      f"Label={item['match_scores']['label']}, "
                      f"Keywords={item['match_scores']['keywords']}")
                
        return results
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Check if a file path was provided as a command-line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = None
        
        # Check if an output file was provided
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
            
        # Run the test
        test_fdd_header_extraction(input_file, output_file)
    else:
        # If no file was provided, look for a sample file in the data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "data", "huridoc_analysis_output")
        
        # Get the first JSON file in the directory
        json_files = [f for f in os.listdir(data_dir) if f.endswith("_huridocs_analysis.json")]
        
        if json_files:
            sample_file = os.path.join(data_dir, json_files[0])
            output_file = os.path.splitext(sample_file)[0] + "_extracted_headers.json"
            
            print(f"No file specified, using sample file: {sample_file}")
            test_fdd_header_extraction(sample_file, output_file)
        else:
            print("No sample files found in the data directory and no file provided as argument.")
            print("Usage: python fdd_header_test.py [input_file] [output_file]") 