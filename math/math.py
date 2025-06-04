import numpy as np

def tournament_structure(position, num_players, buy_in, payout_percentages=None):
    """
    Calculate the payout s(x) for each position in the tournament.
    
    Args:
        position (int): Final position in tournament (1 = 1st place)
        num_players (int): Total number of players in tournament
        buy_in (float): Tournament buy-in amount
        payout_percentages (list, optional): List of percentages for each paying position.
            If None, uses a standard payout structure:
            - 50% for 1st
            - 30% for 2nd
            - 20% for 3rd
            - 0% for all others
    
    Returns:
        float: Payout for given position s(x)
    """
    if payout_percentages is None:
        payout_percentages = [0.5, 0.3, 0.2] + [0] * (num_players - 3)
    
    # Ensure payout_percentages matches number of players
    if len(payout_percentages) != num_players:
        payout_percentages = payout_percentages + [0] * (num_players - len(payout_percentages))
    
    # Calculate prize pool
    prize_pool = buy_in * num_players
    
    # Calculate payout for position
    payout = prize_pool * payout_percentages[position - 1]
    
    return payout

def player_distribution(num_players, distribution_type="uniform"):
    """
    Generate probability distribution p(x) of player finishing positions.
    
    Args:
        num_players (int): Total number of players in tournament
        distribution_type (str): Type of distribution to use
            - "uniform": Equal probability of finishing in each position
            - Additional distributions can be added later based on player data
    
    Returns:
        numpy.ndarray: Array of probabilities for each position
    """
    if distribution_type == "uniform":
        # Equal probability of finishing in each position
        probabilities = np.ones(num_players) / num_players
    else:
        raise ValueError(f"Distribution type '{distribution_type}' not supported")
    
    return probabilities

def calculate_tournament_ev(num_players, buy_in, num_rebuys=0, p_distribution=None, payout_percentages=None):
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
            If None, uses uniform distribution
        payout_percentages (list, optional): Custom payout structure.
            If None, uses default structure
    
    Returns:
        float: Expected value of playing in the tournament
    
    Example:
        # Calculate EV for a 10-player tournament with:
        # - $100 buy-in
        # - 1 expected rebuy
        ev = calculate_tournament_ev(
            num_players=10,
            buy_in=100,
            num_rebuys=1
        )
    """
    # Get probability distribution
    if p_distribution is None:
        p_distribution = player_distribution(num_players)
    
    # Calculate s(x) (payout) for each position
    s_values = [tournament_structure(pos, num_players, buy_in, payout_percentages) 
                for pos in range(1, num_players + 1)]
    
    # Calculate EV using formula: EV = sum[p(x)s(x)] - c(1 + r)
    total_cost = buy_in * (1 + num_rebuys)  # c(1 + r)
    ev = sum(p * s for p, s in zip(p_distribution, s_values)) - total_cost
    
    return ev

# Example usage
if __name__ == "__main__":
    # Example: 10-player tournament with $100 buy-in and 1 expected rebuy
    NUM_PLAYERS = 150
    BUY_IN = 200
    NUM_REBUYS = 0
    
    # Calculate EV using uniform distribution
    ev = calculate_tournament_ev(NUM_PLAYERS, BUY_IN, NUM_REBUYS)
    print(f"\nTournament EV Analysis:")
    print(f"Number of players: {NUM_PLAYERS}")
    print(f"Buy-in: ${BUY_IN}")
    print(f"Expected rebuys: {NUM_REBUYS}")
    print(f"Total investment: ${BUY_IN * (1 + NUM_REBUYS)}")
    print(f"Expected Value: ${ev:.2f}")
    
    # Show payout structure
    print("\nPayout Structure:")
    for pos in range(1, NUM_PLAYERS + 1):
        payout = tournament_structure(pos, NUM_PLAYERS, BUY_IN)
        if payout > 0:  # Only show paying positions
            print(f"{pos}th place: ${payout:.2f}")
    
    # Show probability distribution
    print("\nProbability Distribution (Uniform):")
    p_dist = player_distribution(NUM_PLAYERS)
    for pos, prob in enumerate(p_dist, 1):
        print(f"Position {pos}: {prob:.1%}")
