import os
import plaid
import schedule
import time
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Plaid API Configuration
configuration = plaid.Configuration(
    host=plaid.Environment.Development,
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET'),
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# Global Variables
ACCESS_TOKEN = os.getenv('PLAID_ACCESS_TOKEN')

def get_transactions(days=30):
    """Fetch transactions from last N days using Plaid API"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    request = TransactionsGetRequest(
        access_token=ACCESS_TOKEN,
        start_date=start_date,
        end_date=end_date,
        options=TransactionsGetRequestOptions()
    )
    
    response = client.transactions_get(request)
    return response.to_dict()

def categorize_transaction(transaction):
    """Rule-based transaction categorization"""
    name = transaction['name'].lower()
    
    categories = {
        'food': ['wholefoods', 'kroger', 'restaurant'],
        'housing': ['rent', 'mortgage', 'apt'],
        'entertainment': ['netflix', 'spotify', 'hulu']
    }
    
    for category, keywords in categories.items():
        if any(keyword in name for keyword in keywords):
            return category
    return 'other'

def auto_pay_bills():
    """Pay bills if balance exceeds threshold"""
    balance = get_account_balance()
    bills = {'rent': 1200, 'internet': 80}
    
    for bill, amount in bills.items():
        if balance > amount + 500:  # $500 buffer
            print(f"Paying {bill}: ${amount}")
            # initiate_payment(amount, bill)  # Uncomment with real bank API

def get_account_balance():
    """Fetch checking account balance"""
    accounts = client.accounts_get(ACCESS_TOKEN)
    for account in accounts['accounts']:
        if account['type'] == 'depository':
            return account['balances']['current']
    return 0

def smart_savings():
    """Save 10% if income exceeds threshold"""
    transactions = get_transactions(30)
    income = sum(t['amount'] for t in transactions['transactions'] 
                if t['transaction_type'] == 'credit')
    
    if income >= 4000:
        savings = income * 0.10
        print(f"Transferring ${savings:.2f} to savings")
        # transfer_to_savings(savings)  # Uncomment with real bank API

def run_scheduler():
    """Schedule recurring tasks"""
    schedule.every().day.at("09:00").do(auto_pay_bills)
    schedule.every().month.last_day.at("18:00").do(smart_savings)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Example: Print categorized transactions
    transactions = get_transactions(7)
    df = pd.DataFrame([{
        'Date': t['date'],
        'Description': t['name'],
        'Amount': t['amount'],
        'Category': categorize_transaction(t)
    } for t in transactions['transactions']])
    
    print("\n🤑 Weekly Expense Report:")
    print(df.groupby('Category').sum())
    
    # Uncomment to run scheduler
    # run_scheduler()