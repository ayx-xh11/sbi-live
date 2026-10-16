"""
Unit tests for AuthState state machine and transitions.
"""

from app.state import AuthState, StateManager


def test_initial_state():
    sm = StateManager()
    assert sm.current_state == AuthState.STARTING
    assert not sm.is_authenticated()
    assert not sm.requires_user_action()


def test_state_transitions_and_listeners():
    sm = StateManager()
    transitions = []

    def on_change(old, new, msg):
        transitions.append((old, new, msg))

    sm.add_listener(on_change)

    sm.set_state(AuthState.CHECKING_SESSION, "Checking...")
    assert sm.current_state == AuthState.CHECKING_SESSION

    sm.set_state(AuthState.AUTHENTICATION_REQUIRED, "Need auth")
    assert sm.requires_user_action()

    sm.set_state(AuthState.CAPTCHA_REQUIRED, "User solve captcha")
    assert sm.requires_user_action()

    sm.set_state(AuthState.AUTHENTICATED, "Logged in")
    assert sm.is_authenticated()
    assert not sm.requires_user_action()

    sm.set_state(AuthState.MONITORING, "Idle in background")
    assert sm.is_authenticated()

    assert len(transitions) == 5
    assert transitions[0] == (AuthState.STARTING, AuthState.CHECKING_SESSION, "Checking...")
    assert transitions[4] == (AuthState.AUTHENTICATED, AuthState.MONITORING, "Idle in background")


def test_deduplicate_identical_state():
    sm = StateManager()
    notifications = []
    sm.add_listener(lambda o, n, m: notifications.append(n))

    sm.set_state(AuthState.MONITORING, "Same")
    sm.set_state(AuthState.MONITORING, "Same")

    assert len(notifications) == 1
