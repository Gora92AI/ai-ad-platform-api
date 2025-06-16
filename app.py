from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()
app = Flask(__name__)
CORS(app)

# OpenAI client for API v1.x (new syntax)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure SQLite/SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campaigns.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Campaign Model
class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business = db.Column(db.String(120))
    audience = db.Column(db.String(120))
    goal = db.Column(db.String(120))
    ad_copy = db.Column(db.Text)

# Ensure database & table are created
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Flask server running with SQLite and OpenAI v1!"

@app.route('/generate_ad_copy', methods=['POST'])
def generate_ad_copy():
    if request.method != 'POST':
        return jsonify({"error": "Method not allowed, use POST."}), 405

    data = request.json
    if not all (k in data for k in ("business", "audience", "goal")):
        return jsonify({"error": "Missing required fields"}), 400

    prompt = f"Write 3 Facebook ad headlines and 2 descriptions for {data['business']} targeting {data['audience']} to accomplish {data['goal']}."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful ad copy generator."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=120
    )
    ad_copy = response.choices[0].message.content.strip()

    # Save campaign to DB
    campaign = Campaign(
        business=data['business'],
        audience=data['audience'],
        goal=data['goal'],
        ad_copy=ad_copy
    )
    db.session.add(campaign)
    db.session.commit()
    return jsonify({'copy': ad_copy})

@app.route('/campaigns', methods=['GET'])
def get_campaigns():
    campaigns = Campaign.query.order_by(Campaign.id.desc()).all()
    output = []
    for camp in campaigns:
        output.append({
            'id': camp.id,
            'business': camp.business,
            'audience': camp.audience,
            'goal': camp.goal,
            'ad_copy': camp.ad_copy
        })
    return jsonify(output)

if __name__ == "__main__":
    # Use 0.0.0.0 for all interfaces, pick up port from env (Render, Heroku, etc)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    port = int(os.environ.get("PORT", 10000))  # Use the port Render provides, or default to 10000
    app.run(host="0.0.0.0", port=port)