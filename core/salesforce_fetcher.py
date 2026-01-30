#!/usr/bin/env python
"""
Salesforce Loan Terms Fetcher
=============================
Fetches loan terms from Salesforce by loan ID or loan name.

Usage:
    from salesforce_fetcher import SalesforceFetcher

    # Initialize with credentials
    fetcher = SalesforceFetcher(
        client_id="your_client_id",
        client_secret="your_client_secret",
        client_url="https://your-instance.salesforce.com/services/oauth2/token"
    )

    # Fetch by loan ID
    loan_terms = fetcher.get_loan_terms_by_id("a0ial000003EBTKAA4")

    # Fetch by loan name (exact match)
    loan_terms = fetcher.get_loan_terms_by_name("Vitalia Stow - Preferred Equity")

    # Search loans by name prefix
    loans = fetcher.search_loans(name_prefix="Vitalia")
"""

import math
import re
import time
from typing import Any, Dict, List, Optional

from simple_salesforce import Salesforce
import pandas as pd


class SalesforceFetcher:
    """Salesforce client for fetching loan terms and related data."""

    def __init__(self, client_id: str, client_secret: str, client_url: str):
        """
        Initialize Salesforce fetcher with OAuth credentials.

        Args:
            client_id: Salesforce OAuth client ID
            client_secret: Salesforce OAuth client secret
            client_url: Salesforce OAuth token endpoint URL
        """
        self.credentials = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_url": client_url,
        }
        self._sf_connection = None

    def _connect(self) -> Salesforce:
        """Establish or return existing Salesforce connection."""
        if self._sf_connection is None:
            self._sf_connection = self._create_connection()
        return self._sf_connection

    def _create_connection(self) -> Salesforce:
        """Create a new Salesforce connection using OAuth client credentials."""
        import requests
        import base64

        client_id = self.credentials['client_id']
        client_secret = self.credentials['client_secret']
        client_url = self.credentials['client_url']

        authorization = base64.b64encode(
            bytes(f"{client_id}:{client_secret}", "ISO-8859-1")
        ).decode("ascii")

        headers = {
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        body = {"grant_type": "client_credentials"}

        response = requests.post(client_url, data=body, headers=headers)
        response_data = response.json()

        if "access_token" not in response_data:
            raise ConnectionError(f"Failed to authenticate with Salesforce: {response_data}")

        return Salesforce(
            instance_url=response_data["instance_url"],
            session_id=response_data["access_token"]
        )

    def _get_sf_data(self, object_name: str, field_names: List[str]) -> pd.DataFrame:
        """
        Query Salesforce object and return as DataFrame.

        Args:
            object_name: Salesforce object API name (e.g., "LLC_BI__Loan__c")
            field_names: List of field API names to retrieve

        Returns:
            DataFrame with uppercased column names
        """
        sf = self._connect()

        fields_str = ', '.join(field_names)
        query = f"SELECT {fields_str} FROM {object_name}"

        data = sf.query_all(query)
        records = data['records']

        # Remove Salesforce metadata attributes
        normalized_records = []
        for record in records:
            if 'attributes' in record:
                del record['attributes']
            normalized_records.append(record)

        # Convert to DataFrame
        if normalized_records:
            df = pd.DataFrame(normalized_records)
        else:
            df = pd.DataFrame(columns=field_names)

        # Uppercase all column names for consistency
        df.columns = df.columns.str.upper()

        return df

    def _filter_dataframe(self, df: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
        """Filter DataFrame by column/value if non-empty."""
        if df.empty:
            return df
        return df[df[column] == value].copy()

    def _records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to list of dictionaries, removing None values."""
        if df.empty:
            return []

        records = df.to_dict("records")

        # Remove None/NaN values from each record
        cleaned_records = []
        for record in records:
            cleaned_record = {
                key: value
                for key, value in record.items()
                if value is not None and not (isinstance(value, float) and math.isnan(value))
            }
            cleaned_records.append(cleaned_record)

        return cleaned_records

    def _dict_keys_upper(self, d):
        """Recursively convert all dictionary keys to uppercase."""
        if isinstance(d, dict):
            return {k.upper(): self._dict_keys_upper(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [self._dict_keys_upper(i) for i in d]
        else:
            return d

    def get_loan_terms_by_id(self, loan_id: str) -> Dict[str, Any]:
        """
        Fetch complete loan terms for a given loan ID.

        Args:
            loan_id: Salesforce loan identifier (18-character ID)

        Returns:
            Dictionary with loan terms including:
                - Core loan fields (ID, NAME, AMOUNT, dates, etc.)
                - PRICING_DETAILS: List of pricing/rate components
                - PAYMENT_DETAILS: List of payment streams
                - FEE_DETAILS: List of fees
                - DRAW_DETAILS: List of draw/funding schedules
                - A_B_AMOUNT_FACTOR: Factor for A/B tranche loans

        Raises:
            ValueError: If loan_id is empty or loan not found
        """
        if not loan_id:
            raise ValueError("loan_id must be provided.")

        sf = self._connect()

        # ===================================================================
        # 1. Fetch core loan information
        # ===================================================================
        loans_df = self._get_sf_data(
            "LLC_BI__Loan__c",
            [
                "ID",
                "NAME",
                "LLC_BI__Amount__c",
                "LLC_BI__Maturity_Date__c",
                "LLC_BI__CloseDate__c",
                "LLC_BI__First_Payment_Date__c",
                "LLC_BI__Term_Months__c",
                "LLC_BI__Amortized_Term_Months__c",
                "LLC_BI__Prepayment_Penalty__c",
                "cm_Prepayment_Minimal_Interest_Months__c",
                "LLC_BI__Prepayment_Penalty_Description__c",
                "LLC_BI__Funding_at_Close__c",
                "LLC_BI__ParentLoan__c",
            ],
        )

        loan_row = self._records(self._filter_dataframe(loans_df, "ID", loan_id))
        if not loan_row:
            raise ValueError(f"Loan {loan_id} not found in Salesforce.")

        loan_terms = loan_row[0]
        loan_name = loan_terms.get("NAME", "")

        # ===================================================================
        # 2. Handle A/B-Tranche logic
        # ===================================================================
        tranche_pattern = r'[AB][\s-]*[Tt]ranche'
        is_tranche_loan = re.search(tranche_pattern, loan_name)

        if is_tranche_loan and loan_terms.get("LLC_BI__PARENTLOAN__C"):
            parent_loan_id = loan_terms["LLC_BI__PARENTLOAN__C"]

            parent_loan_df = self._get_sf_data(
                "LLC_BI__Loan__c",
                ["ID", "LLC_BI__Amount__c"],
            )
            parent_loan_row = self._records(
                self._filter_dataframe(parent_loan_df, "ID", parent_loan_id)
            )

            if parent_loan_row and parent_loan_row[0].get("LLC_BI__AMOUNT__C"):
                parent_amount = parent_loan_row[0]["LLC_BI__AMOUNT__C"]
                this_loan_amount = loan_terms.get("LLC_BI__AMOUNT__C", 0)

                if this_loan_amount and this_loan_amount != 0:
                    loan_terms["A_B_AMOUNT_FACTOR"] = parent_amount / this_loan_amount
                else:
                    loan_terms["A_B_AMOUNT_FACTOR"] = 1
            else:
                loan_terms["A_B_AMOUNT_FACTOR"] = 1
        else:
            loan_terms["A_B_AMOUNT_FACTOR"] = 1

        # ===================================================================
        # 3. Fetch pricing rate components
        # ===================================================================
        pricing_rate_df = self._get_sf_data(
            "LLC_BI__Pricing_Rate_Component__c",
            [
                "cm_Partial_Period_Interst_Accrual_Method__c",
                "cm_Interest_Accrual_Method__c",
                "cm_Accrued_Rate__c",
                "LLC_BI__All_In_Rate__c",
                "LLC_BI__Applied_Loan_Percentage__c",
                "LLC_BI__Applied_Rate__c",
                "LLC_BI__Auto_Pay_Rate_Discount__c",
                "LLC_BI__Calculated_Monthly_Interest_Rate__c",
                "LLC_BI__Comments__c",
                "LLC_BI__Effective_Date__c",
                "LLC_BI__Employee_Rate_Discount__c",
                "LLC_BI__End_Date__c",
                "LLC_BI__Index__c",
                "LLC_BI__Index_Spread_Type__c",
                "LLC_BI__Initial_Adjustment_Rate_Cap__c",
                "LLC_BI__Interest_Rate_Adjustment_Frequency__c",
                "LLC_BI__Interest_Rate_Adjustment_Unit__c",
                "LLC_BI__Interest_Rate_Type__c",
                "LLC_BI__Is_Fixed__c",
                "LLC_BI__Is_Swap__c",
                "LLC_BI__Lifetime_Rate_Cap__c",
                "cm_Loan__c",
                "LLC_BI__lookupKey__c",
                "LLC_BI__Next_Interest_Rate_Change_Date__c",
                "LLC_BI__Periodic_Rate_Cap__c",
                "LLC_BI__Pricing_Stream__c",
                "LLC_BI__Rate__c",
                "LLC_BI__Rate_Adjustment__c",
                "LLC_BI__Rate_Ceiling__c",
                "LLC_BI__Rate_Floor__c",
                "LLC_BI__Sequence__c",
                "LLC_BI__Spread__c",
                "LLC_BI__Term_Length__c",
                "LLC_BI__Term_Unit__c",
                "cm_Minimum_Exit_Multiple__c",
                "cm_Maximum_Exit_IRR__c",
            ],
        )
        pricing_rate_filtered = self._filter_dataframe(pricing_rate_df, "CM_LOAN__C", loan_id)

        # ===================================================================
        # 4. Fetch pricing streams
        # ===================================================================
        pricing_stream_df = self._get_sf_data(
            "LLC_BI__Pricing_Stream__c",
            [
                "ID",
                "LLC_BI__LOAN__C",
                "LLC_BI__Effective_Date__c",
                "LLC_BI__Term_Length__c",
                "LLC_BI__Term_Unit__c",
                "LLC_BI__Is_Payment_Stream__c",
                "LLC_BI__Is_Rate_Stream__c",
                "LLC_BI__Is_Template__c",
                "LLC_BI__Period_Type__c",
                "LLC_BI__Pricing_Option__c",
            ],
        )
        pricing_stream_filtered = self._filter_dataframe(
            pricing_stream_df, "LLC_BI__LOAN__C", loan_id
        )

        # Merge pricing rates with streams
        overall_pricing_df = pricing_rate_filtered.merge(
            pricing_stream_df,
            left_on="LLC_BI__PRICING_STREAM__C",
            right_on="ID",
            how="left",
        )
        overall_pricing_filtered = self._filter_dataframe(
            overall_pricing_df, "CM_LOAN__C", loan_id
        )

        # ===================================================================
        # 5. Fetch payment components
        # ===================================================================
        payments_df = self._get_sf_data(
            "LLC_BI__Pricing_Payment_Component__c",
            [
                "LLC_BI__Count__c",
                "cm_Amortized_Term_Months__c",
                "LLC_BI__Includes_Interest__c",
                "LLC_BI__Includes_Principal__c",
                "LLC_BI__Interest_Frequency__c",
                "LLC_BI__Interest_Unit__c",
                "LLC_BI__Interest_Value__c",
                "LLC_BI__Rate_Stream__c",
                "LLC_BI__Amount__c",
                "LLC_BI__Principal_As_Percent__c",
                "LLC_BI__Base_Principal_Payment_On__c",
                "LLC_BI__Capitalized_Interest_Day_Of_Month__c",
                "LLC_BI__Capitalized_Interest_Effective_Date__c",
                "LLC_BI__Capitalized_Interest_Frequency__c",
                "LLC_BI__Comments__c",
                "LLC_BI__Effective_Date__c",
                "LLC_BI__End_Date__c",
                "LLC_BI__Has_Capitalized_Interest__c",
                "LLC_BI__Interest_Payment_Frequency__c",
                "LLC_BI__Is_Fixed__c",
                "cm_Loan__c",
                "LLC_BI__lookupKey__c",
                "LLC_BI__Maximum_Payment__c",
                "LLC_BI__Minimum_Payment__c",
                "Name",
                "LLC_BI__Number_Of_Payments__c",
                "LLC_BI__Frequency__c",
                "LLC_BI__Payment_Type__c",
                "LLC_BI__Percent_Of_Total_Loan_Amount__c",
                "LLC_BI__Pricing_Stream__c",
                "LLC_BI__Principal_Amount__c",
                "LLC_BI__Principal_Payment_Frequency__c",
                "LLC_BI__Sequence__c",
                "LLC_BI__Skip_Months__c",
                "LLC_BI__Skip_Stream_Target_Index__c",
                "LLC_BI__Term_Length__c",
                "LLC_BI__Term_Unit__c",
                "LLC_BI__Type__c",
            ],
        )
        payments_filtered = self._filter_dataframe(payments_df, "CM_LOAN__C", loan_id)

        # Merge payments with pricing streams
        overall_payments_df = payments_filtered.merge(
            pricing_stream_df,
            left_on="LLC_BI__PRICING_STREAM__C",
            right_on="ID",
            how="left",
        )
        overall_payments_filtered = self._filter_dataframe(
            overall_payments_df, "CM_LOAN__C", loan_id
        )

        # ===================================================================
        # 6. Fetch fees and draws
        # ===================================================================
        fees_and_draws_df = self._get_sf_data(
            "LLC_BI__Fee__c",
            [
                "ID",
                "NAME",
                "LLC_BI__Loan__c",
                "LLC_BI__Status__c",
                "LLC_BI__Fee_Type__c",
                "LLC_BI__Amount__c",
                "cm_Fee_Date__c",
                "cm_End_Date__c",
                "cm_Draw_Date_Deadline__c",
                "cm_Draw_Frequency__c",
                "cm_Draw_Reset_Type__c",
                "LLC_BI__Paid_at_Closing__c",
                "LLC_BI__Percentage__c",
                "LLC_BI__Calculation_Type__c",
                "cm_Exit_Fee_Payable_Upon__c",
                "LLC_BI__Basis_Source__c",
                "cm_Conditional_Exit_Fee_Reduction__c",
                "cm_Exit_Fee_Reduction_Condition_Met__c",
                "cm_Conditional_Exit_Fee_Percentage__c",
                "cm_Conditional_Exit_Fee_Amount__c",
                "cm_Fee_Share__c",
            ],
        )
        fees_and_draws_filtered = self._filter_dataframe(
            fees_and_draws_df, "LLC_BI__LOAN__C", loan_id
        )

        # Exclude Equity Waterfall fee types
        equity_waterfall_mask = (
            fees_and_draws_filtered["LLC_BI__FEE_TYPE__C"]
            .fillna("")
            .str.contains("Equity Waterfall")
        )
        fees_and_draws_filtered = fees_and_draws_filtered[~equity_waterfall_mask].copy()

        # Separate fees from draws
        fees_mask = (
            fees_and_draws_filtered["LLC_BI__FEE_TYPE__C"]
            .fillna("")
            .str.contains("Fee")
        )
        fees_df = fees_and_draws_filtered[fees_mask].copy()
        draws_df = fees_and_draws_filtered[~fees_mask].copy()

        # ===================================================================
        # 7. Assemble loan terms structure
        # ===================================================================
        loan_terms["PRICING_DETAILS"] = self._records(overall_pricing_filtered)

        # Convert CM_MAXIMUM_EXIT_IRR__C from percentage to decimal
        for pricing in loan_terms["PRICING_DETAILS"]:
            if "CM_MAXIMUM_EXIT_IRR__C" in pricing and pricing["CM_MAXIMUM_EXIT_IRR__C"] is not None:
                pricing["CM_MAXIMUM_EXIT_IRR__C"] = pricing["CM_MAXIMUM_EXIT_IRR__C"] / 100

        loan_terms["PAYMENT_DETAILS"] = self._records(overall_payments_filtered)
        loan_terms["FEE_DETAILS"] = self._records(fees_df)
        loan_terms["DRAW_DETAILS"] = self._records(draws_df)

        # ===================================================================
        # 8. Handle draw details special processing
        # ===================================================================
        # Remove "Funded at Closing" draws (they get recreated as synthetic draw)
        loan_terms['DRAW_DETAILS'] = [
            draw for draw in loan_terms['DRAW_DETAILS']
            if draw.get('LLC_BI__PAID_AT_CLOSING__C', '') not in ['Funded at Closing']
        ]

        # Handle "Funded at Modification" draws
        for draw in loan_terms['DRAW_DETAILS']:
            if (draw.get('LLC_BI__PAID_AT_CLOSING__C', '') == 'Funded at Modification'
                and 'CM_FEE_DATE__C' in draw):
                draw['CM_END_DATE__C'] = draw['CM_FEE_DATE__C']

        # Create synthetic "Funded At Closing" draw
        now = int(time.time())
        funded_at_close_draw = {
            'ID': f'MADE_UP_ID_{now}',
            'NAME': f'MADE_UP_NAME_{now}',
            'LLC_BI__LOAN__C': loan_terms['ID'],
            'LLC_BI__STATUS__C': 'Active',
            'LLC_BI__FEE_TYPE__C': 'Funded At Closing',
            'CM_DRAW_FREQUENCY__C': 'Monthly',
            'CM_DRAW_RESET_TYPE__C': 'Skip',
            'LLC_BI__CALCULATION_TYPE__C': 'Flat Amount',
            'CM_CONDITIONAL_EXIT_FEE_REDUCTION__C': False,
            'CM_EXIT_FEE_REDUCTION_CONDITION_MET__C': False
        }

        if 'LLC_BI__FUNDING_AT_CLOSE__C' in loan_terms:
            funded_at_close_draw['LLC_BI__AMOUNT__C'] = loan_terms['LLC_BI__FUNDING_AT_CLOSE__C']

        if 'LLC_BI__CLOSEDATE__C' in loan_terms:
            funded_at_close_draw['CM_FEE_DATE__C'] = loan_terms['LLC_BI__CLOSEDATE__C']
            funded_at_close_draw['CM_END_DATE__C'] = loan_terms['LLC_BI__CLOSEDATE__C']

        loan_terms['DRAW_DETAILS'].append(funded_at_close_draw)

        # Return with all keys uppercased
        return self._dict_keys_upper(loan_terms)

    def get_loan_terms_by_name(self, loan_name: str, exact_match: bool = True) -> Dict[str, Any]:
        """
        Fetch loan terms by loan name.

        Args:
            loan_name: Name of the loan to search for
            exact_match: If True, require exact name match. If False, find first match containing name.

        Returns:
            Dictionary with loan terms (same structure as get_loan_terms_by_id)

        Raises:
            ValueError: If loan_name is empty or no matching loan found
        """
        if not loan_name:
            raise ValueError("loan_name must be provided.")

        # Get list of all loans
        loans_df = self._get_sf_data(
            "LLC_BI__Loan__c",
            ["ID", "NAME"],
        )

        # Search for matching loan
        if exact_match:
            matching_loans = loans_df[loans_df['NAME'] == loan_name]
        else:
            matching_loans = loans_df[
                loans_df['NAME'].str.contains(loan_name, case=False, na=False)
            ]

        if matching_loans.empty:
            match_type = "exact match" if exact_match else "containing"
            raise ValueError(f"No loan found with name {match_type} '{loan_name}'")

        if len(matching_loans) > 1 and exact_match:
            raise ValueError(
                f"Multiple loans found with exact name '{loan_name}'. "
                f"Please use loan ID instead."
            )

        # Get first matching loan ID
        loan_id = matching_loans.iloc[0]['ID']

        # Fetch full loan terms using ID
        return self.get_loan_terms_by_id(loan_id)

    def search_loans(
        self,
        name_prefix: Optional[str] = None,
        exclude_statuses: Optional[List[str]] = None,
        exclude_stages: Optional[List[str]] = None,
        exclude_products: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """
        Search for loans with various filters.

        Args:
            name_prefix: Filter loans whose name starts with this prefix (case-insensitive)
            exclude_statuses: List of loan statuses to exclude (default: ['Declined', 'Withdrawn', 'Superseded'])
            exclude_stages: List of loan stages to exclude (default: ['Complete'])
            exclude_products: List of product types to exclude (default: ['Main'])

        Returns:
            List of dictionaries with loan ID, NAME, and other metadata
        """
        if exclude_statuses is None:
            exclude_statuses = ['Declined', 'Withdrawn', 'Superseded']
        if exclude_stages is None:
            exclude_stages = ['Complete']
        if exclude_products is None:
            exclude_products = ['Main']

        # Fetch loan list
        df = self._get_sf_data(
            "LLC_BI__Loan__c",
            [
                "ID",
                "NAME",
                "LLC_BI__lookupKey__c",
                "LLC_BI__STATUS__C",
                "LLC_BI__STAGE__C",
                "LLC_BI__Product__c"
            ]
        )

        # Apply filters
        if exclude_statuses:
            df = df[~df['LLC_BI__STATUS__C'].isin(exclude_statuses)]

        if exclude_stages:
            df = df[df['LLC_BI__STAGE__C'] != exclude_stages[0]]  # Simplified for single stage

        if exclude_products:
            df = df[df['LLC_BI__PRODUCT__C'] != exclude_products[0]]  # Simplified for single product

        # Filter by name prefix if provided
        if name_prefix:
            df = df[df['NAME'].str.lower().str.startswith(name_prefix.lower())]

        # Sort by name
        df = df.sort_values(by='NAME', ascending=True)

        return df.to_dict('records')

    def get_all_loans(self) -> List[Dict[str, str]]:
        """
        Get all active loans (convenience method).

        Returns:
            List of loan dictionaries with ID and NAME
        """
        return self.search_loans()
