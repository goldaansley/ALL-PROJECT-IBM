"""
=============================================================
  NutriBot — AI-Powered Nutrition Agent
  Backend: Flask + IBM Watsonx.ai (Granite)
=============================================================
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from agent_instructions import AGENT_INSTRUCTIONS

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv()

# ── Flask setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "nutribot-secret-2024")
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── IBM Watsonx.ai setup ──────────────────────────────────────────────────────
IBM_API_KEY    = os.getenv("IBM_API_KEY")
IBM_PROJECT_ID = os.getenv("IBM_PROJECT_ID")
IBM_URL        = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

_watsonx_model: ModelInference | None = None


def get_watsonx_model() -> ModelInference | None:
    """Lazily initialise the Watsonx Granite model client."""
    global _watsonx_model
    if _watsonx_model is not None:
        return _watsonx_model

    if not IBM_API_KEY or not IBM_PROJECT_ID:
        logger.error("IBM_API_KEY or IBM_PROJECT_ID not set in .env")
        return None

    try:
        params = AGENT_INSTRUCTIONS["model_params"]
        credentials = Credentials(api_key=IBM_API_KEY, url=IBM_URL)
        client = APIClient(credentials=credentials, project_id=IBM_PROJECT_ID)
        _watsonx_model = ModelInference(
            model_id=params["model_id"],
            api_client=client,
            project_id=IBM_PROJECT_ID,
            params={
                "max_new_tokens":    params["max_new_tokens"],
                "temperature":       params["temperature"],
                "top_p":             params["top_p"],
                "top_k":             params["top_k"],
                "repetition_penalty": params["repetition_penalty"],
                "decoding_method":   params["decoding_method"],
            },
        )
        logger.info("Watsonx Granite model initialised ✓")
        return _watsonx_model
    except Exception as exc:
        logger.error("Failed to initialise Watsonx model: %s", exc)
        return None


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_system_prompt(user_context: dict | None = None) -> str:
    """Assemble the full system prompt from AGENT_INSTRUCTIONS."""
    inst = AGENT_INSTRUCTIONS
    ctx_block = ""

    if user_context:
        ctx_block = "\n\n=== ACTIVE USER CONTEXT ===\n"
        if user_context.get("name"):
            ctx_block += f"Name: {user_context['name']}\n"
        if user_context.get("age"):
            ctx_block += f"Age: {user_context['age']} years\n"
        if user_context.get("gender"):
            ctx_block += f"Gender: {user_context['gender']}\n"
        if user_context.get("weight"):
            ctx_block += f"Weight: {user_context['weight']} kg\n"
        if user_context.get("height"):
            ctx_block += f"Height: {user_context['height']} cm\n"
        if user_context.get("goal"):
            ctx_block += f"Health Goal: {user_context['goal']}\n"
        if user_context.get("diet_type"):
            ctx_block += f"Diet Preference: {user_context['diet_type']}\n"
        if user_context.get("health_conditions"):
            ctx_block += f"Health Conditions: {user_context['health_conditions']}\n"
        if user_context.get("activity_level"):
            ctx_block += f"Activity Level: {user_context['activity_level']}\n"

    safety = "\n".join(f"- {r}" for r in inst["safety_rules"])
    specs   = "\n".join(f"- {s}" for s in inst["specializations"])
    prefs   = inst["indian_food_preferences"]
    pref_block = (
        f"Preferred Grains: {', '.join(prefs['preferred_grains'])}\n"
        f"Preferred Proteins: {', '.join(prefs['preferred_proteins'])}\n"
        f"Preferred Vegetables: {', '.join(prefs['preferred_vegetables'])}\n"
        f"Preferred Fruits: {', '.join(prefs['preferred_fruits'])}\n"
        f"Healthy Snacks: {', '.join(prefs['healthy_snacks'])}\n"
        f"Spices to Highlight: {', '.join(prefs['spices_to_highlight'])}\n"
        f"Foods to Limit: {', '.join(prefs['foods_to_limit'])}"
    )

    return f"""=== PERSONA ===
{inst['persona']}

=== SPECIALIZATIONS ===
{specs}

=== INDIAN FOOD PREFERENCES ===
{pref_block}

=== RESPONSE FORMAT ===
{inst['response_format']}

=== SAFETY RULES ===
{safety}

=== FAMILY PROFILE RULES ===
{inst['family_profile_rules']}

=== LANGUAGE RULES ===
{inst['language_rules']}
{ctx_block}"""


def query_granite(user_message: str, conversation_history: list, user_context: dict | None = None) -> str:
    """Send a message to Granite and return the response text."""
    model = get_watsonx_model()

    if model is None:
        return (
            "⚠️ IBM Watsonx.ai is not configured yet. "
            "Please add your IBM_API_KEY and IBM_PROJECT_ID to the .env file and restart the server."
        )

    system_prompt = build_system_prompt(user_context)

    # Build conversation string
    history_str = ""
    for turn in conversation_history[-8:]:          # last 8 turns to stay within token budget
        role  = "User" if turn["role"] == "user" else "NutriBot"
        history_str += f"{role}: {turn['content']}\n"

    full_prompt = (
        f"<|system|>\n{system_prompt}\n<|end|>\n"
        f"{history_str}"
        f"User: {user_message}\n"
        f"NutriBot:"
    )

    try:
        response = model.generate_text(prompt=full_prompt)
        return response.strip() if response else AGENT_INSTRUCTIONS["fallback"]
    except Exception as exc:
        logger.error("Watsonx generation error: %s", exc)
        return f"I'm experiencing a technical issue. Please try again in a moment. (Error: {exc})"


# ── Utility: BMI & Calorie calculators ────────────────────────────────────────

def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if   bmi < 16.0:   category, color = "Severe Underweight", "danger"
    elif bmi < 18.5:   category, color = "Underweight",        "warning"
    elif bmi < 25.0:   category, color = "Normal Weight",      "success"
    elif bmi < 30.0:   category, color = "Overweight",         "warning"
    elif bmi < 35.0:   category, color = "Obese Class I",      "danger"
    elif bmi < 40.0:   category, color = "Obese Class II",     "danger"
    else:              category, color = "Obese Class III",     "danger"

    ideal_min = round(18.5 * height_m ** 2, 1)
    ideal_max = round(24.9 * height_m ** 2, 1)

    return {
        "bmi":      round(bmi, 1),
        "category": category,
        "color":    color,
        "ideal_min": ideal_min,
        "ideal_max": ideal_max,
    }


def calculate_tdee(weight_kg: float, height_cm: float, age: int, gender: str, activity: str) -> dict:
    """Mifflin-St Jeor BMR → TDEE."""
    if gender.lower() in ("male", "m"):
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    multipliers = {
        "sedentary":    1.2,
        "light":        1.375,
        "moderate":     1.55,
        "active":       1.725,
        "very_active":  1.9,
    }
    factor = multipliers.get(activity.lower(), 1.55)
    tdee   = bmr * factor

    return {
        "bmr":           round(bmr),
        "tdee":          round(tdee),
        "weight_loss":   round(tdee - 500),
        "weight_gain":   round(tdee + 300),
        "maintenance":   round(tdee),
        "protein_g":     round(weight_kg * 1.6),
        "carbs_g":       round((tdee * 0.45) / 4),
        "fat_g":         round((tdee * 0.30) / 9),
    }


# ── Flask routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", greeting=AGENT_INSTRUCTIONS["greeting"])


@app.route("/api/chat", methods=["POST"])
def chat():
    data    = request.get_json(force=True)
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Retrieve / update session conversation history
    history = session.get("conversation_history", [])
    user_context = session.get("user_context", {})

    # Optionally update context from payload
    if data.get("user_context"):
        user_context.update(data["user_context"])
        session["user_context"] = user_context

    reply = query_granite(message, history, user_context)

    # Persist conversation
    history.append({"role": "user",      "content": message, "timestamp": datetime.now().isoformat()})
    history.append({"role": "assistant", "content": reply,   "timestamp": datetime.now().isoformat()})
    session["conversation_history"] = history[-30:]   # keep last 30 messages

    return jsonify({"reply": reply, "timestamp": datetime.now().strftime("%H:%M")})


@app.route("/api/bmi", methods=["POST"])
def bmi_api():
    data = request.get_json(force=True)
    try:
        weight = float(data["weight"])
        height = float(data["height"])
        result = calculate_bmi(weight, height)

        # Also get TDEE if full data is provided
        if all(k in data for k in ("age", "gender", "activity")):
            result["tdee"] = calculate_tdee(weight, height, int(data["age"]), data["gender"], data["activity"])

        return jsonify(result)
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/meal-plan", methods=["POST"])
def meal_plan():
    data = request.get_json(force=True)
    goal       = data.get("goal", "balanced nutrition")
    days       = min(int(data.get("days", 7)), 7)
    diet_type  = data.get("diet_type", "vegetarian")
    calories   = data.get("calories", 2000)
    conditions = data.get("health_conditions", "none")

    prompt = (
        f"Create a detailed {days}-day Indian {diet_type} meal plan for someone with the goal of '{goal}'. "
        f"Target daily calories: {calories} kcal. Health conditions: {conditions}. "
        f"Include Breakfast, Mid-Morning Snack, Lunch, Evening Snack, and Dinner for each day. "
        f"Use traditional Indian foods. Provide approximate calories for each meal. "
        f"Format each day clearly as 'Day 1:', 'Day 2:', etc."
    )

    history      = session.get("conversation_history", [])
    user_context = session.get("user_context", {})
    plan_text    = query_granite(prompt, history, user_context)

    return jsonify({"plan": plan_text, "days": days, "goal": goal})


@app.route("/api/family-profile", methods=["POST"])
def family_profile():
    data    = request.get_json(force=True)
    members = data.get("members", [])
    if not members:
        return jsonify({"error": "No family members provided"}), 400

    members_text = "\n".join(
        f"- {m.get('name','Member')}: Age {m.get('age','?')}, "
        f"Gender {m.get('gender','?')}, Weight {m.get('weight','?')}kg, "
        f"Goal: {m.get('goal','healthy eating')}, "
        f"Conditions: {m.get('conditions','none')}"
        for m in members
    )

    prompt = (
        f"Create personalized nutrition recommendations for this family:\n{members_text}\n\n"
        f"For each member, provide:\n"
        f"1. Daily calorie target\n"
        f"2. Key nutrients to focus on\n"
        f"3. Sample one-day Indian meal plan\n"
        f"4. One common healthy family dinner recipe that can be adapted for everyone.\n"
        f"Flag any special dietary considerations per member."
    )

    history = session.get("conversation_history", [])
    result  = query_granite(prompt, history)

    return jsonify({"recommendations": result, "member_count": len(members)})


@app.route("/api/analyze-meal", methods=["POST"])
def analyze_meal():
    data  = request.get_json(force=True)
    meal  = data.get("meal", "").strip()
    if not meal:
        return jsonify({"error": "Meal description required"}), 400

    prompt = (
        f"Analyze the nutritional content of this meal: '{meal}'. "
        f"Provide: estimated calories, protein (g), carbohydrates (g), fat (g), fiber (g), "
        f"key vitamins and minerals, healthiness score out of 10, and 2–3 suggestions to make it healthier. "
        f"Present data in a clean structured format."
    )

    history = session.get("conversation_history", [])
    result  = query_granite(prompt, history)

    return jsonify({"analysis": result, "meal": meal})


@app.route("/api/clear-session", methods=["POST"])
def clear_session():
    session.clear()
    return jsonify({"status": "Session cleared"})


@app.route("/api/set-context", methods=["POST"])
def set_context():
    data = request.get_json(force=True)
    session["user_context"] = data
    return jsonify({"status": "Context saved", "context": data})


@app.route("/api/health")
def health_check():
    model_ready = _watsonx_model is not None
    return jsonify({
        "status":      "healthy",
        "model_ready": model_ready,
        "model_id":    AGENT_INSTRUCTIONS["model_params"]["model_id"],
        "timestamp":   datetime.now().isoformat(),
    })


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.getenv("APP_PORT", 5000))
    host  = os.getenv("APP_HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    logger.info("🌿 NutriBot starting on http://%s:%s", host, port)
    app.run(host=host, port=port, debug=debug)
