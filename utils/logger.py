# utils\logger.py
def log(context, *args):
    if context.get("debug"):
        print(*args)