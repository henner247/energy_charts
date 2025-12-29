import urllib.request
import urllib.parse
import json

def main():
    base_url = "https://api.energy-charts.info"
    params = {
        "country": "de",
        "start": "2024-01-01T00:00Z",
        "end": "2024-01-01T02:00Z"
    }
    
    url = f"{base_url}/price?{urllib.parse.urlencode(params)}"
    print(f"--- price ---")
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
