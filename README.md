# gi_cleaner

A command-line tool to clean files that are ignored by `.gitignore`.

## Overview

`gi_cleaner` scans your project directory, identifies files and directories that match `.gitignore` patterns, and removes them after confirmation. This is useful for cleaning up build artifacts, cache files, and other generated files that shouldn't be committed to Git.

## Features

- Follows standard Git `.gitignore` behavior
- Supports nested `.gitignore` files in subdirectories
- Shows a list of files to be deleted before deletion
- Asks for confirmation before deleting
- Supports dry-run mode to preview what would be deleted
- Simple command-line interface

## Installation

### Using pip

```bash
git clone https://github.com/yourusername/gi_cleaner.git
cd gi_cleaner
pip install -e .
```

After installing with pip, the `gi_cleaner` command will be available globally:

```bash
gi_cleaner
```

## Usage

### Basic usage

Navigate to a directory with a `.gitignore` file and run:

```bash
gi_cleaner
```

### Options

```
usage: gi_cleaner [-h] [-d DIRECTORY] [-n] [-y] [-v]

Clean files that are ignored by .gitignore

options:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        Directory to clean (default: current directory)
  -n, --dry-run         Show what would be deleted without actually deleting
  -y, --yes             Skip confirmation prompt
  -v, --version         show program's version number and exit
```

### Examples

**Preview files to be deleted (dry-run mode):**

```bash
gi_cleaner --dry-run
```

**Clean a specific directory:**

```bash
gi_cleaner -d /path/to/project
```

**Skip confirmation prompt:**

```bash
gi_cleaner --yes
```

**Combine options:**

```bash
gi_cleaner -d /path/to/project --dry-run
```

## How it works

1. Reads `.gitignore` file(s) from the target directory and all subdirectories
2. Scans all files and directories in the project
3. Identifies files/directories that match any `.gitignore` pattern
4. Displays a list of items to be deleted
5. Asks for user confirmation
6. Deletes the confirmed items

The tool follows the same pattern matching rules as Git:
- Patterns in parent directories apply to all subdirectories
- Patterns in subdirectory `.gitignore` files apply only to that subdirectory and its children
- The `.git` directory is always excluded from scanning

## Requirements

- Python 3.10 or higher
- pathspec library (installed automatically)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
