"""
Helper methods
"""

from typing import List
from math import gcd, sqrt

def divisors(number: int) -> List[int]:
    """Returns a list of all divisors of the input"""
    divs = [1]
    for candidate in range(2,int(sqrt(number))+1):
        if number%candidate == 0:
            divs.extend([candidate,number//candidate])
    divs.extend([number])
    return list(set(divs))

def lcm(number1: int, number2: int) -> int:
    """Compute the least common multiple of two numbers"""
    return number1*number2//gcd(number1, number2)

def convexify(nonconvex: List[int]) -> List[int]:
    """Transforms a list to be nondecreasing by replacing each element by the running maximum"""
    if len(nonconvex) == 0:
        return []
    running_maximum = nonconvex[0]
    return [running_maximum := max(running_maximum, item) for item in nonconvex]
