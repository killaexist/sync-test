import pynetbox
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class NetBoxClient:
    def __init__(self, url: str, token: str, verify_ssl: bool = False, port: int = 8000):
        self.nb = pynetbox.api(
            f"{url}:{port}",
            token=token
        )
        self.nb.http_session.verify = verify_ssl
        self._cache = {}
    
    def get_or_create_manufacturer(self, name: str, slug: str) -> Any:
        """Получаем или создаем производителя"""
        cache_key = f"manufacturer_{slug}"
        if cache_key not in self._cache:
            manufacturer = self.nb.dcim.manufacturers.get(slug=slug)
            if not manufacturer:
                manufacturer = self.nb.dcim.manufacturers.create(
                    name=name,
                    slug=slug
                )
                logger.info(f"Created manufacturer: {name}")
            self._cache[cache_key] = manufacturer
        return self._cache[cache_key]
    
    def get_or_create_device_type(self, manufacturer: str, model: str, slug: str) -> Any:
        """Получаем или создаем тип устройства"""
        cache_key = f"device_type_{slug}"
        if cache_key not in self._cache:
            device_type = self.nb.dcim.device_types.get(slug=slug)
            if not device_type:
                manufacturer_obj = self.get_or_create_manufacturer(manufacturer, manufacturer.lower())
                device_type = self.nb.dcim.device_types.create(
                    manufacturer=manufacturer_obj.id,
                    model=model,
                    slug=slug
                )
                logger.info(f"Created device type: {model}")
            self._cache[cache_key] = device_type
        return self._cache[cache_key]
    
    def get_or_create_device_role(self, name: str, slug: str) -> Any:
        """Получаем или создаем роль устройства"""
        cache_key = f"device_role_{slug}"
        if cache_key not in self._cache:
            device_role = self.nb.dcim.device_roles.get(slug=slug)
            if not device_role:
                device_role = self.nb.dcim.device_roles.create(
                    name=name,
                    slug=slug,
                    color="2196f3"
                )
                logger.info(f"Created device role: {name}")
            self._cache[cache_key] = device_role
        return self._cache[cache_key]
    
    def get_or_create_site(self, name: str, slug: str) -> Any:
        """Получаем или создаем сайт"""
        cache_key = f"site_{slug}"
        if cache_key not in self._cache:
            site = self.nb.dcim.sites.get(slug=slug)
            if not site:
                site = self.nb.dcim.sites.create(
                    name=name,
                    slug=slug
                )
                logger.info(f"Created site: {name}")
            self._cache[cache_key] = site
        return self._cache[cache_key]
    
    def get_or_create_vrf(self, name: str) -> Any:
        """Получаем или создаем VRF"""
        cache_key = f"vrf_{name}"
        if cache_key not in self._cache:
            vrf = self.nb.ipam.vrfs.get(name=name)
            if not vrf:
                vrf = self.nb.ipam.vrfs.create(
                    name=name,
                    rd=f"{name}:1"
                )
                logger.info(f"Created VRF: {name}")
            self._cache[cache_key] = vrf
        return self._cache[cache_key]
    
    def get_or_create_vlan(self, vlan_id: int, name: str, site: Any) -> Any:
        """Получаем или создаем VLAN"""
        cache_key = f"vlan_{site.slug}_{vlan_id}"
        if cache_key not in self._cache:
            vlan = self.nb.ipam.vlans.get(vid=vlan_id, site_id=site.id)
            if not vlan:
                vlan = self.nb.ipam.vlans.create(
                    vid=vlan_id,
                    name=name or f"VLAN-{vlan_id}",
                    site=site.id
                )
                logger.info(f"Created VLAN: {vlan_id} - {name}")
            self._cache[cache_key] = vlan
        return self._cache[cache_key]
