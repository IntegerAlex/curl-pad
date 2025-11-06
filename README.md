## curlpad

A tiny terminal scratchpad for crafting and running `curl` commands with Vim/Neovim autocomplete.

### Install

- User install (recommended):

```bash
./scripts/install_curlpad.sh
# installs to ~/.local/bin/curlpad
```

- System-wide (needs sudo):

```bash
./scripts/install_curlpad.sh --sudo
# installs to /usr/local/bin/curlpad
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