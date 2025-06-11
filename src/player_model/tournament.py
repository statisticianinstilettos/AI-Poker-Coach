import numpy as np
import pandas as pd

def tournament_structure(num_players, buy_in, rake_percent=0.1, paid_percent=0.15, curve_exponent=1.3, rounding=5):
    """
    Generate a poker tournament payout structure s(x).

    Parameters:
        num_players (int): Total number of players in the tournament.
        buy_in (float): Buy-in amount per player.
        rake_percent (float): Percentage of rake taken from the buy-in (default 10%).
        paid_percent (float): Percentage of players who get paid (default 15%).
        curve_exponent (float): Exponent for power-law payout curve (higher = more top-heavy).
        rounding (int): Round payouts to the nearest multiple of this value.

    Returns:
        pd.DataFrame: A table with Place and Payout ($).
        float: Total prize pool.
    """
    total_buy_in = num_players * buy_in
    prize_pool = total_buy_in * (1 - rake_percent)

    num_paid = max(1, int(num_players * paid_percent))

    # Generate weights for the payout curve
    weights = np.array([1 / (i + 1) ** curve_exponent for i in range(num_paid)])
    total_weight = np.sum(weights)

    raw_payouts = prize_pool * (weights / total_weight)
    payouts = np.round(raw_payouts / rounding) * rounding

    # Adjust for any rounding error
    rounding_error = prize_pool - np.sum(payouts)
    payouts[0] += rounding_error  # Fix the top payout to match exact prize pool

    # Generate payout table
    payout_table = pd.DataFrame({
        'Place': [f'{i+1}' for i in range(num_paid)],
        'Payout ($)': payouts.astype(int)
    })

    return payout_table