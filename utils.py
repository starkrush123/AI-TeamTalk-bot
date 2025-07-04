
import time

def format_uptime(seconds: float) -> str:
    if seconds < 0: return "N/A"
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    parts = []
    if days >= 1: parts.append(f"{int(days)}d")
    if hours >= 1: parts.append(f"{int(hours)}h")
    if mins >= 1: parts.append(f"{int(mins)}m")
    parts.append(f"{int(secs)}s")
    return " ".join(parts) if parts else "0s"
