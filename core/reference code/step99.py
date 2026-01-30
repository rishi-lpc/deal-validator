#!/usr/bin/env python

from typing import Dict, List, Optional
from datetime import date, datetime
import pandas as pd
import re
from numpy_financial import irr
import numpy as np
from math import isclose


def get_loan_terms_metadata() :
    return [
    {
        "FIELD": "ID",
        "DISPLAYNAME": "Loan ID",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 1
    },
    {
        "FIELD": "NAME",
        "DISPLAYNAME": "Loan Name",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 2
    },
    {
        "FIELD": "LLC_BI__AMOUNT__C",
        "DISPLAYNAME": "Loan Amount",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": True,
        "DATA_TYPE": "currency",
        "ORDER": 3
    },
    {
        "FIELD": "LLC_BI__FUNDING_AT_CLOSE__C",
        "DISPLAYNAME": "Funding at Close",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": True,
        "DATA_TYPE": "currency",
        "ORDER": 4
    },
    {
        "FIELD": "LLC_BI__CLOSEDATE__C",
        "DISPLAYNAME": "Close Date",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 5
    },
    {
        "FIELD": "LLC_BI__FIRST_PAYMENT_DATE__C",
        "DISPLAYNAME": "First Payment Date",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 6
    },
    {
        "FIELD": "LLC_BI__TERM_MONTHS__C",
        "DISPLAYNAME": "Term (Months)",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": True,
        "DATA_TYPE": "number",
        "ORDER": 7
    },
    {
        "FIELD": "LLC_BI__AMORTIZED_TERM_MONTHS__C",
        "DISPLAYNAME": "Amortized Term (Months)",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": True,
        "DATA_TYPE": "number",
        "ORDER": 8
    },
    {
        "FIELD": "LLC_BI__PREPAYMENT_PENALTY__C",
        "DISPLAYNAME": "Prepayment Penalty",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 9
    },
    {
        "FIELD": "LLC_BI__MATURITY_DATE__C",
        "DISPLAYNAME": "Maturity Date",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 10
    },
    {
        "FIELD": "CM_PREPAYMENT_MINIMAL_INTEREST_MONTHS__C",
        "DISPLAYNAME": "Prepayment Minimal Interest (Months)",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": False,
        "DATA_TYPE": "number",
        "ORDER": 11
    },
    {
        "FIELD": "LLC_BI__PREPAYMENT_PENALTY_DESCRIPTION__C",
        "DISPLAYNAME": "Prepayment Penalty Description",
        "TABLE": "LOAN_INFO",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 12
    },
    {
        "FIELD": "LLC_BI__ACCRUAL_INTEREST_RATE__C",
        "DISPLAYNAME": "Accrual Interest Rate",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 1
    },
    {
        "FIELD": "LLC_BI__ALL_IN_RATE__C",
        "DISPLAYNAME": "All-In Rate",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 2
    },
    {
        "FIELD": "LLC_BI__APPLIED_LOAN_PERCENTAGE__C",
        "DISPLAYNAME": "Applied Loan Percentage",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 3
    },
    {
        "FIELD": "LLC_BI__APPLIED_RATE__C",
        "DISPLAYNAME": "Applied Rate",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 4
    },
    {
        "FIELD": "LLC_BI__BASE_INTEREST_RATE__C",
        "DISPLAYNAME": "Base Interest Rate",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 5
    },
    {
        "FIELD": "LLC_BI__RATE_CEILING__C",
        "DISPLAYNAME": "Ceiling Rate",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 6
    },
    {
        "FIELD": "CM_ACCRUED_RATE__C",
        "DISPLAYNAME": "Accrued Rate",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 7
    },
    {
        "FIELD": "LLC_BI__CALCULATED_MONTHLY_INTEREST_RATE__C",
        "DISPLAYNAME": "Calc Monthly Interest Rate",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "percentage",
        "ORDER": 8
    },
    {
        "FIELD": "CM_INTEREST_ACCRUAL_METHOD__C",
        "DISPLAYNAME": "Interest Accrual Method",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 9
    },
    {
        "FIELD": "CM_LOAN__C",
        "DISPLAYNAME": "CM Loan",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 10
    },
    {
        "FIELD": "LLC_BI__RATE_FLOOR__C",
        "DISPLAYNAME": "Floor Rate",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "percentage",
        "ORDER": 11
    },
    {
        "FIELD": "ID",
        "DISPLAYNAME": "ID",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 12
    },
    {
        "FIELD": "LLC_BI__INDEX_RATE__C",
        "DISPLAYNAME": "Index Rate",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 13
    },
    {
        "FIELD": "LLC_BI__INDEX_RATE_BASIS__C",
        "DISPLAYNAME": "Index Rate Basis",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 14
    },
    {
        "FIELD": "LLC_BI__INTEREST_ACCRUAL_METHOD__C",
        "DISPLAYNAME": "Interest Accrual Method",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 15
    },
    {
        "FIELD": "LLC_BI__INTEREST_RATE_TYPE__C",
        "DISPLAYNAME": "Interest Rate Type",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 16
    },
    {
        "FIELD": "LLC_BI__IS_FIXED__C",
        "DISPLAYNAME": "Is Fixed",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 17
    },
    {
        "FIELD": "LLC_BI__IS_PAYMENT_STREAM__C",
        "DISPLAYNAME": "Is Payment Stream",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 18
    },
    {
        "FIELD": "LLC_BI__IS_RATE_STREAM__C",
        "DISPLAYNAME": "Is Rate Stream",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 19
    },
    {
        "FIELD": "LLC_BI__IS_SWAP__C",
        "DISPLAYNAME": "Is Swap",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 20
    },
    {
        "FIELD": "LLC_BI__IS_TEMPLATE__C",
        "DISPLAYNAME": "Is Template",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 21
    },
    {
        "FIELD": "LLC_BI__LOAN__C",
        "DISPLAYNAME": "Loan",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 22
    },
    {
        "FIELD": "LLC_BI__NUMBER_OF_RATE_CHANGES__C",
        "DISPLAYNAME": "Number of Rate Changes",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "number",
        "ORDER": 23
    },
    {
        "FIELD": "CM_PARTIAL_PERIOD_INTERST_ACCRUAL_METHOD__C",
        "DISPLAYNAME": "Partial Period Interest Accrual Method",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 24
    },
    {
        "FIELD": "LLC_BI__PRICING_STREAM__C",
        "DISPLAYNAME": "Pricing Stream",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 25
    },
    {
        "FIELD": "LLC_BI__PRICING_TYPE__C",
        "DISPLAYNAME": "Pricing Type",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 26
    },
    {
        "FIELD": "LLC_BI__RATE__C",
        "DISPLAYNAME": "Rate",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 27
    },
    {
        "FIELD": "LLC_BI__RATE_EFFECTIVE_DATE__C",
        "DISPLAYNAME": "Rate Effective Date",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "date",
        "ORDER": 28
    },
    {
        "FIELD": "LLC_BI__EFFECTIVE_DATE__C_Y",
        "DISPLAYNAME": "Rate Effective Date",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 29
    },
    {
        "FIELD": "LLC_BI__RATE_TERM_LENGTH__C",
        "DISPLAYNAME": "Rate Term Length",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "number",
        "ORDER": 30
    },
    {
        "FIELD": "LLC_BI__TERM_LENGTH__C_Y",
        "DISPLAYNAME": "Rate Term Length",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "number",
        "ORDER": 31
    },
    {
        "FIELD": "LLC_BI__RATE_TERM_UNIT__C",
        "DISPLAYNAME": "Rate Term Unit",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 32
    },
    {
        "FIELD": "LLC_BI__TERM_UNIT__C_Y",
        "DISPLAYNAME": "Rate Term Unit",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 33
    },
    {
        "FIELD": "LLC_BI__SPREAD__C",
        "DISPLAYNAME": "Spread",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 34
    },
    {
        "FIELD": "CM_SPREAD_2__C",
        "DISPLAYNAME": "Spread 2",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "percentage",
        "ORDER": 35
    },
    {
        "FIELD": "LLC_BI__TERM_MONTHS__C_X",
        "DISPLAYNAME": "Term (Months)",
        "TABLE": "PRICING",
        "IN_SUMMARY": True,
        "DATA_TYPE": "number",
        "ORDER": 36
    },
    {
        "FIELD": "LLC_BI__TERM_UNIT__C_X",
        "DISPLAYNAME": "Term Unit",
        "TABLE": "PRICING",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 37
    },
    {
        "FIELD": "LLC_BI__ACCRUAL_INTEREST_RATE__C",
        "DISPLAYNAME": "Accrual Interest Rate",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 1
    },
    {
        "FIELD": "LLC_BI__AMOUNT__C",
        "DISPLAYNAME": "Amount",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "currency",
        "ORDER": 2
    },
    {
        "FIELD": "LLC_BI__BASE_INTEREST_RATE__C",
        "DISPLAYNAME": "Base Interest Rate",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 3
    },
    {
        "FIELD": "CM_LOAN__C",
        "DISPLAYNAME": "CM Loan",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 4
    },
    {
        "FIELD": "LLC_BI__EFFECTIVE_DATE__C_Y",
        "DISPLAYNAME": "Effective Date",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 5
    },
    {
        "FIELD": "LLC_BI__FIRST_PAYMENT_DATE__C",
        "DISPLAYNAME": "First Payment Date",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 6
    },
    {
        "FIELD": "LLC_BI__FREQUENCY__C",
        "DISPLAYNAME": "Frequency",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 7
    },
    {
        "FIELD": "LLC_BI__GRACE_PERIOD_MONTHS__C",
        "DISPLAYNAME": "Grace Period (Months)",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "integer",
        "ORDER": 8
    },
    {
        "FIELD": "LLC_BI__HAS_CAPITALIZED_INTEREST__C",
        "DISPLAYNAME": "Has Capitalized Interest",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 9
    },
    {
        "FIELD": "ID",
        "DISPLAYNAME": "ID",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 10
    },
    {
        "FIELD": "LLC_BI__INCLUDES_INTEREST__C",
        "DISPLAYNAME": "Includes Interest",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 11
    },
    {
        "FIELD": "LLC_BI__INCLUDES_PRINCIPAL__C",
        "DISPLAYNAME": "Includes Principal",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 12
    },
    {
        "FIELD": "LLC_BI__INDEX_RATE_BASIS__C",
        "DISPLAYNAME": "Index Rate Basis",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 13
    },
    {
        "FIELD": "LLC_BI__INTEREST_ACCRUAL_METHOD__C",
        "DISPLAYNAME": "Interest Accrual Method",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 14
    },
    {
        "FIELD": "LLC_BI__INTEREST_FREQUENCY__C",
        "DISPLAYNAME": "Interest Frequency",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 15
    },
    {
        "FIELD": "LLC_BI__INTEREST_ONLY_PERIOD_MONTHS__C",
        "DISPLAYNAME": "Interest Only Period (Months)",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "integer",
        "ORDER": 16
    },
    {
        "FIELD": "LLC_BI__INTEREST_PAYMENT_FREQUENCY__C",
        "DISPLAYNAME": "Interest Payment Frequency",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 17
    },
    {
        "FIELD": "LLC_BI__INTEREST_RATE_TYPE__C",
        "DISPLAYNAME": "Interest Rate Type",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 18
    },
    {
        "FIELD": "LLC_BI__IS_FIXED__C",
        "DISPLAYNAME": "Is Fixed",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 19
    },
    {
        "FIELD": "LLC_BI__IS_PAYMENT_STREAM__C",
        "DISPLAYNAME": "Is Payment Stream",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 20
    },
    {
        "FIELD": "LLC_BI__IS_RATE_STREAM__C",
        "DISPLAYNAME": "Is Rate Stream",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 21
    },
    {
        "FIELD": "LLC_BI__IS_TEMPLATE__C",
        "DISPLAYNAME": "Is Template",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 22
    },
    {
        "FIELD": "LLC_BI__LAST_PAYMENT_DATE__C",
        "DISPLAYNAME": "Last Payment Date",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 23
    },
    {
        "FIELD": "LLC_BI__LOAN__C",
        "DISPLAYNAME": "Loan",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 24
    },
    {
        "FIELD": "NAME",
        "DISPLAYNAME": "Name",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 25
    },
    {
        "FIELD": "LLC_BI__NUMBER_OF_PAYMENTS__C",
        "DISPLAYNAME": "Number of Payments",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "integer",
        "ORDER": 26
    },
    {
        "FIELD": "LLC_BI__PAYMENT_AMOUNT__C",
        "DISPLAYNAME": "Payment Amount",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "currency",
        "ORDER": 27
    },
    {
        "FIELD": "LLC_BI__PAYMENT_DUE_DAY__C",
        "DISPLAYNAME": "Payment Due Day",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "integer",
        "ORDER": 28
    },
    {
        "FIELD": "CM_PAYMENT_END_DATE__C",
        "DISPLAYNAME": "Payment End Date",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 29
    },
    {
        "FIELD": "LLC_BI__PAYMENT_FREQUENCY__C",
        "DISPLAYNAME": "Payment Frequency",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 30
    },
    {
        "FIELD": "LLC_BI__PAYMENT_MODE__C",
        "DISPLAYNAME": "Payment Mode",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 31
    },
    {
        "FIELD": "CM_PAYMENT_START_DATE__C",
        "DISPLAYNAME": "Payment Start Date",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 32
    },
    {
        "FIELD": "LLC_BI__PAYMENT_TYPE__C",
        "DISPLAYNAME": "Payment Type",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 33
    },
    {
        "FIELD": "LLC_BI__PRICING_STREAM__C",
        "DISPLAYNAME": "Pricing Stream",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 34
    },
    {
        "FIELD": "LLC_BI__PRICING_TYPE__C",
        "DISPLAYNAME": "Pricing Type",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 35
    },
    {
        "FIELD": "LLC_BI__PRINCIPAL_AS_PERCENT__C",
        "DISPLAYNAME": "Principal As Percent",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 36
    },
    {
        "FIELD": "LLC_BI__PRINCIPAL_PAYMENT_FREQUENCY__C",
        "DISPLAYNAME": "Principal Payment Frequency",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 37
    },
    {
        "FIELD": "LLC_BI__TERM_LENGTH__C_Y",
        "DISPLAYNAME": "Term Length",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "number",
        "ORDER": 38
    },
    {
        "FIELD": "LLC_BI__TERM_MONTHS__C_X",
        "DISPLAYNAME": "Term (Months)",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "number",
        "ORDER": 39
    },
    {
        "FIELD": "LLC_BI__TERM_UNIT__C_X",
        "DISPLAYNAME": "Term Unit",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 40
    },
    {
        "FIELD": "LLC_BI__TERM_UNIT__C_Y",
        "DISPLAYNAME": "Term Unit (Y)",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 41
    },
    {
        "FIELD": "LLC_BI__TYPE__C",
        "DISPLAYNAME": "Type",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 42
    },
    {
        "FIELD": "CM_AMORTIZED_TERM_MONTHS__C",
        "DISPLAYNAME": "Loan Amortization Term (Months)",
        "TABLE": "PAYMENT",
        "IN_SUMMARY": True,
        "DATA_TYPE": "integer",
        "ORDER": 43
    },
    {
        "FIELD": "ID",
        "DISPLAYNAME": "ID",
        "TABLE": "FEE",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 1
    },
    {
        "FIELD": "NAME",
        "DISPLAYNAME": "Name",
        "TABLE": "FEE",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 2
    },
    {
        "FIELD": "LLC_BI__LOAN__C",
        "DISPLAYNAME": "Loan",
        "TABLE": "FEE",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 3
    },
    {
        "FIELD": "LLC_BI__STATUS__C",
        "DISPLAYNAME": "Status",
        "TABLE": "FEE",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 4
    },
    {
        "FIELD": "LLC_BI__FEE_TYPE__C",
        "DISPLAYNAME": "Fee Type",
        "TABLE": "FEE",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 5
    },
    {
        "FIELD": "LLC_BI__AMOUNT__C",
        "DISPLAYNAME": "Fee Amount",
        "TABLE": "FEE",
        "IN_SUMMARY": True,
        "DATA_TYPE": "currency",
        "ORDER": 6
    },
    {
        "FIELD": "CM_FEE_DATE__C",
        "DISPLAYNAME": "Fee Date",
        "TABLE": "FEE",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 7
    },
    {
        "FIELD": "CM_END_DATE__C",
        "DISPLAYNAME": "Fee End Date",
        "TABLE": "FEE",
        "IN_SUMMARY": True,
        "DATA_TYPE": "date",
        "ORDER": 8
    },
    {
        "FIELD": "CM_DRAW_FREQUENCY__C",
        "DISPLAYNAME": "Fee Frequency",
        "TABLE": "FEE",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 9
    },
    {
        "FIELD": "CM_DRAW_RESET_TYPE__C",
        "DISPLAYNAME": "Fee Reset Type",
        "TABLE": "FEE",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 10
    },
    {
        "FIELD": "LLC_BI__PAID_AT_CLOSING__C",
        "DISPLAYNAME": "Paid At Closing",
        "TABLE": "FEE",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 11
    },
    {
        "FIELD": "LLC_BI__PERCENTAGE__C",
        "DISPLAYNAME": "Fee Percentage",
        "TABLE": "FEE",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 12
    },
    {
        "FIELD": "LLC_BI__CALCULATION_TYPE__C",
        "DISPLAYNAME": "Calculation Type",
        "TABLE": "FEE",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 13
    },
    {
        "FIELD": "CM_EXIT_FEE_PAYABLE_UPON__C",
        "DISPLAYNAME": "Exit Fee Payable Upon",
        "TABLE": "FEE",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 14
    },
    {
        "FIELD": "LLC_BI__BASIS_SOURCE__C",
        "DISPLAYNAME": "Basis Source",
        "TABLE": "FEE",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 15
    },
    {
        "FIELD": "CM_CONDITIONAL_EXIT_FEE_REDUCTION__C",
        "DISPLAYNAME": "Conditional Exit Fee Reduction",
        "TABLE": "FEE",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 16
    },
    {
        "FIELD": "CM_EXIT_FEE_REDUCTION_CONDITION_MET__C",
        "DISPLAYNAME": "Exit Fee Reduction Condition Met",
        "TABLE": "FEE",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 17
    },
    {
        "FIELD": "CM_FEE_SHARE__C",
        "DISPLAYNAME": "Fee Share",
        "TABLE": "FEE",
        "IN_SUMMARY": True,
        "DATA_TYPE": "percentage",
        "ORDER": 18
    },
    {
        "FIELD": "ID",
        "DISPLAYNAME": "ID",
        "TABLE": "DRAW",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 1
    },
    {
        "FIELD": "NAME",
        "DISPLAYNAME": "Name",
        "TABLE": "DRAW",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 2
    },
    {
        "FIELD": "LLC_BI__LOAN__C",
        "DISPLAYNAME": "Loan",
        "TABLE": "DRAW",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 3
    },
    {
        "FIELD": "LLC_BI__STATUS__C",
        "DISPLAYNAME": "Status",
        "TABLE": "DRAW",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 4
    },
    {
        "FIELD": "LLC_BI__FEE_TYPE__C",
        "DISPLAYNAME": "Draw Type",
        "TABLE": "DRAW",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 5
    },
    {
        "FIELD": "LLC_BI__AMOUNT__C",
        "DISPLAYNAME": "Draw Amount",
        "TABLE": "DRAW",
        "IN_SUMMARY": True,
        "DATA_TYPE": "currency",
        "ORDER": 6
    },
    {
        "FIELD": "CM_DRAW_FREQUENCY__C",
        "DISPLAYNAME": "Draw Frequency",
        "TABLE": "DRAW",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 7
    },
    {
        "FIELD": "CM_DRAW_RESET_TYPE__C",
        "DISPLAYNAME": "Draw Reset Type",
        "TABLE": "DRAW",
        "IN_SUMMARY": False,
        "DATA_TYPE": "string",
        "ORDER": 8
    },
    {
        "FIELD": "LLC_BI__PAID_AT_CLOSING__C",
        "DISPLAYNAME": "Paid At Closing",
        "TABLE": "DRAW",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 9
    },
    {
        "FIELD": "LLC_BI__CALCULATION_TYPE__C",
        "DISPLAYNAME": "Calculation Type",
        "TABLE": "DRAW",
        "IN_SUMMARY": True,
        "DATA_TYPE": "string",
        "ORDER": 10
    },
    {
        "FIELD": "CM_CONDITIONAL_EXIT_FEE_REDUCTION__C",
        "DISPLAYNAME": "Conditional Exit Fee Reduction",
        "TABLE": "DRAW",
        "IN_SUMMARY": True,
        "DATA_TYPE": "boolean",
        "ORDER": 11
    },
    {
        "FIELD": "CM_EXIT_FEE_REDUCTION_CONDITION_MET__C",
        "DISPLAYNAME": "Exit Fee Reduction Condition Met",
        "TABLE": "DRAW",
        "IN_SUMMARY": False,
        "DATA_TYPE": "boolean",
        "ORDER": 12
    },
    {
        "FIELD": "CM_FEE_DATE__C",
        "DISPLAYNAME": "Draw Date",
        "TABLE": "DRAW",
        "IN_SUMMARY": False,
        "DATA_TYPE": "date",
        "ORDER": 13
    },
        {
        "FIELD": "CM_END_DATE__C",
        "DISPLAYNAME": "Draw End Date",
        "TABLE": "DRAW",
        "IN_SUMMARY": False,
        "DATA_TYPE": "date",
        "ORDER": 14
    },


    ]

def get_draw_columns_Renames(X):
    draw_columns = [c for c in X.columns if c.startswith('draw:') and ':details' not in c] 
    draw_columns.sort()
    draw_columns = list(draw_columns)


    draw_amount = [draw_amt for draw_amt in draw_columns if draw_amt.endswith(":amount")]
    draw_fee = [draw_amt for draw_amt in draw_columns if draw_amt.endswith(":fee")]
    draw_unfunded = [draw_amt for draw_amt in draw_columns if draw_amt.endswith(":unfunded")]
    draw_fee_unfunded = [draw_amt for draw_amt in draw_columns if draw_amt.endswith(":fee-unfunded")]

    renamed_d = [amt_col.split(":")[1].split("[")[0].rstrip() for amt_col in draw_amount]
    renamed_u = ["Unfunded:" + unfunded_col.split(":")[1].split("[")[0].rstrip()  for unfunded_col in draw_unfunded]
    renamed_f = ["Fee:" + fee_col.split(":")[1].split("[")[0].rstrip()  for fee_col in draw_fee]
    renamed_uf = ["Fee-Unfunded:" + fee_unfunded.split(":")[1].split("[")[0].rstrip()  for fee_unfunded in draw_fee_unfunded]

    print(">>>> " ,renamed_d)
    
    all_formatted_draw_names = []

    ## VERY VERY VERY VERY IMP: the column names are sorted and so for each draw they are always 
    # amount, fee, fee-unfunded and then unfunded - so the order in which the zip below is provided
    ## need to stay the same
    for x in zip(renamed_d, renamed_f,  renamed_uf, renamed_u):
        all_formatted_draw_names.extend(list(x))


    column_rename = {}
    for idx, i in enumerate(draw_columns):
        print(idx, i)
        column_rename[draw_columns[idx]] = all_formatted_draw_names[idx]

    return draw_columns, column_rename

def prepare_for_client(X):
    draw_columns_original, renames = get_draw_columns_Renames(X)
    print(draw_columns_original)

    # this will set the order in which the columns should appear
    all_output_columns = ['accrual_period','accrual_start_date', 'accrual_end_date']
    all_output_columns.extend(draw_columns_original)
    all_output_columns.extend(['interest_paid_at_start','principal_paid_at_start','cummulative_outstanding_principal','interest_accrual_method','actual_accrual_days','adjusted_30_360_accrual_days','interest_rate_type','base_interest_rate','period_multiplier','period_base_interest_multiplier'])
    all_output_columns.extend(['base_interest_amount_due_for_this_period','base_interest_amount_unpaid_from_previous_period','base_interest_amount_due_at_start_of_next_period','cummulative_pik_amount_due'])
    all_output_columns.extend(['payment_type','is_principal_due_at_start','principal_paid_at_start','principal_due_at_start_of_next_period'])
    all_output_columns.extend(['closing_fee_due','draw_fee_due','exit_fee_due_at_start_of_next_period','cummulative_unpaid_exit_fee_due_at_start_of_next_period','all_fees_due'])
    # Pref equity columns from step7_pref_equity.py
    all_output_columns.extend(['pref_amount_drawn','pref_equity_catch_up','min_moic_catch_up','pref_cashflow'])



    # this can happen if say exit fee did not exits then its related columns never got added to the df
    missing_columns = [col for col in all_output_columns if col not in X.columns] 
    for col in missing_columns:
        X[col] = 0

    
    new_col_names = [re.sub(r'_[0-9]+', '', c.replace(' ', '_') .replace(':', '_') .replace('[', '') .replace(']', '').replace('-','_')) for c in all_output_columns]
    name_mapping = dict(zip(all_output_columns, new_col_names))
    X = X.rename(columns=name_mapping)
    X = X[new_col_names] # do this to enforce column order


    schema = []
    for idx, col in enumerate(X.columns):

        
        template = { "field": "accrual_period", "displayName": "accrual_period", "dataType": "int",  "view": "summary", "aggregation": None ,}
        template = {}
        template['field']  = col.upper()
        template['table'] = "AMORT"

        col = col.lower()
        template['displayName'] = col.replace('_',' ').title()
        template['in_summary'] = False

        
        if('date' in col):
            template['data_type'] = 'date'
            template['in_summary'] = True
        elif(col.startswith('is_')):
            template['data_type'] = 'bool'
        elif('_days' in col or '_multiplier' in col and '_type' not in col):
            template['data_type'] = 'num'
        elif('_rate' in col and '_type' not in col):
           template['data_type'] = 'percentage' 
        elif('amount' in col or 'fee' in col or 'amount' in col or '_paid' in col or 'principal' in col):
            template['data_type'] = 'currency'
            template['in_summary'] = True
        else:
            template['data_type'] = 'string'

        # Special handling for pref equity columns:
        # - pref_equity_catch_up and min_moic_catch_up should be IN_SUMMARY (users want to see these)
        # - pref_amount_drawn should NOT be in summary (less important)
        if col == 'pref_equity_catch_up' or col == 'min_moic_catch_up':
            template['in_summary'] = True
            template['data_type'] = 'currency'
        elif col == 'pref_amount_drawn':
            template['in_summary'] = False

        template['order'] = idx+1


        # special adjustment for Draw Columns:

        'draw_Funded_At_Closing_amount', 'draw_Funded_At_Closing_fee', 'draw_Funded_At_Closing_fee_unfunded', 'draw_Funded_At_Closing_unfunded'
        if(col.startswith('draw_')):
            if(col.endswith('_amount')):
               template['displayName'] = template['displayName'].replace('Draw ','').replace(' Amount','(Funded)')
            if(col.endswith('_fee')):
               template['displayName'] = template['displayName'].replace('Draw ','').replace(' Fee','(Fee)')

            # check for _unfunded before checking _fee_unfunded
            if(col.endswith('_fee_unfunded')):
               template['displayName'] = template['displayName'].replace('Draw ','').replace(' Fee Unfunded','(Unfunded Fee)')
            if(col.endswith('_unfunded') and not col.endswith("_fee_unfunded")):
               template['displayName'] = template['displayName'].replace('Draw ','').replace(' Unfunded','(Unfunded)')

            

        schema.append(template)
        print(template['displayName'])


    print("\n\n\n****** ****** ****** ****** ****** ****** ****** \n")
    print(schema.extend(get_loan_terms_metadata()))
    print("\n\n\n****** ****** ****** ****** ****** ****** ****** \n")

    for idx, elem in enumerate(schema):
        elem['order'] = idx+1
    
    print(X.shape)
    return X, schema 



def compute_cashflows(df):
    #df = df.copy()
    df['returns_related_date'] = pd.to_datetime(df['accrual_start_date'])
    
    df['interest_paid_at_start'] = df['interest_paid_at_start'].fillna(0)
    df['principal_paid_at_start'] = df['principal_paid_at_start'].fillna(0)
    df['all_fees_due'] = df['all_fees_due'].fillna(0)
    # Handle pref equity catch-up columns if they exist
    df['pref_equity_catch_up'] = df['pref_equity_catch_up'].fillna(0) if 'pref_equity_catch_up' in df.columns else 0
    df['min_moic_catch_up'] = df['min_moic_catch_up'].fillna(0) if 'min_moic_catch_up' in df.columns else 0
    df['cashflow'] = 0

    draw_amount_columns = [draw_amt_cols for draw_amt_cols in df.columns if draw_amt_cols.startswith('draw') and draw_amt_cols.endswith('_amount')]
    df['all_draw_totals'] = -df[draw_amount_columns].fillna(0).sum(axis=1)
    # We technically also gave them the fees that they then paid back to us. So fees need to be added as amount that left out pocket
    # now you might say why add "all_draw_fee_totals" and then negate with "add_fees_due" - just drop but NO - because all_fees_due will
    # also have Exit fees which are not negated out by all_draw_fee_total
    draw_fee_amount_columns = [draw_amt_cols for draw_amt_cols in df.columns if draw_amt_cols.startswith('draw') and draw_amt_cols.endswith('_fee')]
    df['all_draw_fee_totals'] = -df[draw_fee_amount_columns].fillna(0).sum(axis=1)
    
    cashflow_components = [
        'all_draw_totals',
        'all_draw_fee_totals',
        'interest_paid_at_start',
        'principal_paid_at_start',
        'all_fees_due',
        'pref_equity_catch_up',
        'min_moic_catch_up'
    ]

    df['cashflow'] = df[cashflow_components].fillna(0).sum(axis=1)
    #baloon payment and last interest
    df.loc[df.index[df.shape[0]-1], 'cashflow'] += df.loc[df.index[df.shape[0]-1], 'base_interest_amount_due_at_start_of_next_period'] + df.loc[df.index[df.shape[0]-1], 'principal_due_at_start_of_next_period'] 





def calculate_IRR(df):
    print(irr(df['cashflow']))
    return irr(df['cashflow'])

def calculate_XIRR(df):
    df = df.sort_values('returns_related_date')
    years = (df['returns_related_date'] - df['returns_related_date'].iloc[0]).dt.days / 365.0
    func = lambda r: np.sum(df['cashflow'] / (1 + r) ** years)
    rate = 0.1
    for _ in range(100):
        f = func(rate)
        f_prime = np.sum(-years * df['cashflow'] / (1 + rate) ** (years + 1))
        if f_prime == 0: break
        new_rate = rate - f / f_prime
        if isclose(new_rate, rate, rel_tol=1e-9): 
            print("1. XIRR :::::::::::: ",rate, " ::::::::::::")
            return rate
        rate = new_rate
    print("2. XIRR :::::::::::: ",rate, " ::::::::::::")
    return rate

def calculate_MOIC(df):
    inflows = df.loc[df['cashflow'] > 0, 'cashflow'].sum()
    outflows = -df.loc[df['cashflow'] < 0, 'cashflow'].sum()
    return inflows / outflows if outflows else np.nan


