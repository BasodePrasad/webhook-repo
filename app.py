from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))
db = client["github_events"]
collection = db["events"]


def format_timestamp(ts_string):
    dt = datetime.strptime(ts_string, "%Y-%m-%dT%H:%M:%SZ")
    day = dt.day
    suffix = "th"
    if day in [1, 21, 31]:
        suffix = "st"
    elif day in [2, 22]:
        suffix = "nd"
    elif day in [3, 23]:
        suffix = "rd"
    return dt.strftime(f"%-d{suffix} %B %Y - %-I:%M %p UTC")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "push":
        author = data["pusher"]["name"]
        to_branch = data["ref"].replace("refs/heads/", "")
        timestamp = data["head_commit"]["timestamp"][:19] + "Z" if data.get("head_commit") else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        request_id = data["after"]

        doc = {
            "request_id": request_id,
            "author": author,
            "action": "PUSH",
            "from_branch": to_branch,
            "to_branch": to_branch,
            "timestamp": timestamp
        }
        collection.update_one({"request_id": request_id}, {"$set": doc}, upsert=True)

    elif event_type == "pull_request":
        pr = data["pull_request"]
        action = data["action"]

        if action in ["opened", "reopened"]:
            author = pr["user"]["login"]
            from_branch = pr["head"]["ref"]
            to_branch = pr["base"]["ref"]
            timestamp = pr["created_at"][:19] + "Z"
            request_id = str(pr["id"])

            doc = {
                "request_id": request_id,
                "author": author,
                "action": "PULL_REQUEST",
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }
            collection.update_one({"request_id": request_id}, {"$set": doc}, upsert=True)

        elif action == "closed" and pr.get("merged"):
            author = pr["merged_by"]["login"]
            from_branch = pr["head"]["ref"]
            to_branch = pr["base"]["ref"]
            timestamp = pr["merged_at"][:19] + "Z"
            request_id = "merge_" + str(pr["id"])

            doc = {
                "request_id": request_id,
                "author": author,
                "action": "MERGE",
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }
            collection.update_one({"request_id": request_id}, {"$set": doc}, upsert=True)

    return jsonify({"status": "ok"}), 200


@app.route("/events", methods=["GET"])
def get_events():
    events = list(collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(20))

    result = []
    for e in events:
        ts = format_timestamp(e["timestamp"])
        author = e["author"]
        action = e["action"]
        from_b = e["from_branch"]
        to_b = e["to_branch"]

        if action == "PUSH":
            message = f'"{author}" pushed to "{to_b}" on {ts}'
        elif action == "PULL_REQUEST":
            message = f'"{author}" submitted a pull request from "{from_b}" to "{to_b}" on {ts}'
        elif action == "MERGE":
            message = f'"{author}" merged branch "{from_b}" to "{to_b}" on {ts}'
        else:
            message = ""

        result.append({
            "request_id": e["request_id"],
            "action": action,
            "message": message,
            "timestamp": e["timestamp"]
        })

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
