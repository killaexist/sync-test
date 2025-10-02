# netbox_iptr_sync/sync_logic.py
import logging
from typing import Dict, List
from .netbox_api import NetBoxAPI

def sync_to_netbox(config: Dict, data: Dict[str, List[Dict]]):
    """
    Synchronize Excel data to NetBox.
    """
    nb_api = NetBoxAPI(config)
    
    # Create manufacturer and device types
    nb_api.create_or_update_manufacturer("Generic")
    nb_api.create_or_update_device_type("Generic Switch")
    nb_api.create_or_update_device_type("Generic Server")
    nb_api.create_or_update_role("switch")
    nb_api.create_or_update_role("server")
    
    # Create VRFs
    for vrf in data["vrfs"]:
        nb_api.create_or_update_vrf(vrf["name"], vrf["rd"], vrf["description"])
    
    # Create VLANs
    for vlan in data["vlans"]:
        nb_api.create_or_update_vlan(vlan["name"], vlan["vid"], vlan["site"], vlan["vrf"])
    
    # Create prefixes
    for prefix in data["prefixes"]:
        nb_api.create_or_update_prefix(prefix["prefix"], prefix["vrf"], prefix["site"])
    
    # Create devices
    for device in data["devices"]:
        device_type = "Generic Switch" if device["role"] == "switch" else "Generic Server"
        nb_api.create_or_update_device(
            device["hostname"],
            device["site"],
            device["role"],
            device_type,
            device["description"]
        )
    
    # Create interfaces
    for interface in data["interfaces"]:
        nb_api.create_or_update_interface(
            interface["device"],
            interface["name"],
            interface["type"],
            interface["vlan"]
        )
    
    # Create IP addresses
    for ip in data["ip_addresses"]:
        nb_api.create_or_update_ip_address(
            ip["address"],
            ip["device"],
            ip["interface"],
            ip["vrf"]
        )
    
    logging.info("Synchronization completed.")
