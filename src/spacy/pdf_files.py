# Define a list of dictionaries to store PDF paths and their names
pdf_files = [
  {
    "path": r"C:\Users\quokka\Documents\Engineering Fun\scrape\muni_templates\idaho_health\IDHealthFacilities01a-FIN.pdf",
    "name": "idaho_health",
  },
  {
    "path": r"C:\Users\quokka\Documents\Engineering Fun\scrape\muni_templates\tufts\tufts.pdf",
    "name": "tufts",
  },
  {
    "path": r"C:\Users\quokka\Documents\Engineering Fun\scrape\muni_templates\maryland\maryland.pdf",
    "name": "maryland",
  },
  {
    "path": r"C:\Users\quokka\Documents\Engineering Fun\scrape\muni_templates\northwell\northwell.pdf",
    "name": "northwell",
  },
]

# # tests



# # Call the function and store the results
# pdf_results2 = find_underwriter.extract_party_names_from_pdf(pdf_files.pdf_path2)
# pdf_results3 = find_underwriter.extract_party_names_from_pdf(pdf_files.pdf_path3)
# pdf_results4 = find_underwriter.extract_party_names_from_pdf(pdf_files.pdf_path4)



# # Print the results
# print("PDF results:")

# print("Tufts")
# print("Lead Underwriter:", pdf_results2['underwriter_lead_left'])
# print("All Underwriters:", pdf_results2['underwriter_all'])

# print("Maryland")
# print("Lead Underwriter:", pdf_results3['underwriter_lead_left'])
# print("All Underwriters:", pdf_results3['underwriter_all'])

# print("Northwell")
# print("Lead Underwriter:", pdf_results4['underwriter_lead_left'])
# print("All Underwriters:", pdf_results4['underwriter_all'])

# # results:
# # Tufts
# # Lead Underwriter: J.P. Morgan Securities LLC
# # All Underwriters: ['J.P. Morgan Securities LLC']
# # Maryland
# # Lead Underwriter: Morgan Stanley & Co.
# # All Underwriters: ['Morgan Stanley & Co.', 'RBC Capital Markets', 'Loop Capital Markets LLC', 'Siebert Williams Shank & Co.']
# # Northwell
# # Lead Underwriter: None
# # All Underwriters: []

# # Test the function with various PDF files and print the results.
# test1 = extract_underwriting_discount_from_pdf(pdf_files.pdf_files[0]['path'])
# print(pdf_files.pdf_files[0]['name'], test1)

# test2 = extract_underwriting_discount_from_pdf(pdf_files.pdf_files[1]['path'])
# print(pdf_files.pdf_files[1]['name'], test2)

# test3 = extract_underwriting_discount_from_pdf(pdf_files.pdf_files[2]['path'])
# print(pdf_files.pdf_files[2]['name'], test3)

# test4 = extract_underwriting_discount_from_pdf(pdf_files.pdf_files[3]['path'])
# print(pdf_files.pdf_files[3]['name'], test4)
