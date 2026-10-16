"""
Mock HTML fixtures and page text representing SBI internet banking pages
for testing balance parsing and account extraction.
"""

# Text representation of a single savings account dashboard
MOCK_SINGLE_SAVINGS_TEXT = """
Personal Banking
Welcome John Doe
Accounts & Deposits

Savings Bank Account
Account No: XXXXXXXX4521
Available Balance: ₹ 34,812.50
Uncleared Balance: ₹ 0.00
Hold Amount: ₹ 500.00

Quick Transfer
e-Services
Logout
"""

# Text representation of multiple accounts (two savings accounts)
MOCK_MULTIPLE_ACCOUNTS_TEXT = """
Personal Banking
Welcome Jane Doe

Savings Bank Account
Account No: XXXXXXXX1234
Available Balance: ₹ 1,45,290.75
Lien Amount: ₹ 2,000.00

Savings Bank Account
Account No: XXXXXXXX5678
Available Balance: ₹ 24,582.37
Hold Amount: ₹ 0.00

Current Account
Account No: XXXXXXXX9999
Available Balance: ₹ 5,00,000.00

Logout
"""

# Text representation with tricky hold and lien amounts before available balance
MOCK_TRICKY_AMOUNTS_TEXT = """
Account Summary
Savings Bank Account ••••8812
Hold Amount: ₹ 12,000.00
Lien Amount: ₹ 5,000.00
Ledger Balance: ₹ 95,000.00
Available Balance
₹ 78,000.00
"""
