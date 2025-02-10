import re
import spacy
import fitz  

# Initialize the spaCy English language model. Consider using a larger model if more detailed NLP processing is required.
nlp = spacy.load("en_core_web_sm")

def extract_underwriting_discount_from_pdf(pdf_path):
    """
    Analyzes a PDF document to extract underwriting/purchaser discount values.
    
    Matches two different patterns:
    Pattern 1 (of format):
    - underwriting discount|fee|expenses of $XXX.XX
    - underwriter's/s' discount|fee|expenses of $XXX.XX
    - purchaser's/s' discount|fee|expenses of $XXX.XX
    
    Pattern 2 (is format):
    - The underwriting compensation|discount|fee ... is $XXX.XX
    
    Returns:
        str: The discount value (e.g., "$1,444.00"), or None if not found
    """
    # Pattern 1: "of $" format
    of_pattern = re.compile(
        r"(?:"                           # Start main non-capturing group
            r"(?:underwriting|underwriter|purchaser)"  # The main terms
            r"(?:s|['’]s|s['’]?)?\s+"    # Optional possessive forms with both apostrophe types
            r"(?:compensation|discount|fee|expenses)"  # The type of charge
            r"\s+of\s+"                  # " of " with flexible spacing
        r")"

        r"(\$\d+(?:,?\d+)*(?:\.\d+)?)", # Capture any number after $
        re.IGNORECASE | re.DOTALL
    )

    # Pattern 2: "is $" format
    is_pattern = re.compile(
        r"(?:"                           # Start main non-capturing group
            r"(?:underwriting|underwriter|purchaser)"  # The main terms
            r"(?:s|['’]s|s['’]?)?\s+"    # Optional possessive forms with both apostrophe types
            r"(?:compensation|discount|fee|expenses)"  # The type of charge
            r"[^$]*?"                    # Match any characters (non-greedy) until dollar sign
            r"is\s+"                     # Match "is" with optional whitespace
        r")"
        r"(\$\d+(?:,?\d+)*(?:\.\d+)?)", # Capture any number after $
        re.IGNORECASE | re.DOTALL
    )
    
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()
            
            # Try Pattern 1 first
            match = of_pattern.search(text)
            if match:
                return match.group(1)
            
            # If Pattern 1 fails, try Pattern 2
            match = is_pattern.search(text)
            if match:
                return match.group(1)
    
    return None

