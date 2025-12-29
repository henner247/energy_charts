import urllib.request
import urllib.parse
import json

def main():
    base_url = "https://api.energy-charts.info"
    params = {
        "country": "de",
        "start": "2024-01-01T00:00Z",
        "end": "2024-01-01T01:00Z"
    }
    
    for endpoint in ["total_power", "public_power"]:
        url = f"{base_url}/{endpoint}?{urllib.parse.urlencode(params)}"
        print(f"--- {endpoint} ---")
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                if 'production_types' in data:
                    for pt in data['production_types']:
                        print(f"Name: {pt['name']}, Data points: {len(pt.get('data', []))}")
                else:
                    print(f"Keys: {list(data.keys())}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
