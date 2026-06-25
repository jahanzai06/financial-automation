import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# Base directory for the app
BASE_DIR = Path(__file__).parent.resolve()

# SQLite Database location
DB_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "ledger.db"))

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Account mapping metadata
ACCOUNTS = {
    "HBL (Muhammad Jahanzaib)": {
        "owner": "Muhammad Jahanzaib",
        "description": "HBL Account for Muhammad Jahanzaib (Default HBL)",
        "fallback_rule": "Matches when 'Jahanzaib' or 'Muhammad' appears alongside HBL metrics. Default HBL option."
    },
    "HBL (Sana Kanwal)": {
        "owner": "Sana Kanwal",
        "description": "HBL Account for Sana Kanwal",
        "fallback_rule": "Triggers only if account title explicitly identifies 'Sana Kanwal'."
    },
    "EasyPaisa": {
        "owner": "User Mobile Node",
        "description": "EasyPaisa Mobile Wallet",
        "fallback_rule": "Triggered by EasyPaisa transaction headers or application-specific watermarks."
    },
    "JazzCash": {
        "owner": "Muhammad Jahanzaib",
        "description": "JazzCash Mobile Wallet",
        "fallback_rule": "Triggered by JazzCash brand tags or incoming confirmation string templates."
    },
    "Cash": {
        "owner": "Physical Ledger",
        "description": "Physical cash ledger",
        "fallback_rule": "Assigned automatically whenever input logs contain no bank-specific metadata or brand references."
    }
}

# Keyboard Hook Configurations
HOTKEYS = {
    "<ctrl>+<alt>+v": "process_clipboard",
    "<ctrl>+<alt>+f": "generate_report"
}
