import simplejson as json

# Ler um arquivo JSON
with open('topologia_overlay.json', 'r') as f:
    data = json.load(f)

json.dumps(data, indent=4, sort_keys=True)

print(data['nodes'])