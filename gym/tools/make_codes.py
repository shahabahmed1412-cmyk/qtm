#!/usr/bin/env python3
"""Create Iron Log activation codes.

Writes the new codes to a private CSV (keep it to yourself; never commit it) and
adds their hashes to the app so it accepts them.

    python3 gym/tools/make_codes.py 100
    python3 gym/tools/make_codes.py 50 --out ~/ironlog-codes-batch2.csv

After running, commit and push gym/index.html so the published app knows the new codes.
"""
import argparse, csv, datetime, hashlib, os, re, secrets, sys

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford base32: no I, L, O, U
START, END = "/*LICENSES-START*/", "/*LICENSES-END*/"


def code_hash(code12):
    # Must match codeHash() in the app.
    return hashlib.sha256(("ironlog:" + code12).encode()).hexdigest()[:24]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("count", type=int, help="how many codes to create")
    ap.add_argument("--out", help="CSV file for the codes (default: your home folder)")
    ap.add_argument("--app", nargs="+", default=[os.path.join(here, "..", "index.html")],
                    help="app file(s) whose license list gets the new hashes")
    a = ap.parse_args()

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = os.path.expanduser(a.out or f"~/ironlog-codes-{stamp}.csv")
    repo = os.path.abspath(os.path.join(here, "..", ".."))
    if os.path.abspath(out).startswith(repo + os.sep):
        sys.exit("Refusing to write codes inside the repository; the repo is public. Use --out with a path outside it.")

    codes = []
    for _ in range(a.count):
        raw = "".join(secrets.choice(ALPHABET) for _ in range(12))
        codes.append(raw)

    for path in a.app:
        src = open(path, encoding="utf-8").read()
        m = re.search(re.escape(START) + r"(.*?)" + re.escape(END), src, re.S)
        if not m:
            sys.exit(f"License markers not found in {path}")
        existing = re.findall(r'"([0-9a-f]{24})"', m.group(1))
        merged = existing + [code_hash(c) for c in codes]
        body = "\n" + "\n".join(",".join(f'"{h}"' for h in merged[i:i + 6]) + "," for i in range(0, len(merged), 6)) + "\n"
        src = src[:m.start(1)] + body + src[m.end(1):]
        open(path, "w", encoding="utf-8").write(src)
        print(f"{path}: {len(existing)} existing + {len(codes)} new = {len(merged)} codes")

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "created", "sold_to", "notes"])
        for c in codes:
            w.writerow([f"IRON-{c[:4]}-{c[4:8]}-{c[8:]}", stamp, "", ""])
    print(f"Codes written to {out} — keep this file private.")


if __name__ == "__main__":
    main()
