import numpy as np
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO) # Uncomment for standalone testing

def calculate_arithmetic_grid_levels(lower_price: float, upper_price: float, num_grids: int) -> Optional[List[float]]:
    """
    Calculates grid levels using an arithmetic progression (equal price difference).

    Args:
        lower_price: The lower bound of the price range.
        upper_price: The upper bound of the price range.
        num_grids: The number of grid lines (orders to place).

    Returns:
        A list of grid price levels, or None if inputs are invalid.
    """
    if not (isinstance(lower_price, (int, float)) and isinstance(upper_price, (int, float)) and isinstance(num_grids, int)):
         logger.error("Invalid input types for arithmetic grid calculation.")
         return None
    if lower_price <= 0 or upper_price <= lower_price or num_grids <= 0:
        logger.error(f"Invalid grid parameters: lower={lower_price}, upper={upper_price}, num_grids={num_grids}")
        return None
    if num_grids == 1: # Edge case: only one grid line
         return [(lower_price + upper_price) / 2] # Place it in the middle

    # Calculate the price difference between grids
    price_diff = (upper_price - lower_price) / num_grids

    # Generate grid levels (excluding the upper bound itself, as orders are typically placed between levels)
    # Or include bounds depending on strategy - this generates num_grids levels *within* the range
    levels = [lower_price + i * price_diff for i in range(num_grids + 1)] 
    
    # Alternative: linspace includes endpoints, adjust num_grids if needed
    # levels = np.linspace(lower_price, upper_price, num_grids + 1).tolist() 

    logger.info(f"Calculated {len(levels)} arithmetic grid levels between {lower_price} and {upper_price}.")
    # Return levels excluding bounds, or adjust based on how orders are placed (at level vs between levels)
    # This example returns num_grids+1 levels including bounds
    return levels


def calculate_geometric_grid_levels(lower_price: float, upper_price: float, num_grids: int) -> Optional[List[float]]:
    """
    Calculates grid levels using a geometric progression (equal price ratio).

    Args:
        lower_price: The lower bound of the price range.
        upper_price: The upper bound of the price range.
        num_grids: The number of grid lines (orders to place).

    Returns:
        A list of grid price levels, or None if inputs are invalid.
    """
    if not (isinstance(lower_price, (int, float)) and isinstance(upper_price, (int, float)) and isinstance(num_grids, int)):
         logger.error("Invalid input types for geometric grid calculation.")
         return None
    if lower_price <= 0 or upper_price <= lower_price or num_grids <= 0:
        logger.error(f"Invalid grid parameters: lower={lower_price}, upper={upper_price}, num_grids={num_grids}")
        return None
    if num_grids == 1:
         return [(lower_price + upper_price) / 2] # Or sqrt(lower*upper) for geometric mean?

    # Calculate the common ratio between grid levels
    ratio = (upper_price / lower_price) ** (1 / num_grids)

    # Generate grid levels
    levels = [lower_price * (ratio ** i) for i in range(num_grids + 1)]
    
    # Ensure upper bound is included accurately due to potential float precision issues
    levels[-1] = upper_price 

    logger.info(f"Calculated {len(levels)} geometric grid levels between {lower_price} and {upper_price} with ratio {ratio:.4f}.")
    return levels


def calculate_order_size_per_grid(total_investment: float, num_buy_grids: int, entry_price: float) -> Optional[float]:
    """
    Calculates the quantity (size) for each buy order in the grid.
    Assumes equal investment per buy grid level.

    Args:
        total_investment: The total amount of quote currency (e.g., USDT) to invest across buy grids.
        num_buy_grids: The number of buy orders to place below the entry price.
        entry_price: The price at which the grid strategy is initiated (used for initial calculation).
                     Note: A more complex calculation might average expected buy prices.

    Returns:
        The quantity of base asset (e.g., BTC) to buy per grid line, or None if inputs invalid.
    """
    if not (isinstance(total_investment, (int, float)) and isinstance(num_buy_grids, int) and isinstance(entry_price, (int, float))):
         logger.error("Invalid input types for order size calculation.")
         return None
    if total_investment <= 0 or num_buy_grids <= 0 or entry_price <= 0:
        logger.error(f"Invalid parameters for order size: investment={total_investment}, num_grids={num_buy_grids}, entry_price={entry_price}")
        return None

    investment_per_grid = total_investment / num_buy_grids
    # Estimate quantity based on entry price - actual quantity might vary slightly per level
    # A more precise method would calculate quantity based on each specific grid level price.
    quantity_per_grid = investment_per_grid / entry_price 

    logger.info(f"Calculated order size: {quantity_per_grid:.8f} per grid for {num_buy_grids} buy grids, total investment {total_investment}")
    return quantity_per_grid

# --- Example Usage ---
if __name__ == "__main__":
    lower = 50000.0
    upper = 60000.0
    grids = 5
    investment = 1000.0 # USDT
    entry = 55000.0

    logger.info("--- Arithmetic Grid ---")
    arith_levels = calculate_arithmetic_grid_levels(lower, upper, grids)
    if arith_levels:
        logger.info(f"Levels ({len(arith_levels)}): {[f'{lvl:.2f}' for lvl in arith_levels]}")
        order_size = calculate_order_size_per_grid(investment, grids // 2, entry) # Assume half buy grids
        logger.info(f"Estimated Order Size: {order_size}")


    logger.info("\n--- Geometric Grid ---")
    geom_levels = calculate_geometric_grid_levels(lower, upper, grids)
    if geom_levels:
        logger.info(f"Levels ({len(geom_levels)}): {[f'{lvl:.2f}' for lvl in geom_levels]}")
        order_size = calculate_order_size_per_grid(investment, grids // 2, entry) # Assume half buy grids
        logger.info(f"Estimated Order Size: {order_size}")

    logger.info("\n--- Invalid Cases ---")
    calculate_arithmetic_grid_levels(60000, 50000, 5)
    calculate_geometric_grid_levels(50000, 60000, 0)
    calculate_order_size_per_grid(1000, 0, 55000)