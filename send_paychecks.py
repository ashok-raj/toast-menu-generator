#!/usr/bin/env python3
"""Send paycheck PDFs as email attachments via mutt.

Picks the current-year directory under the Paychecks folder, shows the
5 most recently modified files in a simple TUI, lets the user select
which ones to attach, then sends them as attachments using the
~/.mutt/chennai.mutt profile.
"""

import argparse
import curses
import datetime
import subprocess
import sys
from pathlib import Path

PAYCHECKS_ROOT = Path(
    "/Users/araj/Documents/iCloud/Documents/ChennaiMasala Finance/Paychecks"
)
MUTT_PROFILE = Path.home() / ".mutt" / "chennai.mutt"
MAX_FILES_SHOWN = 5
RECIPIENTS = ["nickm@aboveallaccounting.com", "aroth@aboveallaccounting.com"]
CC = "sumathi@chennaimasala.net"


def find_current_year_dir(root: Path) -> Path:
    year = str(datetime.datetime.now().year)
    year_dir = root / year
    if not year_dir.is_dir():
        sys.exit(f"error: no directory found for current year at {year_dir}")
    return year_dir


def most_recent_files(directory: Path, count: int) -> list[Path]:
    files = [p for p in directory.iterdir() if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:count]


def select_files_tui(files: list[Path]) -> list[Path]:
    """Checkbox-style TUI. Space toggles, Enter confirms, q aborts."""

    def _run(stdscr):
        curses.curs_set(0)
        selected = [False] * len(files)
        cursor = 0

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Select paycheck files to email (space=toggle, enter=send, q=quit)")
            for i, f in enumerate(files):
                mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
                mark = "x" if selected[i] else " "
                prefix = ">" if i == cursor else " "
                line = f"{prefix} [{mark}] {f.name}  ({mtime:%Y-%m-%d %H:%M})"
                stdscr.addstr(i + 2, 0, line)
            stdscr.refresh()

            key = stdscr.getch()
            if key in (curses.KEY_UP, ord("k")):
                cursor = (cursor - 1) % len(files)
            elif key in (curses.KEY_DOWN, ord("j")):
                cursor = (cursor + 1) % len(files)
            elif key == ord(" "):
                selected[cursor] = not selected[cursor]
            elif key in (curses.KEY_ENTER, 10, 13):
                return [f for f, s in zip(files, selected) if s]
            elif key in (ord("q"), 27):
                return []

    return curses.wrapper(_run)


BODY = "Hi Nick,\nPayroll data attached\n\nCheers,\nAshok\n"


def default_subject() -> str:
    return f"Payroll information attached. {datetime.datetime.now():%d/%m/%Y}"


def send_email(files: list[Path], subject: str, recipients: list[str], dry_run: bool) -> None:
    attach_args = []
    for f in files:
        attach_args.extend(["-a", str(f)])

    cmd = [
        "mutt",
        "-F", str(MUTT_PROFILE),
        "-s", subject,
        "-c", CC,
        *attach_args,
        "--",
        *recipients,
    ]

    if dry_run:
        print("Dry run - would execute:")
        print(" ".join(cmd))
        print("\nBody:")
        print(BODY)
        print("Attachments:")
        for f in files:
            print(f"  {f}")
        return

    subprocess.run(cmd, input=BODY.encode(), check=True)
    print(f"Sent {len(files)} attachment(s) to {', '.join(recipients)} (cc: {CC})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Select recent paycheck files from the current year's Paychecks "
            "directory and email them as attachments via mutt "
            f"(profile: {MUTT_PROFILE}) to {', '.join(RECIPIENTS)}, cc {CC}."
        )
    )
    parser.add_argument(
        "-s", "--subject", default=None,
        help='Email subject (default: "Payroll information attached. DD/MM/YYYY")',
    )
    parser.add_argument(
        "--to",
        action="append",
        help=(
            "Send only to this address instead of the default recipients "
            f"({', '.join(RECIPIENTS)}). Can be repeated for multiple addresses. "
            f"The cc ({CC}) is always included."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be sent without actually sending the email",
    )
    args = parser.parse_args()

    year_dir = find_current_year_dir(PAYCHECKS_ROOT)
    files = most_recent_files(year_dir, MAX_FILES_SHOWN)

    if not files:
        sys.exit(f"error: no files found in {year_dir}")

    if not args.dry_run and not MUTT_PROFILE.is_file():
        sys.exit(f"error: mutt profile not found at {MUTT_PROFILE}")

    selected = select_files_tui(files)
    if not selected:
        print("No files selected, aborting.")
        return

    recipients = args.to if args.to else RECIPIENTS
    subject = args.subject if args.subject else default_subject()
    send_email(selected, subject, recipients, args.dry_run)


if __name__ == "__main__":
    main()
