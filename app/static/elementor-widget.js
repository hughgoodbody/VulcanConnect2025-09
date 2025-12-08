/**
 * Lightweight script to embed the configurator in Elementor via an HTML widget.
 * Usage: paste into an Elementor HTML block and set API_URL to your deployed endpoint.
 */
const API_URL = window.VULCAN_API_URL || "https://your-domain.com/api";

function renderConfigurator(rootId) {
  const root = document.getElementById(rootId);
  if (!root) return;

  root.innerHTML = `
    <form id="onshape-config-form" style="display:flex;gap:8px;align-items:flex-end;">
      <label style="display:flex;flex-direction:column;flex:1;">
        <span>Onshape URL</span>
        <input type="url" name="onshape_url" required placeholder="https://cad.onshape.com/documents/..." style="padding:8px;border:1px solid #ccc;border-radius:4px;" />
      </label>
      <button type="submit" style="padding:10px 16px;background:#0073e6;color:white;border:none;border-radius:4px;cursor:pointer;">Load</button>
    </form>
    <div id="config-results" style="margin-top:16px;"></div>
  `;

  const form = document.getElementById("onshape-config-form");
  const results = document.getElementById("config-results");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const url = form.onshape_url.value;
    results.textContent = "Loading configurations...";

    try {
      const response = await fetch(`${API_URL}/configurations/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ onshape_url: url }),
      });
      if (!response.ok) throw new Error(`Request failed: ${response.status}`);
      const data = await response.json();
      results.innerHTML = renderOptions(data.options);
    } catch (error) {
      results.textContent = `Error: ${error.message}`;
    }
  });
}

function renderOptions(options) {
  if (!options?.length) {
    return "No configuration parameters found.";
  }
  return options
    .map((option) => {
      if (option.type === "quantity") {
        return `
          <label style="display:block;margin-bottom:12px;">
            <strong>${option.display_name}</strong><br />
            <input type="number" value="${option.default ?? ""}" style="padding:6px;border:1px solid #ccc;border-radius:4px;width:200px;" />
            <small>${option.help_text ?? ""}</small>
          </label>
        `;
      }
      const inputType = option.type === "radio" ? "radio" : "select";
      if (inputType === "radio") {
        return `
          <fieldset style="margin-bottom:12px;">
            <legend><strong>${option.display_name}</strong></legend>
            ${(option.values || []).map(
              (value) => `
                <label style="margin-right:12px;">
                  <input type="radio" name="${option.key}" value="${value}" ${
                option.default === value ? "checked" : ""
              } /> ${value}
                </label>
              `
            ).join("")}
            <div><small>${option.help_text ?? ""}</small></div>
          </fieldset>
        `;
      }
      return `
        <label style="display:block;margin-bottom:12px;">
          <strong>${option.display_name}</strong><br />
          <select style="padding:6px;border:1px solid #ccc;border-radius:4px;">
            ${(option.values || []).map(
              (value) => `<option value="${value}" ${option.default === value ? "selected" : ""}>${value}</option>`
            ).join("")}
          </select>
          <div><small>${option.help_text ?? ""}</small></div>
        </label>
      `;
    })
    .join("");
}

window.renderOnshapeConfigurator = renderConfigurator;
