## curlpad

A tiny terminal scratchpad for crafting and running `curl` commands with Vim/Neovim autocomplete.

### Install

**Windows (PowerShell):**

```powershell
# Quick install (recommended)
irm curlpad-installer.gossorg.in/install.ps1 | iex

# Or download and inspect first
Invoke-WebRequest -Uri curlpad-installer.gossorg.in/install.ps1 -OutFile install.ps1
.\install.ps1
```

**Linux/macOS (Bash):**

```bash
# Quick install (recommended)
curl -fsSL curlpad-installer.gossorg.in/install.sh | bash

# Or download and inspect first
curl -fsSL curlpad-installer.gossorg.in/install.sh -o install.sh
chmod +x install.sh
./install.sh
```

**From source:**

```bash
# Linux/macOS
./scripts/install_curlpad.sh           # user install (~/.local/bin)
./scripts/install_curlpad.sh --sudo    # system-wide (/usr/local/bin)

# Windows
.\scripts\install_curlpad.ps1
```

**PATH setup:**

- **Linux/macOS:** If `~/.local/bin` is not on PATH:
  ```bash
  export PATH="$HOME/.local/bin:$PATH"
  ```

- **Windows:** The installer will prompt you to add to PATH automatically.

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

- **Windows:** PowerShell 5.0+, `curl` (required), `vim` or `nvim` (one required)
- **Linux/macOS:** `curl` (required), `vim` or `nvim` (one required)
- `jq` (optional, for JSON formatting)

### License

GPL-3.0-or-later. See SPDX identifier in source files.

### Author

Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>