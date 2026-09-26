import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def scan_and_save_apps(output_path: str = "data/apps.json") -> int:
    """Scans the Start Menu and Desktop for installed apps and saves to a JSON file."""
    apps = {}
    
    paths = [
        Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs',
        Path(os.environ.get('PROGRAMDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs',
        Path(os.environ.get('USERPROFILE', '')) / 'Desktop',
        Path(os.environ.get('PUBLIC', '')) / 'Desktop',
    ]
    
    for p in paths:
        if not p.exists():
            continue
        for root, _, files in os.walk(p):
            for f in files:
                if f.lower().endswith('.lnk') or f.lower().endswith('.exe'):
                    name = Path(f).stem.lower().strip()
                    if 'uninstall' not in name:
                        # Prevent overwriting if already found in a higher priority path
                        if name not in apps:
                            apps[name] = str(Path(root) / f)

    # Ensure output directory exists
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=2)
        
    logger.info(f"Scanned and saved {len(apps)} apps to {output_path}")
    return len(apps)
