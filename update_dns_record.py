import os
import datetime
import requests
import json
from dotenv import load_dotenv

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Load environment variables from .env file
load_dotenv()

# Load API Token and Domain from environment variables
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
DOMAIN = os.getenv('DOMAIN')

if not CLOUDFLARE_API_TOKEN or not DOMAIN:
    raise ValueError("Environment variables CLOUDFLARE_API_TOKEN and DOMAIN must be set in the .env file.")

# Define subdomains and records
sub_domains = ['nextcloud', 'portainer']
records = [DOMAIN] + [f"{sub}.{DOMAIN}" for sub in sub_domains]

CLOUDFLARE_RECORD_PROXIED = True

# Headers for Cloudflare API requests
headers = {
    'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
    'Content-Type': 'application/json'
}

# Get Zone ID from Cloudflare
response = requests.get(f"https://api.cloudflare.com/client/v4/zones?name={DOMAIN}", headers=headers)
result = response.json()

# Get current IP
ip_response = requests.get("https://api.ipify.org?format=json")
ip_data = ip_response.json()
ip = ip_data['ip']

print(f"---------------------------------\nRunning at: {now} with Ipv4: {ip}")

if 'result' in result and result['result']:
    CLOUDFLARE_ID = result['result'][0]['id']

    for idx, record in enumerate(records):
        print(f"Processing {record}")
        
        # Get DNS record details
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ID}/dns_records?type=A&name={record}",
            headers=headers
        )
        dns_result = response.json()

        if 'result' in dns_result and dns_result['result']:
            CLOUDFLARE_RECORD_ID = dns_result['result'][0]['id']
            old_ip = dns_result['result'][0]['content']
            
            print(f"\tOld IP: {old_ip}")

            if old_ip == ip:
                print("\tNothing to update.")
                continue

            # Validate IP and update if different
            if ip != old_ip:
                payload = {
                    "type": "A",
                    "name": record,
                    "content": ip,
                    "proxied": CLOUDFLARE_RECORD_PROXIED
                }
                update_response = requests.put(
                    f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ID}/dns_records/{CLOUDFLARE_RECORD_ID}",
                    headers=headers,
                    data=json.dumps(payload)
                )
                update_result = update_response.json()

                if update_result.get('success'):
                    print(f"\tRecord {record} updated.\nOld IP: {old_ip}\nNew IP: {ip}")
                else:
                    print("\tFailed to update record.")
        else:
            print("\tRecord not found.")
else:
    print("Error: Zone ID not found.")
print("\n")