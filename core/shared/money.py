from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.domain.exceptions import DomainError


class CurrencyMismatchError(DomainError, ValueError):
    def __init__(self, left: str, right: str) -> None:
        super().__init__(f"Currency mismatch: {left} vs {right}")
        self.left = left
        self.right = right


def _is_valid_currency(code: str) -> bool:
    return len(code) == 3 and code.isalpha() and code == code.upper()


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError(f"Money.amount must be a Decimal, got {type(self.amount).__name__}")
        if not _is_valid_currency(self.currency):
            raise ValueError(f"Invalid ISO 4217 currency code: {self.currency!r}")

    def _check_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(self.currency, other.currency)

    def __add__(self, other: "Money") -> "Money":
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __lt__(self, other: "Money") -> bool:
        self._check_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._check_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        self._check_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        self._check_currency(other)
        return self.amount >= other.amount
