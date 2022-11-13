def pretty_int(input) -> str:
    n = int(input)
    if n > 10 ** 6:
        return str(n // 10 ** 6) + "M"
    if n > 1000:
        return str(n // 1000) + "K"
    return str(n)
