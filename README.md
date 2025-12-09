# AI Sports Injury Tracking and Prevention System

This project is an AI-driven athlete monitoring platform designed to identify injury risk using session metrics such as heart rate, sleep duration, calories burned, steps, intensity, and strain. It blends machine learning predictions with sports science principle—specifically the _Acute:Chronic Workload Ratio (ACWR)_—to provide personalized injury prevention recommendations.

---

## Purpose

Athletes often get injured not just from one intense workout but from load spikes over time. This system was created to:

- Monitor athlete workload trends
- Measure fatigue and strain levels
- Predict injury likelihood before it happens
- Offer actionable, science-backed prevention guidance

---

## Key Features

| Feature                    | Description                                                        |
| -------------------------- | ------------------------------------------------------------------ |
| ML Injury Prediction       | Produces a risk percentage using a trained TensorFlow model        |
| ACWR Workload Tracking     | Detects unsafe spikes in training load using recent sessions       |
| Strain & Intensity Metrics | Converts raw data into meaningful physiological load indicators    |
| Recommendations Engine     | Advises athletes when to rest, reduce volume, or continue training |
| Dashboard UI               | Built in Streamlit for easy interpretation and demonstration       |
| REST API                   | Django-based backend powering prediction endpoints                 |

---

## System Architecture

Streamlit Frontend (dashboard.py)
|
v
Django REST API (tracker app)
|
v
ML Model (predict_injury)
|
v
SQLite Database (Athlete, Sessions, Predictions)

---

## Technology Stack

| Layer      | Technology               |
| ---------- | ------------------------ |
| Frontend   | Streamlit                |
| Backend    | Django REST Framework    |
| ML         | TensorFlow / Keras       |
| DB         | SQLite                   |
| Deployment | GitHub + Local execution |

---

## Core Performance Metrics

### **Intensity**

Measures how _hard_ a session felt.

Derived using:
calories burned + heart rate + steps = effort score

### **Strain**

Measures the _overall load_ placed on the body:
strain = intensity × duration

---

## ACWR – Athlete Workload Safety Layer

The Acute:Chronic Workload Ratio compares recent training load to longer-term load:

acute load = average strain of last 3 sessions
chronic load = average strain of last 7 sessions
ACWR = acute / chronic

**Interpretation**:

| ACWR Value | Meaning       | Risk   |
| ---------- | ------------- | ------ |
| < 0.8      | Underprepared | Medium |
| 0.8 – 1.3  | Optimal zone  | Low    |
| > 1.5      | Load spike    | High   |

> Even if the ML model predicts a low risk, ACWR may warn the athlete to reduce workload due to dangerous spikes — this provides context the ML model alone can’t infer.

---

## Why ACWR Matters

Machine learning analyzes patterns from a single session.  
ACWR ensures we don't miss the _bigger picture_.

Without ACWR, an athlete could:

- Have great sleep
- Low heart rate
- Good recovery

…but still be at high injury risk because they spiked workload yesterday.

ACWR prevents hidden danger.

---

## Future Enhancements

Integrate ACWR directly as an ML feature  
 Add wearable device support (Garmin / Fitbit / WHOOP)  
 Deploy to a cloud server  
 Track team-based comparisons

---

## Setup Instructions

```bash
git clone https://github.com/DiegoSoto16/AI-Sports-injury-tracker
cd ai_sports_injury_prevention
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver     # start backend
streamlit run dashboard.py     # run UI
when running and prompted to login screen, use "mia thompson"
```
