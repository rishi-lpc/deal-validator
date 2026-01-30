#!/usr/bin/env python

from datetime import timedelta
from typing import Any, Dict, Iterable, List, Tuple

import json

import numpy as np
import pandas as pd


def _clear_all_draws_from_new_row(new_row, original_row):
    all_cols = list(new_row.columns)
    draw_cols = [c for c in all_cols if c.startswith('draw:') and c.endswith(':amount')]
    for c in draw_cols:
        new_row.loc[0, c] = 0


def _add_amount(schedule: pd.DataFrame, index: int, column: str, amount: Any) -> None:
    """Accumulate numeric amounts on the target column for the given row."""
    if column not in schedule.columns:
        schedule[column] = 0

    current = schedule.at[index, column]
    current = 0 if pd.isna(current) else current
    schedule.at[index, column] = current + (amount or 0)


def fold_draw_cols_two_levels(event_schedule: pd.DataFrame) -> pd.DataFrame:
    """Convert draw columns into a MultiIndex (<draw name>, <field>) layout."""
    df = event_schedule.copy()
    if not isinstance(df.columns, pd.MultiIndex):
        df.columns = pd.MultiIndex.from_product([[""], df.columns])

    lower = df.columns.get_level_values(-1).astype(str)
    draw_mask = lower.str.startswith("draw:")
    if not draw_mask.any():
        return df

    draw_cols = df.columns[draw_mask]
    other_cols = df.columns[~draw_mask]

    def split_draw(name: str) -> Tuple[str, str]:
        _, mid_field = name.split("draw:", 1)
        middle, field = mid_field.rsplit(":", 1)
        return (middle.strip(), field.strip().lower())

    new_tuples = [split_draw(col[-1]) for col in draw_cols]
    draw_df = df.loc[:, draw_cols].copy()
    draw_df.columns = pd.MultiIndex.from_tuples(new_tuples, names=["Draw", "Field"])

    return pd.concat([df.loc[:, other_cols], draw_df], axis=1)


def _coerce_event_details(details: Any) -> Dict[str, Any]:
    if isinstance(details, dict):
        return details
    if isinstance(details, str):
        try:
            return json.loads(details)
        except json.JSONDecodeError:
            return {"raw": details}
    return {"raw": details}


def add_event_to_row(
    event: Dict[str, Any],
    event_type: str,
    event_date: pd.Timestamp,
    event_amount: Any,
    amortization_term: Any,
    schedule: pd.DataFrame,
    index: int,
) -> None:
    if event_type == "interest payment":
        _add_amount(schedule, index, "interest_paid_at_start", event_amount)

    elif event_type == "interest due":
        schedule.at[index, "is_interest_due_at_start"] = True

    elif event_type == "principal payment":
        _add_amount(schedule, index, "principal_paid_at_start", event_amount)

    elif event_type == "principal due":
        schedule.at[index, "is_principal_due_at_start"] = True
        schedule.at[index, "amortization_term"] = amortization_term

    elif event_type == "principal payoff due":
        schedule.at[index, "principal_payoff"] = True

    elif event_type == "interest payoff due":
        schedule.at[index, "interest_payoff"] = True

    elif event_type == "draw":
        schedule.at[index, "is_draw"] = True

        details = _coerce_event_details(event.get("event_details"))
        account = details.get("LLC_BI__FEE_TYPE__C", "Unknown")
        policy_index = event.get("draw_policy_index")

        column_prefix = f"draw:{account} [{int(policy_index)}]" if policy_index is not None else f"draw:{account}"
        schedule.at[index, f"{column_prefix}:details"] = json.dumps(details, sort_keys=True)
        schedule.at[index, f"{column_prefix}:amount"] = event_amount

        _add_amount(schedule, index, "amount_drawn", event_amount)


def reset_event_indicators(rows: pd.DataFrame, index: int) -> None:
    rows.at[index, "interest_paid_at_start"] = np.nan
    rows.at[index, "principal_due_at_start"] = np.nan
    rows.at[index, "is_draw"] = np.nan
    rows.at[index, "amount_drawn"] = 0
    rows.at[index, "is_interest_due_at_start"] = np.nan
    rows.at[index, "is_principal_due_at_start"] = np.nan


def split_or_update_event(
    event: Dict[str, Any],
    pricing_schedule: pd.DataFrame,
    additional_values_to_add: Dict[str, Any] | None = None,
) -> pd.DataFrame:

    event_date = pd.to_datetime(event["event_date"]).normalize()
    event_type = event["event_type"]
    event_amount = event.get("amount")
    amortization_term = event.get("amortization_term")

    pricing_schedule["accrual_start_date"] = pd.to_datetime(
        pricing_schedule["accrual_start_date"]
    ).dt.normalize()
    pricing_schedule["accrual_end_date"] = pd.to_datetime(
        pricing_schedule["accrual_end_date"]
    ).dt.normalize()

    mask = (pricing_schedule["accrual_start_date"] <= event_date) & (
        pricing_schedule["accrual_end_date"] >= event_date
    )

    if not mask.any():
        raise ValueError(f"No matching accrual period found for event_date {event_date.date()}")

    row_to_update = pricing_schedule[mask]

    # event is on the same date as accrual start date - so just update; no need to split
    exact_match = row_to_update["accrual_start_date"] == event_date
    if exact_match.any():
        idx = row_to_update[exact_match].index[0]
        add_event_to_row(event, event_type, event_date, event_amount, amortization_term, pricing_schedule, idx)
        if additional_values_to_add:
            for key, value in additional_values_to_add.items():
                pricing_schedule.at[idx, key] = value
        return pricing_schedule

    else:
        to_split = row_to_update[~exact_match].copy()
        pricing_schedule.loc[to_split.index, "accrual_end_date"] = event_date - timedelta(days=1)
        new_rows = to_split.copy().reset_index(drop=True)

        #ensure any draws that were from the original row are wiped out
        #if this is a draw event then the appropriate draw amount will added later down in the code
        _clear_all_draws_from_new_row(new_rows, to_split)

        new_rows["accrual_start_date"] = event_date
        new_rows["accrual_sub_period"] = new_rows["accrual_sub_period"] + 1

        reset_event_indicators(new_rows, 0)

        add_event_to_row(event, event_type, event_date, event_amount, amortization_term, new_rows, 0)
        if additional_values_to_add:
            for key, value in additional_values_to_add.items():
                new_rows[key] = value

        if event_type != "draw":
            new_rows["draw_type"] = np.nan

        pricing_schedule = pd.concat([pricing_schedule, new_rows], ignore_index=True)
        pricing_schedule.sort_values(by="accrual_start_date", inplace=True)
        pricing_schedule.reset_index(drop=True, inplace=True)
        pricing_schedule["event_date"] = pd.to_datetime(pricing_schedule["event_date"]).dt.date

        return pricing_schedule


def process_draw(event: Dict[str, Any], pricing_schedule: pd.DataFrame) -> pd.DataFrame:
    print(
        "\033[94m",
        f"Event: {event['event_date']}",
        "\033[0m",
    )


    return split_or_update_event(event, pricing_schedule)


def process_p_and_i(event: Dict[str, Any], pricing_schedule: pd.DataFrame) -> pd.DataFrame:
    return split_or_update_event(event, pricing_schedule, {"payment_type": event.get("event_details")})


def get_event_handler(event_type: str):
    event_handlers = {
        "draw": process_draw,
        "principal due": process_p_and_i,
        "interest due": process_p_and_i,
        "principal payment": process_p_and_i,
        "interest payment": process_p_and_i,
        "interest payoff due": process_p_and_i,
        "principal payoff due": process_p_and_i,
    }
    try:
        return event_handlers[event_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported event type: {event_type}") from exc


def _iter_events(events: Iterable[Dict[str, Any]] | pd.DataFrame) -> List[Dict[str, Any]]:
    if isinstance(events, pd.DataFrame):
        return events.sort_values("event_date", ascending=True).to_dict("records")
    return list(events)


def _calculate_draw_unfunded(schedule: pd.DataFrame) -> pd.DataFrame:

    result = schedule.copy()
    draw_columns = pd.Index(result.columns).astype(str)
    draw_buckets = (
        draw_columns.str.extract(r"^draw:(.+?):")[0].dropna().drop_duplicates().tolist()
    )

    for bucket in draw_buckets:
        detail_col = f"draw:{bucket}:details"
        amount_col = f"draw:{bucket}:amount"
        if detail_col not in result.columns or amount_col not in result.columns:
            continue

        details_series = result[detail_col].dropna()
        if details_series.empty:
            continue

        first_details = details_series.iloc[0]
        details_dict = _coerce_event_details(first_details)
        total_amount = float(details_dict.get("LLC_BI__AMOUNT__C", 0))

        funded = pd.to_numeric(result[amount_col], errors="coerce").fillna(0)
        result[f"draw:{bucket}:unfunded"] = total_amount - funded.cumsum()

    result["principal_paid_at_start"] = np.nan
    return result


def merge_transactions_into_schedule(
    loan_terms: Dict,
    event_schedule: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge transaction events into the accrual schedule.

    Args:
        loan_terms: Loan metadata dictionary (currently unused, reserved for future logic).
        event_schedule: DataFrame produced by `step1.generate_accrual_schedule`.
        events: Iterable of events or DataFrame from `step2.form_transactions`.

    Returns:
        Tuple of:
            - DataFrame equivalent to `3. transactions_merged.xlsx`.
            - DataFrame equivalent to `3.1 transactions_merged_and_draws.xlsx`.
    """
    merged_schedule = event_schedule.copy()
    for event in _iter_events(events):
        handler = get_event_handler(event["event_type"])
        merged_schedule = handler(event, merged_schedule)


    # draw_buckets = list(pd.Index(merged_schedule.columns).str.extract(r'^draw:(.+?):')[0]   .dropna().pipe(pd.unique))
    # for bucket in draw_buckets:
    #     details = list(merged_schedule[f'draw:{bucket}:details'].dropna())[0] #just get first non-nan value
    #     total_amount = json.loads(details)['LLC_BI__AMOUNT__C']
    #     amt = pd.to_numeric(merged_schedule[f'draw:{bucket}:amount'], errors='coerce').fillna(0)
    #     merged_schedule[f'draw:{bucket}:unfunded'] = float(total_amount) - amt.cumsum()

    # merged_schedule['principal_paid_at_start'] = np.nan
    # return merged_schedule
    merged_with_draws = _calculate_draw_unfunded(merged_schedule)
    return merged_with_draws
