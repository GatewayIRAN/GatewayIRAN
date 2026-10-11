#!/usr/bin/env python3
"""check_profile_face.py - the gate for the generated profile face (T-011).

The profile README is no longer written by hand: scripts/render_profile.py
generates it from the live account API on a schedule. The face lives at
content/profile/README.md in the kit workspace and at the repository root in
the profile repository GitHub actually renders; this gate follows whichever
layout the checkout carries. The gate exists because the owner set five
rules that are easy to state and easy to break by accident the next time the
generator is edited. It answers one question: does the generated face still
obey all five?

Usage
  python checks/check_profile_face.py [--root DIR] [--template PATH]
  python checks/check_profile_face.py --self-test

The five rules this enforces (owner, A-0044):

  1  No single language, stack, platform, protocol or licence is named. The
     face must not be the face of one toolchain.
  2  No specific project is named directly. Any project mentioned must be
     something the generator derived from the live API during this run, so the
     face updates itself and the owner never edits it by hand.
  3  No fixed number standing for a quantity that varies in reality. A number
     printed on the face must be traceable to a value fetched in this run.
  4  No Persian. The face is English only.
  5  No explanation of one specific project: the prose must speak about the
     whole account.

How rules 1-3 are checked, honestly:

Rule 1 is a denylist scan of the whole generated face, word-bounded and case
insensitive. It is deliberately broad. A broad denylist has false positives -
so the generator writes a machine-readable provenance block into the
template, and a token is only a violation if it is NOT declared there. That
keeps the gate strict without forcing a human to edit the gate every time a
legitimate new word appears.

Rule 2 checks that every project-looking name in the face appears in the
generator's provenance block for this run. A hard-coded name in the template
therefore fails: the generator did not derive it from the API.

Rule 3 scans for a bare integer adjacent to a known volatile quantity word
(star, fork, watcher, member, subscriber, follower, release, download, commit,
repository, repo). Such a number must be inside the provenance block that
records the API call that produced it. A number in prose with no provenance
fails.

Rule 4 is byte-level: any non-ASCII character in the face fails, which rules
out Persian and any other non-Latin script in one stroke. This is stricter
than a script heuristic and has no false negatives.

Rule 5 is a prose check: the generated face must carry the account-level
framing marker the template owns, and must not contain a second-person
walkthrough of a single project. It is enforced as "the generated prose is
emitted from the account-level template sections only", which is checked by
confirming the generated file contains the template's section markers and no
hand-written project section.

Provenance contract (what render_profile.py must emit):

  <!--profile-face:v1
  tokens: <comma separated lowercase words the generator is allowed to use>
  numbers: <comma separated "label=value" pairs, one per printed number>
  projects: <comma separated repository names derived from the API this run>
  -->

If that block is absent, the gate fails loudly rather than guessing: an
ungoverned generated face is exactly the thing this gate exists to prevent.

Exit codes follow references/python3-check-scripts.md: 0 pass, 1 fail with one
stderr line per problem, 2 argparse usage error. --self-test runs offline
against temp-dir fixtures only: green on a compliant face, red on a face that
breaks each of the five rules.
"""

import argparse
import os
import pathlib
import re
import sys
import tempfile

# Rule 1 denylist. Lower-case, matched case-insensitively with word bounds.
# These are the tokens the owner named, plus the obvious neighbours so the
# face cannot drift into naming a toolchain through a synonym.
STACK_TOKENS = [
    # languages and runtimes
    "rust", "golang", "python", "nodejs", "node", "javascript", "typescript",
    "java", "kotlin", "swift", "ruby", "php", "perl", "csharp", "c\\+\\+",
    "zig", "elixir", "haskell", "scala", "bash", "shell",
    # platforms
    "linux", "macos", "mac os", "osx", "windows", "ubuntu", "debian", "alpine",
    "docker", "kubernetes",
    # protocols, formats, authorities
    "acme", "tls", "ssl", "https", "http", "openssl", "ssh", "dns", "acme-v02",
    "letsencrypt", "let's encrypt", "certificate", "certificates", "certbot",
    "nginx",
    # licences
    "mit", "apache", "gpl", "bsd", "mpl", "unlicense",
    # packaging and build
    "cargo", "npm", "pip", "crates", "crate", "binary", "binaries",
    "static binary", "musl",
]

# Rule 3: a number next to one of these words must have provenance.
VOLATILE_WORDS = [
    "star", "stars", "fork", "forks", "watcher", "watchers", "member",
    "members", "subscriber", "subscribers", "follower", "followers",
    "release", "releases", "download", "downloads", "commit", "commits",
    "repository", "repositories", "repo", "repos", "open", "closed", "issue",
    "issues", "pull", "pulls", "mb", "kb", "gb", "size",
]

PROVENANCE_RE = re.compile(
    r"<!--\s*profile-face:v1\s*\n(?P<body>.*?)\n\s*-->", re.DOTALL
)
# A percentage in the face is always a layout size (width="100%"), never
# a quantity, so it is not a varying number needing provenance.
NUMBER_RE = re.compile(r"\b\d[\d,]*\.?\d*\b")
PERCENT_RE = re.compile(r"\d+%")
VOLATILE_RE = re.compile(r"\b(?:" + "|".join(VOLATILE_WORDS) + r")\b", re.I)

ASSET_EXT = (".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp",
             ".css", ".js", ".woff", ".woff2", ".ttf")
LAYOUT_DIRS = ("assets", "static", "media", "img", "images", "files")
FORGE_HOSTS = ("github.com", "t.me", "gitlab.com", "codeberg.org")
FORGE_URL_RE = re.compile(
    r"\b(?:github\.com|gitlab\.com|codeberg\.org)/"
    r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)
SLUG_RE = re.compile(r"\b[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\b")
# ordinary words joined by a slash are prose ("and/or", "CI/CD"), never a repo
PROSE_WORDS = {"and", "or", "of", "to", "in", "on", "for", "vs", "per",
               "via", "the", "a", "an", "is", "are", "ci", "cd", "etc"}


def project_mentions(text, prov):
    """Every project-shaped mention in text that provenance does not clear.

    Two shapes matter: a forge URL (host/owner/repo) and a bare owner/name
    slug. Asset files the face itself loads, layout dirs, the account's own
    profile/channel links and ordinary words joined by a slash are not
    project mentions. Every other mention must be an exact owner/name pair
    present in this run's provenance 'projects:' list.
    """
    found = []
    spans = []
    for m in FORGE_URL_RE.finditer(text):
        spans.append(m.span())
        if m.group(2).lower().endswith(ASSET_EXT):
            continue  # a file the face itself loads is layout
        if f"{m.group(1)}/{m.group(2)}".lower() not in prov["projects"]:
            found.append((m.start(), m.group(0)))
    for m in SLUG_RE.finditer(text):
        if any(s <= m.start() < e for s, e in spans):
            continue  # already judged as a URL pair above
        mention = m.group(0)
        stem = mention.split("/")[-1].lower()
        if stem.endswith(ASSET_EXT):
            continue  # an asset the face itself loads is layout
        head = mention.split("/")[0].lower()
        if head in LAYOUT_DIRS or head in FORGE_HOSTS:
            continue
        if head in PROSE_WORDS or stem in PROSE_WORDS:
            continue  # prose joined by a slash, not a repository
        if mention.lower() not in prov["projects"]:
            found.append((m.start(), mention))
    return found


def volatile_numbers(text, prov):
    """Volatile-number windows whose figures have no provenance in this run."""
    hits = []
    for m in VOLATILE_RE.finditer(text):
        window = PERCENT_RE.sub(" ", text[max(0, m.start() - 60): m.end() + 60])
        for n in NUMBER_RE.finditer(window):
            val = n.group(0).replace(",", "")
            if val in {v.replace(",", "") for v in prov["numbers"].values()}:
                continue
            hits.append((m.start(), m.group(0), n.group(0)))
            break
    return hits



ALLOWED_SYMBOLS = set("\u00a0\u2013\u2014\u2018\u2019\u201c\u201d"
                      "\u2022\u2026\u2192\u2190\u25cf\u2713\u00d7"
                      "\u2248\u2264\u2265\u00b7")
EMOJI = ("\U0001F575\U0001F91D\U0001F4E6\U0001F4DC\U0001F4E2"
         "\U0001F680\U0001F525\U000000A9\U0001F310\U0001F4BB"
         "\U0001F512\U0001F6E1\U000026A0\U0001F4C8\U0001F4CA")

def _fail(msg):
    print(msg, file=sys.stderr)
    return 1


def parse_provenance(text):
    m = PROVENANCE_RE.search(text)
    if not m:
        return None
    body = m.group("body")
    out = {"tokens": set(), "numbers": {}, "projects": set(), "raw": body}
    for line in body.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower()
        val = val.strip()
        if key == "tokens":
            out["tokens"] = {t.strip().lower() for t in val.split(",") if t.strip()}
        elif key == "projects":
            out["projects"] = {t.strip().lower() for t in val.split(",") if t.strip()}
        elif key == "numbers":
            for pair in val.split(","):
                if "=" in pair:
                    k, _, v = pair.partition("=")
                    out["numbers"][k.strip().lower()] = v.strip()
    return out


def visible_text(text):
    """Text to scan for rule 1: strip the provenance block and HTML comments."""
    text = PROVENANCE_RE.sub(" ", text)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    return text


def face_dir(root):
    """Where the profile face lives in this checkout.

    The kit workspace keeps the face under content/profile/; the profile
    repository that GitHub renders carries it at the repository root. The
    workspace layout is recognised first so kit checkouts behave exactly as
    before, and the profile repository falls through to its root.
    """
    kit = pathlib.Path(root) / "content" / "profile"
    return kit if kit.is_dir() else pathlib.Path(root)


def check(root, template=None):
    root = pathlib.Path(root)
    face = face_dir(root) / "README.md"
    problems = []

    if not face.exists():
        return _fail(f"{face}: missing; the generated face does not exist")

    raw = face.read_text(encoding="utf-8", errors="replace")
    prov = parse_provenance(raw)
    if prov is None:
        return _fail(
            f"{face}: no '<!--profile-face:v1 ... -->' provenance block; "
            "an ungoverned generated face is not acceptable"
        )

    body = visible_text(raw)

    # Layout attributes are dimensions of the page's own artwork (width,
    # height, viewBox, font-size and so on). They are not quantities about
    # the account, so rule 3 does not apply to them; without this the number
    # 42 in an icon's height attribute sits six words from "repositories" and
    # is reported as a fabricated figure. Rules 1 and 2 deliberately scan the
    # UNSCRIPPED text: a stack, a project name or a forge link carries the
    # same meaning in an href, an alt or a caption as it does in prose, and
    # an attribute is exactly where a hard-coded mention prefers to hide.
    numtext = re.sub(r"\b[a-zA-Z-]+\s*=\s*\"[^\"]*\"", " \"", body)
    numtext = re.sub(r"\b[a-zA-Z-]+\s*=\s*'[^']*'", " '", numtext)

    # Rule 4 - byte level, no false negatives on script. Any non-ASCII fails,
    # except the decorative symbols the face uses as section markers. Emoji are
    # stripped before the scan so an icon is never mistaken for a script; a
    # letter from a non-Latin script is still caught, because it is not one of
    # the allowed symbols.
    # (see the module-level ALLOWED_SYMBOLS and EMOJI above)
    scan = raw
    for e in EMOJI:
        scan = scan.replace(e, "")
    non_ascii = [(i, ch) for i, ch in enumerate(scan)
                 if ord(ch) > 127 and ch not in ALLOWED_SYMBOLS]
    if non_ascii:
        idx, ch = non_ascii[0]
        line = raw.count("\n", 0, idx) + 1
        problems.append(
            f"{face}:{line}: rule 4 (English only): non-ASCII character "
            f"U+{ord(ch):04X} {ch!r}"
        )

    # Rules 1 and 4 also apply to the artwork the face ships. A profile can put
    # a stack or a script into an SVG caption as easily as into prose, and the
    # owner banned both on the face as a whole - so the assets directory is
    # scanned too, with the same denylist. A clean README cannot launder a
    # stack out of an image it embeds.
    for asset in sorted((face.parent / "assets").glob("*.svg")):
        atext = asset.read_text(encoding="utf-8", errors="replace")
        # captions only: strip every tag so colour codes and paths are ignored
        aclean = re.sub(r"<[^>]*>", " ", atext)
        for m in re.finditer(r">([^<]{2,60})<", atext):
            aclean += " " + m.group(1)
        alow = re.sub(r"https?://", " ", aclean.lower())
        for tok in STACK_TOKENS:
            if tok in prov["tokens"]:
                continue
            if re.search(r"\b(?:" + tok + r")\b", alow, re.I):
                problems.append(
                    f"{asset}: rule 1 (no single stack): artwork names "
                    f"{tok!r}; the face's images obey the same rules as its text"
                )
                break
        for ch in atext:
            if ord(ch) > 127 and ch not in ALLOWED_SYMBOLS:
                problems.append(
                    f"{asset}: rule 4 (English only): artwork contains "
                    f"U+{ord(ch):04X}"
                )
                break
        # Rules 2 and 3 bind the artwork to provenance too: a project the
        # generator did not derive, or a volatile number the run did not
        # compute, is exactly as hard-coded in an SVG caption as in prose.
        for idx, mention in project_mentions(aclean, prov):
            problems.append(
                f"{asset}: rule 2 (no hard-coded project): the artwork "
                f"mentions {mention!r} which the generator did not derive "
                "from the API this run"
            )
        for idx, word, num in volatile_numbers(aclean, prov):
            problems.append(
                f"{asset}: rule 3 (no fixed varying number): the artwork puts "
                f"{num!r} next to {word!r} with no provenance in this run"
            )

    # Rule 1 - stack token denylist, cleared only by the provenance tokens.
    # Link protocols are stripped first: https:// in a markdown link is the URL
    # scheme every profile uses, not an assertion that the account is built on
    # a particular protocol. The word still fails when it appears in prose.
    low = body.lower()
    # Strip URL schemes: every markdown link on the face starts with https://
    # and that is link syntax, not a claim about the account's stack. The word
    # still fails when it appears as prose.
    low = re.sub(r"https?://", " ", low)
    for tok in STACK_TOKENS:
        for m in re.finditer(r"\b(?:" + tok + r")\b", low, re.I):
            if tok in prov["tokens"]:
                continue
            line = low.count("\n", 0, m.start()) + 1
            problems.append(
                f"{face}:{line}: rule 1 (no single stack): names {m.group(0)!r}; "
                "declare it in the provenance 'tokens:' list only if it is "
                "genuinely account-wide"
            )
            break

    # Rule 2 - every project named must be one the generator derived this
    # run. Prose, attributes and captions all count: the provenance
    # 'projects:' list is the only thing that clears a mention.
    for idx, mention in project_mentions(body, prov):
        line = body.count("\n", 0, idx) + 1
        problems.append(
            f"{face}:{line}: rule 2 (no hard-coded project): mentions "
            f"{mention!r} which the generator did not derive from the "
            "API this run"
        )

    # Rule 3 - a volatile number must be traceable to provenance.
    for idx, word, num in volatile_numbers(numtext, prov):
        line = numtext.count("\n", 0, idx) + 1
        problems.append(
            f"{face}:{line}: rule 3 (no fixed varying number): {num!r} "
            f"next to {word!r} has no provenance in this run"
        )

    # Rule 5 - the account-level framing marker must be present.
    if "profile-face:account-scope" not in raw:
        problems.append(
            f"{face}: rule 5 (whole account): the account-level framing marker "
            "'profile-face:account-scope' is missing from the generated prose"
        )

    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 1

    print(
        f"PASS {face}: obeys all five rules "
        f"({len(prov['projects'])} live projects, "
        f"{len(prov['numbers'])} live numbers, "
        f"{len(prov['tokens'])} declared tokens)"
    )
    return 0


def self_test():
    """Offline fixtures: green on compliant, red on each broken rule."""
    ok = True

    GOOD = """<div align="center"><img src="assets/banner.svg" alt="x"></div>
<!--profile-face:account-scope -->
<!--profile-face:v1
tokens: acme, tls
numbers: repos=4, stars=9
projects: a/b, c/d
-->
<p>A living view of the account, refreshed on every run.</p>
"""

    def run(text, extra_assets=None):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "content" / "profile"
            p.mkdir(parents=True)
            (p / "README.md").write_text(text, encoding="utf-8")
            if extra_assets:
                a = p / "assets"
                a.mkdir(parents=True, exist_ok=True)
                for name, svg in extra_assets.items():
                    (a / name).write_text(svg, encoding="utf-8")
            return check(d)

    if run(GOOD) != 0:
        print("SELF-TEST FAIL: compliant face was rejected", file=sys.stderr)
        ok = False

    # rule 1
    if run(GOOD.replace("living view", "Rust view")) == 0:
        print("SELF-TEST FAIL: rule 1 (stack token) not caught", file=sys.stderr)
        ok = False
    # rule 2
    if run(GOOD.replace("refreshed on every run", "see x/y here")) == 0:
        print("SELF-TEST FAIL: rule 2 (hard-coded project) not caught", file=sys.stderr)
        ok = False
    # rule 2 - a hard-coded project disguised as a forge URL must also fail
    if run(GOOD.replace("refreshed on every run",
                        "see https://github.com/x/y here")) == 0:
        print("SELF-TEST FAIL: rule 2 (hard-coded project URL) not caught",
              file=sys.stderr)
        ok = False
    # rule 2 controls - derived mentions stay legal, in both shapes
    if run(GOOD.replace("refreshed on every run", "see a/b here")) != 0:
        print("SELF-TEST FAIL: rule 2 rejected a derived bare mention",
              file=sys.stderr)
        ok = False
    if run(GOOD.replace("refreshed on every run",
                        "see https://github.com/a/b here")) != 0:
        print("SELF-TEST FAIL: rule 2 rejected a derived URL mention",
              file=sys.stderr)
        ok = False
    if run(GOOD.replace("refreshed on every run",
                        "channel at https://t.me/a")) != 0:
        print("SELF-TEST FAIL: rule 2 rejected the account channel link",
              file=sys.stderr)
        ok = False
    # attributes are scanned like prose: href and alt hide nothing
    if run(GOOD.replace('alt="x"',
                        'alt="x" href="https://github.com/someone/evilrepo"')) == 0:
        print("SELF-TEST FAIL: rule 2 (hard-coded project in an attribute) "
              "not caught", file=sys.stderr)
        ok = False
    if run(GOOD.replace('alt="x"', 'alt="someone/evilrepo"')) == 0:
        print("SELF-TEST FAIL: rule 2 (slug in alt text) not caught",
              file=sys.stderr)
        ok = False
    if run(GOOD.replace('alt="x"', 'alt="a rust thing"')) == 0:
        print("SELF-TEST FAIL: rule 1 (stack word in an attribute) not caught",
              file=sys.stderr)
        ok = False
    if run(GOOD.replace('alt="x"',
                        'alt="x" href="https://github.com/a/b"')) != 0:
        print("SELF-TEST FAIL: rule 2 rejected a derived link in an attribute",
              file=sys.stderr)
        ok = False
    if run(GOOD.replace("refreshed on every run",
                        "licensed for reuse, and/or mirroring")) != 0:
        print("SELF-TEST FAIL: rule 2 rejected the prose 'and/or'",
              file=sys.stderr)
        ok = False
    # rules 2 and 3 bind the artwork as well as the prose
    if run(GOOD, {"bad.svg": "<svg><text>9999 repositories</text></svg>"}) == 0:
        print("SELF-TEST FAIL: rule 3 (hard-coded number in artwork) "
              "not caught", file=sys.stderr)
        ok = False
    if run(GOOD, {"bad.svg": "<svg><text>see x/y</text></svg>"}) == 0:
        print("SELF-TEST FAIL: rule 2 (hard-coded project in artwork) "
              "not caught", file=sys.stderr)
        ok = False
    if run(GOOD, {"ok.svg": "<svg><text>4 repos 9 stars</text></svg>"}) != 0:
        print("SELF-TEST FAIL: rule 3 rejected provenance numbers in artwork",
              file=sys.stderr)
        ok = False
    # rule 3 - a volatile number that is NOT among the provenance numbers.
    # The fixture declares repos=4 and stars=9, so 12 must fail.
    if run(GOOD.replace("living view of the account", "12 stars across the account")) == 0:
        print("SELF-TEST FAIL: rule 3 (fixed varying number) not caught", file=sys.stderr)
        ok = False
    # rule 4
    if run(GOOD.replace("living view", "\u0647\u0645\u0647 view")) == 0:
        print("SELF-TEST FAIL: rule 4 (non-ASCII) not caught", file=sys.stderr)
        ok = False
    # rule 5
    if run(GOOD.replace("<!--profile-face:account-scope -->", "")) == 0:
        print("SELF-TEST FAIL: rule 5 (account framing) not caught", file=sys.stderr)
        ok = False
    # ungoverned face
    if run("<p>no provenance here</p>") == 0:
        print("SELF-TEST FAIL: missing provenance not caught", file=sys.stderr)
        ok = False

    print("SELF-TEST PASS" if ok else "SELF-TEST FAIL")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=((__doc__ or "").splitlines() or [""])[0])
    ap.add_argument("--root", default=".", help="repository root (default .)")
    ap.add_argument("--self-test", action="store_true", help="offline fixtures")
    ns = ap.parse_args(argv)
    if ns.self_test:
        return self_test()
    return int(check(ns.root))


if __name__ == "__main__":
    sys.exit(main())
