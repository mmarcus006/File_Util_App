"""
Entry point script for the FDD Verification Package.
"""

from fdd_verification.core import PDFProcessor, JSONProcessor, EnhancedVerificationEngine

__all__ = ['run_verification']

def run_verification(pdf_path, json_path, output_path=None, use_transformer=True, use_llm=True, verbose=False):
    """
    Run the verification process on the specified PDF and JSON files.
    
    Args:
        pdf_path: Path to the PDF file
        json_path: Path to the JSON file with header information
        output_path: Path to save the verification results (optional)
        use_transformer: Whether to use transformer-based verification
        use_llm: Whether to use LLM-based verification
        verbose: Whether to print verbose output
    
    Returns:
        dict: Verification results
    """
    if verbose:
        print(f"Processing PDF: {pdf_path}")
        print(f"Using header data from: {json_path}")
    
    # Initialize processors
    pdf_processor = PDFProcessor(pdf_path)
    json_processor = JSONProcessor(json_path)
    
    # Create verification engine
    engine = EnhancedVerificationEngine(
        pdf_processor, 
        json_processor,
        use_transformer=use_transformer,
        use_llm=use_llm
    )
    
    # Verify all headers
    if verbose:
        print("Verifying headers...")
    
    results = engine.verify_all_headers()
    
    # Get summary
    summary = engine.get_verification_summary()
    
    if verbose:
        print("\nVerification Summary:")
        print(f"Total headers: {summary['total']}")
        print(f"Verified: {summary['verified']}")
        print(f"Likely correct: {summary['likely_correct']}")
        print(f"Needs review: {summary['needs_review']}")
        print(f"Likely incorrect: {summary['likely_incorrect']}")
        print(f"Not found: {summary['not_found']}")
        
        print("\nVerification methods used:")
        for method, count in summary['by_method'].items():
            print(f"  {method}: {count}")
    
    # Save results to file if output path is provided
    if output_path:
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        if verbose:
            print(f"\nResults saved to: {output_path}")
    
    return results
