#!/usr/bin/env python3
import json

with open('check_runs.json', 'r') as f:
    data = json.load(f)

print("=== FAILING CHECKS ===")
for check in data['check_runs']:
    if check['conclusion'] == 'failure':
        print(f"\n{check['name']}:")
        print(f"  Status: {check['status']}")
        print(f"  Conclusion: {check['conclusion']}")
        print(f"  Title: {check['output'].get('title', 'No title')}")
        print(f"  Summary: {check['output'].get('summary', 'No summary')}")
        print(f"  Details URL: {check.get('details_url', 'No details URL')}") 