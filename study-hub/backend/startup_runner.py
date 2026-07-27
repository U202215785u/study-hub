"""Internal detached-process runner used by start-background.ps1."""

import argparse
import os
import runpy
import sys
import traceback
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--stdout", required=True)
    parser.add_argument("--stderr", required=True)
    args = parser.parse_args()

    main_path = str(Path(args.main).resolve())
    os.environ["PORT"] = args.port
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.argv = [main_path]

    for inherited_stream in (sys.stdout, sys.stderr):
        try:
            inherited_stream.close()
        except OSError:
            pass

    stdout_log = open(args.stdout, "w", encoding="utf-8", buffering=1)
    stderr_log = open(args.stderr, "w", encoding="utf-8", buffering=1)
    sys.stdout = sys.__stdout__ = stdout_log
    sys.stderr = sys.__stderr__ = stderr_log

    try:
        runpy.run_path(main_path, run_name="__main__")
    except SystemExit as exc:
        if exc.code is None:
            return 0
        return exc.code if isinstance(exc.code, int) else 1
    except BaseException:
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
