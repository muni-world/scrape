import spacy
import fitz  # PyMuPDF; install via `pip install PyMuPDF`
import pdf_files

# Load the spaCy English model (you may try a larger model if needed)
nlp = spacy.load("en_core_web_md")

def unique_preserve_order(seq):
    """
    Remove duplicates from a list while preserving the original order.
    """
    seen = set()
    result = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def extract_party_names_from_pdf(pdf_path):
    """
    Process a PDF file page by page and extract organization names (ORG)
    that occur in sentences containing either of the phrases:
      - (the “Underwriters”)
      - are being purchased by

    Returns a dictionary with:
      - 'underwriter_lead_left': the first organization encountered (or None)
      - 'underwriter_all': a list of all unique organization names found
    """
    all_entities = []
    exclude_entities = {"Authority", "Underwriter", "Underwriters", "Purchaser", "Purchasers", "the Obligated Group Representative", "Issuer", "Obligated Group", "Bond Counsel", "DANSY", "LLC"}
    

    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()
            spacy_doc = nlp(text)
            for sent in spacy_doc.sents:
                sentence_lower = sent.text.lower()
                # Check if the sentence contains one of the target phrases
                if ('(“Underwriters”)' in sentence_lower or 
                    '(“Underwriter”)' in sentence_lower or
                    '(“Purchaser”)' in sentence_lower or
                    '(“Purchasers”)' in sentence_lower or
                    'are being purchased by' in sentence_lower):
                    for ent in sent.ents:
                        # Remove newline characters from entity text
                        clean_text = ent.text.replace("\n", "").strip()
                        if ent.label_ == "ORG" and clean_text not in exclude_entities:
                            all_entities.append(clean_text)
    
    all_entities = unique_preserve_order(all_entities)
    return {
        'underwriter_lead_left': all_entities[0] if all_entities else None,
        'underwriter_all': all_entities
    }




# Call the function and store the results
pdf_results2 = find_underwriter.extract_party_names_from_pdf(pdf_files.pdf_path2)
pdf_results3 = find_underwriter.extract_party_names_from_pdf(pdf_files.pdf_path3)
pdf_results4 = find_underwriter.extract_party_names_from_pdf(pdf_files.pdf_path4)



# Print the results
print("PDF results:")

print("Tufts")
print("Lead Underwriter:", pdf_results2['underwriter_lead_left'])
print("All Underwriters:", pdf_results2['underwriter_all'])

print("Maryland")
print("Lead Underwriter:", pdf_results3['underwriter_lead_left'])
print("All Underwriters:", pdf_results3['underwriter_all'])

print("Northwell")
print("Lead Underwriter:", pdf_results4['underwriter_lead_left'])
print("All Underwriters:", pdf_results4['underwriter_all'])

# results:
# Tufts
# Lead Underwriter: J.P. Morgan Securities LLC
# All Underwriters: ['J.P. Morgan Securities LLC']
# Maryland
# Lead Underwriter: Morgan Stanley & Co.
# All Underwriters: ['Morgan Stanley & Co.', 'RBC Capital Markets', 'Loop Capital Markets LLC', 'Siebert Williams Shank & Co.']
# Northwell
# Lead Underwriter: None
# All Underwriters: []

