# 🔬 Scholar AI — Research Assistant

An intelligent, conversational AI agent built for students and researchers.
Powered by **Groq's ultra-fast inference** + **LLaMA 3.3 70B**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔬 Research Mode | Deep-dive research on any topic with academic rigour |
| 💡 Explain Mode | Feynman-style explanations with analogies |
| 📝 Quiz Me Mode | Auto-generated quizzes with scoring & feedback |
| 📋 Summarize Mode | Structured academic summaries |
| ⚖️ Critique Mode | Balanced, evidence-based analysis |
| 🧠 Smart Tool Router | Auto-detects math, code, paper, analogy tasks |
| 💬 Memory | Maintains conversation context across turns |
| ⚡ Ultra-fast | Groq's LPU delivers near-instant responses |

---

## 🚀 Quick Start

### 1. Clone / Download the project
```bash
git clone <your-repo>
cd research_agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a Groq API Key (FREE)
- Visit https://console.groq.com
- Sign up and create an API key (it's free!)
- Copy the key (starts with `gsk_`)

### 4. Run the app
```bash
streamlit run app.py
```

### 5. Paste your Groq API key in the sidebar → Start asking!

---

## 🏗️ Project Structure

```
research_agent/
├── app.py                  # Main Streamlit UI
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── utils/
    ├── __init__.py
    ├── agent.py            # Core AI agent (Groq integration)
    ├── memory.py           # Conversation memory management
    └── tools.py            # Tool router (8 specialized tools)
```

---

## 🤖 Agent Architecture

```
User Input
    │
    ▼
┌─────────────┐
│ Tool Router │  ← Detects: math / code / quiz / paper / explain…
└──────┬──────┘
       │ tool context
       ▼
┌─────────────────────┐
│  Mode System Prompt │  ← Research / Explain / Quiz / Summarize / Critique
└──────┬──────────────┘
       │
       ▼
┌─────────────────┐
│ Conversation    │  ← Sliding window memory (last 8 turns)
│ Memory          │
└──────┬──────────┘
       │
       ▼
┌─────────────────────────────┐
│  Groq API  (LLaMA 3.3 70B)  │  ← Ultra-fast inference
└──────┬──────────────────────┘
       │
       ▼
   Response
```

---

## 💡 Example Use Cases

- **"Explain attention mechanisms like I'm a beginner"** → Explain mode + Analogy Builder
- **"Quiz me on Bayesian statistics"** → Quiz Me mode + Quiz Generator
- **"What are the limitations of transformer models?"** → Critique mode + Debate Analyzer
- **"Summarize the key ideas behind RLHF"** → Summarize mode + Paper Summarizer
- **"Solve: P(A|B) = P(B|A) * P(A) / P(B)"** → Research mode + Math Helper

---

## 🛠️ Built With

- **[Streamlit](https://streamlit.io)** — Web UI framework
- **[Groq](https://groq.com)** — Ultra-fast LLM inference (LPU)
- **LLaMA 3.3 70B** — State-of-the-art open-source LLM
- **Python 3.10+**

---

## 📄 License
MIT — Free to use, modify, and build upon.
