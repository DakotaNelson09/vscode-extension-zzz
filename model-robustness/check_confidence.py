import requests, json
resp = requests.post("http://localhost:8000/detect", json={"text": "AWS_SECRET_ACCESS_KEY=AKIAXJZR6VNQPLKJ2FGH", "max_results": 10, "batch_size": 1})
print(json.dumps(resp.json(), indent=2))