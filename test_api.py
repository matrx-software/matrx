import json

import requests

data = {
    "properties": ["location", "isAgent"],
    "filters": {
        "class_inheritance": 'HumanAgentBrain'
    }
}

headers = {'content-type': 'application/json'}
r = requests.post(
    "http://localhost:3001/get_filtered_latest_state/['human2_79', 'human_78']",
    data=json.dumps(data), headers=headers,
)

print()