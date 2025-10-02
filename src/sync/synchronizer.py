import logging
from typing import Dict, Any
from ..models.device import ExcelDevice
from ..netbox.client import NetBoxClient

logger = logging.getLogger(__name__)

class NetBoxSynchronizer:
    def __init__(self, netbox_client: NetBoxClient, config: Dict[str, Any]):
        self.nb = netbox_client
        self.config = config
    
    def sync_device(self, excel_device: ExcelDevice) -> None:
        """Синхронизируем одно устройство в NetBox"""
        try:
            # Получаем или создаем необходимые объекты
            site = self._get_site(excel_device.location)
            device_type_config = self.config['mappings']['device_types'][excel_device.device_type]
            device_role_config = self.config['mappings']['device_roles'][excel_device.device_type]
            
            device_type = self.nb.get_or_create_device_type(
                device_type_config['manufacturer'],
                device_type_config['model'],
                device_type_config['slug']
            )
            
            device_role = self.nb.get_or_create_device_role(
                device_role_config,
                excel_device.device_type
            )
            
            # Создаем или обновляем устройство
            device = self.nb.nb.dcim.devices.get(name=excel_device.hostname)
            if not device:
                device = self.nb.nb.dcim.devices.create(
                    name=excel_device.hostname,
                    device_type=device_type.id,
                    device_role=device_role.id,
                    site=site.id,
                    status=self.config['defaults']['device_status'],
                    comments=excel_device.description
                )
                logger.info(f"Created device: {excel_device.hostname}")
            else:
                logger.info(f"Device already exists: {excel_device.hostname}")
            
            # Создаем интерфейс
            interface = self._create_interface(device, excel_device)
            
            # Создаем и привязываем IP адрес
            self._create_ip_address(interface, excel_device)
            
            # Создаем VLAN если указан
            if excel_device.vlan_id:
                self._create_vlan(excel_device, site)
                
        except Exception as e:
            logger.error(f"Error syncing device {excel_device.hostname}: {e}")
    
    def _get_site(self, location: str) -> Any:
        """Получаем сайт по location коду"""
        site_mapping = self.config['mappings']['site_mapping']
        if location in site_mapping:
            site_name = site_mapping[location]
            return self.nb.get_or_create_site(site_name, site_name.lower())
        else:
            # Default site if location not mapped
            return self.nb.get_or_create_site("Default", "default")
    
    def _create_interface(self, device: Any, excel_device: ExcelDevice) -> Any:
        """Создаем интерфейс для устройства"""
        interface_name = excel_device.interface_name
        
        # Проверяем существующий интерфейс
        existing_interface = self.nb.nb.dcim.interfaces.get(
            device_id=device.id,
            name=interface_name
        )
        
        if existing_interface:
            return existing_interface
        
        # Создаем новый интерфейс
        interface = self.nb.nb.dcim.interfaces.create(
            device=device.id,
            name=interface_name,
            type=self.config['defaults']['interface_type']
        )
        logger.info(f"Created interface {interface_name} for device {excel_device.hostname}")
        return interface
    
    def _create_ip_address(self, interface: Any, excel_device: ExcelDevice) -> Any:
        """Создаем и привязываем IP адрес"""
        full_ip = excel_device.full_ip_address
        
        # Проверяем существующий IP
        existing_ip = self.nb.nb.ipam.ip_addresses.get(address=full_ip)
        if existing_ip:
            logger.info(f"IP address already exists: {full_ip}")
            return existing_ip
        
        # Создаем VRF если указан
        vrf = None
        if excel_device.vrf and excel_device.vrf != 'MGMT':
            vrf = self.nb.get_or_create_vrf(excel_device.vrf)
        
        # Создаем IP адрес
        ip_address = self.nb.nb.ipam.ip_addresses.create(
            address=full_ip,
            assigned_object_type="dcim.interface",
            assigned_object_id=interface.id,
            vrf=vrf.id if vrf else None,
            description=f"Management IP for {excel_device.hostname}"
        )
        logger.info(f"Created IP address: {full_ip} for {excel_device.hostname}")
        return ip_address
    
    def _create_vlan(self, excel_device: ExcelDevice, site: Any) -> Any:
        """Создаем VLAN если указан ID"""
        if excel_device.vlan_id:
            return self.nb.get_or_create_vlan(
                excel_device.vlan_id,
                excel_device.vlan_name,
                site
            )
