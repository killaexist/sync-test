"""
Скрипт для первоначальной настройки NetBox
Создает необходимые объекты перед синхронизацией
"""
import yaml
import os
import sys

# Добавляем src в путь для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.netbox.client import NetBoxClient

def setup_netbox():
    """Создает необходимые объекты в NetBox"""
    config_path = os.path.join('config', 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    nb_config = config['netbox']
    netbox_client = NetBoxClient(
        url=nb_config['url'],
        token=nb_config['token'],
        verify_ssl=nb_config['verify_ssl'],
        port=nb_config['port']
    )
    
    # Создаем сайты
    for site_code, site_name in config['mappings']['site_mapping'].items():
        netbox_client.get_or_create_site(site_name, site_name.lower())
        print(f"Site created/verified: {site_name}")
    
    # Создаем производителей и типы устройств
    for device_type, type_config in config['mappings']['device_types'].items():
        netbox_client.get_or_create_device_type(
            type_config['manufacturer'],
            type_config['model'],
            type_config['slug']
        )
        print(f"Device type created/verified: {type_config['model']}")
    
    # Создаем роли устройств
    for role_key, role_name in config['mappings']['device_roles'].items():
        netbox_client.get_or_create_device_role(role_name, role_key)
        print(f"Device role created/verified: {role_name}")
    
    print("NetBox setup completed!")

if __name__ == "__main__":
    setup_netbox()
