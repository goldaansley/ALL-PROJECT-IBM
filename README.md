# 🌿 NutriBot — AI-Powered Nutrition Agent

> Personalized nutrition planning powered by **IBM Watsonx Granite** + **Flask**  
> Indian diet expertise · Family profiles · BMI calculator · Dark mode · Fully responsive

---

## 📁 Project Structure

```
nutrition-agent/
├── app.py                    ← Flask backend + all API routes
├── agent_instructions.py     ← ⭐ Customize agent behavior HERE
├── requirements.txt
├── .env.example              ← Copy to .env and fill credentials
├── templates/
│   └── index.html            ← Full frontend (Bootstrap 5)
├── static/
│   ├── css/style.css         ← Custom styles + dark mode
│   └── js/app.js             ← Frontend logic (vanilla JS)
└── README.md
```

---

## ⚡ Quick Start (5 Steps)

### 1. Clone / Copy the Project

```bash
cd nutrition-agent
```

### 2. Create a Python Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure IBM Watsonx Credentials

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` with your credentials:

```env
IBM_API_KEY=your_ibm_cloud_api_key_here
IBM_PROJECT_ID=your_watsonx_project_id_here
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
FLASK_SECRET_KEY=change-this-to-a-random-string
```

**Where to get credentials:**
- IBM Cloud API Key → [IBM Cloud Console](https://cloud.ibm.com/iam/apikeys) → IAM → API Keys → Create
- Project ID → [IBM Watsonx.ai](https://dataplatform.cloud.ibm.com) → Your Project → Manage → Project ID

### 5. Run the App

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🎛️ Customizing Agent Behavior (`agent_instructions.py`)

The `AGENT_INSTRUCTIONS` dictionary is your control panel. Edit it freely:

| Section | What to Change |
|---|---|
| `persona` | Agent name, tone, personality style |
| `specializations` | Add/remove diet specializations |
| `indian_food_preferences` | Regional cuisine, preferred foods, foods to avoid |
| `response_format` | How answers are structured |
| `safety_rules` | Medical disclaimers, calorie limits, restrictions |
| `family_profile_rules` | How family recommendations are generated |
| `language_rules` | Units, language, localization |
| `greeting` | First message users see |
| `model_params` | Granite model ID, temperature, token limits |

**Example — switch to Keto diet focus:**
```python
"specializations": [
    "Ketogenic diet planning",
    "Low-carb Indian alternatives",
    ...
],
"indian_food_preferences": {
    "preferred_grains": ["none — keto avoids grains"],
    "preferred_proteins": ["paneer", "eggs", "chicken", "fish", "mutton"],
    ...
}
```

**Example — change Granite model:**
```python
"model_params": {
    "model_id": "ibm/granite-13b-instruct-v2",  # switch model here
    "max_new_tokens": 1500,
    "temperature": 0.5,
    ...
}
```

---

## 🖥️ Features

| Feature | Description |
|---|---|
| 💬 **AI Chat** | Conversational nutrition Q&A with session memory |
| 📊 **Nutrition Dashboard** | Calorie & macro targets, donut chart, meal analyzer |
| 🍽️ **Meal Planner** | 1–7 day Indian meal plans (goal + diet type + calories) |
| ⚖️ **BMI Calculator** | BMI + TDEE using Mifflin-St Jeor formula, animated scale |
| 👨‍👩‍👧 **Family Profiles** | Add family members, get individualized recommendations |
| 🌙 **Dark Mode** | Persistent dark/light theme toggle |
| 📱 **Mobile Responsive** | Works on all screen sizes |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET  | `/` | Main web UI |
| POST | `/api/chat` | Chat with NutriBot |
| POST | `/api/bmi` | Calculate BMI + TDEE |
| POST | `/api/meal-plan` | Generate meal plan |
| POST | `/api/analyze-meal` | Analyze meal nutrition |
| POST | `/api/family-profile` | Family nutrition plan |
| POST | `/api/set-context` | Save user profile to session |
| POST | `/api/clear-session` | Clear conversation history |
| GET  | `/api/health` | Server + model health check |

**Example — chat API:**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a 3-day weight loss meal plan for a 30-year-old vegetarian"}'
```

---

## 🚀 Deployment Options

### Option A — Gunicorn (Linux/Mac Production)

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app --timeout 120
```

### Option B — Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app", "--timeout", "120"]
```

```bash
docker build -t nutribot .
docker run -p 5000:5000 --env-file .env nutribot
```

### Option C — IBM Cloud Code Engine

```bash
# Install IBM Cloud CLI + Code Engine plugin first
ibmcloud login
ibmcloud ce project create --name nutribot-project
ibmcloud ce application create \
  --name nutribot \
  --image your-registry/nutribot:latest \
  --port 5000 \
  --env-from-secret nutribot-secrets
```

### Option D — Railway / Render / Fly.io

1. Push code to GitHub
2. Connect repo to Railway/Render
3. Set environment variables in dashboard
4. Deploy — these platforms auto-detect Flask/Gunicorn

---

## 🔒 Security Notes

- `.env` is in `.gitignore` — **never commit API keys**
- Session data is server-side (Flask sessions)
- All user inputs are sanitized before rendering
- Medical disclaimers are enforced by `safety_rules` in agent instructions

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `Watsonx model not ready` | Check `IBM_API_KEY` and `IBM_PROJECT_ID` in `.env` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in your venv |
| `Port already in use` | Change `APP_PORT=5001` in `.env` |
| Slow responses | Reduce `max_new_tokens` in `agent_instructions.py` |
| Wrong region | Change `IBM_WATSONX_URL` to your IBM Cloud region URL |

**IBM Watsonx Region URLs:**
```
US South:  https://us-south.ml.cloud.ibm.com
EU DE:     https://eu-de.ml.cloud.ibm.com
EU GB:     https://eu-gb.ml.cloud.ibm.com
AP North:  https://jp-tok.ml.cloud.ibm.com
```

---

## 📦 Dependencies

```
flask==3.0.3           — Web framework
flask-cors==4.0.1      — Cross-origin resource sharing
python-dotenv==1.0.1   — .env file loading
ibm-watsonx-ai==1.1.2  — IBM Watsonx AI SDK
requests==2.32.3       — HTTP client
gunicorn==22.0.0       — Production WSGI server
```

Frontend (CDN, no install needed):
- Bootstrap 5.3.3
- Bootstrap Icons 1.11.3

---

## 📝 License

MIT — Free to use, modify, and deploy.

---

*Made with ❤️ using IBM Watsonx Granite + Flask*
