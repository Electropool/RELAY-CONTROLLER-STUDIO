import json
import urllib.request
from typing import Optional, Dict, Any
from core.constants import APP_VERSION
from core.logger import get_logger

logger = get_logger()


def check_for_updates() -> Optional[Dict[str, Any]]:
    """
    Check the GitHub repository for the latest release version.
    Returns a dict with version details if an update is available, otherwise None.
    """
    url = "https://api.github.com/repos/Electropool/REALY-CONTROLER/releases/latest"
    logger.info("Checking for updates from %s...", url)
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "RelayControllerStudio-Updater"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            
        latest_version = data.get("tag_name", "").strip().lstrip("v")
        current_version = APP_VERSION.split("-")[0].strip().lstrip("v")

        logger.info("Current version: %s, Latest version: %s", current_version, latest_version)

        # Basic semantic version parts check
        latest_parts = [int(x) for x in latest_version.split(".") if x.isdigit()]
        current_parts = [int(x) for x in current_version.split(".") if x.isdigit()]

        is_newer = False
        for lp, cp in zip(latest_parts, current_parts):
            if lp > cp:
                is_newer = True
                break
            elif lp < cp:
                break
        else:
            if len(latest_parts) > len(current_parts):
                is_newer = True

        if is_newer:
            logger.info("A new version (%s) is available!", latest_version)
            return {
                "version": latest_version,
                "url": data.get("html_url", ""),
                "notes": data.get("body", "No release notes provided.")
            }
        
        logger.info("Application is up to date.")
        return None
    except Exception as e:
        logger.warning("Failed to check for updates: %s", e)
        return None
