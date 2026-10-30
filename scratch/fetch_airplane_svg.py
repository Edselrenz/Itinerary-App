# Let's inspect the clarity:airplane-solid icon definition from the standard clarity set
# Standard clarity airplane-solid:
# viewBox="0 0 36 36"
# <path d="..."/>
# Or we can check if it's in node_modules or search web
import urllib.request
import json

try:
    url = "https://api.iconify.design/clarity:airplane-solid.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print("Clarity airplane data:", data)
except Exception as e:
    print("Error fetching:", e)

