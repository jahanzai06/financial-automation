import os
from typing import List, Union
from google import genai
from pydantic import BaseModel, Field
from PIL import Image
from config import GEMINI_API_KEY

# Schema definitions matching the specification but with corrected owner names
class TransactionModel(BaseModel):
    date: str = Field(description="Transaction date in YYYY-MM-DD format.")
    amount: float = Field(description="Net numerical currency volume in PKR.")
    source_account: str = Field(
        description="Must map to one of these exact values: 'HBL (Muhammad Jahanzaib)', 'HBL (Sana Kanwal)', 'EasyPaisa', 'JazzCash', or 'Cash'."
    )
    recipient: str = Field(description="Destination target entity or utility account identifier.")
    comment: str = Field(description="Internal reference keys, transaction ID or transaction notes.")

class TransactionListModel(BaseModel):
    transactions: List[TransactionModel] = Field(description="List of parsed financial transactions.")

def execute_ai_multimodal_inference(data_input: Union[Image.Image, str]) -> List[TransactionModel]:
    """
    Passes the image or text block to Gemini 2.5 Flash.
    Returns a list of parsed TransactionModel instances.
    """
    # Initialize the client. By default, the SDK looks for GEMINI_API_KEY in the environment.
    # We can also pass it explicitly if loaded from our config.
    api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please configure it in your .env file.")

    client = genai.Client(api_key=api_key)

    # Detailed system prompt outlining classification rules
    prompt = """
    Analyze the provided financial transaction document, screenshot, or text.
    Extract all transactions present. This could be a single transaction receipt or a list of transactions (like in a monthly statement).
    
    For each transaction, parse:
    1. 'date': The date of transaction (YYYY-MM-DD format). If only month/day or relative terms are used, resolve it against the current context (June 2026).
    2. 'amount': Net numerical volume in PKR.
    3. 'source_account': Must map to one of:
       - 'HBL (Muhammad Jahanzaib)' (Use if HBL is mentioned along with owner Jahanzaib or Janzeb, or if it is the default HBL account)
       - 'HBL (Sana Kanwal)' (Use ONLY if HBL is mentioned and the owner title explicitly identifies 'Sana Kanwal' or 'Sana Gawan')
       - 'EasyPaisa' (Use if EasyPaisa UI, branding, watermark, or transaction header is present)
       - 'JazzCash' (Use if JazzCash brand tags or incoming confirmation string templates are present)
       - 'Cash' (Use if it is an unstructured physical ledger entry, or if no bank-specific metadata or brand references are present)
    4. 'recipient': Destination entity, merchant, or beneficiary name.
    5. 'comment': Contextual notes, Reference ID, Transaction ID, or reason for transaction.
    
    Enforce temperature=0.0 for deterministic parsing.
    """

    contents = []
    if isinstance(data_input, Image.Image):
        contents.append(data_input)
    elif isinstance(data_input, str):
        contents.append(data_input)
    else:
        raise TypeError("Input data must be a PIL Image or a text string.")

    contents.append(prompt)

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=dict(
            response_mime_type="application/json",
            response_schema=TransactionListModel,
            temperature=0.0
        )
    )

    # Parse and validate the response
    parsed_data = TransactionListModel.model_validate_json(response.text)
    return parsed_data.transactions
