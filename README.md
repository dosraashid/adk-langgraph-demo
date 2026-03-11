# 🤖 DigitalOcean ADK + LangGraph: DevOps Agent Demo

This repository is a production-ready, dual-purpose template demonstrating the "Golden Path" for building stateful, tool-enabled AI agents. It integrates **LangGraph** orchestration with **DigitalOcean Serverless Inference** and uses the **Gradient ADK** for seamless local testing and cloud deployment.

---

## 🌟 Key Capabilities
* **LangGraph Orchestration**: Handles multi-step reasoning (e.g., finding a user, then checking their assigned servers).
* **Managed Persistence**: Uses LangGraph Checkpointers to remember conversation history and isolate sessions via `thread_id`.
* **Standardized Tools**: Implements `ToolNode` with an interconnected mock database for User and Server management.
* **Serverless Intelligence**: Securely connects to DigitalOcean's hosted Llama 3.3 models—no local GPU required.

---

## 🛠️ Initial Setup

### 1. Installation
Clone the repository and set up your Python environment:
```bash
git clone <your-repo-url>
cd adk-langgraph-demo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials
Create a `.env` file in the root directory and add your DigitalOcean Model Access Key:
```bash
GRADIENT_MODEL_ACCESS_KEY="your_model_access_key_here"
```

---

## 🚀 Choose Your Path

This template is designed to work perfectly in two different environments without changing any code.

### Option 1: Run Locally (Fast Testing)
Keep the agent logic on your local machine while using DigitalOcean Serverless GPUs for the AI "brain."

**1. Start the server:**
```bash
gradient agent run
```

**2. Test the "Golden Path" (in a new terminal):**
*Step A: Multi-step reasoning (Find user -> Check servers)*
```bash
curl -X POST http://localhost:8080/run \
-H "Content-Type: application/json" \
-d '{"prompt": "Hi, I am alice@dev.com. Are any of my servers failing?", "thread_id": "demo-1"}'
```

*Step B: Action & Persistence (Fix the issue)*
```bash
curl -X POST http://localhost:8080/run \
-H "Content-Type: application/json" \
-d '{"prompt": "Please restart the failing one.", "thread_id": "demo-1"}'
```

### Option 2: Deploy to Cloud (Production)
Push your agent to the DigitalOcean Cloud Panel for 24/7 access, automatic scaling, and built-in observability.

**1. Export your Personal Access Token:**
*(This token requires Read/Write API permissions from your DO Dashboard)*
```bash
export DIGITALOCEAN_API_TOKEN="dop_v1_your_personal_token_here"
```

**2. Deploy the agent:**
```bash
gradient agent deploy
```

**3. Monitor & Manage:**
Once deployed, your agent will be live and accessible via a public endpoint. You can view logs, execution traces, and manage API keys in the **GenAI > Agents** section of your DigitalOcean Console.
