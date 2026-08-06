# Same-day deployment guide

## Option A: Streamlit Community Cloud

1. Create a GitHub repository and push this folder. Keep `.streamlit/secrets.toml`, `data/trustestate.db`, and `.venv` out of Git.
2. In Streamlit Community Cloud, select **Create app**, choose the repository and branch, and set the entrypoint to `streamlit_app.py`.
3. Open **Advanced settings** and paste the private secrets in TOML form:

```toml
ADMIN_USERNAME = "..."
ADMIN_PASSWORD = "..."
USER_USERNAME = "..."
USER_PASSWORD = "..."
AUTH_PEPPER = "..."
```

4. Deploy, open the generated `streamlit.app` address, and test both roles.
5. Rotate the two initial passwords after the demonstration and keep the pepper unchanged for existing password hashes.

### Important persistence note

SQLite is suitable for a single academic demo instance. Community Cloud may recreate the app filesystem during redeployment or maintenance, so saved cases are not guaranteed durable. For real users, point the database layer at managed PostgreSQL/PostGIS and add backups before collecting important records.

## Option B: Docker / Render

1. Push the project to GitHub.
2. Create a Render Blueprint from `render.yaml` or build the included Dockerfile on another host.
3. Add all five secrets as environment variables.
4. Attach persistent storage or migrate to PostgreSQL before production use.

## Post-deployment verification

- `/_stcore/health` returns a healthy response.
- Admin and buyer passwords both work; a wrong password does not.
- Buyer cannot see the Admin Console.
- A due-diligence case can be saved and a PDF downloaded.
- A critical failed check produces a high-risk stop decision.
- GPS permission can be denied safely, and manual coordinates still work.
- The 360 viewer loads the demo and an uploaded 2:1 panorama.
- Official portal buttons open government domains.
- Secrets and the SQLite database are absent from the public repository.

