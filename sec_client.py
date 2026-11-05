import re
import requests


class SECClient:
    COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    COMPANY_FACTS_URL = (
        "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    )

    def __init__(self, user_agent):
        """
        user_agent example:
        "InvestmentAnalyzer contact@example.com"
        """

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate"
        })

        self._company_index = None

    def _get_json(self, url):
        """
        Sends a GET request and returns JSON.
        Raises an error if the request fails.
        """

        response = self.session.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    def _load_company_index(self):
        """
        Downloads the SEC ticker/CIK company database.

        The result is cached so we do not download it
        again every time find_company() is called.
        """

        if self._company_index is None:
            self._company_index = self._get_json(
                self.COMPANY_TICKERS_URL
            )

        return self._company_index

    @staticmethod
    def _normalize_text(text):
        """
        Makes company-name matching a little more forgiving.

        Example:
        "Apple Inc."
        becomes
        "APPLEINC"
        """

        return re.sub(
            r"[^A-Z0-9]",
            "",
            text.upper()
        )

    def find_company(self, query):
        """
        Finds a company using either:

        - ticker
        - exact company name
        - normalized company name
        - partial company name

        Returns company information including its CIK.
        """

        query = query.strip()

        if not query:
            raise ValueError(
                "Company name or ticker cannot be empty."
            )

        companies = self._load_company_index()

        company_list = list(companies.values())

        query_upper = query.upper()
        normalized_query = self._normalize_text(query)

        # -----------------------------------------
        # 1. Exact ticker match
        # -----------------------------------------

        for company in company_list:

            if company["ticker"].upper() == query_upper:

                return self._build_company_result(
                    company,
                    company_list
                )

        # -----------------------------------------
        # 2. Exact company-name match
        # -----------------------------------------

        for company in company_list:

            if company["title"].upper() == query_upper:

                return self._build_company_result(
                    company,
                    company_list
                )

        # -----------------------------------------
        # 3. Normalized company-name match
        # -----------------------------------------

        for company in company_list:

            normalized_title = self._normalize_text(
                company["title"]
            )

            if normalized_title == normalized_query:

                return self._build_company_result(
                    company,
                    company_list
                )

        # -----------------------------------------
        # 4. Partial company-name match
        # -----------------------------------------

        matches = []

        for company in company_list:

            if query_upper in company["title"].upper():
                matches.append(company)

        # Remove duplicates caused by companies
        # having multiple share classes.
        unique_matches = {}

        for company in matches:

            cik = company["cik_str"]

            if cik not in unique_matches:
                unique_matches[cik] = company

        matches = list(unique_matches.values())

        if len(matches) == 1:

            return self._build_company_result(
                matches[0],
                company_list
            )

        if len(matches) > 1:

            names = [
                company["title"]
                for company in matches[:10]
            ]

            raise ValueError(
                f"Multiple companies matched '{query}'. "
                f"Try a ticker or a more specific name.\n"
                f"Matches: {', '.join(names)}"
            )

        raise ValueError(
            f"Company '{query}' was not found in the SEC database."
        )

    def _build_company_result(
        self,
        selected_company,
        company_list
    ):
        """
        Builds standardized company information.

        Also finds multiple ticker/share classes belonging
        to the same CIK.
        """

        cik = int(selected_company["cik_str"])

        tickers = sorted({
            company["ticker"]
            for company in company_list
            if int(company["cik_str"]) == cik
        })

        return {
            "title": selected_company["title"],
            "ticker": selected_company["ticker"],
            "tickers": tickers,
            "cik": cik,
            "cik_padded": str(cik).zfill(10)
        }

    def get_company_facts(self, cik):
        """
        Retrieves SEC Company Facts using a CIK.
        """

        cik_padded = str(cik).zfill(10)

        url = self.COMPANY_FACTS_URL.format(
            cik=cik_padded
        )

        return self._get_json(url)

    def get_company_data(self, query):
        """
        Main SEC method.

        Input:
            "GOOGL"
            "Alphabet Inc."
            "Apple"
            etc.

        Returns:
            company metadata
            raw SEC Company Facts
        """

        company = self.find_company(query)

        facts = self.get_company_facts(
            company["cik"]
        )

        return company, facts