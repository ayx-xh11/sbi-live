"""
Unit tests for Indian Rupee currency formatting and Available Balance parsing.
"""

from app.sbi.balance_parser import (
    format_inr,
    parse_inr_amount,
    extract_accounts_from_text,
    select_account_balance,
)
from tests.fixtures.mock_sbi_pages import (
    MOCK_SINGLE_SAVINGS_TEXT,
    MOCK_MULTIPLE_ACCOUNTS_TEXT,
    MOCK_TRICKY_AMOUNTS_TEXT,
)


def test_format_inr():
    cases = [
        (0.00, "₹ 0.00"),
        (500.00, "₹ 500.00"),
        (24582.37, "₹ 24,582.37"),
        (123456.78, "₹ 1,23,456.78"),
        (1000000.00, "₹ 10,00,000.00"),
        (12345678.90, "₹ 1,23,45,678.90"),
    ]
    for val, expected in cases:
        assert format_inr(val) == expected, f"Mismatch for {val}: expected {expected}, got {format_inr(val)}"


def test_parse_inr_amount():
    cases = [
        ("₹ 24,582.37", 24582.37),
        ("₹24,582.37", 24582.37),
        ("Rs. 1,45,290.75", 145290.75),
        ("INR 10,00,000.00", 1000000.00),
        ("500.00", 500.00),
        ("Available Balance: ₹ 34,812.50", 34812.50),
    ]
    for text, expected in cases:
        res = parse_inr_amount(text)
        assert res == expected, f"Failed parsing '{text}', expected {expected}, got {res}"


def test_extract_single_account():
    accounts = extract_accounts_from_text(MOCK_SINGLE_SAVINGS_TEXT)
    assert len(accounts) == 1
    acc = accounts[0]
    assert acc.account_type == "Savings Account"
    assert acc.masked_number == "••••4521"
    assert acc.available_balance == 34812.50
    assert acc.formatted_balance == "₹ 34,812.50"


def test_extract_multiple_accounts():
    accounts = extract_accounts_from_text(MOCK_MULTIPLE_ACCOUNTS_TEXT)
    assert len(accounts) == 3

    # Savings 1
    assert accounts[0].masked_number == "••••1234"
    assert accounts[0].available_balance == 145290.75

    # Savings 2
    assert accounts[1].masked_number == "••••5678"
    assert accounts[1].available_balance == 24582.37

    # Current
    assert accounts[2].account_type == "Current Account"
    assert accounts[2].masked_number == "••••9999"
    assert accounts[2].available_balance == 500000.00


def test_tricky_amounts_isolation():
    # Page contains Hold Amount (12000), Lien (5000), Ledger (95000), and Available Balance (78000)
    accounts = extract_accounts_from_text(MOCK_TRICKY_AMOUNTS_TEXT)
    assert len(accounts) == 1
    assert accounts[0].masked_number == "••••8812"
    # Available Balance must be exactly 78000, NOT the hold or ledger balances!
    assert accounts[0].available_balance == 78000.00
    assert accounts[0].formatted_balance == "₹ 78,000.00"


def test_select_account_balance():
    accounts = extract_accounts_from_text(MOCK_MULTIPLE_ACCOUNTS_TEXT)

    # Default should select the first account
    selected_default = select_account_balance(accounts)
    assert selected_default.masked_number == "••••1234"

    # Selection by suffix
    selected_custom = select_account_balance(accounts, preferred_suffix="••••5678")
    assert selected_custom.masked_number == "••••5678"
    assert selected_custom.available_balance == 24582.37
