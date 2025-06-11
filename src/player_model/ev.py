import numpy as np
from tournament import tournament_structure
from player import player_pdf

def calculate_tournament_ev(num_players, buy_in, num_rebuys=0, p_distribution=None, rake_percent=0.1, paid_percent=0.15, tournament_history=None, format_filter=None, buyin_range=None):
    """
    Calculate tournament Expected Value using formula:
    EV = sum[p(x)s(x)] - c(1 + r)
    where:
    - p(x) is probability of finishing in position x
    - s(x) is payout for position x
    - c is initial buy-in cost
    - r is number of rebuys
    
    Args:
        num_players (int): Total number of players in tournament
        buy_in (float): Tournament buy-in amount (c)
        num_rebuys (int): Expected number of rebuys (r)
        p_distribution (numpy.ndarray, optional): Custom probability distribution.
            If None, uses player_pdf (which handles both personalized and uniform distributions)
        rake_percent (float): Percentage of rake taken from buy-in
        paid_percent (float): Percentage of players who get paid
        tournament_history (list, optional): Historical tournament data for personalized distribution
        format_filter (str, optional): Filter historical data by format
        buyin_range (tuple, optional): Filter historical data by buy-in range
    
    Returns:
        float: Expected value of playing in the tournament
        dict: Additional metadata if personalized distribution is used
    """
    metadata = None
    
    # Get probability distribution using centralized player_pdf method
    if p_distribution is not None:
        # Use provided distribution
        pass
    else:
        # Use player_pdf for all probability calculations (handles both personalized and uniform)
        p_distribution, metadata = player_pdf(
            tournament_history, num_players, format_filter, buyin_range
        )
    
    # Get payout structure
    payout_table = tournament_structure(num_players, buy_in, rake_percent, paid_percent)
    
    # Create array of all possible payouts (0 for non-paying positions)
    s_values = np.zeros(num_players)
    s_values[:len(payout_table)] = payout_table['Payout ($)'].values
    
    # Calculate EV using formula: EV = sum[p(x)s(x)] - c(1 + r)
    total_cost = buy_in * (1 + num_rebuys)  # c(1 + r)
    ev = sum(p * s for p, s in zip(p_distribution, s_values)) - total_cost
    
    if metadata:
        return ev, metadata
    else:
        return ev

# Example usage
if __name__ == "__main__":
    # Example: 10-player tournament with $100 buy-in, rebuy allowed, and no add-on
    player = "William"
    casino = "Planet Hollywood"
    NUM_PLAYERS = 150
    BUY_IN = 200
    NUM_REBUYS = 0
    ADD_ON = 0
    RAKE_PERCENT = 0.1  # 10% rake
    PAID_PERCENT = 0.15  # Top 15% get paid

    # Calculate EV using uniform distribution
    ev = calculate_tournament_ev(NUM_PLAYERS, BUY_IN, NUM_REBUYS, 
                               rake_percent=RAKE_PERCENT, 
                               paid_percent=PAID_PERCENT)
    
    # Get payout structure for display
    payout_structure = tournament_structure(NUM_PLAYERS, BUY_IN, 
                                         rake_percent=RAKE_PERCENT, 
                                         paid_percent=PAID_PERCENT)

    print(f"\nPlayer Name: {player}")
    print(f"\nCasino Name: {casino}")
    print(f"\nTournament EV Analysis:")
    print(f"Expected number of players: {NUM_PLAYERS}")
    print(f"Buy-in: ${BUY_IN}")
    print(f"Add-on: ${ADD_ON}")
    print(f"Rebuy cost: ${NUM_REBUYS}")
    print(f"Rake: {RAKE_PERCENT*100}%")
    print(f"Players paid: {PAID_PERCENT*100}%")
    print(f"Total investment: ${BUY_IN * (1 + NUM_REBUYS)}")
    print(f"Expected Value: ${ev:.2f}")
    print("\nPayout Structure:")
    print(payout_structure.to_string(index=False))
