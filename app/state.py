"""
State machine management for SBI Balance Desktop Widget.
Defines all explicit lifecycle and authentication states.
"""

from enum import Enum
from typing import Callable, List, Optional
import threading


class AuthState(Enum):
    STARTING = "STARTING"
    CHECKING_SESSION = "CHECKING_SESSION"
    AUTHENTICATED = "AUTHENTICATED"
    READING_BALANCE = "READING_BALANCE"
    MONITORING = "MONITORING"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    SBI_LOGIN = "SBI_LOGIN"
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"
    OTP_REQUIRED = "OTP_REQUIRED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    NETWORK_ERROR = "NETWORK_ERROR"
    SITE_CHANGED = "SITE_CHANGED"
    UNEXPECTED_REDIRECT = "UNEXPECTED_REDIRECT"
    BROWSER_ERROR = "BROWSER_ERROR"


class StateManager:
    """Thread-safe state manager with observer callbacks."""

    def __init__(self, initial_state: AuthState = AuthState.STARTING):
        self._state: AuthState = initial_state
        self._lock = threading.Lock()
        self._listeners: List[Callable[[AuthState, AuthState, Optional[str]], None]] = []
        self._message: Optional[str] = None

    @property
    def current_state(self) -> AuthState:
        with self._lock:
            return self._state

    @property
    def current_message(self) -> Optional[str]:
        with self._lock:
            return self._message

    def add_listener(self, listener: Callable[[AuthState, AuthState, Optional[str]], None]) -> None:
        """Register a callback for state changes: callback(old_state, new_state, message)"""
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[AuthState, AuthState, Optional[str]], None]) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def set_state(self, new_state: AuthState, message: Optional[str] = None) -> None:
        """Atomically transition state and notify all registered listeners."""
        with self._lock:
            old_state = self._state
            if old_state == new_state and self._message == message:
                return
            self._state = new_state
            self._message = message
            listeners = list(self._listeners)

        for listener in listeners:
            try:
                listener(old_state, new_state, message)
            except Exception as e:
                # Observers must never crash the state machine
                pass

    def is_authenticated(self) -> bool:
        with self._lock:
            return self._state in (AuthState.AUTHENTICATED, AuthState.READING_BALANCE, AuthState.MONITORING)

    def requires_user_action(self) -> bool:
        with self._lock:
            return self._state in (
                AuthState.AUTHENTICATION_REQUIRED,
                AuthState.SBI_LOGIN,
                AuthState.CAPTCHA_REQUIRED,
                AuthState.OTP_REQUIRED,
                AuthState.SESSION_EXPIRED,
            )
