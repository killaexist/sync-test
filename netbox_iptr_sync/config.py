# netbox_iptr_sync/config.py
import os
import yaml
from typing import Dict

def load_config(file_path: str) -> Dict:
    """
    Load and validate configuration from a YAML file.
    Override with environment variables if present.
    """
    try:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate required fields
        required_fields = [
            ("netbox.url", config.get("netbox", {}).get("url")),
            ("netbox.token", config.get("netbox", {}).get("token")),
            ("excel.file_path", config.get("excel", {}).get("file_path"))
        ]
        for field_name, value in required_fields:
            if not value:
                raise ValueError(f"Missing required config parameter: {field_name}")
        
        # Override with environment variables
        config["netbox"]["url"] = os.environ.get("IPTR_NETBOX_URL", config["netbox"]["url"])
        config["netbox"]["token"] = os.environ.get("IPTR_NETBOX_TOKEN", config["netbox"]["token"])
        config["excel"]["file_path"] = os.environ.get("IPTR_EXCEL_FILE", config["excel"]["file_path"])
        config["netbox"]["port"] = config["netbox"].get("port", 443)
        config["netbox"]["ssl_verify"] = config["netbox"].get("ssl_verify", True)
        config["logging"]["level"] = config["logging"].get("level", "INFO")
        config["logging"]["file"] = config["logging"].get("file", "netbox_sync.log")
        config["sync"]["dry_run"] = config["sync"].get("dry_run", False)
        config["sync"]["tag"] = config["sync"].get("tag", "iptr-synced")
        
        return config
    except Exception as e:
        raise ValueError(f"Failed to load config: {str(e)}")
