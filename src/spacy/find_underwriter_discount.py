import re
import spacy
import fitz  

# Initialize the spaCy English language model.
# Think of this model as a helper that understands English well.
nlp = spacy.load("en_core_web_sm")

def extract_underwriting_discount_from_pdf(pdf_path):
  """
  Analyzes a PDF document to extract underwriting/purchaser discount or fee amounts
  using four regex patterns.

  Pattern 1 ("of $" format):
    Matches phrases like:
      - "underwriting discount|fee|expenses of $XXX.XX"
      - "underwriter's/s' discount|fee|expenses of $XXX.XX"
      - "purchaser's/s' discount|fee|expenses of $XXX.XX"

  Pattern 2 ("is $" format):
    Matches phrases where a discount is stated with "is $XXX.XX"

  Pattern 3 ("will pay ... fee" format):
    Matches phrases like:
      "will pay the underwriter/underwriters/purchaser/purchasers a fee"
    and then ignores text until the dollar sign, capturing only the number after "$".

  Pattern 4 (New Pattern):
    Matches a dollar amount immediately followed by phrases like:
      "of underwriter's/underwriters'/purchaser's/purchasers' discount/fees"
    This pattern captures only the digits after "$".

  Pattern 5: Matches "$XXX.XX as compensation for underwriting/purchasing"

  For all patterns, only the number (without the "$") is captured.
  Example:
    Input: "Pursuant to ... less $725,500.00 of Underwriter's discount plus ..."
    Output: "725,500.00"

  Args:
    pdf_path (str): The file path to the PDF document.

  Returns:
    dict or None: The extracted discount or fee amount (digits only), or None if not found.
  """

  # Validate that pdf_path is a string.
  if not isinstance(pdf_path, str):
    raise TypeError("pdf_path must be a string")

  # Pattern 1: Matches phrases like "underwriting discount ... of $123.45"
  of_pattern = re.compile(
    r"(?:"                              # start non-capturing group
    r"(?:underwriting|underwriter|purchaser)"  # keywords
    r"(?:s|['’]s|s['’]?)?\s+"            # optional possessive forms
    r"(?:compensation|discount|fee|expenses)"  # type of charge
    r"\s+(?:[^$]*?\s+)?of\s+"            # match until "of"
    r")"
    r"\$(\d+(?:,?\d+)*(?:\.\d+)?),?"      # capture number after "$"
    , re.IGNORECASE | re.DOTALL
  )

  # Pattern 2: Matches phrases like "discount ... is $123.45" or "discount ... will be $123.45"
  is_pattern = re.compile(
    r"(?:"                              # start non-capturing group
    r"(?:underwriting|underwriter|purchaser)"  # keywords
    r"(?:s|['’]s|s['’]?)?\s*"            # optional possessive forms, with flexible spacing
    r"(?:compensation|discount|fee|expenses)"  # type of charge
    r"[\s\S]*?"                         # match any character including newlines (non-greedy)
    r"(?:is|will\s+be)\s*"              # match "is" or "will be" with flexible spacing
    r")"
    r"\$(\d+(?:,?\d+)*(?:\.\d+)?),?"      # capture number after "$"
    , re.IGNORECASE
  )

  # Pattern 3: Matches phrases like "will pay the underwriter(s)/purchaser(s) a fee"
  # or "will also pay the underwriter(s)/purchaser(s) a fee"
  # then captures the first number after "$"
  will_pay_pattern = re.compile(
    r"(?:"                              # start non-capturing group
    r"will\s+(?:also\s+)?pay\s+the\s+"  # match "will pay the" or "will also pay the"
    r"(?:underwriter(?:s)?|purchaser(?:s)?)"  # match keywords plus optional plural
    r"\s+a\s+fee"                         # match "a fee"
    r")"
    r".*?"                                # non-greedy match until "$"
    r"\$(\d+(?:,?\d+)*(?:\.\d+)?),?"      # capture number after "$"
    , re.IGNORECASE | re.DOTALL
  )

  # Pattern 4: Matches a dollar amount immediately before phrases like
  # "of underwriter's/underwriters'/purchaser's/purchasers' discount/fees"
  before_discount_pattern = re.compile(
    r"\$(\d+(?:,?\d+)*(?:\.\d+)?)"       # match "$" then capture number
    r"(?:\s+of\s+"                         # non-capturing group: " of "
    r"(?:underwriting|underwriter|purchaser)"  # keywords
    r"(?:s|['’]s|s['’]?)?\s+"                # optional possessive forms
    r"(?:discount|fees|expenses))",                    # capture "discount" or "fees"
    re.IGNORECASE | re.DOTALL
  )

  # Pattern 5: Matches "$XXX.XX as compensation for underwriting/purchasing"
  compensation_pattern = re.compile(
    r"\$(\d+(?:,?\d+)*(?:\.\d+?))"      # Capture the number after $
    r"(?:\s|\n)*as\s+compensation\s+for" # Match "as compensation for" with flexible whitespace
    r"(?:\s|\n)*"                        # Allow any whitespace/newlines
    r"(?:underwriting|purchasing)",       # Match either activity
    re.IGNORECASE | re.MULTILINE         # Add MULTILINE flag for better newline handling
  )

  # Initialize collection list (like empty folders for our findings)
  amounts = []
  
  with fitz.open(pdf_path) as doc:
    # Search every page/drawer in the PDF cabinet
    for page in doc:
      text = page.get_text()
      
      # Create list of all our search patterns
      patterns = [
        of_pattern, is_pattern, will_pay_pattern,
        before_discount_pattern, compensation_pattern
      ]
      
      # Check each pattern like using different search filters
      for pattern in patterns:
        # Find all matches in current page
        matches = pattern.finditer(text)
        for match in matches:
          # Clean and convert found numbers (remove $ and commas)
          amount_str = match.group(1).replace(",", "")
          try:
            amount = float(amount_str)
            amounts.append(amount)  # File the finding
          except ValueError:
            continue  # Skip invalid numbers like empty strings

  # Handle case where no amounts found
  if not amounts:
    return None

  # Analyze findings like sorting documents
  are_identical = len(set(amounts)) == 1  # Check if all copies are same
  total = amounts[0] if are_identical else sum(amounts)
  needs_review = len(amounts) > 1  # Flag if multiple documents found

  # Package results like final report
  return {
    "total": total,
    "scrape_breakdown": {
      "amounts": amounts,
      "are_amounts_identical": are_identical,
      "is_dupe_review_completed": not needs_review
    }
  }

