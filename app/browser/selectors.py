"""
Resilient DOM selectors and URLs for SBI YONO Retail and Personal Internet Banking.
Identified during live reconnaissance with fallback selectors.
"""

from typing import List

# Primary official entry points
SBI_YONO_WELCOME_URL = "https://yonoretail.sbi.bank.in/registration/welcome?srcChn=RINB"
SBI_CLASSIC_LOGIN_URL = "https://retail.onlinesbi.sbi/retail/login.htm"

# Login form input selectors (ordered by specificity)
USERNAME_SELECTORS: List[str] = [
    "input[aria-label='UserName']",
    "input[formcontrolname='userName']",
    "input#mat-input-1",
    "input[placeholder*='Username' i]",
    "input[name='username' i]",
]

PASSWORD_SELECTORS: List[str] = [
    "input[type='password']",
    "input[formcontrolname='password']",
    "input#mat-input-2",
    "input[aria-label*='Password' i]",
]

CAPTCHA_INPUT_SELECTORS: List[str] = [
    "input[aria-label='enterCaptchaLabel']",
    "input[formcontrolname='captcha']",
    "input#mat-input-0",
    "input[placeholder*='Captcha' i]",
]

CAPTCHA_IMAGE_SELECTORS: List[str] = [
    "img[alt='captcha']",
    "img[src*='captcha' i]",
    "img.captcha",
]

LOGIN_BUTTON_SELECTORS: List[str] = [
    "button:has-text('Login')",
    "button.login-button",
    "button.login-button-invalid",
    "input[type='submit'][value*='Login' i]",
]

# OTP detection selectors
OTP_INDICATOR_SELECTORS: List[str] = [
    "text='Enter OTP'",
    "text='Enter One Time Password'",
    "text='One Time Password'",
    "input[aria-label*='OTP' i]",
    "input[placeholder*='OTP' i]",
    "input[name*='otp' i]",
    "input[formcontrolname*='otp' i]",
]

# Authenticated state indicator selectors
AUTHENTICATED_INDICATORS: List[str] = [
    "text='Available Balance'",
    "text='Accounts & Deposits'",
    "app-dashboard",
    "app-accounts",
    "a:has-text('Logout')",
    "button:has-text('Logout')",
    "[aria-label='Logout']",
    "text='My Accounts'",
]

# Balance revealing eye / toggle buttons (if balance is masked by default)
BALANCE_VIEW_TOGGLES: List[str] = [
    "button:has-text('View Balance')",
    "button[aria-label*='view balance' i]",
    "[title*='view balance' i]",
    "button:has-text('Click here for balance')",
    "a:has-text('Click here for balance')",
]
