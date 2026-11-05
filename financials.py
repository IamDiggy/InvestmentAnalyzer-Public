from datetime import datetime

import pandas as pd


# =========================================================
# POSSIBLE XBRL TAGS
# =========================================================

FINANCIAL_TAGS = {

    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet"
    ],

    "operating_income": [
        "OperatingIncomeLoss"
    ],

    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss"
    ],

    "total_assets": [
        "Assets"
    ],

    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
    ]
}


# Metrics measured over a period of time.
DURATION_METRICS = {
    "revenue",
    "operating_income",
    "net_income"
}


# Metrics measured at one point in time.
INSTANT_METRICS = {
    "total_assets",
    "cash"
}


# =========================================================
# DATE HELPERS
# =========================================================

def _parse_date(date_string):
    """
    Converts:
        "2025-12-31"

    into a Python date object.
    """

    return datetime.strptime(
        date_string,
        "%Y-%m-%d"
    ).date()


def _duration_in_days(start, end):
    """
    Calculates how long a reported financial period lasted.
    """

    start_date = _parse_date(start)
    end_date = _parse_date(end)

    return (end_date - start_date).days


# =========================================================
# FACT VALIDATION
# =========================================================

def _is_valid_annual_fact(
    fact,
    metric_type
):
    """
    Determines whether an SEC fact looks like a legitimate
    annual 10-K observation.
    """

    if fact.get("form") not in {
        "10-K",
        "10-K/A"
    }:
        return False

    if fact.get("val") is None:
        return False

    if fact.get("end") is None:
        return False

    # -----------------------------------------
    # Duration metrics
    # Revenue, operating income, net income
    # -----------------------------------------

    if metric_type == "duration":

        start = fact.get("start")
        end = fact.get("end")

        if start is None:
            return False

        try:
            days = _duration_in_days(
                start,
                end
            )
        except ValueError:
            return False

        # Normal annual periods are roughly one year.
        # Gives room for 52/53-week fiscal years.
        if not 300 <= days <= 430:
            return False

    return True


# =========================================================
# GET HISTORY FOR ONE METRIC
# =========================================================

def get_annual_history(
    company_data,
    possible_tags,
    metric_type,
    unit="USD",
    years=5
):
    """
    Finds annual SEC data for one financial metric.

    Handles:

    - multiple possible XBRL tags
    - duplicated SEC observations
    - later 10-Ks repeating prior-year values
    - amended filings

    Data is deduplicated by the actual period-end date.
    """

    facts = company_data.get(
        "facts",
        {}
    )

    gaap_facts = facts.get(
        "us-gaap",
        {}
    )

    observations = {}

    # Earlier tags in possible_tags have higher priority.
    for priority, tag in enumerate(possible_tags):

        if tag not in gaap_facts:
            continue

        tag_data = gaap_facts[tag]

        units = tag_data.get(
            "units",
            {}
        )

        if unit not in units:
            continue

        for fact in units[unit]:

            if not _is_valid_annual_fact(
                fact,
                metric_type
            ):
                continue

            period_end = fact["end"]

            candidate = {
                "year": int(
                    period_end[:4]
                ),
                "value": fact["val"],
                "period_end": period_end,
                "filed": fact.get("filed"),
                "form": fact.get("form"),
                "accession": fact.get("accn"),
                "tag": tag,
                "priority": priority
            }

            existing = observations.get(
                period_end
            )

            if existing is None:
                observations[period_end] = candidate
                continue

            # Prefer higher-priority XBRL tags.
            if candidate["priority"] < existing["priority"]:

                observations[period_end] = candidate

                continue

            # If both use the same tag priority,
            # prefer the most recently filed version.
            if candidate["priority"] == existing["priority"]:

                candidate_filed = (
                    candidate["filed"] or ""
                )

                existing_filed = (
                    existing["filed"] or ""
                )

                if candidate_filed > existing_filed:

                    observations[period_end] = candidate

    if not observations:
        return []

    sorted_periods = sorted(
        observations.values(),
        key=lambda item: item["period_end"],
        reverse=True
    )

    selected = sorted_periods[:years]

    # Return oldest -> newest for financial modeling.
    selected.reverse()

    # Remove internal priority value.
    for item in selected:
        item.pop(
            "priority",
            None
        )

    return selected


# =========================================================
# LATEST FINANCIAL VALUE
# =========================================================

def get_latest_annual_value(
    company_data,
    possible_tags,
    metric_type,
    unit="USD"
):
    """
    Gets the most recent annual value for one metric.
    """

    history = get_annual_history(
        company_data=company_data,
        possible_tags=possible_tags,
        metric_type=metric_type,
        unit=unit,
        years=1
    )

    if not history:
        return None

    return history[0]


# =========================================================
# KEY FINANCIALS
# =========================================================

def get_key_financials(company_data):
    """
    Retrieves the latest annual:

    - revenue
    - operating income
    - net income
    - total assets
    - cash
    """

    results = {}

    for metric, tags in FINANCIAL_TAGS.items():

        if metric in DURATION_METRICS:
            metric_type = "duration"

        else:
            metric_type = "instant"

        results[metric] = get_latest_annual_value(
            company_data=company_data,
            possible_tags=tags,
            metric_type=metric_type
        )

    return results


# =========================================================
# HISTORICAL FINANCIALS
# =========================================================

def get_historical_financials(
    company_data,
    years=5
):
    """
    Retrieves several years of key historical financial data.
    """

    history = {}

    for metric, tags in FINANCIAL_TAGS.items():

        if metric in DURATION_METRICS:
            metric_type = "duration"

        else:
            metric_type = "instant"

        history[metric] = get_annual_history(
            company_data=company_data,
            possible_tags=tags,
            metric_type=metric_type,
            years=years
        )

    return history


# =========================================================
# CONVERT TO DATAFRAME
# =========================================================

def build_financial_dataframe(history):
    """
    Converts historical financial data into a pandas DataFrame.

    Example:

    Year | Revenue | Operating Income | Net Income | ...
    """

    rows = {}

    column_names = {
        "revenue": "Revenue",
        "operating_income": "Operating Income",
        "net_income": "Net Income",
        "total_assets": "Total Assets",
        "cash": "Cash"
    }

    for metric, values in history.items():

        column_name = column_names.get(
            metric,
            metric
        )

        for item in values:

            year = item["year"]

            if year not in rows:

                rows[year] = {
                    "Year": year
                }

            rows[year][column_name] = item["value"]

    if not rows:

        return pd.DataFrame()

    dataframe = pd.DataFrame(
        rows.values()
    )

    dataframe = dataframe.sort_values(
        "Year"
    )

    dataframe = dataframe.reset_index(
        drop=True
    )

    # =====================================================
    # ANALYTICAL METRICS
    # =====================================================

    if "Revenue" in dataframe.columns:

        dataframe["Revenue Growth"] = (
            dataframe["Revenue"].pct_change()
        )

    if (
        "Operating Income" in dataframe.columns
        and
        "Revenue" in dataframe.columns
    ):

        dataframe["Operating Margin"] = (
            dataframe["Operating Income"]
            / dataframe["Revenue"]
        )

    if (
        "Net Income" in dataframe.columns
        and
        "Revenue" in dataframe.columns
    ):

        dataframe["Net Margin"] = (
            dataframe["Net Income"]
            / dataframe["Revenue"]
        )

    return dataframe