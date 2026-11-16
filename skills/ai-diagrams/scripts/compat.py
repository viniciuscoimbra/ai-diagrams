"""Names from 0.1.x that still work until 0.3.0, with a warning on stderr."""
import os
import sys


def warn(old, new):
    print('ai-diagrams: %s is deprecated; use %s' % (old, new), file=sys.stderr)


def take_flag(argv, new, old=None, error=None):
    """Remove `--new X` / `--new=X` (or the deprecated `--old`) from argv. Returns (value or None, rest).
    error: message for a flag without a value; without it, a missing value is None."""
    names = [new] + ([old] if old else [])
    out, value, i = [], None, 0
    while i < len(argv):
        a = argv[i]
        name = next((n for n in names if a == n or a.startswith(n + '=')), None)
        if name is None:
            out.append(a)
            i += 1
            continue
        if name == old:
            warn(old, new)
        if a == name:
            if i + 1 >= len(argv) or argv[i + 1].startswith('--'):
                if error:
                    sys.exit(error)
                i += 1
                continue
            value, i = argv[i + 1], i + 2
        else:
            value, i = a.split('=', 1)[1], i + 1
    return value, out


def has_flag(argv, new, old=None):
    """True if --new (or the deprecated --old) is in argv."""
    if old and old in argv:
        warn(old, new)
        return True
    return new in argv


def env(new, old):
    """Value of the environment variable, reading the deprecated name too."""
    if os.environ.get(new):
        return os.environ[new]
    if os.environ.get(old):
        warn(old, new)
        return os.environ[old]
    return None
