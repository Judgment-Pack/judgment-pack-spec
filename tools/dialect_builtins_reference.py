#!/usr/bin/env python3
"""Expected values for format 4.0.0's `distance` built-in (spec/dialect.md §2.2.5), by another method.

The companion fixes `distance` as one exact integer algorithm: a haversine in fixed point at scale
10**30, an arcsine by bisection, rounded down to a millimetre. This script does not run that
algorithm to produce a value. It computes the great-circle distance on the same sphere with another
formula, the arctangent form of the central angle, in decimal arithmetic at 90 significant digits,
with its own series for the sine, the cosine, the arctangent and pi. The hand-written vectors take
their expected millimetres from it, at inputs whose distance lies far from a whole millimetre.

    python3 tools/dialect_builtins_reference.py distance LAT1 LON1 LAT2 LON2
        prints the reference distance in millimetres, to twelve decimal places, and its floor.

    python3 tools/dialect_builtins_reference.py sweep [COUNT]
        compares the reference reader's algorithm (tools/dialect_verify.py), before its final
        rounding, with this reference over fixed edge cases and COUNT pseudo-random pairs (default
        2000), and prints the largest difference in millimetres. It exits 1 when a difference
        reaches one micrometre, the bound the companion states for the sweep.

Neither mode shows that the bound holds for every input: the sweep measures the inputs it tries.
"""

from __future__ import annotations

import random
import sys
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

PRECISION = 90
RADIUS_MM = Decimal(6371008800)
EPSILON = Decimal(10) ** -(PRECISION + 5)


def _pi() -> Decimal:
    # Machin's formula: pi = 16 atan(1/5) - 4 atan(1/239)
    return 16 * _atan_series(Decimal(1) / 5) - 4 * _atan_series(Decimal(1) / 239)


def _atan_series(x: Decimal) -> Decimal:
    total, power, k, square = Decimal(0), x, 0, x * x
    while True:
        term = power / (2 * k + 1)
        if abs(term) < EPSILON:
            return total
        total += -term if k % 2 else term
        power *= square
        k += 1


def _atan(x: Decimal, pi: Decimal) -> Decimal:
    if x < 0:
        return -_atan(-x, pi)
    if x > 1:
        return pi / 2 - _atan(1 / x, pi)
    # twice halve the argument: atan(x) = 2 atan(x / (1 + sqrt(1 + x^2)))
    for _ in range(2):
        x = x / (1 + (1 + x * x).sqrt())
    return 4 * _atan_series(x)


def _atan2(y: Decimal, x: Decimal, pi: Decimal) -> Decimal:
    if x > 0:
        return _atan(y / x, pi)
    if x < 0:
        return _atan(y / x, pi) + (pi if y >= 0 else -pi)
    return pi / 2 if y > 0 else (-pi / 2 if y < 0 else Decimal(0))


def _sin(x: Decimal) -> Decimal:
    total, term, k, square = Decimal(0), x, 0, x * x
    while abs(term) >= EPSILON:
        total += term
        k += 1
        term = -term * square / ((2 * k) * (2 * k + 1))
    return total


def _cos(x: Decimal) -> Decimal:
    total, term, k, square = Decimal(0), Decimal(1), 0, x * x
    while abs(term) >= EPSILON:
        total += term
        k += 1
        term = -term * square / ((2 * k - 1) * (2 * k))
    return total


def reference_mm(latitude_1: str, longitude_1: str, latitude_2: str, longitude_2: str) -> Decimal:
    """The great-circle distance on the sphere of radius 6371008800 mm, by the arctangent form."""
    with localcontext() as context:
        context.prec = PRECISION + 10
        pi = _pi()
        radians = pi / 180
        phi_1, phi_2 = Decimal(latitude_1) * radians, Decimal(latitude_2) * radians
        delta = (Decimal(longitude_2) - Decimal(longitude_1)) * radians
        sin_1, cos_1, sin_2, cos_2 = _sin(phi_1), _cos(phi_1), _sin(phi_2), _cos(phi_2)
        sin_d, cos_d = _sin(delta), _cos(delta)
        across = cos_2 * sin_d
        along = cos_1 * sin_2 - sin_1 * cos_2 * cos_d
        numerator = (across * across + along * along).sqrt()
        denominator = sin_1 * sin_2 + cos_1 * cos_2 * cos_d
        return RADIUS_MM * _atan2(numerator, denominator, pi)


def _reader() -> object:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dialect_verify  # noqa: E402

    return dialect_verify


def algorithm_unrounded_mm(reader: object, coordinates: tuple[str, str, str, str]) -> Fraction:
    """The reader's algorithm (§2.2.5) before its final rounding down: 2 R theta / SCALE, exactly."""
    theta = reader.central_angle_scaled(*(Fraction(c) for c in coordinates))  # type: ignore[attr-defined]
    return Fraction(2 * reader.RADIUS_MM * theta, reader.SCALE)  # type: ignore[attr-defined]


EDGES = [
    ("0", "0", "0", "0"),
    ("0", "0", "0", "180"),
    ("0", "0", "0", "-180"),
    ("90", "0", "-90", "0"),
    ("45", "10", "-45", "-170"),
    ("51.5007", "-0.1246", "-51.5007", "179.8754"),
    ("0", "0", "0", "179.999999999"),
    ("0", "0", "0.000000001", "0"),
    ("0", "0", "0", "0.000000001"),
    ("90", "0", "90", "123.4"),
    ("-90", "45", "89.999999999", "45"),
    ("12.5", "179.5", "-12.5", "-179.5"),
    ("40.7128", "-74.0060", "51.5074", "-0.1278"),
    ("-33.8688", "151.2093", "35.6762", "139.6503"),
]


def _random_coordinates(generator: random.Random) -> tuple[str, str, str, str]:
    def number(bound: int) -> str:
        nanodegrees = generator.randint(-bound * 10**9, bound * 10**9)
        sign = "-" if nanodegrees < 0 else ""
        whole, fraction = divmod(abs(nanodegrees), 10**9)
        return f"{sign}{whole}.{fraction:09d}"

    return number(90), number(180), number(90), number(180)


def sweep(count: int) -> int:
    reader = _reader()
    generator = random.Random(316)
    pairs = list(EDGES) + [_random_coordinates(generator) for _ in range(count)]
    worst, where = Fraction(0), pairs[0]
    for coordinates in pairs:
        expected = Fraction(reference_mm(*coordinates))
        difference = abs(algorithm_unrounded_mm(reader, coordinates) - expected)
        if difference > worst:
            worst, where = difference, coordinates
    print(f"pairs {len(pairs)}; largest difference {float(worst):.3e} mm at {' '.join(where)}")
    return 0 if worst < Fraction(1, 1000) else 1


def main(argv: list[str]) -> int:
    if len(argv) == 5 and argv[0] == "distance":
        value = reference_mm(*argv[1:])
        print(f"{value:.12f} mm; floor {int(value // 1)}")
        return 0
    if argv and argv[0] == "sweep" and len(argv) <= 2:
        return sweep(int(argv[1]) if len(argv) == 2 else 2000)
    print(__doc__, file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
