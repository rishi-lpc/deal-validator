"""
Preferred Equity Catch-Up Module (Server Adapted)

Calculates the pref_equity_catch_up amount needed on the last row to achieve
a target IRR return, then checks if min_moic is met and adds additional
catch-up if needed.

Logic:
1. Calculate catch-up based on target IRR (using pref-specific cashflows)
2. Check if result meets min_moic threshold
3. If not, calculate additional catch-up needed for min_moic
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
from scipy.optimize import brentq

try:
    import numpy_financial as npf
    HAS_NPF = True
except ImportError:
    HAS_NPF = False


def safe_get_column(df: pd.DataFrame, col: str, default=0) -> pd.Series:
    """Safely get a column from DataFrame, returning default Series if missing."""
    if col not in df.columns:
        return pd.Series(default, index=df.index)
    return df[col].fillna(default)


def prepare_server_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame by adding columns needed for pref equity calculation.

    Server column mappings:
    - total_period_draw: Sum all draw_*_amount columns
    - is_accrual_period_complete: Default to 1 (all complete)
    - period_fees_paid: Use all_fees_due
    - cummulative_draw_amount: Cumsum of total_period_draw
    - pre_payment_fee: Default to 0 (not present in server)

    Args:
        df: Server DataFrame with server-specific columns

    Returns:
        DataFrame with additional columns for pref equity
    """
    df = df.copy()

    # Calculate total_period_draw from all draw amount columns
    # Handle both formats:
    # - Underscore format: draw_*_amount (after prepare_for_client)
    # - Colon format: draw:*:amount (before prepare_for_client)
    draw_amount_cols = [col for col in df.columns if
                       (col.startswith('draw_') and col.endswith('_amount')) or
                       (col.startswith('draw:') and col.endswith(':amount'))]
    if draw_amount_cols:
        df['total_period_draw'] = df[draw_amount_cols].fillna(0).sum(axis=1)
    else:
        df['total_period_draw'] = 0.0

    # is_accrual_period_complete: Default to 1 (all periods complete)
    if 'is_accrual_period_complete' not in df.columns:
        df['is_accrual_period_complete'] = 1

    # period_fees_paid: Use all_fees_due from server
    if 'period_fees_paid' not in df.columns:
        df['period_fees_paid'] = safe_get_column(df, 'all_fees_due', 0)

    # cummulative_draw_amount: Cumulative sum of draws
    if 'cummulative_draw_amount' not in df.columns:
        df['cummulative_draw_amount'] = df['total_period_draw'].cumsum()

    # pre_payment_fee: Not present in server, default to 0
    if 'pre_payment_fee' not in df.columns:
        df['pre_payment_fee'] = 0.0

    return df


def calculate_irr(cashflows: pd.Series) -> Optional[float]:
    """
    Calculate IRR (Internal Rate of Return) - per-period rate.

    Args:
        cashflows: Series of cashflow amounts

    Returns:
        Per-period rate of return, or None if calculation fails
    """
    if not HAS_NPF:
        return None

    cf = cashflows.values

    # Filter out zero cashflows at the end
    while len(cf) > 0 and cf[-1] == 0:
        cf = cf[:-1]

    if len(cf) < 2:
        return None

    try:
        irr = npf.irr(cf)
        if np.isnan(irr) or np.isinf(irr):
            return None
        return irr
    except (ValueError, RuntimeError):
        return None


def calculate_moic(total_outflows: float, total_inflows: float) -> float:
    """
    Calculate MOIC (Multiple on Invested Capital).

    MOIC = Total Inflows / Total Outflows

    Args:
        total_outflows: Total capital invested (positive number)
        total_inflows: Total returns received (positive number)

    Returns:
        MOIC value
    """
    if total_outflows == 0:
        return 0.0

    return total_inflows / total_outflows


def create_pref_draws_for_period(df: pd.DataFrame) -> pd.Series:
    """
    Create pref-specific draws by consolidating draws to first of each period.

    Uses is_accrual_period_complete to identify period boundaries.
    Draws should be placed on the first row of each accrual period.
    The first draw (closing date) stays where it is.

    Args:
        df: DataFrame with total_period_draw and is_accrual_period_complete columns

    Returns:
        Series with pref-adjusted draws (consolidated to period start)
    """
    draws = safe_get_column(df, 'total_period_draw', 0).copy()
    is_complete = safe_get_column(df, 'is_accrual_period_complete', 1)

    n = len(df)
    pref_draws = np.zeros(n)

    i = 0
    while i < n:
        if is_complete.iloc[i] == 1:
            # Complete period - draw stays here
            pref_draws[i] = draws.iloc[i]
            i += 1
        else:
            # Start of split period - consolidate all draws until next complete period
            period_draw_sum = draws.iloc[i]
            j = i + 1
            while j < n and is_complete.iloc[j] == 0:
                period_draw_sum += draws.iloc[j]
                j += 1
            # Put consolidated draw on first row of this period
            pref_draws[i] = period_draw_sum
            i = j

    return pd.Series(pref_draws, index=df.index)


def calculate_catch_up_for_irr(df: pd.DataFrame, pref_draws: pd.Series,
                                interest_paid: pd.Series, principal_paid: pd.Series,
                                fees_paid: pd.Series, target_irr: float) -> float:
    """
    Calculate the catch-up amount needed to achieve EXACTLY the target IRR.

    Uses goal-seek approach: find the catch-up amount that makes IRR = target_irr
    on pref-specific cashflows.

    Args:
        df: DataFrame
        pref_draws: Pref-specific draws (consolidated to period start)
        interest_paid: Interest payments
        principal_paid: Principal payments
        fees_paid: Fees paid
        target_irr: Target IRR as decimal (e.g., 0.23 for 23%) - this is per-period rate

    Returns:
        Catch-up amount needed
    """
    # Build base pref cashflow (without catch-up)
    # Same as period_cashflow but with draws shifted to first of month
    base_pref_cashflow = -pref_draws + interest_paid + principal_paid + fees_paid

    # Function to calculate IRR with a given catch-up added to last row
    def irr_with_catchup(catch_up_amount):
        cf = base_pref_cashflow.values.copy()
        cf[-1] += catch_up_amount

        # Filter out trailing zeros
        while len(cf) > 0 and cf[-1] == 0:
            cf = cf[:-1]

        if len(cf) < 2:
            return None

        try:
            irr = npf.irr(cf)
            if np.isnan(irr) or np.isinf(irr):
                return None
            return irr
        except (ValueError, RuntimeError):
            return None

    # Function for goal-seek: difference from target IRR
    def irr_diff(catch_up_amount):
        irr = irr_with_catchup(catch_up_amount)
        if irr is None:
            return float('inf')
        return irr - target_irr

    # Check current IRR without catch-up
    current_irr = irr_with_catchup(0)

    if current_irr is not None and current_irr >= target_irr:
        # Already meeting target
        return 0.0

    # Goal-seek: find catch_up such that IRR = target_irr
    # Start with reasonable bounds
    total_outflows = abs(pref_draws.sum())
    low = 0
    high = total_outflows * 5  # Start with 5x the investment as upper bound

    # Expand upper bound if needed
    max_iterations = 20
    iteration = 0
    while irr_diff(high) < 0 and iteration < max_iterations:
        high *= 2
        iteration += 1

    try:
        catch_up = brentq(irr_diff, low, high, maxiter=1000)
        return max(catch_up, 0)
    except (ValueError, RuntimeError):
        # Fallback: if brentq fails, return 0
        return 0.0


def calculate_pref_equity_catch_up(
    df: pd.DataFrame,
    target_irr: Optional[float] = None,
    min_moic: Optional[float] = None
) -> Tuple[pd.DataFrame, dict]:
    """
    Calculate pref equity catch-up based on target IRR and/or min_moic.

    Safeguards:
    1. If both values are absent or zero - return with zero catch-up columns
    2. If only target_irr is present - calculate IRR catch-up only, no MOIC consideration
    3. If only min_moic is present - calculate MOIC catch-up only

    When both are present:
    1. Calculate catch-up needed to achieve target_irr (using pref cashflows)
    2. Check if resulting MOIC meets min_moic threshold
    3. If not, calculate additional catch-up needed for min_moic

    MOIC calculation uses:
    - Outflows: cummulative_draw_amount (all capital ever funded)
    - Inflows: interest_paid + principal_paid + fees_paid (excluding pre_payment_fee) + catch_up

    Args:
        df: DataFrame from server output
        target_irr: Target IRR as decimal (e.g., 0.12 for 12% per period), optional
        min_moic: Minimum MOIC threshold (e.g., 1.5 for 1.5x), optional

    Returns:
        Tuple of:
        - Modified DataFrame with pref columns added
        - Dictionary with metrics
    """
    print(f"=== PREF EQUITY DEBUG: Starting calculation ===")
    print(f"Input DataFrame shape: {df.shape}")
    print(f"Target IRR: {target_irr}, Min MOIC: {min_moic}")
    print(f"DataFrame columns: {list(df.columns)[:10]}...")

    # Prepare server columns for pref equity calculation
    df = prepare_server_columns(df)
    print(f"After prepare_server_columns, shape: {df.shape}")

    # Ensure date column exists
    if 'accrual_start_date' not in df.columns:
        raise ValueError("DataFrame must have accrual_start_date column")

    df['accrual_start_date'] = pd.to_datetime(df['accrual_start_date'])

    # Create pref-specific draws (consolidated to period start)
    pref_draws = create_pref_draws_for_period(df)
    df['pref_amount_drawn'] = pref_draws

    # Get cashflow components
    interest_paid = safe_get_column(df, 'interest_paid_at_start', 0).copy()
    principal_paid = safe_get_column(df, 'principal_paid_at_start', 0).copy()
    fees_paid = safe_get_column(df, 'period_fees_paid', 0)

    # Add balloon payment on last row (for interest-only loans)
    # principal_due_at_start_of_next_period represents the balloon principal payment
    # base_interest_amount_due_at_start_of_next_period represents the final interest payment
    balloon_principal = safe_get_column(df, 'principal_due_at_start_of_next_period', 0)
    balloon_interest = safe_get_column(df, 'base_interest_amount_due_at_start_of_next_period', 0)

    # Add balloon to last row cashflows
    principal_paid.iloc[-1] += balloon_principal.iloc[-1]
    interest_paid.iloc[-1] += balloon_interest.iloc[-1]

    print(f"Balloon payment added: Principal=${balloon_principal.iloc[-1]:,.2f}, Interest=${balloon_interest.iloc[-1]:,.2f}")

    # MOIC uses cummulative_draw_amount as the denominator (all capital funded)
    cummulative_draw_amount = safe_get_column(df, 'cummulative_draw_amount', 0)
    total_funded = cummulative_draw_amount.iloc[-1]  # Total capital ever funded

    # MOIC inflows: interest + principal + fees (excluding pre_payment_fee)
    pre_payment_fee = safe_get_column(df, 'pre_payment_fee', 0)
    # Fees excluding prepayment penalty
    fees_excl_prepay = fees_paid - pre_payment_fee

    total_interest = interest_paid.sum()
    total_principal = principal_paid.sum()
    total_fees = fees_excl_prepay.sum()
    base_inflows = total_interest + total_principal + total_fees

    print(f"Total inflows: Interest=${total_interest:,.2f}, Principal=${total_principal:,.2f}, Fees=${total_fees:,.2f}")

    # Normalize None/0 values
    has_target_irr = target_irr is not None and target_irr != 0
    has_min_moic = min_moic is not None and min_moic != 0

    # Convert annual target_irr to monthly rate for IRR calculations
    # target_irr from Salesforce is annual (e.g., 0.175 = 17.5% annual)
    # IRR = monthly_rate * 12, so monthly_rate = annual_rate / 12
    monthly_target_irr = None
    if has_target_irr:
        monthly_target_irr = target_irr / 12
        print(f"Converting annual IRR {target_irr:.2%} to monthly IRR {monthly_target_irr:.4%}")

    irr_catch_up = 0.0
    moic_catch_up = 0.0

    # Safeguard 1: Both absent or zero - keep catch-up columns at 0
    if not has_target_irr and not has_min_moic:
        pass  # Both catch-ups stay at 0

    # Safeguard 2: Only target_irr present - calculate IRR catch-up only
    elif has_target_irr and not has_min_moic:
        irr_catch_up = calculate_catch_up_for_irr(
            df, pref_draws, interest_paid, principal_paid, fees_paid, monthly_target_irr
        )

    # Safeguard 3: Only min_moic present - calculate MOIC catch-up only
    elif not has_target_irr and has_min_moic:
        current_moic = calculate_moic(total_funded, base_inflows)
        if current_moic < min_moic:
            required_inflows = min_moic * total_funded
            moic_catch_up = required_inflows - base_inflows
            moic_catch_up = max(moic_catch_up, 0)

    # Both present: IRR first, then check MOIC
    else:
        # Step 1: Calculate IRR-based catch-up
        irr_catch_up = calculate_catch_up_for_irr(
            df, pref_draws, interest_paid, principal_paid, fees_paid, monthly_target_irr
        )

        # Step 2: Check MOIC with IRR catch-up
        total_inflows_with_irr_catchup = base_inflows + irr_catch_up
        moic_with_irr_catchup = calculate_moic(total_funded, total_inflows_with_irr_catchup)

        # Step 3: Check if min_moic is met, calculate additional catch-up if needed
        if moic_with_irr_catchup < min_moic:
            required_inflows = min_moic * total_funded
            moic_catch_up = required_inflows - total_inflows_with_irr_catchup
            moic_catch_up = max(moic_catch_up, 0)

    # Total catch-up
    total_catch_up = irr_catch_up + moic_catch_up

    # Initialize catch-up columns
    df['pref_equity_catch_up'] = 0.0
    df['min_moic_catch_up'] = 0.0

    last_idx = df.index[-1]
    df.loc[last_idx, 'pref_equity_catch_up'] = irr_catch_up
    df.loc[last_idx, 'min_moic_catch_up'] = moic_catch_up

    # Build pref cashflow (with total catch-up on last row)
    # Same as period_cashflow but with draws shifted to first of month
    pref_cashflow = -pref_draws + interest_paid + principal_paid + fees_paid
    pref_cashflow.iloc[-1] += total_catch_up
    df['pref_cashflow'] = pref_cashflow

    # Update period_cashflow to include total catch-up if it exists
    if 'period_cashflow' in df.columns:
        df.loc[last_idx, 'period_cashflow'] = df.loc[last_idx, 'period_cashflow'] + total_catch_up

    # Calculate resulting metrics
    resulting_irr = calculate_irr(pref_cashflow)

    # Annualize IRR (assuming monthly periods)
    resulting_irr_annual = None
    if resulting_irr is not None:
        resulting_irr_annual = (1 + resulting_irr) ** 12 - 1

    # Final MOIC
    final_total_inflows = base_inflows + total_catch_up
    resulting_moic = calculate_moic(total_funded, final_total_inflows)

    metrics = {
        'target_irr': target_irr,
        'min_moic': min_moic,
        'irr_catch_up': irr_catch_up,
        'moic_catch_up': moic_catch_up,
        'total_catch_up': total_catch_up,
        'resulting_irr_periodic': resulting_irr,
        'resulting_irr_annual': resulting_irr_annual,
        'resulting_moic': resulting_moic,
        'total_funded': total_funded,
        'total_inflows': final_total_inflows
    }

    # Update Comments on last row only if there's any catch-up
    if total_catch_up > 0:
        current_comment = df.loc[last_idx, 'Comments'] if 'Comments' in df.columns else None
        if pd.isna(current_comment):
            current_comment = ""
        else:
            current_comment = str(current_comment)

        # Build pref equity comment based on what parameters were provided
        pref_comment_parts = []

        if has_target_irr and irr_catch_up > 0:
            pref_comment_parts.append(f"Pref Equity Catch-Up: ${irr_catch_up:,.2f} (target IRR: {target_irr:.2%} annual)")
        elif has_min_moic and not has_target_irr and moic_catch_up > 0:
            # Only MOIC was provided
            pref_comment_parts.append(f"MOIC Catch-Up: ${moic_catch_up:,.2f} (min MOIC: {min_moic:.2f}x)")

        if has_target_irr and has_min_moic and moic_catch_up > 0:
            pref_comment_parts.append(f"Min MOIC Catch-Up: ${moic_catch_up:,.2f} (min MOIC: {min_moic:.2f}x)")

        pref_comment_parts.append(f"Total Catch-Up: ${total_catch_up:,.2f}")

        # Add resulting metrics
        result_parts = []
        if resulting_irr is not None:
            result_parts.append(f"Resulting IRR: {resulting_irr:.2%}/period")
        if resulting_irr_annual is not None:
            result_parts.append(f"Annual: {resulting_irr_annual:.2%}")
        result_parts.append(f"MOIC: {resulting_moic:.2f}x")
        pref_comment_parts.append(' | '.join(result_parts))

        pref_comment = '\n'.join(pref_comment_parts)

        if 'Comments' not in df.columns:
            df['Comments'] = ""

        if current_comment:
            df.loc[last_idx, 'Comments'] = f"{current_comment}\n{pref_comment}"
        else:
            df.loc[last_idx, 'Comments'] = pref_comment

    return df, metrics
