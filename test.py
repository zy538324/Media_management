import requests

qb_url = "http://127.0.0.1:8080"  # Update if qBittorrent runs on a different host/port
username = "admin"        # Replace with your qBittorrent username
password = "72RedHoundingDucks!"        # Replace with your qBittorrent password

# Log in to qBittorrent
session = requests.Session()
login_response = session.post(f"{qb_url}/api/v2/auth/login", data={"username": username, "password": password})

if login_response.status_code == 200:
    print("Login successful.")
else:
    print(f"Login failed: {login_response.status_code} - {login_response.text}")

# Check torrent info endpoint
torrents_response = session.get(f"{qb_url}/api/v2/torrents/info")
if torrents_response.status_code == 200:
    print("Torrents fetched successfully:")
    print(torrents_response.json())
else:
    print(f"Error fetching torrents: {torrents_response.status_code} - {torrents_response.text}")
