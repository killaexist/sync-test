import pandas as pd
from typing import List, Optional
from ..models.device import ExcelDevice
import logging

logger = logging.getLogger(__name__)

class ExcelParser:
    def __init__(self, file_path: str, sheet_name: str, start_row: int = 4):
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.start_row = start_row
    
    def parse_devices(self) -> List[ExcelDevice]:
        """Парсим Excel файл и возвращаем список устройств"""
        try:
            df = pd.read_excel(
                self.file_path, 
                sheet_name=self.sheet_name,
                header=self.start_row - 1
            )
            
            devices = []
            for _, row in df.iterrows():
                # Пропускаем пустые строки
                if pd.isna(row.get('Hostname')) or not str(row['Hostname']).strip():
                    continue
                
                device = ExcelDevice(
                    hostname=str(row['Hostname']).strip(),
                    vlan_id=self._safe_int(row.get('ID')),
                    vlan_name=str(row.get('VLAN', '')).strip(),
                    vrf=str(row.get('VRF', '')).strip() or 'MGMT',
                    ip_address=str(row.get('IP', '')).strip(),
                    mask=str(row.get('MASK', '')).strip(),
                    gateway=str(row.get('GW', '')).strip(),
                    location=str(row.get('LOCATION', '')).strip(),
                    system=str(row.get('Система', '')).strip(),
                    description=str(row.get('Description', '')).strip()
                )
                
                if device.is_valid():
                    devices.append(device)
                else:
                    logger.warning(f"Invalid device data skipped: {device.hostname}")
            
            logger.info(f"Successfully parsed {len(devices)} devices from Excel")
            return devices
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {e}")
            raise
    
    def _safe_int(self, value) -> Optional[int]:
        """Безопасное преобразование в int"""
        try:
            if pd.isna(value):
                return None
            return int(float(value))
        except (ValueError, TypeError):
            return None
