from dataclasses import dataclass
from typing import Optional
import ipaddress

@dataclass
class ExcelDevice:
    hostname: str
    vlan_id: Optional[int]
    vlan_name: str
    vrf: str
    ip_address: str
    mask: str
    gateway: str
    location: str
    system: str
    description: str
    
    @property
    def device_type(self) -> str:
        """Определяем тип устройства по hostname и описанию"""
        hostname_upper = self.hostname.upper()
        description_upper = (self.description or "").upper()
        
        # Определение по префиксам в hostname
        if any(prefix in hostname_upper for prefix in ['ASW', 'CSW', 'MASW']):
            return 'switch'
        elif 'UPS' in hostname_upper:
            return 'ups'
        elif 'ASA' in hostname_upper:
            return 'firewall'
        elif 'WLC' in hostname_upper:
            return 'wlc'
        elif any(prefix in hostname_upper for prefix in ['SRV', 'MHPV', 'M1ST', 'M2ST']):
            return 'server'
        elif 'ST' in hostname_upper and 'STORAGE' in description_upper:
            return 'storage'
        elif 'RRL' in hostname_upper or 'РАДИО' in description_upper:
            return 'radio'
        else:
            return 'server'  # default
    
    @property
    def full_ip_address(self) -> str:
        """Формируем полный IP адрес с маской"""
        if self.mask.startswith('/'):
            return f"{self.ip_address}{self.mask}"
        else:
            return f"{self.ip_address}/{self.mask}"
    
    @property
    def interface_name(self) -> str:
        """Генерируем имя интерфейса"""
        device_type = self.device_type
        if device_type in ['switch', 'router', 'firewall']:
            return "Management1"
        elif device_type in ['server', 'storage']:
            return "eth0"
        elif device_type == 'ups':
            return "Network-Port"
        else:
            return "mgmt0"
    
    def is_valid(self) -> bool:
        """Проверяем валидность данных устройства"""
        return all([
            self.hostname and self.hostname.strip(),
            self.ip_address,
            self.location in ['STM', 'STU', 'TPU']
        ])
