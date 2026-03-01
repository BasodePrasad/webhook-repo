# webhook-repo

Flask app that receives GitHub webhooks, stores them in MongoDB, and shows a live UI.

## Setup

### 1. Install Python
Download from https://python.org (3.10 or above)

### 2. Install MongoDB
Download Community Server from https://www.mongodb.com/try/download/community
Run it and keep it running in background.

### 3. Clone this repo and install dependencies
```
git clone https://github.com/YOUR_USERNAME/webhook-repo
cd webhook-repo
pip install -r requirements.txt
```

### 4. Run the Flask app
```
python app.py
```
App runs at http://localhost:5000

### 5. Expose your local server using ngrok
Download ngrok from https://ngrok.com, then run:
```
ngrok http 5000
```
Copy the https URL it gives you (e.g. https://abc123.ngrok.io)

### 6. Set up GitHub webhook on action-repo
- Go to action-repo → Settings → Webhooks → Add webhook
- Payload URL: https://abc123.ngrok.io/webhook
- Content type: application/json
- Events: select "Pushes" and "Pull requests"
- Save

### 7. Test it
Push something to action-repo and watch the UI at http://localhost:5000
