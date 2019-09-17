from decimal import Decimal
from typing import Union

ATOMIC_UNIT = int(1e12)

def decimal_to_atomic(amount: Union[Decimal, str]) -> int:
    """
    Convert a Decimal monero amount into an atomic (piconero) integer amount

        >>> decimal_to_atomic(Decimal('10'))
        10000000000000
    
    """
    return int(Decimal(amount) * Decimal(ATOMIC_UNIT))

def atomic_to_decimal(amount: int) -> Decimal:
    """
    Convert an integer atomic monero amount into a normal Decimal amount
    
        >>> atomic_to_decimal(10000000000000)
        Decimal('10')
    
    """
    return Decimal(amount) / Decimal(ATOMIC_UNIT)

