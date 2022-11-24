def extract_chanel_name(name):
    name = name.strip()
    prefix = "https://t.me/"
    if name[:len(prefix)] == prefix:
        name = name[len(prefix):]
    if name.startswith("@"):
        name = name[1:]
    return name
