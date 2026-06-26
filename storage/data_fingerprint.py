import hashlib
import json

def json_hash(data) -> str:
    content = json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return hashlib.md5(
        content.encode("utf-8")
    ).hexdigest()