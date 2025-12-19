# Pair Code Lookup (Flask)

This app looks up a config by email and phone in Supabase, extracts a token, calls an external route, and shows the returned `paircode`.

## Setup

1. Create a virtualenv and install dependencies:
   
   ```bash
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create `.env` based on `.env.example` and fill in values.

3. Run the app:

   ```bash
   python app.py
   ```

Open `http://localhost:5000`.
