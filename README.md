# curlpad

A simple, interactive terminal editor for crafting `curl` commands.

**Note:** This project is a complete Python port of the original Bash script. It no longer depends on `vi` or `vim` and uses a modern, built-in terminal editor with rich features.

## Features

  * **Modern Terminal Editor:**
      * As-you-type **autocomplete** (press `Tab`).
      * Bash/curl **syntax highlighting** (powered by `pygments`).
      * `vi` keybindings for familiar navigation.
  * **No Dependencies:** The compiled version runs without needing Python, `vim`, or `jq` installed.
  * **JSON Formatting:** Automatically formats JSON payloads in `-d` flags on save.
  * **Safety Check:** Shows you the final command and asks for confirmation before running.

-----

## Installation

We provide a simple installer script that automatically downloads the latest compiled binary and moves it to your system's PATH.

**One-Liner Install (Recommended):**

```sh
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/curlpad/main/install.sh | sudo bash
```

**Manual Install:**

1.  Go to the [Releases page](https://www.google.com/search?q=https://github.com/IntegerAlex/curlpad/releases/latest).
2.  Download the `curlpad` binary.
3.  Make it executable and move it to your PATH:
    ```sh
    chmod +x ./curlpad
    sudo mv ./curlpad /usr/local/bin/curlpad
    ```

-----

## Usage

Simply run the command:

```sh
curlpad
```

This will open the interactive editor.

1.  Press `i` to enter **Insert (Edit) mode**.
2.  Write your `curl` command. Use `Tab` for autocomplete.
3.  Press `Esc` to exit Insert mode.
4.  Type `:wq` and press `Enter` to **save and quit** the editor.
5.  Review the final command and press `Enter` to execute it.

-----

## License

This program is free software, distributed under the GNU General Public License v3.0.
