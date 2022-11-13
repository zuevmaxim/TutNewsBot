def pretty_int(input) -> str:
    n = int(input)
    if n > 10 ** 6:
        return str(n // 10 ** 6) + "M"
    if n > 1000:
        return str(n // 1000) + "K"
    return str(n)


def extract_chanel_name(name):
    name = name.strip()
    prefix = "https://t.me/"
    if name[:len(prefix)] == prefix:
        name = name[len(prefix):]
    return name
