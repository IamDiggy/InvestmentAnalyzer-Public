# InvestmentAnalyzer

A Python command-line project for exploring public-company financial data from the U.S. Securities and Exchange Commission (SEC).

**Status:** Work in progress. The application is intended for learning and analysis, not investment advice.

## What it does

- Accepts a company name or ticker symbol.
- Retrieves company details and XBRL Company Facts through the SEC's public endpoints.
- Extracts selected annual financial figures from SEC filings.
- Builds a pandas table of up to five years of reported financial data when available.
- Calculates revenue growth, operating margin, and net margin where the underlying values are available.
- Prints a formatted financial summary in the terminal.

**Limitations:** SEC reporting practices and XBRL tags vary across issuers. Missing metrics, year-to-year comparability, and fiscal-period selection may affect outputs. Results should be checked against original SEC filings. Automated tests and a complete live-API verification are not yet provided.

## Requirements

- Python 3.10 or newer
- Packages listed in `requirements.txt`
- Internet connection for SEC data access

## Setup

1. Clone the repository and change into the project directory.
2. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Set `SEC_CONTACT_EMAIL` to an email address you are comfortable supplying to the SEC API as part of the required User-Agent identification. **Do not commit private contact information or credentials to Git.**

   macOS/Linux:

   ```bash
   export SEC_CONTACT_EMAIL="your-email@example.com"
   ```

   Windows PowerShell:

   ```powershell
   $env:SEC_CONTACT_EMAIL="your-email@example.com"
   ```

4. Run:

   ```bash
   python main.py
   ```

5. Enter a ticker (for example, `AAPL`) or a company name when prompted.

## Source files

- `main.py`: Command-line interface and terminal formatting.
- `sec_client.py`: SEC company lookup and Company Facts retrieval.
- `financials.py`: XBRL-tag selection, historical data preparation, and financial calculations.

## Data source and attribution

Financial facts come from the [SEC EDGAR APIs](https://www.sec.gov/edgar/sec-api-documentation). Information remains subject to the SEC's usage guidelines and the original filings.

## Project background

Independent Python learning project. The code is being refined as part of an early undergraduate data science portfolio.
