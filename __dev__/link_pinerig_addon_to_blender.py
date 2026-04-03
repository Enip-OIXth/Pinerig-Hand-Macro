# EnipOIXth 2026


# ---------------------------------------------------------------------
"""
This script creates a symbolic link to the specified Blender addons in BLENDER_VERSIONS.
Must be set in a subfolder inside the main addon folder.
Simply execute this file through VS Code or something. 
Can automatically detect Blender versions and print them out.
Can also delete symbolic links which equates to uninstalling addons.
"""
# ---------------------------------------------------------------------


import os
from pathlib import Path
import platform
import shutil
import subprocess
import re


# ---------------------------------------------------------------------
# User config
BLENDER_VERSIONS = ["4.2", "4.3", "4.4", "4.5", "5.0"]
FORCE_REPLACE = True  # Set False to skip if the link already exists.
UNINSTALL = False # Set to True to remove links and uninstall addons.
# ---------------------------------------------------------------------


# Auto-detects addon root and name
SCRIPT_PATH = Path(__file__).resolve()
ADDON_ROOT = SCRIPT_PATH.parent.parent
ADDON_NAME = ADDON_ROOT.name


class C: # For colored prints
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"


# ---------------------------------------------------------------------


def detect_blender_versions() -> list[str]:
    system = platform.system()

    # Windows
    if system == "Windows":
        appdata = os.getenv("APPDATA")
        if not appdata:
            return []
        base = Path(appdata) / "Blender Foundation" / "Blender"

    # macOS
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "Blender"

    # Linux (native + Flatpak)
    else:
        linux_paths = [
            Path.home() / ".config" / "blender",
            Path.home() / ".var" / "app" / "org.blender.Blender" / "config" / "blender",
        ]
        # Pick the first existing one
        for p in linux_paths:
            if p.exists():
                base = p
                break
        else:
            base = linux_paths[0]

    if not base.exists():
        return []

    version_pattern = re.compile(r"^\d+\.\d+$")
    versions = [
        d.name for d in base.iterdir()
        if d.is_dir() and version_pattern.match(d.name)
    ]

    return sorted(versions)



def get_addon_dir(version: str) -> Path:
    system = platform.system()

    # Windows
    if system == "Windows":
        appdata = os.getenv("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA is not set; cannot determine Blender addons directory.")
        return Path(appdata) / "Blender Foundation" / "Blender" / version / "scripts" / "addons"
    
    # Mac
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Blender" / version / "scripts" / "addons"
    
    # Linux
    else:
        linux_paths = [
            Path.home() / ".config" / "blender" / version / "scripts" / "addons",
            Path.home() / ".var" / "app" / "org.blender.Blender" / "config" / "blender" / version / "scripts" / "addons",
        ]

        #  Return the first existing path, or the native one if none exist yet
        for p in linux_paths:
            if p.exists():
                return p
            
        return linux_paths[0]


def path_lexists(p: Path) -> bool:
    """Detects broken symlinks."""
    return os.path.lexists(str(p))


def is_windows_junction(p: Path) -> bool:
    """Detects Windows Junctions."""
    if platform.system() != "Windows":
        return False
    try:
        # If this succeeds, it's a symlink OR a junction
        os.readlink(str(p))
        return True
    except OSError:
        return False


def safe_remove(p: Path) -> None:
    """Safely remove files, directories, symlinks, or junctions."""
    try:
        # Windows junction or symlink
        if p.is_symlink() or os.path.islink(str(p)) or is_windows_junction(p):
            p.unlink()
        
        # Regular file
        elif p.is_file():
            p.unlink()
        
        # Regular directory
        elif p.exists():
            shutil.rmtree(p)
        
        # Broken symlink or odd reparse point.
        else:
            if path_lexists(p):
                p.unlink(missing_ok=True)

    except Exception as e:
        raise RuntimeError(f"Failed to remove existing path: {p} ({e})")


def remove_link(link: Path) -> str:
    if not path_lexists(link):
        return f"Nothing to remove: {link}"

    try:
        safe_remove(link)
        return f"Removed link: {link}"
    except Exception as e:
        return f"ERROR removing {link}: {e}"
    

def create_dir_link_windows(target: Path, link: Path) -> str:
    """Try true symlink first. If not permitted, fall back to a junction"""
    try:
        link.symlink_to(target, target_is_directory=True)
        return "symlink"
    except OSError:
        # mklink /J usually works without special privileges
        cmd = ["cmd", "/c", "mklink", "/J", str(link), str(target)]
        subprocess.run(
            cmd, 
            check=True, 
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return "junction"


def create_dir_link_posix(target: Path, link: Path) -> str:
    """Creates a Linux posix."""
    link.symlink_to(target, target_is_directory=True)
    return "symlink"


def ensure_link(target: Path, link: Path, force: bool = False) -> str:
    """
    Checks if the link already exists, and either skip it or remove it.
    Then installs the link.
    """

    if not target.exists():
        raise FileNotFoundError(f"Source addon path does not exist: {target}")

    link.parent.mkdir(parents=True, exist_ok=True)

    if path_lexists(link):
        # If something exists at link, decide what to do.
        if force:
            safe_remove(link)
        else:
            return f"Skipped (exists): {link}"

    system = platform.system()
    try:
        if system == "Windows":
            kind = create_dir_link_windows(target, link)
        else:
            kind = create_dir_link_posix(target, link)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create link via system command: {e}") from e
    except OSError as e:
        raise RuntimeError(f"Failed to create link: {e}") from e
    
    return f"{C.GREEN}Created {kind}:{C.RESET} {C.CYAN}Addon root{C.RESET} {C.GREEN}<<===>>{C.RESET} {link}"


# ---------------------------------------------------------------------


def main():
    print(f"{C.CYAN}Detected Blender versions:{C.RESET} {detect_blender_versions()}")
    print(f"{C.CYAN}Targeted Blender versions:{C.RESET} {BLENDER_VERSIONS}")
    print(f"{C.CYAN}Detected addon:{C.RESET} {ADDON_NAME}")
    print(f"{C.CYAN}Addon root:{C.RESET} {ADDON_ROOT}")

    for version in BLENDER_VERSIONS:
        addon_dir = get_addon_dir(version)
        link_path = addon_dir / ADDON_NAME

        # -------------------------
        # UNINSTALL LINK MODE
        # -------------------------
        if UNINSTALL:
            result = remove_link(link_path)
            color = C.GREEN if result.startswith("Removed") else C.YELLOW
            print(f"[{version}] {color}{result}{C.RESET}")
            continue

        # -------------------------
        # CREATE LINK MODE
        # -------------------------
        try:
            result = ensure_link(ADDON_ROOT.resolve(), link_path, force=FORCE_REPLACE)
            
            if result.startswith("Created"):
                color = C.GREEN
            elif result.startswith("Skipped"):
                color = C.YELLOW
            else:
                color = C.CYAN
            
            print(f"[{version}] {color}{result}{C.RESET}")
            
        except Exception as e:
            print(f"[{version}] {C.RED}ERROR: {e}{C.RESET}")


# ---------------------------------------------------------------------


if __name__ == "__main__":
    main()