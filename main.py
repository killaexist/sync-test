import logging
import yaml
import os
from src.parsers.excel_parser import ExcelParser
from src.netbox.client import NetBoxClient
from src.sync.synchronizer import NetBoxSynchronizer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config() -> dict:
    """Загружаем конфигурацию из YAML файла"""
    config_path = os.path.join('config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def main():
    """Основная функция синхронизации"""
    try:
        # Загружаем конфигурацию
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Инициализируем парсер Excel
        excel_config = config['excel']
        parser = ExcelParser(
            file_path=excel_config['file_path'],
            sheet_name=excel_config['sheet_name'],
            start_row=excel_config['start_row']
        )
        
        # Парсим устройства из Excel
        devices = parser.parse_devices()
        logger.info(f"Found {len(devices)} devices in Excel file")
        
        # Инициализируем клиент NetBox
        nb_config = config['netbox']
        netbox_client = NetBoxClient(
            url=nb_config['url'],
            token=nb_config['token'],
            verify_ssl=nb_config['verify_ssl'],
            port=nb_config['port']
        )
        
        # Инициализируем синхронизатор
        synchronizer = NetBoxSynchronizer(netbox_client, config)
        
        # Синхронизируем каждое устройство
        for device in devices:
            synchronizer.sync_device(device)
        
        logger.info("Synchronization completed successfully!")
        
    except Exception as e:
        logger.error(f"Synchronization failed: {e}")
        raise

if __name__ == "__main__":
    main()
