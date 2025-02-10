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

  For all patterns, only the number (without the "$") is captured.
  Example:
    Input: "Pursuant to ... less $725,500.00 of Underwriter's discount plus ..."
    Output: "725,500.00"

  Args:
    pdf_path (str): The file path to the PDF document.

  Returns:
    str or None: The extracted discount or fee amount (digits only), or None if not found.
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

  # Pattern 2: Matches phrases like "discount ... is $123.45"
  is_pattern = re.compile(
    r"(?:"                              # start non-capturing group
    r"(?:underwriting|underwriter|purchaser)"  # keywords
    r"(?:s|['’]s|s['’]?)?\s+"            # optional possessive forms
    r"(?:compensation|discount|fee|expenses)"  # type of charge
    r"[^$]*?"                           # non-greedy match until "$"
    r"is\s+"                            # match "is"
    r")"
    r"\$(\d+(?:,?\d+)*(?:\.\d+)?),?"      # capture number after "$"
    , re.IGNORECASE | re.DOTALL
  )

  # Pattern 3: Matches phrases like "will pay the underwriter(s)/purchaser(s) a fee"
  # then captures the first number after "$"
  will_pay_pattern = re.compile(
    r"(?:"                              # start non-capturing group
    r"will\s+pay\s+the\s+"               # match "will pay the"
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


  # Open the PDF document using the fitz library.
  with fitz.open(pdf_path) as doc:
    # Loop through each page in the PDF.
    for page in doc:
      text = page.get_text()

      # Try Pattern 1.
      match = of_pattern.search(text)
      if match:
        return match.group(1)

      # Try Pattern 2.
      match = is_pattern.search(text)
      if match:
        return match.group(1)

      # Try Pattern 3.
      match = will_pay_pattern.search(text)
      if match:
        return match.group(1)

      # Try Pattern 4.
      match = before_discount_pattern.search(text)
      if match:
        return match.group(1)

  # Return None if no patterns match.
  return None

