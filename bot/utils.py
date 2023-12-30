import asyncio


def extract_chanel_name(name: str) -> str:
    name = name.strip()
    prefix = "https://t.me/"
    if name[:len(prefix)] == prefix:
        name = name[len(prefix):]
    if name.startswith("@"):
        name = name[1:]
    return name


async def wait_unless_triggered(timeout: int, event: asyncio.Event) -> bool:
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
        event.clear()
        return True
    except asyncio.TimeoutError:
        return False
