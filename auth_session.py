import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

import streamlit as st

AUTH_COOKIE_NAME = "qfl4_auth"
AUTH_COOKIE_TTL_SECONDS = 12 * 60 * 60


def _signing_key() -> bytes:
    configured_key = os.getenv("QFL4_AUTH_COOKIE_SECRET") or st.secrets.get(
        "QFL4_AUTH_COOKIE_SECRET", ""
    )
    if configured_key:
        key = configured_key.encode("utf-8")
        if len(key) < 32:
            raise ValueError("QFL4_AUTH_COOKIE_SECRET must be at least 32 characters.")
        return key

    app_data = Path(os.getenv("LOCALAPPDATA") or Path.home() / ".local" / "share")
    key_path = app_data / "QFL4-Audit-Intelligence" / "auth-cookie.key"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with key_path.open("xb") as key_file:
            key_file.write(os.urandom(32))
    except FileExistsError:
        pass
    return key_path.read_bytes()


def create_auth_token(email: str) -> str:
    payload = {
        "email": email.strip().lower(),
        "expires": int(time.time()) + AUTH_COOKIE_TTL_SECONDS,
    }
    encoded_payload = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")
    signature = hmac.new(
        _signing_key(), encoded_payload.encode("ascii"), hashlib.sha256
    ).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{encoded_payload}.{encoded_signature}"


def restore_auth_session(token: str, users: dict) -> tuple[str, str] | None:
    signing_key = _signing_key()
    try:
        encoded_payload, encoded_signature = token.split(".", maxsplit=1)
        expected_signature = hmac.new(
            signing_key, encoded_payload.encode("ascii"), hashlib.sha256
        ).digest()
        supplied_signature = base64.urlsafe_b64decode(
            encoded_signature + "=" * (-len(encoded_signature) % 4)
        )
        if not hmac.compare_digest(expected_signature, supplied_signature):
            return None

        payload = json.loads(
            base64.urlsafe_b64decode(
                encoded_payload + "=" * (-len(encoded_payload) % 4)
            )
        )
        email = payload["email"]
        expires = payload["expires"]
        if (
            not isinstance(email, str)
            or type(expires) is not int
            or expires < int(time.time())
        ):
            return None
        user = users.get(email)
        if not user or user.get("status") != "approved":
            return None
        return email, user.get("role", "user")
    except (ValueError, KeyError, TypeError, binascii.Error):
        return None


def set_auth_cookie(token: str) -> None:
    encoded_token = json.dumps(token)
    st.html(
        f"""
        <script>
        const secure = window.parent.location.protocol === "https:" ? "; Secure" : "";
        window.parent.document.cookie =
            "qfl4_auth=" + {encoded_token} +
            "; Path=/; Max-Age={AUTH_COOKIE_TTL_SECONDS}; SameSite=Lax" + secure;
        window.setTimeout(() => window.parent.location.reload(), 100);
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def clear_auth_cookie() -> None:
    st.html(
        """
        <script>
        const secure = window.parent.location.protocol === "https:" ? "; Secure" : "";
        window.parent.document.cookie =
            "qfl4_auth=; Path=/; Max-Age=0; SameSite=Lax" + secure;
        window.setTimeout(() => window.parent.location.reload(), 100);
        </script>
        """,
        unsafe_allow_javascript=True,
    )
