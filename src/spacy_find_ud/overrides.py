"""
Manual URL-to-Document Type Reference Book (Like a Cheat Sheet)
---------------------------------------------------------------
This file acts like a special dictionary that corrects categorziation mistakes from the scrape source. Often EMMA will mislabel things or use 10 different names for the same event type. This normalized the data.

How it works:
1. When the system finds a document with a URL (we use this as the unique identifier) 
2. It uses the manual label instead of what is scraped (if anything)

Example: For the URL "https://www.munios.com/...", we force the type to be
"COMMERCIAL PAPER OFFERING MEMORANDUM" instead of what it was previously scraped as. 
"""

overrides = {
    "https://www.munios.com/munios-notice.aspx?e=602FW": {
        "os_type": "COMMERCIAL PAPER OFFERING MEMORANDUM"
    },
    # Add other overrides as needed
}


# TODO: Look at Supplements and figure out how to adjust to ensure things are note duped.

# TODO: figure out how to combine remarkting 

# TOD: