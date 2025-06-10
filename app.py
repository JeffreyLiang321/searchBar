from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
# small changes
@app.route("/search-apartments", methods=["POST"])
def search_apartments():
    try:
        data = request.get_json()
        print("Received payload:", data)

        print("Using DB ID:", DATABASE_ID)
        print("Using Notion Key:", NOTION_API_KEY[:8], "...")

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

        print("Querying Notion with:", payload)

        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = requests.post(url, headers=headers, json=payload)

        print("Notion response:", response.status_code)
        print("Notion body:", response.text)

        if response.status_code != 200:
            return jsonify({"error": "Notion request failed"}), 500

        results = response.json()["results"]
        output = []

        for r in results:
            props = r["properties"]
            description = props["Description"]["rich_text"][0]["plain_text"] if props["Description"]["rich_text"] else ""
            image_url = ""
            if props["Image"]["files"]:
                first_file = props["Image"]["files"][0]
                if "file" in first_file:
                    image_url = first_file["file"]["url"]
                elif "external" in first_file:
                    image_url = first_file["external"]["url"]

            output.append({
                "name": props["Apartment Name"]["title"][0]["plain_text"],
                "rent": props["Monthly Rent"]["number"],
                "district": props["District"]["rich_text"][0]["plain_text"],
                "description": description,
                "image_url": image_url
            })

        return jsonify(output)
    
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
