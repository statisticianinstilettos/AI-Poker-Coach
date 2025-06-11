import numpy as np
import pandas as pd

def player_pdf(tournament_history, field_size, format_filter=None, buyin_range=None):
    """
    Create a personalized probability distribution based on historical tournament performance.
    If no tournament history is provided, returns uniform distribution.
    
    This is the centralized function for ALL probability calculations in the system.
    
    Args:
        tournament_history (list): List of tournament results dictionaries (can be None/empty for uniform)
        field_size (int): Expected field size for the tournament being analyzed
        format_filter (str, optional): Filter by format ('Live' or 'Online')
        buyin_range (tuple, optional): Filter by buy-in range (min_buyin, max_buyin)
    
    Returns:
        numpy.ndarray: Probability array for each finishing position (personalized or uniform)
        dict: Analysis metadata (confidence_level, sample_size, method, etc.)
    """
    
    if not tournament_history:
        # No data available, return uniform distribution
        return np.ones(field_size) / field_size, {"confidence_level": "low", "sample_size": 0, "method": "uniform_fallback"}
    
    # Filter tournaments based on criteria
    filtered_tournaments = tournament_history.copy()
    
    if format_filter:
        filtered_tournaments = [t for t in filtered_tournaments if t.get('format') == format_filter]
    
    if buyin_range:
        min_buyin, max_buyin = buyin_range
        filtered_tournaments = [t for t in filtered_tournaments 
                              if min_buyin <= t.get('buy_in', 0) <= max_buyin]
    
    if not filtered_tournaments:
        # No tournaments match the criteria, return uniform distribution
        return np.ones(field_size) / field_size, {"confidence_level": "low", "sample_size": 0, "method": "no_matching_data"}
    
    # Extract finish percentages (position/total_entries) from historical data
    finish_percentages = []
    for tournament in filtered_tournaments:
        position = tournament.get('position_finished', 0)
        total_entries = tournament.get('total_entries', 0)
        if position > 0 and total_entries > 0:
            # Convert to percentile (lower is better in poker)
            percentile = position / total_entries
            finish_percentages.append(percentile)
    
    if not finish_percentages:
        return np.ones(field_size) / field_size, {"confidence_level": "low", "sample_size": 0, "method": "invalid_data"}
    
    # Create distribution based on historical performance
    sample_size = len(finish_percentages)
    probabilities = np.zeros(field_size)
    
    # Method 1: Kernel Density Estimation for larger sample sizes
    if sample_size >= 10:
        try:
            from scipy import stats
            
            # Create kernel density estimation
            kde = stats.gaussian_kde(finish_percentages)
            
            # Generate probabilities for each position
            for position in range(1, field_size + 1):
                percentile = position / field_size
                # Sample around this percentile with some bandwidth
                prob_density = kde(percentile)[0]
                probabilities[position - 1] = prob_density
            
            # Normalize probabilities
            probabilities = probabilities / probabilities.sum()
            confidence_level = "high" if sample_size >= 20 else "medium"
            method = "kde"
        except ImportError:
            # Fall back to histogram method if scipy is not available
            # Create histogram bins
            num_bins = min(10, field_size // 10, sample_size)
            bin_edges = np.linspace(0, 1, num_bins + 1)
            
            # Count frequencies in each bin
            hist, _ = np.histogram(finish_percentages, bins=bin_edges)
            
            # Map histogram to position probabilities
            for position in range(1, field_size + 1):
                percentile = position / field_size
                bin_index = min(int(percentile * num_bins), num_bins - 1)
                probabilities[position - 1] = hist[bin_index]
            
            # Normalize probabilities
            if probabilities.sum() > 0:
                probabilities = probabilities / probabilities.sum()
            else:
                probabilities = np.ones(field_size) / field_size
                
            confidence_level = "medium"
            method = "histogram_fallback"
    
    # Method 2: Histogram-based approach for medium sample sizes
    elif sample_size >= 5:
        # Create histogram bins
        num_bins = min(10, field_size // 10, sample_size)
        bin_edges = np.linspace(0, 1, num_bins + 1)
        
        # Count frequencies in each bin
        hist, _ = np.histogram(finish_percentages, bins=bin_edges)
        
        # Map histogram to position probabilities
        for position in range(1, field_size + 1):
            percentile = position / field_size
            bin_index = min(int(percentile * num_bins), num_bins - 1)
            probabilities[position - 1] = hist[bin_index]
        
        # Normalize probabilities
        if probabilities.sum() > 0:
            probabilities = probabilities / probabilities.sum()
        else:
            probabilities = np.ones(field_size) / field_size
            
        confidence_level = "medium"
        method = "histogram"
    
    # Method 3: Simple weighted approach for small sample sizes
    else:
        # For small sample sizes, create a weighted distribution
        # Give higher probability to positions similar to historical performance
        avg_percentile = np.mean(finish_percentages)
        std_percentile = np.std(finish_percentages) if sample_size > 1 else 0.2
        
        # Create gaussian-like distribution centered on average performance
        for position in range(1, field_size + 1):
            percentile = position / field_size
            # Calculate weight based on distance from average performance
            weight = np.exp(-((percentile - avg_percentile) ** 2) / (2 * std_percentile ** 2))
            probabilities[position - 1] = weight
        
        # Normalize probabilities
        probabilities = probabilities / probabilities.sum()
        confidence_level = "low"
        method = "gaussian_weighted"
    
    # Calculate additional metadata
    avg_finish_percentile = np.mean(finish_percentages)
    best_finish_percentile = min(finish_percentages)
    worst_finish_percentile = max(finish_percentages)
    
    metadata = {
        "confidence_level": confidence_level,
        "sample_size": sample_size,
        "method": method,
        "avg_finish_percentile": avg_finish_percentile,
        "best_finish_percentile": best_finish_percentile,
        "worst_finish_percentile": worst_finish_percentile,
        "expected_finish_position": int(avg_finish_percentile * field_size),
        "filters_applied": {
            "format": format_filter,
            "buyin_range": buyin_range
        }
    }
    
    return probabilities, metadata