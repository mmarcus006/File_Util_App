from typing import List, Dict, Any, Optional, Tuple
import re
from datetime import datetime
from .models import FDDItem1, FDDItem7, FDDItem19

def validate_item1(item_data: FDDItem1) -> List[str]:
    """Validate Item 1 data for consistency and completeness."""
    warnings = []
    
    # Check for missing brand name
    if not item_data.brand_name:
        warnings.append("Missing brand name in Item 1")
    
    # Check if phone number follows expected format
    if item_data.phone_number and not re.match(r'^\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$', item_data.phone_number):
        warnings.append(f"Phone number format is unusual: {item_data.phone_number}")
    
    # Check website URL format
    if item_data.website and not item_data.website.startswith(('http://', 'https://')):
        warnings.append(f"Website URL may be incomplete: {item_data.website}")
    
    return warnings

# Implement similar validation functions for other items