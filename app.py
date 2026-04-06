"""
MASTER app.py — Connects All 4 Parts Together
=============================================

This file calls:
  - AI model (predict disease)
  - Telegram Bot (alert family) 
  - Twilio (call ambulance)     
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import pickle, json, numpy as np, os

app = Flask(__name__)
CORS(app)

# ── Load AI model artifacts ──────────────────────────
MODEL_DIR = "model"

def load_artifacts():
    with open(f"{MODEL_DIR}/model.pkl",               "rb") as f: model = pickle.load(f)
    with open(f"{MODEL_DIR}/label_encoder.pkl",       "rb") as f: le = pickle.load(f)
    with open(f"{MODEL_DIR}/feature_cols.json")            as f: feature_cols = json.load(f)
    with open(f"{MODEL_DIR}/disease_doctor_map.json")      as f: ddm = json.load(f)
    with open(f"{MODEL_DIR}/disease_severity_map.json")    as f: dsm = json.load(f)
    return model, le, feature_cols, ddm, dsm

model, le, feature_cols, disease_doctor_map, disease_severity_map = load_artifacts()
print("✅ AI Model loaded!")

# ── Import Telegram & Twilio (optional — works without them) ──
try:
    from telegram_alert import send_alert as telegram_alert
    TELEGRAM_ENABLED = True
    print("✅ Telegram Bot ready!")
except:
    TELEGRAM_ENABLED = False
    print("⚠️  Telegram not configured (Member 3 needs to set up telegram_alert.py)")

try:
    from twilio_call import dispatch_emergency as twilio_dispatch
    TWILIO_ENABLED = True
    print("✅ Twilio ready!")
except:
    TWILIO_ENABLED = False
    print("⚠️  Twilio not configured (Member 4 needs to set up twilio_call.py)")


# ── Routes ───────────────────────────────────────────

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status":   "Medical Emergency API running",
        "telegram": TELEGRAM_ENABLED,
        "twilio":   TWILIO_ENABLED,
        "endpoints": {
            "POST /predict":  "Predict disease + trigger all alerts",
            "GET  /symptoms": "List all valid symptoms",
            "GET  /health":   "Health check"
        }
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":   "ok",
        "model":    "RandomForest",
        "diseases": len(le.classes_),
        "symptoms": len(feature_cols),
        "telegram": TELEGRAM_ENABLED,
        "twilio":   TWILIO_ENABLED
    })

@app.route("/symptoms", methods=["GET"])
def symptoms():
    return jsonify({"total": len(feature_cols), "symptoms": feature_cols})

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data         = request.get_json()
        symptoms_in  = data.get("symptoms", [])
        patient_name = data.get("patient_name", "Unknown")
        patient_age  = data.get("patient_age", "N/A")
        location     = data.get("location", "Not provided")
        location_link= data.get("location_link", None)

        if not symptoms_in:
            return jsonify({"success": False, "error": "Symptoms list is empty"}), 400

        # Build input vector
        input_vec = np.zeros(len(feature_cols))
        matched, unmatched = [], []
        for s in symptoms_in:
            sc = s.strip().lower().replace(" ", "_")
            if sc in feature_cols:
                input_vec[feature_cols.index(sc)] = 1
                matched.append(sc)
            else:
                unmatched.append(s)

        if not matched:
            return jsonify({"success": False, "error": "No symptoms matched. Use GET /symptoms"}), 400

        # AI prediction
        probs      = model.predict_proba([input_vec])[0]
        pred_idx   = np.argmax(probs)
        confidence = round(float(probs[pred_idx]) * 100, 2)
        disease    = le.inverse_transform([pred_idx])[0]
        doctor     = disease_doctor_map.get(disease, "General Physician")
        severity   = disease_severity_map.get(disease, "Medium")

        # Top 3
        top3 = [
            {"disease": le.inverse_transform([i])[0], "confidence": round(float(probs[i]) * 100, 2)}
            for i in np.argsort(probs)[::-1][:3]
        ]

        alert_msg = f"Emergency: {disease} detected in {patient_name} (Age:{patient_age}). Need {doctor}. Severity: {severity}."

        # ── Trigger Telegram alert (Member 3) ──
        telegram_sent = False
        if TELEGRAM_ENABLED:
            telegram_sent = telegram_alert(
                patient_name  = patient_name,
                disease       = disease,
                doctor        = doctor,
                severity      = severity,
                confidence    = confidence,
                location_link = location_link
            )

        # ── Trigger Twilio call (Member 4) ──
        twilio_result = None
        if TWILIO_ENABLED and severity == "Critical":
            twilio_result = twilio_dispatch(
                patient_name  = patient_name,
                disease       = disease,
                severity      = severity,
                location      = location,
                location_link = location_link
            )

        return jsonify({
            "success":             True,
            "patient_name":        patient_name,
            "patient_age":         patient_age,
            "matched_symptoms":    matched,
            "unmatched_symptoms":  unmatched,
            "prediction": {
                "disease":    disease,
                "doctor":     doctor,
                "severity":   severity,
                "confidence": confidence
            },
            "top3_predictions": top3,
            "emergency_alert": {
                "message":        alert_msg,
                "severity_color": {"Critical":"red","Medium":"orange","Low":"green"}.get(severity,"orange")
            },
            "notifications": {
                "telegram_sent": telegram_sent,
                "twilio_called": twilio_result is not None
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── Run ──────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

