# netbox_iptr_sync/excel_parser.py
import pandas as pd
from ipaddress import ip_interface
from typing import Dict, List

def parse_excel(file_path: str) -> Dict[str, List[Dict]]:
    """
    Parse the Excel file and extract devices, IPs, VLANs, VRFs, prefixes, and interfaces.
    """
    try:
        xls = pd.ExcelFile(file_path)
        data = {
            "devices": [],
            "ip_addresses": [],
            "vlans": [],
            "vrfs": [],
            "prefixes": [],
            "interfaces": []
        }
        
        # Parse SRV sheet
        srv_df = pd.read_excel(xls, sheet_name="SRV", header=1)
        srv_df = srv_df.dropna(subset=["Hostname"])
        
        for _, row in srv_df.iterrows():
            hostname = row["Hostname"]
            site = row["LOCATION"]
            vlan = row["VLAN"]
            vrf = row["VRF"]
            ip = row["IP"]
            mask = row["MASK"]
            gw = row["GW"]
            port = row["port"] if pd.notna(row["port"]) else None
            system = row["Система"]
            description_cols = [col for col in srv_df.columns if col.startswith("Unnamed") and pd.notna(row[col])]
            description = description_cols[0] if description_cols else ""
            
            # Device
            role = "switch" if system == "NET" else "server"
            data["devices"].append({
                "hostname": hostname,
                "site": site,
                "role": role,
                "description": description
            })
            
            # IP Address
            if pd.notna(ip) and pd.notna(mask):
                try:
                    cidr = str(ip_interface(f"{ip}/{mask}").network).split("/")[1]
                    data["ip_addresses"].append({
                        "address": f"{ip}/{cidr}",
                        "device": hostname,
                        "interface": port,
                        "vrf": vrf
                    })
                except ValueError as e:
                    print(f"Skipping invalid IP {ip}/{mask}: {e}")
            
            # Interface
            if port:
                interface_type = "1000base-t" if any(x in port for x in ["Fa", "Gi", "twe"]) else "virtual"
                data["interfaces"].append({
                    "device": hostname,
                    "name": port,
                    "type": interface_type,
                    "vlan": vlan
                })
            
            # VLAN
            if pd.notna(vlan) and pd.notna(row["ID"]):
                data["vlans"].append({
                    "name": vlan,
                    "vid": int(row["ID"]),
                    "site": site,
                    "vrf": vrf
                })
            
            # VRF
            if pd.notna(vrf):
                data["vrfs"].append({
                    "name": vrf,
                    "rd": None,
                    "description": f"VRF for {vrf}"
                })
        
        # Parse GLOBVBAL NET sheet for prefixes
        glob_df = pd.read_excel(xls, sheet_name="GLOBVBAL NET", header=1)
        for _, row in glob_df.iterrows():
            if pd.notna(row["NET"]) and pd.notna(row["MASK"]):
                data["prefixes"].append({
                    "prefix": f"{row['NET']}/{row['MASK']}",
                    "vrf": row.get("VRF", None),
                    "site": None  # Site will be inferred from SRV
                })
        
        # Parse net sheet for additional VRFs
        net_df = pd.read_excel(xls, sheet_name="net", header=0)
        for _, row in net_df.iterrows():
            vrf_name = row.get("VRF_NAME")
            if pd.notna(vrf_name):
                data["vrfs"].append({
                    "name": vrf_name,
                    "rd": None,
                    "description": row.get("Unnamed: 5", f"VRF for {vrf_name}")
                })
        
        # Deduplicate VRFs and VLANs
        data["vrfs"] = list({v["name"]: v for v in data["vrfs"]}.values())
        data["vlans"] = list({(v["name"], v["vid"]): v for v in data["vlans"]}.values())
        
        return data
    except Exception as e:
        raise ValueError(f"Failed to parse Excel file: {str(e)}")
