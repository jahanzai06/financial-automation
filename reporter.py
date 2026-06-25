from datetime import datetime
from typing import List, Dict, Any, Optional
import database

def format_currency(value: float) -> str:
    """Formats float value as standard currency string, e.g., 4,500.00"""
    return f"{value:,.2f}"

def format_report_title(report_type: str, period: str) -> str:
    """Creates a standardized report title header."""
    return f"\n 📋 {report_type.upper()} REPORT ({period})\n=================================================="

def format_transaction_item(tx: Dict[str, Any]) -> str:
    """Formats a single transaction matching the specified output template."""
    amount_formatted = format_currency(tx.get("amount", 0.0))
    source = tx.get("source_account", "Cash")
    recipient = tx.get("recipient_or_use", "N/A")
    comment = tx.get("comment", "")
    
    return (
        f" ♦ Date: {tx.get('date')}\n"
        f"   Amount: {amount_formatted} PKR\n"
        f"   Account: {source}\n"
        f"   To/Use: {recipient}\n"
        f"   Note: {comment}\n"
    )

def generate_text_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    report_type: str = "custom"
) -> str:
    """
    Generates a full Markdown text report for transactions in the specified date range.
    """
    # Fetch transactions from DB
    txs = database.get_transactions(start_date=start_date, end_date=end_date)
    
    # Calculate period representation for title
    if start_date and end_date:
        if start_date == end_date:
            period = start_date
            if report_type == "custom":
                report_type = "daily"
        elif start_date[:7] == end_date[:7] and start_date.endswith("-01"):
            # Check if full month (approximate check)
            period = start_date[:7]
            if report_type == "custom":
                report_type = "monthly"
        else:
            period = f"{start_date} to {end_date}"
    else:
        period = "All Time"
        
    lines = []
    lines.append(format_report_title(report_type, period))
    
    total_volume = 0.0
    if not txs:
        lines.append(" No transactions recorded for this period.")
    else:
        for idx, tx in enumerate(txs):
            lines.append(format_transaction_item(tx))
            total_volume += tx.get("amount", 0.0)
            # Add separator between items, but not after the last item
            if idx < len(txs) - 1:
                lines.append("--------------------------------------------------")
                
    lines.append("==================================================")
    lines.append(f"💰 TOTAL VOLUMES TRACKED: {format_currency(total_volume)} PKR\n")
    
    return "\n".join(lines)

def generate_daily_report(date_str: str) -> str:
    """Helper to generate a daily report."""
    return generate_text_report(start_date=date_str, end_date=date_str, report_type="daily")

def generate_monthly_report(month_str: str) -> str:
    """
    Helper to generate a monthly statement report.
    month_str should be YYYY-MM format.
    """
    start_date = f"{month_str}-01"
    # Find last day of month or just use a high value like 31
    # SQLite can handle simple string range comparisons up to -31
    end_date = f"{month_str}-31"
    return generate_text_report(start_date=start_date, end_date=end_date, report_type="monthly")
