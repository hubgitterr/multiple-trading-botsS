import logging
from decimal import Decimal, ROUND_DOWN

logger = logging.getLogger(__name__)

def get_step_size_precision(step_size_str: str) -> int:
    """
    Calculates the number of decimal places allowed by a step size.
    e.g., "0.001" -> 3, "1.0" -> 0, "0.00001000" -> 5
    """
    try:
        step_size_dec = Decimal(step_size_str)
        if step_size_dec.is_zero():
            logger.warning(f"Step size is zero ('{step_size_str}'), cannot determine precision. Defaulting to 8.")
            return 8 # Default precision if step size is zero

        # Find the position of the '1'
        if '.' in step_size_str:
            # Count digits after the decimal point up to the last non-zero digit
            normalized_step = step_size_str.rstrip('0')
            if '.' in normalized_step:
                 # Handle cases like "0.1", "0.001"
                 precision = len(normalized_step.split('.')[-1])
            else:
                 # Handle cases like "1.0", "10.0" -> precision 0
                 precision = 0
        else:
            # Handle integer step sizes like "1", "10" -> precision 0
            precision = 0
            
        # Clamp precision to a reasonable range (e.g., 0-8) if needed, though Binance usually provides valid ones.
        # precision = max(0, min(precision, 8)) 
        return precision
    except Exception as e:
        logger.error(f"Error parsing step size '{step_size_str}': {e}. Defaulting precision to 8.")
        return 8 # Default precision in case of error

def format_quantity(quantity: float | Decimal, step_size_str: str) -> float:
    """
    Formats the quantity according to the step size precision, rounding down.

    Args:
        quantity: The quantity to format (float or Decimal).
        step_size_str: The step size from Binance symbol info (e.g., "0.001000").

    Returns:
        The formatted quantity as a float.
    """
    try:
        quantity_dec = Decimal(str(quantity)) # Convert float to Decimal via string for precision
        step_size_dec = Decimal(step_size_str)

        if step_size_dec.is_zero():
             logger.warning(f"Step size is zero ('{step_size_str}'). Cannot apply step size formatting. Returning original quantity.")
             return float(quantity_dec) # Return original if step size is zero

        # Calculate the precision (number of decimal places)
        precision = get_step_size_precision(step_size_str)
        
        # Create the quantizer string, e.g., '0.001' for precision 3
        quantizer_str = '1e-' + str(precision) if precision > 0 else '1'
        quantizer = Decimal(quantizer_str)

        # Round the quantity DOWN to the specified precision
        formatted_quantity = quantity_dec.quantize(quantizer, rounding=ROUND_DOWN)

        logger.debug(f"Formatted quantity {quantity} with stepSize {step_size_str} (precision {precision}) to {formatted_quantity}")
        return float(formatted_quantity)

    except Exception as e:
        logger.error(f"Error formatting quantity {quantity} with step size {step_size_str}: {e}. Returning original quantity.")
        # Fallback to original quantity or handle error appropriately
        return float(quantity) # Return original float quantity on error