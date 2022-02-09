"""
Copyright 2009-2015 Olivier Belanger - modifications by Hans-Jörg Bibiko 2022
"""
import math


p_mathlog10 = math.log10
p_mathsin = math.sin
p_mathcos = math.cos
p_mathatan = math.atan
p_math_pi = math.pi
p_math_pi_2 = p_math_pi / 2


def interpFloat(t, v1, v2):
    "interpolator for a single value; interprets t in [0-1] between v1 and v2"
    return (v2 - v1) * t + v1


def tFromValue(value, v1, v2):
    "returns a t (in range 0-1) given a value in the range v1 to v2"
    return (value - v1) / (v2 - v1)


def clamp(v, vmin, vmax):
    "clamps a value within a range"
    return vmin if v < vmin else vmax if v > vmax else v


def toLog(t, v1, v2):
    return p_mathlog10(t/v1) / p_mathlog10(v2/v1)


def toExp(t, v1, v2):
    v1log = p_mathlog10(v1)
    return 10**(t * (p_mathlog10(v2) - v1log) + v1log)


POWOFTWO = {
    2: 1,
    4: 2,
    8: 3,
    16: 4,
    32: 5,
    64: 6,
    128: 7,
    256: 8,
    512: 9,
    1024: 10,
    2048: 11,
    4096: 12,
    8192: 13,
    16384: 14,
    32768: 15,
    65536: 16,
}


def powOfTwo(x):
    "Return 2 raised to the power of x."
    return 2 ** x


def powOfTwoToInt(x):
    "Return the exponent of 2 correponding to the value x."
    return POWOFTWO[x]
