QFL4 login redirect fix

Updated files:
- voice_app.py: re-checks login state after rendering the login form; stops only if login did not succeed, otherwise reruns into the authenticated portal.
- login_ui.py: safer account field lookup for status/password and retains existing admin role/session behavior.
- auth_session.py: included unchanged so the three authentication-related files stay together.

Deployment:
1. Replace these three files in the GitHub repository root (same folder as streamlit_app.py / the configured main module).
2. Commit and push to the main branch.
3. Wait for Streamlit Community Cloud to redeploy.
4. Open the app in a private/incognito window and try the admin login.

Do not share your password or Streamlit Secrets. This ZIP contains only the three source files uploaded in this chat; it does not contain the other project modules/assets.
