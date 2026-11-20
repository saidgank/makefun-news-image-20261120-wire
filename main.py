"""Entry program for make.fun's news-image-20261120 competition.

The repository holds the finished front page as entry.png (typeset by
compose.py at build time). This program simply copies it, byte for byte,
to entry.png inside the output directory -- MAKEFUN_OUTPUT_DIR when set,
/output otherwise -- so every run writes exactly the same bytes.
"""

import os
import shutil


def main():
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
