import sys
import os
import threading
import time
import logging
import uvicorn

import config
import database
import clipboard_extractor
import gemini_parser
import reporter
import pyperclip
from web_ui import app

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("main")

def on_process_clipboard():
    logger.info("Hotkey [Ctrl+Alt+V] pressed: Triggering clipboard extraction...")
    try:
        # Extract clipboard image or text
        data = clipboard_extractor.extract_clipboard_data()
        if data is None:
            logger.warning("No image or text found on clipboard.")
            return
            
        logger.info("Executing Gemini AI structured analysis...")
        txs = gemini_parser.execute_ai_multimodal_inference(data)
        if not txs:
            logger.warning("Gemini failed to extract any transactions.")
            return
            
        logger.info(f"Successfully extracted {len(txs)} transactions from clipboard.")
        
        # Convert models to database schema dictionary
        tx_dicts = []
        for tx in txs:
            tx_dicts.append({
                "date": tx.date,
                "amount": tx.amount,
                "source_account": tx.source_account,
                "recipient_or_use": tx.recipient,
                "comment": tx.comment
            })
            
        # Insert to SQLite
        ids = database.add_transactions(tx_dicts)
        logger.info(f"Committed transactions to database with IDs: {ids}")
        
    except Exception as e:
        logger.error(f"Error processing clipboard extraction: {e}", exc_info=True)

def on_generate_report():
    logger.info("Hotkey [Ctrl+Alt+F] pressed: Generating monthly report...")
    try:
        # Generate report for current month
        current_month = time.strftime("%Y-%m")
        report_text = reporter.generate_monthly_report(current_month)
        
        # Copy to clipboard
        pyperclip.copy(report_text)
        logger.info("Monthly statement report copied to clipboard successfully!")
        
    except Exception as e:
        logger.error(f"Error generating statement report: {e}", exc_info=True)

def start_keyboard_listener():
    """Initializes the pynput keyboard hook listener."""
    logger.info("Starting keyboard hotkey hooks listener thread...")
    try:
        from pynput import keyboard
        hotkey_map = {
            '<ctrl>+<alt>+v': on_process_clipboard,
            '<ctrl>+<alt>+f': on_generate_report
        }
        
        # GlobalHotKeys is blocking, so this will keep running in this background thread
        with keyboard.GlobalHotKeys(hotkey_map) as listener:
            listener.join()
    except Exception as e:
        logger.warning(f"Global key hook listener could not start (this is expected in headless/cloud environments): {e}")

def main():
    logger.info("=== Starting AI Financial Automation System ===")
    
    # Initialize DB schema
    logger.info("Initializing SQLite database...")
    database.init_db()
    
    # Check for Gemini API key
    if not config.GEMINI_API_KEY:
        logger.warning("WARNING: GEMINI_API_KEY environment variable is not set. API calls will fail until configured.")
    
    # Start keyboard listener in background thread
    listener_thread = threading.Thread(target=start_keyboard_listener, name="KeyboardListener", daemon=True)
    listener_thread.start()
    
    # Start Web UI Server (FastAPI)
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Web UI server at http://0.0.0.0:{port} ...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except KeyboardInterrupt:
        logger.info("Web server stopped by user.")
    except Exception as e:
        logger.error(f"Error starting web server: {e}", exc_info=True)

if __name__ == "__main__":
    main()
