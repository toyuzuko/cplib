#!/usr/bin/env python3

def yneos(result: bool) -> str:
    """
    Convert a boolean into ``'Yes'`` or ``'No'``.

    Args:
        result: Boolean value to convert.

    Returns:
        ``'Yes'`` when ``result`` is true, otherwise ``'No'``.

    Examples:
        >>> yneos(True)
        'Yes'
        >>> yneos(False)
        'No'

    Time Complexity:
        O(1)

    Space Complexity:
        O(1) auxiliary space
    """
    return 'Yes' if result else 'No'
