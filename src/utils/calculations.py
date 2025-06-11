"""
Centralized calculation utilities for Poker Coach application.
Eliminates logic duplication by providing single methods for common calculations.
"""


def calculate_total_investment(buy_in, num_rebuys, addon_cost):
    """
    Calculate total tournament investment.
    
    Args:
        buy_in (float): Tournament buy-in amount
        num_rebuys (int): Number of rebuys
        addon_cost (float): Add-on cost
        
    Returns:
        float: Total investment amount
    """
    return buy_in * (1 + num_rebuys) + addon_cost


def calculate_profit_loss(prize_won, total_investment):
    """
    Calculate profit or loss from tournament.
    
    Args:
        prize_won (float): Prize money won
        total_investment (float): Total amount invested
        
    Returns:
        float: Profit (positive) or loss (negative)
    """
    return prize_won - total_investment


def calculate_roi(profit_loss, total_investment):
    """
    Calculate return on investment percentage.
    
    Args:
        profit_loss (float): Profit or loss amount
        total_investment (float): Total amount invested
        
    Returns:
        float: ROI percentage (handles division by zero)
    """
    if total_investment <= 0:
        return 0.0
    return (profit_loss / total_investment) * 100


def calculate_tournament_metrics(prize_won, buy_in, num_rebuys, addon_cost):
    """
    Calculate all tournament financial metrics at once.
    
    Args:
        prize_won (float): Prize money won
        buy_in (float): Tournament buy-in amount
        num_rebuys (int): Number of rebuys
        addon_cost (float): Add-on cost
        
    Returns:
        dict: Dictionary with total_investment, profit_loss, roi
    """
    total_investment = calculate_total_investment(buy_in, num_rebuys, addon_cost)
    profit_loss = calculate_profit_loss(prize_won, total_investment)
    roi = calculate_roi(profit_loss, total_investment)
    
    return {
        'total_investment': total_investment,
        'profit_loss': profit_loss,
        'roi': roi
    }


def calculate_overall_performance(tournament_results):
    """
    Calculate overall performance statistics from tournament results.
    
    Args:
        tournament_results (list): List of tournament result dictionaries
        
    Returns:
        dict: Overall performance statistics
    """
    if not tournament_results:
        return {
            'total_tournaments': 0,
            'total_profit': 0.0,
            'total_investment': 0.0,
            'overall_roi': 0.0,
            'itm_count': 0,
            'itm_rate': 0.0
        }
    
    total_tournaments = len(tournament_results)
    total_profit = sum(t['prize_won'] - t['total_investment'] for t in tournament_results)
    total_investment = sum(t['total_investment'] for t in tournament_results)
    overall_roi = calculate_roi(total_profit, total_investment)
    
    itm_count = sum(1 for t in tournament_results if t['prize_won'] > 0)
    itm_rate = (itm_count / total_tournaments * 100) if total_tournaments > 0 else 0
    
    return {
        'total_tournaments': total_tournaments,
        'total_profit': total_profit,
        'total_investment': total_investment,
        'overall_roi': overall_roi,
        'itm_count': itm_count,
        'itm_rate': itm_rate
    }


def calculate_performance_by_format(tournament_results):
    """
    Calculate performance statistics by tournament format.
    
    Args:
        tournament_results (list): List of tournament result dictionaries
        
    Returns:
        dict: Performance statistics by format (Live/Online)
    """
    live_tournaments = [t for t in tournament_results if t.get('format') == 'Live']
    online_tournaments = [t for t in tournament_results if t.get('format') == 'Online']
    
    live_stats = calculate_overall_performance(live_tournaments)
    online_stats = calculate_overall_performance(online_tournaments)
    
    return {
        'live': live_stats,
        'online': online_stats
    } 