"""Flask API for generating and storing advertising copy."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------


@dataclass
class Config:
    """Application configuration."""

    SQLALCHEMY_DATABASE_URI: str = "sqlite:///campaigns.db"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    OPENAI_API_KEY: str | None = None


def create_app() -> Flask:
    """Application factory."""
    load_dotenv()
    config = Config(
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", "sqlite:///campaigns.db"
        ),
        OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
    )
    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app)
    db.init_app(app)

    # Initialize OpenAI client using API v1
    global client
    client = OpenAI(api_key=app.config["OPENAI_API_KEY"])

    with app.app_context():
        db.create_all()
    _register_routes(app)
    return app


# ---------------------------------------------------------------------------
# Database models
# ---------------------------------------------------------------------------

db = SQLAlchemy()
client: OpenAI | None = None


class Campaign(db.Model):
    """Stores a generated campaign."""

    id = db.Column(db.Integer, primary_key=True)
    business = db.Column(db.String(120), nullable=False)
    audience = db.Column(db.String(120), nullable=False)
    goal = db.Column(db.String(120), nullable=False)
    ad_copy = db.Column(db.Text)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _register_routes(app: Flask) -> None:
    @app.get("/")
    def home() -> str:
        return "Flask server running with SQLite and OpenAI v1!"

    @app.post("/generate_ad_copy")
    def generate_ad_copy():
        data = request.get_json(silent=True) or {}
        if not all(key in data for key in ("business", "audience", "goal")):
            return jsonify({"error": "Missing required fields"}), 400

        prompt = (
            f"Write 3 Facebook ad headlines and 2 descriptions for {data['business']} "
            f"targeting {data['audience']} to accomplish {data['goal']}."
        )

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful ad copy generator.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=120,
            )
        except Exception as exc:  # pragma: no cover - network call
            return jsonify({"error": str(exc)}), 500

        ad_copy = response.choices[0].message.content.strip()

        campaign = Campaign(
            business=data["business"],
            audience=data["audience"],
            goal=data["goal"],
            ad_copy=ad_copy,
        )
        db.session.add(campaign)
        db.session.commit()

        return jsonify({"copy": ad_copy})

    @app.get("/campaigns")
    def get_campaigns():
        campaigns = Campaign.query.order_by(Campaign.id.desc()).all()
        return jsonify(
            [
                {
                    "id": camp.id,
                    "business": camp.business,
                    "audience": camp.audience,
                    "goal": camp.goal,
                    "ad_copy": camp.ad_copy,
                }
                for camp in campaigns
            ]
        )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    application = create_app()
    port = int(os.getenv("PORT", 10000))
    application.run(host="0.0.0.0", port=port)
