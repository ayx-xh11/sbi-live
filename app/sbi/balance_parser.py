"""
Balance parser and currency formatting for SBI Savings Accounts.
Identifies Available Balance, distinguishes hold/lien/ledger amounts,
and formats Indian Rupee amounts with standard lakh/crore comma grouping.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
from app.security.safe_logger import logger


@dataclass
class AccountInfo:
    account_type: str
    masked_number: str  # E.g. ••••1234
    available_balance: float
    formatted_balance: str


# Regex for amounts in Indian Rupee format
# Matches numbers like: 24,582.37 or 1,23,456.78 or 10,00,000.00 or 500.00
_INR_NUM_REGEX = re.compile(r'(?:₹|Rs\.?|INR)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?)', re.IGNORECASE)

# Keywords to exclude
_EXCLUDED_KEYWORDS = [
    "hold", "lien", "ledger", "uncleared", "minimum", "limit",
    "debit", "credit", "transferred", "spent", "reward", "fee"
]


def format_inr(amount: float) -> str:
    """
    Format a floating-point number into standard Indian Rupee notation (₹ X,XX,XXX.XX).
    Indian format: Last 3 digits before decimal grouped together, subsequent digits grouped in pairs.
    """
    sign = "-" if amount < 0 else ""
    abs_amount = abs(amount)
    parts = f"{abs_amount:.2f}".split(".")
    int_part = parts[0]
    dec_part = parts[1]

    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last3 = int_part[-3:]
        remaining = int_part[:-3]
        # Group remaining digits by 2 from right to left
        groups = []
        while remaining:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        groups.reverse()
        formatted_int = ",".join(groups) + "," + last3

    return f"₹ {sign}{formatted_int}.{dec_part}"


def parse_inr_amount(text: str) -> Optional[float]:
    """Extract and parse numeric value from a currency string."""
    if not text:
        return None

    clean = text.strip()
    match = _INR_NUM_REGEX.search(clean)
    if not match:
        return None

    num_str = match.group(1).replace(",", "")
    try:
        return float(num_str)
    except ValueError:
        return None


def extract_accounts_from_text(page_text: str) -> List[AccountInfo]:
    """
    Parses full-text or block-text content from the SBI accounts page to extract
    savings account details and their corresponding Available Balance.
    """
    accounts: List[AccountInfo] = []
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]

    # Patterns for account numbers
    acc_num_regex = re.compile(r'(?:A/C|Acc(?:ount)?(?:\s*No)?\.?|Savings)\s*[:#]?\s*(?:[xX*•]{3,12}|(\d{6,14}))(\d{4})\b', re.IGNORECASE)

    current_masked = None
    current_acc_type = "Savings Account"

    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Look for account type indicators on current line
        if "current" in line_lower:
            current_acc_type = "Current Account"
        elif "savings" in line_lower:
            current_acc_type = "Savings Account"

        # Look for account number indicators
        acc_match = acc_num_regex.search(line)
        if acc_match:
            last4 = acc_match.group(2)
            current_masked = f"••••{last4}"

        # Check for Available Balance labels
        if "available balance" in line_lower:
            # Ensure it is NOT hold or lien
            if any(k in line_lower for k in ["hold", "lien", "ledger", "uncleared"]):
                continue

            # Look for amount on current line or subsequent 2 lines
            found_amount = None
            amount = parse_inr_amount(line)
            if amount is not None:
                found_amount = amount
            else:
                for next_line in lines[i + 1:i + 3]:
                    next_amount = parse_inr_amount(next_line)
                    if next_amount is not None:
                        found_amount = next_amount
                        break

            if found_amount is not None:
                masked = current_masked or "••••0000"
                accounts.append(AccountInfo(
                    account_type=current_acc_type,
                    masked_number=masked,
                    available_balance=found_amount,
                    formatted_balance=format_inr(found_amount)
                ))
                # Reset for next account card
                current_masked = None
                current_acc_type = "Savings Account"

    return accounts


def select_account_balance(
    accounts: List[AccountInfo],
    preferred_suffix: Optional[str] = None
) -> Optional[AccountInfo]:
    """
    Selects the desired account from the list.
    If preferred_suffix is given (e.g. '••••1234' or '1234'), matches that account.
    Otherwise defaults to the first savings account.
    """
    if not accounts:
        return None

    if preferred_suffix:
        clean_suffix = preferred_suffix.replace("•", "").strip()
        for acc in accounts:
            if acc.masked_number.endswith(clean_suffix):
                return acc

    # Default to first account
    return accounts[0]
