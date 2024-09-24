import asyncio


def extract_chanel_name(name: str) -> str:
    name = name.strip()
    prefix = "https://t.me/"
    if name[:len(prefix)] == prefix:
        name = name[len(prefix):]
    if name.startswith("@"):
        name = name[1:]
    return name


def utf16len(s):
    # Encode the string into UTF-16 (result includes BOM)
    # Each UTF-16 symbol is represented by 2 bytes
    # We subtract 2 to get rid of Byte Order Mark
    return len(s.encode('utf-16')) // 2 - 1


async def wait_unless_triggered(timeout: int, event: asyncio.Event) -> bool:
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
        event.clear()
        return True
    except asyncio.TimeoutError:
        return False
