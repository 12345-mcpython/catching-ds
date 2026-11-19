import json
import os
import sys
import tempfile
from urllib.parse import urlsplit

FISH_PATH = "fish.json"

def parse_mid(raw: str) -> int:
    s = raw.strip()
    if not s:
        raise ValueError("Empty input")

    if s.startswith(("http://", "https://")):
        path = urlsplit(s).path.rstrip("/")
        s = path.rsplit("/", 1)[-1] if path else ""

    try:
        return int(s)
    except ValueError:
        raise ValueError(f"invalid mid: {s!r}")

def load_list(path: str = FISH_PATH) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_atomic(data: list, path: str = FISH_PATH) -> None:
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

def read_input_lines() -> list:
    if not sys.stdin.isatty():
        return [ln for ln in sys.stdin.read().splitlines() if ln.strip()]

    print("Enter url: ")
    lines = []
    while True:
        try:
            line = input("> ")
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    return lines


def main() -> None:
    lines = read_input_lines()
    if not lines:
        return

    fish = load_list()
    existing = set(fish)

    added = []          # [(raw, mid)]
    skipped = []        # [(raw, mid, reason)]
    failed = []         # [(raw, reason)]
    seen_in_batch = set()

    for raw in lines:
        try:
            mid = parse_mid(raw)
        except ValueError as e:
            failed.append((raw, str(e)))
            continue

        if mid in existing:
            skipped.append((raw, mid, "exist duplicate"))
        elif mid in seen_in_batch:
            skipped.append((raw, mid, "batch duplicate"))
        else:
            seen_in_batch.add(mid)
            added.append((raw, mid))

    if added:
        fish.extend(mid for _, mid in added)
        save_atomic(fish, FISH_PATH)

    for _, mid in added:
        print(f"[OK]   {mid}")
    for _, mid, reason in skipped:
        print(f"[SKIP] {mid}  ({reason})")
    for raw, reason in failed:
        print(f"[FAIL] {raw}  -> {reason}")

    print(
        f"Add {len(added)} Skip {len(skipped)} Fail {len(failed)}；"
        f"Total {len(fish)}"
    )


if __name__ == "__main__":
    main()