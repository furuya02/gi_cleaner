#!/usr/bin/env python3
"""
gi_cleaner - Clean files that are ignored by .gitignore

This tool scans the current directory for files that match .gitignore patterns
and removes them after user confirmation.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

import pathspec


def load_gitignore_patterns(directory: Path) -> Optional[pathspec.PathSpec]:
    """
    Load .gitignore patterns from a directory.

    Args:
        directory: The directory to load .gitignore from

    Returns:
        PathSpec object if .gitignore exists, None otherwise
    """
    gitignore_path = directory / ".gitignore"
    if not gitignore_path.exists():
        return None

    with open(gitignore_path, "r", encoding="utf-8") as gitignore_file:
        lines = gitignore_file.readlines()

    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def collect_all_gitignore_specs(root_directory: Path) -> dict[Path, pathspec.PathSpec]:
    """
    Collect all .gitignore files from the root directory and its subdirectories.

    Args:
        root_directory: The root directory to start scanning from

    Returns:
        Dictionary mapping directory paths to their PathSpec objects
    """
    gitignore_specs: dict[Path, pathspec.PathSpec] = {}

    for current_dir, _, _ in os.walk(root_directory):
        current_path = Path(current_dir)
        spec = load_gitignore_patterns(current_path)
        if spec is not None:
            gitignore_specs[current_path] = spec

    return gitignore_specs


def is_file_ignored(
    file_path: Path,
    root_directory: Path,
    gitignore_specs: dict[Path, pathspec.PathSpec]
) -> bool:
    """
    Check if a file is ignored by any applicable .gitignore.

    This follows Git's behavior where .gitignore files apply to their
    directory and all subdirectories.

    Args:
        file_path: The file path to check
        root_directory: The root directory of the project
        gitignore_specs: Dictionary of .gitignore specs by directory

    Returns:
        True if the file is ignored, False otherwise
    """
    relative_to_root = file_path.relative_to(root_directory)

    # Check each .gitignore from root to the file's parent directory
    current_check_dir = root_directory
    for part in relative_to_root.parent.parts:
        if current_check_dir in gitignore_specs:
            spec = gitignore_specs[current_check_dir]
            relative_path = file_path.relative_to(current_check_dir)
            if spec.match_file(str(relative_path)):
                return True
        current_check_dir = current_check_dir / part

    # Check the final directory
    if current_check_dir in gitignore_specs:
        spec = gitignore_specs[current_check_dir]
        relative_path = file_path.relative_to(current_check_dir)
        if spec.match_file(str(relative_path)):
            return True

    # Also check the file's own directory
    file_parent = file_path.parent
    if file_parent in gitignore_specs:
        spec = gitignore_specs[file_parent]
        if spec.match_file(file_path.name):
            return True

    return False


def is_directory_ignored(
    dir_path: Path,
    root_directory: Path,
    gitignore_specs: dict[Path, pathspec.PathSpec]
) -> bool:
    """
    Check if a directory is ignored by any applicable .gitignore.

    Args:
        dir_path: The directory path to check
        root_directory: The root directory of the project
        gitignore_specs: Dictionary of .gitignore specs by directory

    Returns:
        True if the directory is ignored, False otherwise
    """
    relative_to_root = dir_path.relative_to(root_directory)

    # Check each .gitignore from root to the directory's parent
    current_check_dir = root_directory
    for part in relative_to_root.parts:
        if current_check_dir in gitignore_specs:
            spec = gitignore_specs[current_check_dir]
            # For directories, we need to check with trailing slash
            relative_path = dir_path.relative_to(current_check_dir)
            dir_pattern = str(relative_path) + "/"
            if spec.match_file(dir_pattern) or spec.match_file(str(relative_path)):
                return True
        current_check_dir = current_check_dir / part

    return False


def find_ignored_files(root_directory: Path) -> tuple[list[Path], list[Path]]:
    """
    Find all files and directories that are ignored by .gitignore.

    Args:
        root_directory: The root directory to scan

    Returns:
        Tuple of (ignored_files, ignored_directories)
    """
    gitignore_specs = collect_all_gitignore_specs(root_directory)

    if not gitignore_specs:
        return [], []

    ignored_files: list[Path] = []
    ignored_directories: list[Path] = []
    skip_directories: set[Path] = set()

    for current_dir, directories, files in os.walk(root_directory):
        current_path = Path(current_dir)

        # Skip .git directory
        if ".git" in directories:
            directories.remove(".git")

        # Skip already marked ignored directories
        if current_path in skip_directories:
            directories.clear()
            continue

        # Check directories
        dirs_to_remove: list[str] = []
        for dir_name in directories:
            dir_path = current_path / dir_name
            if is_directory_ignored(dir_path, root_directory, gitignore_specs):
                ignored_directories.append(dir_path)
                skip_directories.add(dir_path)
                dirs_to_remove.append(dir_name)

        # Remove ignored directories from further traversal
        for dir_name in dirs_to_remove:
            directories.remove(dir_name)

        # Check files
        for file_name in files:
            file_path = current_path / file_name
            if is_file_ignored(file_path, root_directory, gitignore_specs):
                ignored_files.append(file_path)

    return ignored_files, ignored_directories


def display_ignored_items(
    ignored_files: list[Path],
    ignored_directories: list[Path],
    root_directory: Path
) -> None:
    """
    Display the list of ignored files and directories.

    Args:
        ignored_files: List of ignored file paths
        ignored_directories: List of ignored directory paths
        root_directory: The root directory for relative path display
    """
    total_items = len(ignored_files) + len(ignored_directories)

    if total_items == 0:
        print("No ignored files or directories found.")
        return

    print(f"\nFound {total_items} ignored item(s):\n")

    if ignored_directories:
        print("Directories:")
        for dir_path in sorted(ignored_directories):
            relative_path = dir_path.relative_to(root_directory)
            print(f"  [DIR]  {relative_path}/")

    if ignored_files:
        print("\nFiles:")
        for file_path in sorted(ignored_files):
            relative_path = file_path.relative_to(root_directory)
            print(f"  [FILE] {relative_path}")

    print()


def confirm_deletion() -> bool:
    """
    Ask user for confirmation before deletion.

    Returns:
        True if user confirms, False otherwise
    """
    while True:
        response = input("Do you want to delete these items? (yes/no): ").strip().lower()
        if response in ("yes", "y"):
            return True
        elif response in ("no", "n"):
            return False
        else:
            print("Please enter 'yes' or 'no'.")


def delete_items(
    ignored_files: list[Path],
    ignored_directories: list[Path],
    root_directory: Path,
    dry_run: bool = False
) -> tuple[int, int]:
    """
    Delete the ignored files and directories.

    Args:
        ignored_files: List of files to delete
        ignored_directories: List of directories to delete
        root_directory: The root directory for relative path display
        dry_run: If True, only simulate deletion

    Returns:
        Tuple of (deleted_files_count, deleted_directories_count)
    """
    deleted_files = 0
    deleted_directories = 0

    # Delete files first
    for file_path in ignored_files:
        relative_path = file_path.relative_to(root_directory)
        try:
            if not dry_run:
                file_path.unlink()
            print(f"Deleted file: {relative_path}")
            deleted_files += 1
        except OSError as error:
            print(f"Error deleting {relative_path}: {error}", file=sys.stderr)

    # Delete directories (sorted by depth, deepest first)
    sorted_directories = sorted(
        ignored_directories,
        key=lambda p: len(p.parts),
        reverse=True
    )

    for dir_path in sorted_directories:
        relative_path = dir_path.relative_to(root_directory)
        try:
            if not dry_run:
                shutil.rmtree(dir_path)
            print(f"Deleted directory: {relative_path}/")
            deleted_directories += 1
        except OSError as error:
            print(f"Error deleting {relative_path}/: {error}", file=sys.stderr)

    return deleted_files, deleted_directories


def main() -> int:
    """
    Main entry point for gi_cleaner.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Clean files that are ignored by .gitignore",
        prog="gi_cleaner"
    )
    parser.add_argument(
        "-d", "--directory",
        type=str,
        default=".",
        help="Directory to clean (default: current directory)"
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    args = parser.parse_args()

    root_directory = Path(args.directory).resolve()

    if not root_directory.exists():
        print(f"Error: Directory '{root_directory}' does not exist.", file=sys.stderr)
        return 1

    if not root_directory.is_dir():
        print(f"Error: '{root_directory}' is not a directory.", file=sys.stderr)
        return 1

    # Check if .gitignore exists in root
    if not (root_directory / ".gitignore").exists():
        print(f"Error: No .gitignore found in '{root_directory}'.", file=sys.stderr)
        return 1

    print(f"Scanning directory: {root_directory}")

    ignored_files, ignored_directories = find_ignored_files(root_directory)

    display_ignored_items(ignored_files, ignored_directories, root_directory)

    if not ignored_files and not ignored_directories:
        return 0

    if args.dry_run:
        print("Dry run mode - no files were deleted.")
        return 0

    if not args.yes:
        if not confirm_deletion():
            print("Deletion cancelled.")
            return 0

    deleted_files, deleted_dirs = delete_items(
        ignored_files,
        ignored_directories,
        root_directory
    )

    print(f"\nDeleted {deleted_files} file(s) and {deleted_dirs} directory(ies).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
