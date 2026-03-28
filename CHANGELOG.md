# Changelog

All notable changes to curlpad will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-03-28

### Added
- **Autocomplete improvements**: Dictionary completion now triggers automatically as you type (2+ characters)
- **Tab/Shift-Tab navigation**: Navigate completion suggestions with Tab (forward) and Shift-Tab (backward)
- **--dry-run flag**: Preview and validate curl commands without executing them
- **Command history**: Last 20 executed commands saved to `~/.curlpad/history`
- **History navigation**: Use Up/Down arrow keys in the editor to recall previous commands
- **Config file support**: Create `~/.curlpadrc` to set defaults like `DEFAULT_URL` and `AUTO_FORMAT_JSON`

### Changed
- Autocomplete now uses `completeopt` with `noselect` to prevent auto-inserting the first match
- Tab key intelligently triggers completion when a word prefix exists, otherwise inserts normal indentation
- Both Vim and Neovim configs updated with buffer-local autocomplete and history navigation
- Ctrl+Space and Ctrl+X Ctrl+K still available as manual completion triggers

### Fixed
- Buffer-local scoping for Vim TextChangedI autocmd to prevent affecting other buffers
- Prevented multiple TextChangedI autocmd registrations in Neovim (guard with buffer flag)
- Secure file handling: config and history files opened with explicit UTF-8 encoding and error handling
- UnicodeDecodeError handling in config and history loading for robustness against corrupt files

## [1.3.2] - Previous release
