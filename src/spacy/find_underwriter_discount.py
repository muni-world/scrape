import re
import spacy
import fitz  
import spacy.pdf_files as pdf_files

# Initialize the spaCy English language model. Consider using a larger model if more detailed NLP processing is required.
nlp = spacy.load("en_core_web_sm")

def extract_underwriting_discount_from_pdf(pdf_path):
    """
    Analyzes a PDF document page by page to identify and extract a single underwriting discount value.
    
    The discount value can be identified using two categories of phrases:
    
      1. Underwriting discount phrases:
         - Examples include: "underwriting discount of $1,444.00", "Underwriters’ discount of $1,630,010.14"
    
      2. Purchaser-related phrases (interpreted as the discount):
         - Examples include: "Purchaser’s Expenses of $xxx.xx", "Purchaser’s Fee and Purchaser’s Expenses of $758,951.40"
    
    The regular expressions are applied to the entire text of each page (using re.DOTALL) to ensure values are captured even if they span multiple lines.
    
    Returns:
      A string representing the discount value (e.g., "$1,444.00"), or None if no matching phrase is found.
    """
    # Define a regex pattern to match phrases indicating an underwriting discount.
    discount_pattern = re.compile(
        r"(?:underwriting|underwriters[’']?)\s+discount\s+of\s+(\$\d{1,3}(?:,\d{3})*(?:\.\d{2}))",
        re.IGNORECASE | re.DOTALL
    )
    
    # Define a regex pattern to match phrases related to purchaser expenses or fees, including combined phrases.
    purchaser_pattern = re.compile(
        r"purchaser(?:s|[’']s|s[’']?)?\s+"
        r"(?:fee|fees|expenses)"
        r"(?:\s+and\s+purchaser(?:s|[’']s|s[’']?)?\s+(?:fee|fees|expenses))?"
        r"\s+of\s+(\$\d{1,3}(?:,\d{3})*(?:\.\d{2}))",
        re.IGNORECASE | re.DOTALL
    )
    
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()  # Extracts text while preserving newlines.
            # Attempt to find a match for the underwriting discount pattern.
            match_discount = discount_pattern.search(text)
            if match_discount:
                return match_discount.group(1)
            # If no match is found, attempt to find a match for the purchaser pattern.
            match_purchaser = purchaser_pattern.search(text)
            if match_purchaser:
                return match_purchaser.group(1)
    return None

# Test the function with various PDF files and print the results.
test1 = extract_underwriting_discount_from_pdf(pdf_files.pdf_files[0]['path'])
print(pdf_files.pdf_files[0]['name'], test1)

test2 = extract_underwriting_discount_from_pdf(pdf_files.pdf_files[1]['path'])
print(pdf_files.pdf_files[1]['name'], test2)

test3 = extract_underwriting_discount_from_pdf(pdf_files.pdf_files[2]['path'])
print(pdf_files.pdf_files[2]['name'], test3)

test4 = extract_underwriting_discount_from_pdf(pdf_files.pdf_files[3]['path'])
print(pdf_files.pdf_files[3]['name'], test4)
