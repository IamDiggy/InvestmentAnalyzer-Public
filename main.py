import os
import requests
import pandas as pd

from sec_client import SECClient

from financials import (
    get_key_financials,
    get_historical_financials,
    build_financial_dataframe
)


# =========================================================
# CONFIGURATION
# =========================================================

SEC_CONTACT_EMAIL = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
SEC_USER_AGENT = f"InvestmentAnalyzer {SEC_CONTACT_EMAIL}"


# =========================================================
# FORMATTING FUNCTIONS
# =========================================================

def format_currency(value):
    """
    Converts:

        350018000000

    into:

        $350.02B
    """

    if pd.isna(value):
        return "N/A"

    absolute_value = abs(value)

    if absolute_value >= 1_000_000_000_000:

        return (
            f"${value / 1_000_000_000_000:,.2f}T"
        )

    if absolute_value >= 1_000_000_000:

        return (
            f"${value / 1_000_000_000:,.2f}B"
        )

    if absolute_value >= 1_000_000:

        return (
            f"${value / 1_000_000:,.2f}M"
        )

    return f"${value:,.0f}"


def format_percent(value):
    """
    Converts:

        0.135

    into:

        13.5%
    """

    if pd.isna(value):
        return "-"

    return f"{value * 100:.1f}%"


# =========================================================
# DISPLAY COMPANY
# =========================================================

def print_company_information(company):
    print()
    print("=" * 60)
    print("COMPANY INFORMATION")
    print("=" * 60)
    print(f"Name:     {company['title']}")

    print(
        f"Ticker:   {company['ticker']}"
    )

    print(
        f"Tickers:  {', '.join(company['tickers'])}"
    )

    print(
        f"CIK:      {company['cik_padded']}"
    )


# =========================================================
# DISPLAY LATEST FINANCIALS
# =========================================================

def print_latest_financials(financials):

    print()

    print("=" * 60)

    print("LATEST ANNUAL FINANCIALS")

    print("=" * 60)

    display_names = {
        "revenue": "Revenue",
        "operating_income": "Operating Income",
        "net_income": "Net Income",
        "total_assets": "Total Assets",
        "cash": "Cash"
    }

    for metric, data in financials.items():

        name = display_names.get(
            metric,
            metric
        )

        if data is None:

            print(
                f"{name:<20} Not Found"
            )

            continue

        value = format_currency(
            data["value"]
        )

        period = data["period_end"]

        print(
            f"{name:<20} "
            f"{value:<15} "
            f"Period End: {period}"
        )


# =========================================================
# DISPLAY HISTORICAL DATAFRAME
# =========================================================

def print_historical_financials(dataframe):

    print()

    print("=" * 60)

    print("HISTORICAL FINANCIALS")

    print("=" * 60)

    if dataframe.empty:

        print(
            "No historical financial data found."
        )

        return

    display_df = dataframe.copy()

    currency_columns = [
        "Revenue",
        "Operating Income",
        "Net Income",
        "Total Assets",
        "Cash"
    ]

    percent_columns = [
        "Revenue Growth",
        "Operating Margin",
        "Net Margin"
    ]

    for column in currency_columns:

        if column in display_df.columns:

            display_df[column] = (
                display_df[column]
                .apply(format_currency)
            )

    for column in percent_columns:

        if column in display_df.columns:

            display_df[column] = (
                display_df[column]
                .apply(format_percent)
            )

    print(
        display_df.to_string(
            index=False
        )
    )


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    print()

    print(
        "Automated Investment Analyzer"
    )

    print(
        "-----------------------------"
    )

    company_input = input(
        "Enter company name or ticker: "
    ).strip()

    if not company_input:

        print(
            "You must enter a company name or ticker."
        )

        return

    # -----------------------------------------
    # Create SEC client
    # -----------------------------------------

    if not SEC_CONTACT_EMAIL:
        print("Set SEC_CONTACT_EMAIL to your contact email before running.")
        return

    sec_client = SECClient(
        user_agent=SEC_USER_AGENT
    )

    try:

        # -----------------------------------------
        # SEC lookup
        # -----------------------------------------

        company, company_data = (
            sec_client.get_company_data(
                company_input
            )
        )

        # -----------------------------------------
        # Financial processing
        # -----------------------------------------

        latest_financials = (
            get_key_financials(
                company_data
            )
        )

        historical_financials = (
            get_historical_financials(
                company_data,
                years=5
            )
        )

        dataframe = (
            build_financial_dataframe(
                historical_financials
            )
        )

        # -----------------------------------------
        # Output
        # -----------------------------------------

        print_company_information(
            company
        )

        print_latest_financials(
            latest_financials
        )

        print_historical_financials(
            dataframe
        )

    except ValueError as error:

        print()

        print(
            f"Company lookup error: {error}"
        )

    except requests.RequestException as error:

        print()

        print(
            "SEC request failed."
        )

        print(
            f"Details: {error}"
        )

    except KeyError as error:

        print()

        print(
            "Unexpected SEC data structure."
        )

        print(
            f"Missing field: {error}"
        )


# =========================================================
# RUN PROGRAM
# =========================================================

if __name__ == "__main__":

    main()