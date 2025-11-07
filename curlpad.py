#!/usr/bin/env python3
"""
curlpad - A simple curl editor for the command line
Copyright (C) 2023 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>

SPDX-License-Identifier: GPL-3.0-or-later

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Backward-compatible entry point for curlpad.

This file maintains backward compatibility with the old monolithic structure.
It imports and runs the main function from the new modular package structure.
"""

# Import main from the modular package
# Note: This requires the package to be installed or src/ to be in PYTHONPATH
import sys
from pathlib import Path

# Add src/ to path if running from project root
src_path = Path(__file__).parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from curlpad.cli import main

# Re-export version and author for backward compatibility
from curlpad.constants import __version__, __author__, __license__

if __name__ == '__main__':
    main()
