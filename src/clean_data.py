"""
Data standardization module for financial institutions, law firms, and municipal advisors.

This module provides functionality to standardize company names across different
sources and formats, mapping various spellings and website domains to canonical
company names.
"""


from typing import Dict, List, Set, Optional
import re
from dataclasses import dataclass

@dataclass
class Company:
    """
    Represents a company with its canonical name and all known variations/websites.
    
    Attributes:
        canonical_name: The official/standardized company name
        name_variations: Set of alternative spellings/formats of the company name
        websites: Set of website domains associated with the company
    """
    canonical_name: str
    name_variations: Set[str]
    websites: Set[str]

class CompanyStandardizer:
    """
    Handles standardization of company names and websites to canonical forms.
    """
    
    def __init__(self):
        # Dictionary mapping canonical names to Company objects
        self.companies: Dict[str, Company] = {}
        
        # Lookup dictionaries for quick access
        self._name_to_canonical: Dict[str, str] = {}
        self._website_to_canonical: Dict[str, str] = {}
        
        # Initialize with known companies
        self.initialize_companies()
    
    def clean_website(self, url: Optional[str]) -> Optional[str]:
        """
        Extracts and standardizes domain from URL.
        
        Args:
            url: Raw website URL
            
        Returns:
            Cleaned domain name or None if invalid
        """
        if not url:
            return None
            
        # Remove http://, https://, and www.
        domain = re.sub(r"^(https?://)?(www\.)?", "", url.lower().strip())
        # Remove everything after the domain
        domain = domain.split("/")[0]
        
        return domain
    
    def add_company(
        self,
        canonical_name: str,
        name_variations: List[str],
        websites: List[str],
    ) -> None:
        """
        Adds a new company with all its variations and websites.
        
        Args:
            canonical_name: Official company name
            name_variations: List of alternative names/spellings
            websites: List of website URLs
        """
        # Create sets of cleaned variations and websites
        clean_variations = {name.strip() for name in name_variations}
        clean_websites = {
            domain for url in websites
            if (domain := self.clean_website(url))
        }
        
        # Create or update the company record
        self.companies[canonical_name] = Company(
            canonical_name=canonical_name,
            name_variations=clean_variations,
            websites=clean_websites,
        )
        
        # Update lookup dictionaries
        for variation in clean_variations:
            self._name_to_canonical[variation] = canonical_name
            
        for website in clean_websites:
            self._website_to_canonical[website] = canonical_name
    
    def extract_company_from_website(self, website: str) -> Optional[str]:
        """
        Attempts to extract a company name from a website URL.
        
        Args:
            website: Website URL to extract company name from
            
        Returns:
            Extracted company name or None if extraction not possible
        """
        if not website:
            return None
        
        # Clean the domain first
        domain = self.clean_website(website)
        if not domain:
            return None
        
        # Remove common TLDs
        domain = re.sub(r"\.(com|org|net|edu|gov|co\.uk|io)$", "", domain)
        
        # Split on dots and take first part
        parts = domain.split(".")
        if not parts:
            return None
        
        # Convert to title case and clean up
        company_name = parts[0].replace("-", " ").replace("_", " ").title()
        
        return company_name

    def get_canonical_name(self, raw_name: Optional[str]) -> Optional[str]:
        """
        Converts a raw company name to its canonical form.
        
        Args:
            raw_name: Raw company name with potential variations
            
        Returns:
            Canonical company name, or None if no match found
        """
        if not raw_name:
            return None
        
        # Check if this is actually a website URL
        if raw_name.startswith("http://") or raw_name.startswith("https://") or raw_name.startswith("www."):
            # Try to get canonical name from website
            canonical = self.get_canonical_name_from_website(raw_name)
            if canonical:
                return canonical
            
            print(f"WARNING: No standardized company found for website: {raw_name}")
            return None
            
        cleaned_name = raw_name.strip()
        return self._name_to_canonical.get(cleaned_name)
    
    def get_canonical_name_from_website(self, website: Optional[str]) -> Optional[str]:
        """
        Converts a website to its canonical company name.
        
        Args:
            website: Company website URL
            
        Returns:
            Canonical company name or None if no match
        """
        if not website:
            return None
            
        domain = self.clean_website(website)
        return self._website_to_canonical.get(domain)
    
    def get_company_info(self, identifier: str) -> Optional[Company]:
        """
        Gets all information about a company using either name or website.
        
        Args:
            identifier: Company name or website
            
        Returns:
            Company object if found, None otherwise
        """
        # Try as website first
        canonical = self.get_canonical_name_from_website(identifier)
        if not canonical:
            # Try as name if website lookup failed
            canonical = self.get_canonical_name(identifier)
            
        return self.companies.get(canonical)

    def initialize_companies(self):
        """
        Initialize the standardizer with known financial institutions and law firms.
        """
        # Underwriters (investment banks and securities firms)
        underwriters = [
            {
                "canonical_name": "Barclays Capital",
                "name_variations": [
                    "Barclays",
                    "BARCLAYS",
                    "Barclays Capital",
                    "BARCLAYS CAPITAL",
                    "Barclays Capital Inc.",
                ],
                "websites": [
                    "barclays.com",
                    "barclays.co.uk",
                ],
            },
            {
                "canonical_name": "BofA Securities",
                "name_variations": [
                    "Bank of America",
                    "BofA Securities",
                    "BofA Securities, Inc.",
                    "BofA Merrill Lynch",
                    "BOFA SECURITIES",
                    "BofA SECURITIES",
                    "Bank of America Securities",
                    "Bank of America Securities, Inc.",
                    "BofA"

                ],
                "websites": [
                    "bofaml.com",
                    "bankofamerica.com",
                ],
            },
            {
                "canonical_name": "KeyBanc Capital Markets",
                "name_variations": [
                    "KeyBanc Capital Markets",
                    "KeyBanc Capital Markets Inc.",
                    "KeyBanc",
                    "Key Capital Markets",
                    "Cain Brothers",
                    "Cain Brothers, a division of KeyBanc Capital Markets",
                ],
                "websites": [
                    "key.com",
                    "cainbrothers.com",
                ],
            },
            {
                "canonical_name": "Colliers Securities",
                "name_variations": [
                    "Colliers Securities",
                    "Colliers Securities LLC",
                    "COLLIERS",
                    "COLLIERS SECURITIES LLC",
                ],
                "websites": [
                    "colliers.com",
                ],
            },
            {
                "canonical_name": "Piper Sandler",
                "name_variations": [
                    "Piper Sandler",
                    "Piper Sandler & Co.",
                    "PIPER SANDLER",
                ],
                "websites": [
                    "pipersandler.com",
                ],
            },
            {
                "canonical_name": "Loop Capital Markets",
                "name_variations": [
                    "Loop Capital Markets",
                    "Loop Capital",
                    "LOOP CAPITAL",
                ],
                "websites": [
                    "loopcapital.com",
                ],
            },
            {
                "canonical_name": "Ziegler",
                "name_variations": [
                    "Ziegler",
                    "ZIEGLER",
                    "B.C. Ziegler",
                    "B.C. Ziegler and Company",
                ],
                "websites": [
                    "ziegler.com",
                ],
            },
            {
                "canonical_name": "Fifth Third Securities",
                "name_variations": [
                    "Fifth Third Securities",
                    "Fifth Third Securities, Inc.",
                    "Fifth Third Securities, Inc. (MA)",
                    "Fifth Third",
                    "FIFTH THIRD",
                    "5/3 Securities",
                ],
                "websites": [
                    "53.com",
                ],
            },
            {
                "canonical_name": "Goldman Sachs & Co. LLC",
                "name_variations": [
                    "Goldman Sachs",
                    "GOLDMAN SACHS",
                    "Goldman, Sachs & Co.",
                    "Goldman Sachs & Co.",
                    "Goldman Sachs & Co. LLC",
                    "Goldman Sachs & Co. LLC",
                    "GS",
                ],
                "websites": [
                    "goldmansachs.com",
                    "gs.com",
                ],
            },
            {
                "canonical_name": "J.P. Morgan",
                "name_variations": [
                    "JPMorgan",
                    "J.P. Morgan",
                    "JP Morgan",
                    "JPMorgan Chase",
                    "JPMORGAN",
                    "JPMorgan Chase & Co.",
                    "JPMorgan Chase & Co.",
                    "J.P. MORGAN",
                    "j.p. morgan",
                    "j.p morgan",
                    "j.p. morgan",
                    "j.p. morgan",
                    "j.p.morgan",
                    "jp morgan",
                    "jpmorgan",
                    "j. p. m o r g a n",
                    "j. p. morgan",
                    "j .p. morgan",
                    "j. p.morgan",
                    "j. p. morgan",
                    "pmorgan",
                ],
                "websites": [
                    "jpmorgan.com",
                    "jpmorganchase.com",
                ],
            },
            {
                "canonical_name": "Morgan Stanley",
                "name_variations": [
                    "Morgan Stanley",
                    "MORGAN STANLEY",
                    "Morgan Stanley & Co.",
                    "Morgan Stanley & Co. LLC",
                ],
                "websites": [
                    "morganstanley.com",
                ],
            },
            {
                "canonical_name": "Citigroup",

                "name_variations": [
                    "Citigroup",
                    "CITIGROUP",
                    "Citigroup Inc.",
                ],
                "websites": [
                    "citigroup.com",
                ],
            },
            {
                "canonical_name": "RBC Capital Markets",
                "name_variations": [
                    "RBC Capital Markets",
                    "RBC",
                    "Royal Bank of Canada",
                    "RBC CM",
                ],
                "websites": [
                    "rbccm.com",
                    "rbc.com",
                ],
            },
            {
                "canonical_name": "TD Securities",
                "name_variations": [
                    "TD Securities",
                    "TD SECURITIES",
                    "TD Securities Inc.",
                    "TD Securities LLC",
                ],
                "websites": [
                    "tdsecurities.com",
                    "td.com",
                ],
            },
            {
                "canonical_name": "Wells Fargo",
                "name_variations": [
                    "Wells Fargo",
                    "WELLS FARGO",
                    "Wells Fargo Securities",
                    "Wells Fargo Bank",
                    "Wells Fargo & Company",
                    "Wells Fargo Corporate & Investment Banking",
                    "Wells Fargo & Company, N.A.",
                ],
                "websites": [
                    "wellsfargo.com",
                ],

            },
            {
                "canonical_name": "Jefferies",
                "name_variations": [
                    "Jefferies",
                    "JEFFERIES",
                    "Jefferies LLC",
                    "Jefferies Group",
                ],
                "websites": [
                    "jefferies.com",
                ],
            },
            {
                "canonical_name": "Raymond James",
                "name_variations": [
                    "Raymond James",
                    "RAYMOND JAMES",
                    "Raymond James & Associates",
                ],
                "websites": [
                    "raymondjames.com",
                ],
            },
            {
                "canonical_name": "Truist",
                "name_variations": [
                    "Truist",
                    "TRUIST",
                    "Truist Securities",
                    "BB&T",
                    "SunTrust Robinson Humphrey",
                ],
                "websites": [
                    "truist.com",
                ],
            },
            {
                "canonical_name": "American Veterans Group",
                "name_variations": [
                    "American Veterans Group",
                    "American Veterans Group, PBC"
                ],
                "websites": [
                    "americanveteransgroup.com"
                ]
            },
            {
                "canonical_name": "Blaylock Van",
                "name_variations": [
                    "Blaylock Van",
                    "Blaylock Van, LLC"
                ],
                "websites": [
                    "blaylockvan.com"
                ]
            },
            {
                "canonical_name": "BNY Mellon Capital Markets",
                "name_variations": [
                    "BNY Mellon Capital Markets",
                    "BNY Mellon Capital Markets, LLC"
                ],
                "websites": [
                    "bnymellon.com"
                ]
            },
            {
                "canonical_name": "Siebert Williams Shank",
                "name_variations": [
                    "Siebert Williams Shank",
                    "Siebert Williams Shank & Co.",
                    "Siebert Williams Shank & Co., LLC",
                    "SWS",
                    "Siebert Williams",
                    "SIEBERT WILLIAMS SHANK",
                ],
                "websites": [
                    "siebertwilliams.com",
                ],
            },
            {
                "canonical_name": "Stephens Inc.",
                "name_variations": [
                    "Stephens",
                    "Stephens Inc.",
                    "Stephens Inc",
                    "STEPHENS",
                    "STEPHENS INC",
                ],
                "websites": [
                    "stephens.com",
                ],
            },
            {
                "canonical_name": "UBS Financial Services",
                "name_variations": [
                    "UBS",
                    "UBS Group",
                    "Ubs",
                    "UBS Financial",
                    "UBS Financial Services",
                    "UBS Financial Services Inc.",
                    "UBS Securities",
                    "UBS Investment Bank",
                ],
                "websites": [
                    "ubs.com",
                    "www.ubs.com",
                ],
            },
            {
                "canonical_name": "PNC Capital Markets",
                "name_variations": [
                    "PNC",
                    "PNC Capital Markets",
                    "PNC Capital Markets LLC",
                    "PNC CAPITAL MARKETS",
                    "PNC CAPITAL MARKETS LLC",
                    "PNC Bank",
                    "PNC Financial Services",
                ],
                "websites": [
                    "pnc.com",
                    "pnccapitalmarkets.com",
                ],
            },
            {
                "canonical_name": "HJ Sims",
                "name_variations": [
                    "HJ Sims",
                    "H.J. Sims",
                    "Herbert J. Sims",
                    "Herbert J. Sims & Co.",
                    "Herbert J. Sims & Co., LLC",
                    "HJS",
                    "HJSIMS",
                ],
                "websites": [
                    "hjsims.com",
                ],
            },
            {
                "canonical_name": "U.S. Bank",
                "name_variations": [
                    "U.S. Bank",
                    "US Bank",
                    "USBank",
                    "U.S. Bancorp",
                    "US BANK",
                    "U.S. BANK",
                    "U.S. Bank National Association",
                ],
                "websites": [
                    "usbank.com",
                    "www.usbank.com",
                ],
            },
            {
                "canonical_name": "Northland Securities",
                "name_variations": [
                    "Northland Securities",
                    "Northland Securities, Inc.",
                    "NORTHLAND SECURITIES",
                    "Northland",
                    "NorthlandSecurities",
                    "Northland Capital Markets",
                ],
                "websites": [
                    "northlandsecurities.com",
                    "northlandcapitalmarkets.com",
                ],
            },
            {
                "canonical_name": "Academy Securities",
                "name_variations": [
                    "Academy Securities",
                    "Academy Securities, Inc.",
                    "ACADEMY SECURITIES",
                ],
                "websites": [
                    "academysecurities.com",
                ],
            },
            {
                "canonical_name": "AmeriVet Securities",
                "name_variations": [
                    "AmeriVet Securities",
                    "AmeriVet Securities, Inc.",
                    "AMERIVET SECURITIES",
                ],
                "websites": [
                    "amerivetsecurities.com",
                ],
            },
            {
                "canonical_name": "Bancroft Capital",
                "name_variations": [
                    "Bancroft Capital",
                    "Bancroft Capital, LLC",
                    "BANCROFT CAPITAL",
                ],
                "websites": [
                    "bancroft4vets.com",
                ],
            },
            {
                "canonical_name": "Cabrera Capital Markets",
                "name_variations": [
                    "Cabrera Capital Markets",
                    "Cabrera Capital Markets, LLC",
                    "CABRERA CAPITAL MARKETS",
                ],
                "websites": [
                    "cabreracapital.com",
                ],
            },
            {
                "canonical_name": "Davenport & Company",
                "name_variations": [
                    "Davenport & Company",
                    "Davenport & Company LLC",
                    "Davenport & Co.",
                    "DAVENPORT & COMPANY",
                ],
                "websites": [
                    "davenportllc.com",
                    "investdavenport.com",
                ],
            },
            {
                "canonical_name": "FHN Financial Capital Markets",
                "name_variations": [
                    "FHN Financial Capital Markets",
                    "FHN Financial",
                    "First Horizon",
                    "FHN FINANCIAL",
                ],
                "websites": [
                    "fhnfinancial.com",
                ],
            },
            {
                "canonical_name": "Huntington Capital Markets",
                "name_variations": [
                    "Huntington Capital Markets",
                    "Huntington",
                    "HUNTINGTON CAPITAL MARKETS",
                    "The Huntington Investment Company",
                ],
                "websites": [
                    "huntington.com",
                ],
            },
            {
                "canonical_name": "Janney Montgomery Scott",
                "name_variations": [
                    "Janney Montgomery Scott",
                    "Janney Montgomery Scott LLC",
                    "Janney",
                    "JANNEY MONTGOMERY SCOTT",
                ],
                "websites": [
                    "janney.com",
                ],
            },
            {
                "canonical_name": "Melvin Securities",
                "name_variations": [
                    "Melvin Securities",
                    "Melvin Securities, LLC",
                    "MELVIN SECURITIES",
                ],
                "websites": [
                    "melvinsecurities.com",
                ],
            },
            {
                "canonical_name": "Multi-Bank Securities",
                "name_variations": [
                    "Multi-Bank Securities",
                    "Multi-Bank Securities, Inc.",
                    "MULTI-BANK SECURITIES",
                    "MBS",
                ],
                "websites": [
                    "mbssecurities.com",
                ],
            },
            {
                "canonical_name": "Rice Financial Products Company",
                "name_variations": [
                    "Rice Financial Products Company",
                    "Rice Financial",
                    "RICE FINANCIAL PRODUCTS COMPANY",
                    "Rice Financial Products Co.",
                ],
                "websites": [
                    "ricefin.com",
                ],
            },
            {
                "canonical_name": "SMBC Nikko",
                "name_variations": [
                    "SMBC Nikko",
                    "SMBC Nikko Securities America",
                    "SMBC NIKKO",
                    "SMBC Nikko Securities",
                ],
                "websites": [
                    "smbcnikko-si.com",
                ],
            },
            {
                "canonical_name": "Ramirez & Co.",
                "name_variations": [
                    "Ramirez & Co.",
                    "Ramirez & Co., Inc.",
                    "RAMIREZ & CO., INC.",
                    "Ramirez",
                    "Samuel A. Ramirez & Company",
                ],
                "websites": [
                    "ramirezco.com",
                ],
            },
            {
                "canonical_name": "Estrada Hinojosa",
                "name_variations": [
                    "Estrada Hinojosa",
                    "Estrada Hinojosa & Company",
                    "Estrada Hinojosa & Company, Inc.",
                    "ESTRADA HINOJOSA",
                    "TRB Capital Markets",
                    "TRB Capital Markets, LLC",
                    "Estrada Hinojosa Investment Bankers",
                ],
                "websites": [
                    "ehmuni.com",
                    "estradahinojosa.com",
                ],
            },
            {
                "canonical_name": "Bryant Miller Olive",
                "name_variations": [
                    "Burke, Mayborn, O'Mara",
                    "Burke Mayborn O'Mara",
                    "Bryant Miller Olive",
                    "BMO Law",

                ],
                "websites": [
                    "bmolaw.com",
                ],
            },
            {
                "canonical_name": "Brown Hutchinson",
                "name_variations": [
                    "Brown Hutchinson",
                    "BROWN HUTCHINSON",
                    "Brown Hutchinson LLP",
                ],
                "websites": [
                    "brownhutchinson.com",
                ],
            },
            {
                "canonical_name": "Hardwick Shiver",
                "name_variations": [
                    "Hardwick Shiver",
                    "HARDWICK SHIVER",
                    "Hardwick Shiver Brown",
                    "HSB Law",
                ],
                "websites": [
                    "hsblawfirm.com",
                ],
            },
            {
                "canonical_name": "Katten Muchin Rosenman",
                "name_variations": [
                    "Katten Muchin Rosenman",
                    "Katten",
                    "KATTEN",
                    "Katten Law",
                ],
                "websites": [
                    "kattenlaw.com",
                ],
            },
            {
                "canonical_name": "Nabors, Giblin & Nickerson, P.A.",
                "name_variations": [
                    "NG&N",
                    "Nabors, Giblin & Nickerson",
                    "NGN Law",
                    "Nabors, Giblin & Nickerson, P.A.",	

                ],
                "websites": [
                    "ngnlaw.com",
                ],

            },
            {
                "canonical_name": "Pearlman & Miranda, LLC",
                "name_variations": [
                    "Pearlman & Miranda",
                    "Pearlman & Miranda, LLC",
                    "Pearlman and Miranda",
                    "PEARLMAN & MIRANDA",
                    "Pearlman Miranda",
                ],
                "websites": [
                    "pearlmanmiranda.com",
                ],
            },
            {
                "canonical_name": "Robinson Bradshaw",
                "name_variations": [
                    "Robinson Bradshaw",
                    "ROBINSON BRADSHAW",
                    "Robinson Bradshaw & Hinson",
                    "RBH Law",
                ],
                "websites": [
                    "rbh.com",
                    "robinsonbradshaw.com",
                ],
            },
            {
                "canonical_name": "Saul Ewing",
                "name_variations": [
                    "Saul Ewing",
                    "SAUL EWING",
                    "Saul Ewing LLP",
                    "Saul Ewing Arnstein & Lehr",
                ],
                "websites": [
                    "saul.com",
                ],
            },
            
        ]

        # Municipal Advisors
        municipal_advisors = [
            {
                "canonical_name": "Houlihan Lokey",
                "name_variations": [
                    "Houlihan Lokey",
                    "Houlihan Lokey Capital",
                    "Houlihan Lokey Capital, Inc",
                    "Houlihan Lokey Capital, Inc (MA)",
                ],
                "websites": [
                    "hl.com",
                ],
            },
            {
                "canonical_name": "Echo Financial Products",
                "name_variations": [
                    "Echo Financial Products",
                    "Echo Financial Products, LLC",
                    "Echo Financial Products, LLC (MA)",
                ],
                "websites": [
                    "echo-fp.com",
                ],
            },
            {
                "canonical_name": "Hilltop Securities",
                "name_variations": [
                    "Hilltop Securities",
                    "Hilltop Securities Inc.",
                    "Hilltop Securities Inc. (MA)",
                    "HilltopSecurities",
                    "HILLTOP",
                ],
                "websites": [
                    "hilltopsecurities.com",
                ],
            },
            {
                "canonical_name": "Kaufman Hall",
                "name_variations": [
                    "Kaufman Hall",
                    "Kaufman, Hall & Associates",
                    "Kaufman, Hall & Associates, LLC",
                    "Kaufman, Hall & Associates, LLC (MA)",
                    "kaufm (MA)",
                ],
                "websites": [
                    "kaufmanhall.com",
                ],
            },
            {
                "canonical_name": "PFM Financial Advisors",
                "name_variations": [
                    "PFM",
                    "PFM Financial Advisors",
                    "PFM Financial Advisors LLC",
                    "PFM Financial Advisors LLC (MA)",
                    "Public Financial Management",
                ],
                "websites": [
                    "pfm.com",
                ],
            },
        ]

        # Law Firms (keep existing law_firms list)
        law_firms = [
            {
                "canonical_name": "Cantu Harden Montoya",
                "name_variations": [
                    "Cantu Harden Montoya",
                    "CANTU HARDEN MONTOYA",
                    "Cantu Harden & Montoya",
                ],
                "websites": [
                    "cantuhardenmontoya.com",
                ],
            },
            {
                "canonical_name": "Murray Barnes Finister",
                "name_variations": [
                    "Murray Barnes Finister",
                    "Murray Barnes Law",
                    "MURRAY BARNES",
                ],
                "websites": [
                    "murraybarneslaw.com",
                ],
            },
            {
                "canonical_name": "Balch & Bingham",
                "name_variations": [
                    "Balch & Bingham",
                    "Balch and Bingham",
                    "BALCH",
                ],
                "websites": [
                    "balch.com",
                ],
            },
            {
                "canonical_name": "Ballard Spahr",
                "name_variations": [
                    "Ballard Spahr",
                    "BALLARD SPAHR",
                    "Ballard Spahr LLP",
                ],
                "websites": [
                    "ballardspahr.com",
                ],
            },
            {
                "canonical_name": "Bass Berry & Sims",
                "name_variations": [
                    "Bass Berry & Sims",
                    "Bass, Berry & Sims",
                    "BASS BERRY",
                ],
                "websites": [
                    "bassberry.com",
                ],
            },
            {
                "canonical_name": "Barnes & Thornburg",
                "name_variations": [
                    "Barnes & Thornburg",
                    "Barnes and Thornburg",
                    "BT Law",
                ],
                "websites": [
                    "btlaw.com",
                ],
            },
            {
                "canonical_name": "Bracewell",
                "name_variations": [
                    "Bracewell",
                    "Bracewell LLP",
                    "Bracewell Law",
                ],
                "websites": [
                    "bracewelllaw.com",
                ],
            },
            {
                "canonical_name": "Bricker & Eckler",
                "name_variations": [
                    "Bricker & Eckler",
                    "Bricker Graydon",
                    "BRICKER",
                ],
                "websites": [
                    "brickergraydon.com",
                ],
            },
            {
                "canonical_name": "Chapman and Cutler",
                "name_variations": [
                    "Chapman and Cutler",
                    "Chapman & Cutler",
                    "Chapman",
                ],
                "websites": [
                    "chapman.com",
                ],
            },
            {
                "canonical_name": "Dickinson Wright",
                "name_variations": [
                    "Dickinson Wright",
                    "DICKINSON WRIGHT",
                    "Dickinson Wright PLLC",
                ],
                "websites": [
                    "dickinson-wright.com",
                ],
            },
            {
                "canonical_name": "Dinsmore & Shohl",
                "name_variations": [
                    "Dinsmore & Shohl",
                    "Dinsmore",
                    "DINSMORE",
                ],
                "websites": [
                    "dinsmore.com",
                ],
            },
            {
                "canonical_name": "Dorsey & Whitney",
                "name_variations": [
                    "Dorsey & Whitney",
                    "Dorsey",
                    "DORSEY",
                ],
                "websites": [
                    "dorsey.com",
                ],
            },
            {
                "canonical_name": "Foley & Lardner",
                "name_variations": [
                    "Foley & Lardner",
                    "Foley",
                    "FOLEY",
                ],
                "websites": [
                    "foley.com",
                ],
            },
            {
                "canonical_name": "Fox Rothschild",
                "name_variations": [
                    "Fox Rothschild",
                    "FOX ROTHSCHILD",
                    "Fox Rothschild LLP",
                ],
                "websites": [
                    "foxrothschild.com",
                ],
            },
            {
                "canonical_name": "Gilmore & Bell",
                "name_variations": [
                    "Gilmore & Bell",
                    "Gilmore and Bell",
                    "GILMORE BELL",
                ],
                "websites": [
                    "gilmorebell.com",
                ],
            },
            {
                "canonical_name": "Harris Beach",
                "name_variations": [
                    "Harris Beach",
                    "HARRIS BEACH",
                    "Harris Beach PLLC",
                ],
                "websites": [
                    "harrisbeach.com",
                ],
            },
            {
                "canonical_name": "Hawkins Delafield & Wood",
                "name_variations": [
                    "Hawkins Delafield & Wood",
                    "Hawkins",
                    "HAWKINS",
                ],
                "websites": [
                    "hawkins.com",
                ],
            },
            {
                "canonical_name": "Kutak Rock",
                "name_variations": [
                    "Kutak Rock",
                    "KUTAK ROCK",
                    "Kutak Rock LLP",
                ],
                "websites": [
                    "kutakrock.com",
                ],
            },
            {
                "canonical_name": "McGuireWoods",
                "name_variations": [
                    "McGuireWoods",
                    "McGuire Woods",
                    "MCGUIREWOODS",
                ],
                "websites": [
                    "mcguirewoods.com",
                ],
            },
            {
                "canonical_name": "Mintz Levin",
                "name_variations": [
                    "Mintz Levin",
                    "Mintz",
                    "MINTZ",
                ],
                "websites": [
                    "mintz.com",
                ],
            },
            {
                "canonical_name": "Norton Rose Fulbright",
                "name_variations": [
                    "Norton Rose Fulbright",
                    "Norton Rose",
                    "NORTON ROSE FULBRIGHT",
                ],
                "websites": [
                    "nortonrosefulbright.com",
                ],
            },
            {
                "canonical_name": "Orrick Herrington",
                "name_variations": [
                    "Orrick Herrington",
                    "Orrick",
                    "ORRICK",
                ],
                "websites": [
                    "orrick.com",
                ],
            },
            {
                "canonical_name": "Quarles & Brady",
                "name_variations": [
                    "Quarles & Brady",
                    "Quarles",
                    "QUARLES",
                ],
                "websites": [
                    "quarles.com",
                ],
            },
            {
                "canonical_name": "Squire Patton Boggs",
                "name_variations": [
                    "Squire Patton Boggs",
                    "Squire",
                    "SQUIRE PATTON BOGGS",
                ],
                "websites": [
                    "squirepattonboggs.com",
                ],
            },
            {
                "canonical_name": "Taft Stettinius & Hollister",
                "name_variations": [
                    "Taft Stettinius & Hollister",
                    "Taft Law",
                    "TAFT",
                ],
                "websites": [
                    "taftlaw.com",
                ],
            },
            {
                "canonical_name": "Holley Pearson Farrer",
                "name_variations": [
                    "Holley Pearson Farrer",
                    "Holley Pearson Farrer & Associates"
                ],
                "websites": [
                    "holleypearsonfarrer.com"
                ]
            },
            {
                "canonical_name": "Hinckley Allen",
                "name_variations": [
                    "Hinckley Allen",
                    "HINCKLEY ALLEN",
                    "Hinckley Allen LLP",
                ],
                "websites": [
                    "hinckleyallen.com",  # Existing website
                    "www.hinckleyallen.com",  # New website to add
                ],
            },
        ]

        # Combine all categories
        all_companies = underwriters + municipal_advisors + law_firms
        
        # Add all companies to the standardizer
        for company in all_companies:

            self.add_company(
                canonical_name=company["canonical_name"],
                name_variations=company["name_variations"],
                websites=company["websites"],
            )
