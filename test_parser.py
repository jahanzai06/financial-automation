import database
import reporter

def seed_database():
    """Seeds the SQLite database with high-quality sample transactions."""
    print("Initializing and seeding ledger database...")
    database.init_db()
    
    # Check if database is already populated
    existing = database.get_transactions()
    if len(existing) > 0:
        print(f"Database already contains {len(existing)} records. Skipping seeding.")
        return
        
    sample_txs = [
        {
            "date": "2026-06-25",
            "amount": 4500.00,
            "source_account": "HBL (Muhammad Jahanzaib)",
            "recipient_or_use": "K-Electric",
            "comment": "Bill Payment Ref ID #992834"
        },
        {
            "date": "2026-06-25",
            "amount": 1200.00,
            "source_account": "EasyPaisa",
            "recipient_or_use": "Asif Ali",
            "comment": "Transfer split funds"
        },
        {
            "date": "2026-06-24",
            "amount": 850.00,
            "source_account": "Cash",
            "recipient_or_use": "Pharmacy",
            "comment": "Allergy medicines"
        },
        {
            "date": "2026-06-23",
            "amount": 12000.00,
            "source_account": "HBL (Sana Kanwal)",
            "recipient_or_use": "Metro Superstore",
            "comment": "Monthly grocery shopping"
        },
        {
            "date": "2026-06-20",
            "amount": 2500.00,
            "source_account": "JazzCash",
            "recipient_or_use": "Shell Fuel Station",
            "comment": "Car petrol tank fill"
        },
        {
            "date": "2026-06-15",
            "amount": 3500.00,
            "source_account": "HBL (Muhammad Jahanzaib)",
            "recipient_or_use": "PTCL",
            "comment": "Broadband Internet Bill"
        },
        {
            "date": "2026-06-10",
            "amount": 800.00,
            "source_account": "EasyPaisa",
            "recipient_or_use": "Mobile Load",
            "comment": "Sana mobile balance recharge"
        }
    ]
    
    ids = database.add_transactions(sample_txs)
    print(f"Successfully seeded {len(ids)} transactions into SQLite.")

def verify_reports():
    """Generates monthly report to verify format styling."""
    print("\nVerifying statement generator output:")
    report = reporter.generate_monthly_report("2026-06")
    print(report)

if __name__ == "__main__":
    seed_database()
    verify_reports()
