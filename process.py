import re
import spacy

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Process the extracted text
doc = nlp(pdf_text)

# Define patterns or rules to extract the required information
# This is a simple example and might need to be adjusted based on the document's structure
issuer_name = None
obligor_name = None
total_par_amount = None
all_underwriters = []
lead_underwriters = []
co_underwriters = []

# Regular expression to match underwriters in the underwriting section
underwriters_pattern = re.compile(r"(?<=by\s)(.*?)(?=\s\(collectively, the “Underwriters”\))")

# Iterate over the sentences in the document
for sent in doc.sents:
    text = sent.text.strip()
    if "Issuer name:" in text:
        issuer_name = text.split("Issuer name:")[1].strip()
    elif "Obligor Name:" in text:
        obligor_name = text.split("Obligor Name:")[1].strip()
    elif "Total Par Amount:" in text:
        total_par_amount = text.split("Total Par Amount:")[1].strip()
    elif "UNDERWRITING" in text:
        # Find the underwriters in the underwriting section
        match = underwriters_pattern.search(text)
        if match:
            all_underwriters = match.group(1).split(", ")
    elif "Lead Underwriters:" in text:
        lead_underwriters = text.split("Lead Underwriters:")[1].strip().split(", ")
    elif "Co-underwriters:" in text:
        co_underwriters = text.split("Co-underwriters:")[1].strip().split(", ")

# Print the extracted information
print(f"Issuer Name: {issuer_name}")
print(f"Obligor Name: {obligor_name}")
print(f"Total Par Amount: {total_par_amount}")
print(f"All Underwriters: {all_underwriters}")
print(f"Lead Underwriters: {lead_underwriters}")
print(f"Co-underwriters: {co_underwriters}")