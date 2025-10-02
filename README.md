# NetBox IPTR Sync

This repository provides a Python tool to synchronize network inventory data from an Excel file (`IPTR_IP_PLAN.xlsx`) to NetBox. It creates and updates devices, interfaces, IP addresses, VLANs, VRFs, and prefixes based on the provided Excel data.

## Features
- Parses Excel file (`SRV`, `GLOBVBAL NET`, `net` sheets) to extract network inventory.
- Synchronizes devices, interfaces, IP addresses, VLANs, VRFs, and prefixes to NetBox via REST API.
- Idempotent operations: updates existing objects instead of creating duplicates.
- Supports dry-run mode for testing without modifying NetBox.
- Tags synchronized objects with `iptr-synced` for tracking.
- Configurable via YAML file.

## Prerequisites
- Python 3.8+
- NetBox instance with API access (token with read/write permissions)
- Excel file (`IPTR_IP_PLAN.xlsx`) with the correct structure

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/netbox-iptr-sync.git
   cd netbox-iptr-sync
