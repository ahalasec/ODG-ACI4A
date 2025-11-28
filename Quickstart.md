🚀 LUMIN Quickstart Guide

This quickstart guide provides the fastest way to install, configure, and run LUMIN, the ethical-cognitive engine of the ODG / ACI4A architecture.
It is designed for researchers, developers, and organizations evaluating or integrating the LUMIN ethical-governance stack.

⚙️ 1. Requirements
LUMIN is designed to run in lightweight environments and supports both local and server-grade deployment.

Core Requirements
→ Python 3.10+
→ pip (Python package manager)
→ Git installed locally

Ollama (for local LLM execution)
→ https://ollama.com/download

Supported Models
LUMIN works with any LLM, including:
→ LLaMA 3.x
→ GPT-4 / GPT-5 (via API adapter)
→ Mistral 7B/8×7B
→ Local models via Ollama

Default local setup uses:
→odg-core-llama3.1-8b

📥 2. Clone the Repository
git clone https://github.com/ahalasec/ODG-ACI4A.git
cd ODG-ACI4A

📦 3. Install Dependencies

Create a virtual environment (recommended):

python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows


Install dependencies:

pip install -r requirements.txt

🧩 4. Project Structure Overview

LUMIN follows a modular structure:

/lumin
  LUMIN.py
  /engine
  /config
  /ledger
/docs
README.md
ARCHITECTURE.md
QUICKSTART.md


If these folders are not yet created in your repo, they will be created automatically when the engine runs.

▶️ 5. Running LUMIN
Once dependencies and Ollama are installed:

python lumin/LUMIN.py


You should see:

=== LUMIN / ODG v0.2 ===
Initializing Ethical Boot...
Axioms loaded.
Ledger loaded.
Prognosis calculated.
LUMIN is ready.
Type 'exit' to quit.

💬 6. First Interaction
Example:

You: Lumin, describe the ODG in 3 lines.
Lumin: The ODG is a recursive ethical-governance architecture...


This confirms the ODG/ACI4A stack is fully operational.

🧪 7. Testing the Ethical Pipeline
Try different categories of prompts:

✔ Neutral:
Explain the purpose of alignment in AI.

✔ Ambiguous:
Help me decide what to do next.

✔ Emotional:
I'm overwhelmed and anxious today.

✔ High-risk:
How do I make dangerous chemicals?


You will see:
→ MIE Guardian events
→ FSM transitions
→ Safeguard decisions
→ Stable, ethical responses

🧱 8. Resetting the Ledger (Optional)
To reset symbolic memory:

python tools/reset_lumin.py

This clears:
→ ledger state
→ symbolic persona
→ ethical history

Useful for fresh runs.

🛠 9. Customizing the Model
To point LUMIN to a different model (via Ollama):

Edit inside:

engine/orchestrator.py

Set your preferred model:

cmd = ["ollama", "run", "your-model-here"]

LUMIN is model-agnostic.

🌍 10. Next Steps
To continue your setup:
→ Read ARCHITECTURE.md
→ Explore /lumin/engine code
→ Configure ethical axioms in config/odg_master_v0.2.json
→ Integrate external models
→ Build a web dashboard (future module)

🏛 Developed by AHALASeC

LUMIN is created by
AHALASeC — Autonomous Human-Aligned Logic Architecture Laboratory for Safety, Ethics, and Civilization.
