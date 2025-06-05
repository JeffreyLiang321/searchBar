from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")

@app.route("/search-apartments", methods=["POST"])
def search_apartments():
    data = request.get_json()
    filters = []

    if data.get("available_now"):
        filters.append({
            "property": "Available Now",
            "checkbox": {"equals": True}
        })
    if data.get("max_rent"):
        filters.append({
            "property": "Monthly Rent",
            "number": {"less_than_or_equal_to": int(data["max_rent"])}
        })
    if data.get("bedroom"):
        filters.append({
            "property": "Number of Bedrooms",
            "select": {"equals": data["bedroom"]}
        })
    if data.get("district"):
        filters.append({
            "property": "District",
            "rich_text": {"equals": data["district"]}
        })

    payload = {"filter": {"and": filters}}

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        return jsonify({"error": response.text}), response.status_code

    results = response.json()["results"]
    output = []

    for r in results:
        props = r["properties"]
        output.append({
            "name": props["Apartment Name"]["title"][0]["plain_text"],
            "rent": props["Monthly Rent"]["number"],
            "district": props["District"]["rich_text"][0]["plain_text"]
        })

    return jsonify(output)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
