# utils\logger.py
def short_log(context, *args):
    if context.get("debug"):
        print(*args)


def log(context, *args, tag=None, level="info"):
    if not context.get("debug") and level == "debug":
        return

    prefix = f"[{tag}]" if tag else ""
    print(prefix, *args)