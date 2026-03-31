"""Authentication wrapper using streamlit-authenticator."""

from pathlib import Path

import streamlit as st
import yaml
import streamlit_authenticator as stauth


CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "auth_config.yaml"


def load_auth_config() -> dict:
    """Load auth config from YAML."""
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def save_auth_config(config: dict) -> None:
    """Save updated auth config (e.g., after password hash)."""
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def require_auth() -> str | None:
    """Enforce authentication. Returns username if authenticated, else blocks.

    Call this at the top of each page (after set_page_config).
    """
    config = load_auth_config()

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    try:
        authenticator.login()
    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        st.stop()

    if st.session_state.get("authentication_status"):
        with st.sidebar:
            st.sidebar.markdown(f"👤 **{st.session_state.get('name', '')}**")
            authenticator.logout("Cerrar sesión", "sidebar")
        return st.session_state.get("username")

    elif st.session_state.get("authentication_status") is False:
        st.error("Usuario o contraseña incorrectos.")
        st.stop()

    else:
        st.warning("Ingresa tus credenciales para continuar.")
        st.stop()

    return None
