# VulcanConnect Onshape Configurator

A minimal FastAPI-based service for fetching Onshape configuration metadata and rendering it in a WordPress/Elementor frontend. Users paste an Onshape URL, the backend pulls available configuration parameters, and the frontend renders radio, enum, and quantity controls.

## Project layout

```
app/
  main.py                 # FastAPI entrypoint
  core/                   # Settings and shared configuration
  routes/                 # API routers
  schemas/                # Pydantic models for requests/responses
  services/               # Onshape client and configuration handler
  static/                 # Frontend assets for Elementor embed
  templates/              # Example HTML for local preview
requirements.txt          # Python dependencies
```

## Running locally

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Start the API: `uvicorn app.main:app --reload --port 8000`.
4. Open `http://localhost:8000/docs` to try the `/configurations/resolve` endpoint.

## WordPress / Elementor embedding

1. Deploy the FastAPI app to your cPanel host (via Passenger, WSGI, or a lightweight container) and expose it at `/api` or another path.
2. Upload `app/static/elementor-widget.js` to a public URL (or serve it directly from the app via a `/static` route).
3. In Elementor, add an HTML widget and include:

```html
<div id="configurator-root"></div>
<script src="https://your-domain.com/static/elementor-widget.js"></script>
<script>
  window.VULCAN_API_URL = "https://your-domain.com/api"; // points to FastAPI
  window.renderOnshapeConfigurator("configurator-root");
</script>
```

The widget posts the Onshape URL to the API and renders inputs based on the returned configuration parameters.

## Configuration

Set the following environment variables (or define them in a `.env` file) to connect to Onshape:

- `ONSHAPE_ACCESS_KEY` and `ONSHAPE_SECRET_KEY` for authenticated requests.
- `ONSHAPE_BASE_URL` if you are not using `https://cad.onshape.com`.
- `ONSHAPE_REQUEST_TIMEOUT_SECONDS` to tune outbound request timeouts.

## Notes

- The `OnshapeClient` uses the `/api/parts/.../configurations` endpoint shape. Adjust the path if your Onshape account requires a different resource.
- The frontend is intentionally lightweight so it can be dropped into Elementor without additional tooling.
