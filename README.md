## curlpad

A tiny terminal scratchpad for crafting and running `curl` commands with Vim/Neovim autocomplete.

### Install

Quick install (recommended):

```bash
curl -fsSL curlpad-installer.gossorg.in/install.sh | bash
```

Or download and inspect first:

```bash
curl -fsSL curlpad-installer.gossorg.in/install.sh -o install.sh
chmod +x install.sh
./install.sh
```

From source:

```bash
./scripts/install_curlpad.sh           # user install (~/.local/bin)
./scripts/install_curlpad.sh --sudo    # system-wide (/usr/local/bin)
```

If `~/.local/bin` is not on PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Build from source

```bash
make build
# or
./scripts/build_curlpad.sh
```

Artifacts are placed in `dist/`.

### Usage

```bash
curlpad           # open editor at a scratch file with curl completions
curlpad --help    # options
curlpad --version # version
```

Inside the editor:
- Use Ctrl+X Ctrl+K (or Ctrl+Space in Neovim) for dictionary completion
- Uncomment/edit example lines, then save and exit to run

### Requirements

- Linux or macOS
- `curl` (required)
- `vim` or `nvim` (one required)
- `jq` (optional, for JSON formatting)

### License

GPL-3.0-or-later. See SPDX identifier in source files.

### Author

Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>