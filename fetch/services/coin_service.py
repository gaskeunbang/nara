from decimal import Decimal, getcontext
from typing import Union

# Tingkatkan presisi untuk pembagian big integer -> decimal
getcontext().prec = 50

Numeric = Union[int, str, Decimal]


def _to_decimal(value: Numeric) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        # string dapat berupa integer besar atau desimal
        return Decimal(value)
    raise TypeError(f"Unsupported type for numeric conversion: {type(value)}")


def _format_decimal(value: Decimal, max_fraction_digits: int) -> str:
    # Batasi ke jumlah digit desimal maksimum yang relevan (tanpa notasi ilmiah)
    quant = Decimal(1).scaleb(-max_fraction_digits)  # 10^-max_fraction_digits
    q = value.quantize(quant)
    # Hilangkan trailing zeros dan titik jika tidak perlu
    normalized = q.normalize()
    if normalized == 0:
        return "0"
    as_str = format(normalized, 'f')
    if '.' in as_str:
        as_str = as_str.rstrip('0').rstrip('.')
    return as_str


def wei_to_eth(wei: Numeric) -> str:
    d = _to_decimal(wei) / Decimal(10) ** 18
    return _format_decimal(d, 18)


def satoshi_to_btc(satoshi: Numeric) -> str:
    d = _to_decimal(satoshi) / Decimal(10) ** 8
    return _format_decimal(d, 8)


def lamports_to_sol(lamports: Numeric) -> str:
    d = _to_decimal(lamports) / Decimal(10) ** 9
    return _format_decimal(d, 9)


def to_amount(coin_symbol: str, smallest_unit_value: Numeric) -> str:
    """Konversi nilai dari satuan terkecil ke amount manusiawi.

    - BTC: satoshi -> BTC
    - ETH: wei -> ETH
    - SOL: lamports -> SOL
    """
    symbol = (coin_symbol or "").strip().upper()
    if symbol == "BTC":
        return satoshi_to_btc(smallest_unit_value)
    if symbol == "ETH":
        return wei_to_eth(smallest_unit_value)
    if symbol == "SOL":
        return lamports_to_sol(smallest_unit_value)
    raise ValueError(f"Unsupported coin symbol: {coin_symbol}")


# ================= Reverse conversion: amount -> smallest unit =================

def eth_to_wei(amount: Numeric) -> int:
    d = _to_decimal(amount) * (Decimal(10) ** 18)
    # pastikan integer (trunc toward zero)
    return int(d.to_integral_value(rounding=getcontext().rounding))


def btc_to_satoshi(amount: Numeric) -> int:
    d = _to_decimal(amount) * (Decimal(10) ** 8)
    return int(d.to_integral_value(rounding=getcontext().rounding))


def sol_to_lamports(amount: Numeric) -> int:
    d = _to_decimal(amount) * (Decimal(10) ** 9)
    return int(d.to_integral_value(rounding=getcontext().rounding))


def to_smallest(coin_symbol: str, amount: Numeric) -> int:
    """Konversi amount manusiawi ke satuan terkecil (integer).

    - BTC: BTC -> satoshi
    - ETH: ETH -> wei
    - SOL: SOL -> lamports
    """
    symbol = (coin_symbol or "").strip().upper()
    if symbol == "BTC":
        return btc_to_satoshi(amount)
    if symbol == "ETH":
        return eth_to_wei(amount)
    if symbol == "SOL":
        return sol_to_lamports(amount)
    raise ValueError(f"Unsupported coin symbol: {coin_symbol}")
