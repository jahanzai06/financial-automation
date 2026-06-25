import os
import shutil
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import database
import gemini_parser
import clipboard_extractor
import reporter
from PIL import Image
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Financial Automation System", description="A premium dashboard for multi-account ledger engine")

# Ensure static and templates directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize SQLite database
database.init_db()

# Pydantic schemas for API requests
class TransactionCreate(BaseModel):
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    amount: float = Field(..., description="Transaction amount in PKR")
    source_account: str = Field(..., description="Source account identifier")
    recipient_or_use: Optional[str] = Field(None, description="Recipient or target entity")
    comment: Optional[str] = Field(None, description="Additional comment or transaction ID")

class TransactionUpdate(BaseModel):
    date: Optional[str] = None
    amount: Optional[float] = None
    source_account: Optional[str] = None
    recipient_or_use: Optional[str] = None
    comment: Optional[str] = None

class ManualTextParseRequest(BaseModel):
    text: str = Field(..., description="Paste text of the receipt or statement here")

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/transactions")
async def get_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account: Optional[str] = None,
    search: Optional[str] = None
):
    """Retrieves filtered list of transactions."""
    try:
        txs = database.get_transactions(
            start_date=start_date,
            end_date=end_date,
            source_account=account,
            search=search
        )
        return txs
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transactions")
async def create_transaction(tx: TransactionCreate):
    """Manually creates a transaction."""
    try:
        tx_id = database.add_transaction(
            date=tx.date,
            amount=tx.amount,
            source_account=tx.source_account,
            recipient_or_use=tx.recipient_or_use or "",
            comment=tx.comment or ""
        )
        return {"success": True, "id": tx_id, "message": "Transaction created successfully"}
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/transactions/{tx_id}")
async def update_transaction(tx_id: int, tx: TransactionUpdate):
    """Updates an existing transaction."""
    try:
        updates = tx.model_dump(exclude_unset=True)
        success = database.update_transaction(tx_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found or no changes made")
        return {"success": True, "message": "Transaction updated successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/transactions/{tx_id}")
async def delete_transaction(tx_id: int):
    """Deletes a transaction by ID."""
    try:
        success = database.delete_transaction(tx_id)
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {"success": True, "message": "Transaction deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_statistics():
    """Retrieves analytics and summary metrics."""
    try:
        stats = database.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error compiling stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parse-clipboard")
async def parse_clipboard():
    """Triggers the clipboard buffer parser and returns the extracted transactions."""
    try:
        clipboard_data = clipboard_extractor.extract_clipboard_data()
        if clipboard_data is None:
            return {"success": False, "message": "No image or text data found in clipboard."}
            
        parsed_txs = gemini_parser.execute_ai_multimodal_inference(clipboard_data)
        if not parsed_txs:
            return {"success": False, "message": "Gemini could not identify any transaction in the clipboard."}
            
        # Convert models to dicts and return
        results = []
        for tx in parsed_txs:
            results.append({
                "date": tx.date,
                "amount": tx.amount,
                "source_account": tx.source_account,
                "recipient_or_use": tx.recipient,
                "comment": tx.comment
            })
            
        return {"success": True, "data": results}
    except Exception as e:
        logger.error(f"Error parsing clipboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-receipt")
async def upload_receipt(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    """
    Accepts a receipt image file or pasted text, parses it via Gemini, 
    and returns the structured data for review.
    """
    try:
        data_input = None
        
        if file:
            # Read image file
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            data_input = image
            logger.info(f"Received file upload: {file.filename}")
        elif text:
            data_input = text
            logger.info("Received manual text input.")
        else:
            raise HTTPException(status_code=400, detail="Either a file upload or text is required.")
            
        parsed_txs = gemini_parser.execute_ai_multimodal_inference(data_input)
        
        results = []
        for tx in parsed_txs:
            results.append({
                "date": tx.date,
                "amount": tx.amount,
                "source_account": tx.source_account,
                "recipient_or_use": tx.recipient,
                "comment": tx.comment
            })
            
        return {"success": True, "data": results}
    except Exception as e:
        logger.error(f"Error parsing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commit-parsed")
async def commit_parsed_transactions(transactions: List[TransactionCreate]):
    """Commits a list of parsed transactions to the SQLite database."""
    try:
        tx_dicts = [tx.model_dump() for tx in transactions]
        ids = database.add_transactions(tx_dicts)
        return {"success": True, "ids": ids, "message": f"Successfully saved {len(ids)} transactions."}
    except Exception as e:
        logger.error(f"Error committing parsed transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report")
async def get_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    report_type: str = "custom"
):
    """Generates the shareable markdown statement report."""
    try:
        report_text = reporter.generate_text_report(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type
        )
        return {"success": True, "report": report_text}
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
