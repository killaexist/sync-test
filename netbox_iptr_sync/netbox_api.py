# netbox_iptr_sync/netbox_api.py
import pynetbox
import logging
from typing import Dict, Optional

class NetBoxAPI:
    def __init__(self, config: Dict):
        """
        Initialize NetBox API client.
        """
        self.nb = pynetbox.api(url=config["netbox"]["url"], token=config["netbox"]["token"])
        self.nb.http_session.verify = config["netbox"]["ssl_verify"]
        self.tag = config["sync"]["tag"]
        self.dry_run = config["sync"]["dry_run"]
        
        # Cache existing objects
        self._cache = {
            "manufacturers": {m.name: m for m in self.nb.dcim.manufacturers.all()},
            "device_types": {dt.slug: dt for dt in self.nb.dcim.device_types.all()},
            "device_roles": {dr.slug: dr for dr in self.nb.dcim.device_roles.all()},
            "sites": {s.name: s for s in self.nb.dcim.sites.all()},
            "vrfs": {v.name: v for v in self.nb.ipam.vrfs.all()},
            "vlans": {(v.name, v.vid): v for v in self.nb.ipam.vlans.all()},
            "prefixes": {p.prefix: p for p in self.nb.ipam.prefixes.all()},
            "devices": {d.name: d for d in self.nb.dcim.devices.all()},
            "interfaces": {(i.device.name, i.name): i for i in self.nb.dcim.interfaces.all()},
            "ip_addresses": {ip.address: ip for ip in self.nb.ipam.ip_addresses.all()}
        }
    
    def create_or_update_manufacturer(self, name: str) -> Optional[object]:
        """Create or update a manufacturer."""
        if name in self._cache["manufacturers"]:
            return self._cache["manufacturers"][name]
        if not self.dry_run:
            manufacturer = self.nb.dcim.manufacturers.create(name=name, slug=name.lower())
            self._cache["manufacturers"][name] = manufacturer
            logging.info(f"Created manufacturer: {name}")
        else:
            logging.info(f"[DRY-RUN] Would create manufacturer: {name}")
        return manufacturer
    
    def create_or_update_device_type(self, model: str) -> Optional[object]:
        """Create or update a device type."""
        slug = model.lower().replace(" ", "-")
        if slug in self._cache["device_types"]:
            return self._cache["device_types"][slug]
        if not self.dry_run:
            device_type = self.nb.dcim.device_types.create(
                manufacturer=self.create_or_update_manufacturer("Generic").id,
                model=model,
                slug=slug
            )
            self._cache["device_types"][slug] = device_type
            logging.info(f"Created device type: {model}")
        else:
            logging.info(f"[DRY-RUN] Would create device type: {model}")
        return device_type
    
    def create_or_update_role(self, name: str) -> Optional[object]:
        """Create or update a device role."""
        slug = name.lower()
        if slug in self._cache["device_roles"]:
            return self._cache["device_roles"][slug]
        if not self.dry_run:
            role = self.nb.dcim.device_roles.create(name=name, slug=slug, color="blue")
            self._cache["device_roles"][slug] = role
            logging.info(f"Created role: {name}")
        else:
            logging.info(f"[DRY-RUN] Would create role: {name}")
        return role
    
    def create_or_update_site(self, name: str) -> Optional[object]:
        """Create or update a site."""
        if name in self._cache["sites"]:
            return self._cache["sites"][name]
        if not self.dry_run:
            site = self.nb.dcim.sites.create(name=name, slug=name.lower())
            self._cache["sites"][name] = site
            logging.info(f"Created site: {name}")
        else:
            logging.info(f"[DRY-RUN] Would create site: {name}")
        return site
    
    def create_or_update_vrf(self, name: str, rd: Optional[str], description: str) -> Optional[object]:
        """Create or update a VRF."""
        if name in self._cache["vrfs"]:
            return self._cache["vrfs"][name]
        if not self.dry_run:
            vrf = self.nb.ipam.vrfs.create(name=name, rd=rd, description=description, tags=[{"name": self.tag}])
            self._cache["vrfs"][name] = vrf
            logging.info(f"Created VRF: {name}")
        else:
            logging.info(f"[DRY-RUN] Would create VRF: {name}")
        return vrf
    
    def create_or_update_vlan(self, name: str, vid: int, site_name: str, vrf_name: Optional[str]) -> Optional[object]:
        """Create or update a VLAN."""
        key = (name, vid)
        if key in self._cache["vlans"]:
            return self._cache["vlans"][key]
        site = self.create_or_update_site(site_name)
        data = {
            "name": name,
            "vid": vid,
            "site": site.id,
            "tags": [{"name": self.tag}]
        }
        if vrf_name:
            vrf = self.create_or_update_vrf(vrf_name, None, f"VRF for {vrf_name}")
            data["vrf"] = vrf.id
        if not self.dry_run:
            vlan = self.nb.ipam.vlans.create(**data)
            self._cache["vlans"][key] = vlan
            logging.info(f"Created VLAN: {name} (VID: {vid})")
        else:
            logging.info(f"[DRY-RUN] Would create VLAN: {name} (VID: {vid})")
        return vlan
    
    def create_or_update_prefix(self, prefix: str, vrf_name: Optional[str], site_name: Optional[str]) -> Optional[object]:
        """Create or update a prefix."""
        if prefix in self._cache["prefixes"]:
            return self._cache["prefixes"][prefix]
        data = {
            "prefix": prefix,
            "tags": [{"name": self.tag}]
        }
        if vrf_name:
            vrf = self.create_or_update_vrf(vrf_name, None, f"VRF for {vrf_name}")
            data["vrf"] = vrf.id
        if site_name:
            site = self.create_or_update_site(site_name)
            data["site"] = site.id
        if not self.dry_run:
            prefix_obj = self.nb.ipam.prefixes.create(**data)
            self._cache["prefixes"][prefix] = prefix_obj
            logging.info(f"Created prefix: {prefix}")
        else:
            logging.info(f"[DRY-RUN] Would create prefix: {prefix}")
        return prefix_obj
    
    def create_or_update_device(self, name: str, site: str, role: str, device_type: str, description: str) -> Optional[object]:
        """Create or update a device."""
        if name in self._cache["devices"]:
            device = self._cache["devices"][name]
            data = {
                "name": name,
                "site": self.create_or_update_site(site).id,
                "device_role": self.create_or_update_role(role).id,
                "device_type": self.create_or_update_device_type(device_type).id,
                "description": description,
                "tags": [{"name": self.tag}]
            }
            if not self.dry_run:
                device.update(data)
                logging.info(f"Updated device: {name}")
            return device
        data = {
            "name": name,
            "site": self.create_or_update_site(site).id,
            "device_role": self.create_or_update_role(role).id,
            "device_type": self.create_or_update_device_type(device_type).id,
            "description": description,
            "tags": [{"name": self.tag}]
        }
        if not self.dry_run:
            device = self.nb.dcim.devices.create(**data)
            self._cache["devices"][name] = device
            logging.info(f"Created device: {name}")
        else:
            logging.info(f"[DRY-RUN] Would create device: {name}")
        return device
    
    def create_or_update_interface(self, device_name: str, name: str, type: str, vlan_name: Optional[str]) -> Optional[object]:
        """Create or update an interface."""
        key = (device_name, name)
        device = self._cache["devices"].get(device_name)
        if not device:
            logging.warning(f"Device {device_name} not found for interface {name}")
            return None
        if key in self._cache["interfaces"]:
            interface = self._cache["interfaces"][key]
            data = {
                "device": device.id,
                "name": name,
                "type": type,
                "tags": [{"name": self.tag}]
            }
            if vlan_name:
                vlan = self._cache["vlans"].get((vlan_name, None))
                if vlan:
                    data["untagged_vlan"] = vlan.id
            if not self.dry_run:
                interface.update(data)
                logging.info(f"Updated interface: {device_name}/{name}")
            return interface
        data = {
            "device": device.id,
            "name": name,
            "type": type,
            "tags": [{"name": self.tag}]
        }
        if vlan_name:
            vlan = self._cache["vlans"].get((vlan_name, None))
            if vlan:
                data["untagged_vlan"] = vlan.id
        if not self.dry_run:
            interface = self.nb.dcim.interfaces.create(**data)
            self._cache["interfaces"][key] = interface
            logging.info(f"Created interface: {device_name}/{name}")
        else:
            logging.info(f"[DRY-RUN] Would create interface: {device_name}/{name}")
        return interface
    
    def create_or_update_ip_address(self, address: str, device_name: str, interface_name: Optional[str], vrf_name: Optional[str]) -> Optional[object]:
        """Create or update an IP address."""
        if address in self._cache["ip_addresses"]:
            ip = self._cache["ip_addresses"][address]
            data = {
                "address": address,
                "tags": [{"name": self.tag}]
            }
            if interface_name and device_name in self._cache["devices"]:
                interface = self._cache["interfaces"].get((device_name, interface_name))
                if interface:
                    data["assigned_object_type"] = "dcim.interface"
                    data["assigned_object_id"] = interface.id
            if vrf_name:
                vrf = self._cache["vrfs"].get(vrf_name)
                if vrf:
                    data["vrf"] = vrf.id
            if not self.dry_run:
                ip.update(data)
                logging.info(f"Updated IP address: {address}")
            return ip
        data = {
            "address": address,
            "tags": [{"name": self.tag}]
        }
        if interface_name and device_name in self._cache["devices"]:
            interface = self._cache["interfaces"].get((device_name, interface_name))
            if interface:
                data["assigned_object_type"] = "dcim.interface"
                data["assigned_object_id"] = interface.id
        if vrf_name:
            vrf = self._cache["vrfs"].get(vrf_name)
            if vrf:
                data["vrf"] = vrf.id
        if not self.dry_run:
            ip = self.nb.ipam.ip_addresses.create(**data)
            self._cache["ip_addresses"][address] = ip
            logging.info(f"Created IP address: {address}")
        else:
            logging.info(f"[DRY-RUN] Would create IP address: {address}")
        return ip
