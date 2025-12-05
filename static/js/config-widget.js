// static/js/config-widget.js

async function loadConfigurations(url) {
  if (!url) {
    alert("Please enter an Onshape URL.");
    return;
  }

  const res = await fetch(`/api/config/configurations?url=${encodeURIComponent(url)}`);
  if (!res.ok) {
    alert("Failed to fetch configurations");
    return;
  }
  const data = await res.json();
  renderConfigurations(data.parameters || []);
}

function renderConfigurations(parameters) {
  const container = document.getElementById("config-display");
  if (!container) return;
  container.innerHTML = "";

  parameters.forEach((param) => {
    const wrapper = document.createElement("div");
    wrapper.style.marginBottom = "0.5rem";

    const label = document.createElement("label");
    label.innerText = param.name;
    label.style.display = "block";

    let input;

    if (param.type === "enum") {
      input = document.createElement("select");
      param.options.forEach((opt) => {
        const o = document.createElement("option");
        o.value = opt;
        o.innerText = opt;
        input.appendChild(o);
      });
    } else if (param.type === "boolean") {
      input = document.createElement("input");
      input.type = "checkbox";
      input.checked = !!param.default;
    } else if (param.type === "quantity") {
      input = document.createElement("input");
      input.type = "number";
      if (param.min != null) input.min = param.min;
      if (param.max != null) input.max = param.max;
      if (param.default != null) input.value = param.default;
      input.dataset.units = param.units || "mm";
    } else {
      // unsupported – skip or show read-only
      return;
    }

    input.id = param.id;
    input.dataset.paramId = param.id;
    input.dataset.paramType = param.type;

    wrapper.appendChild(label);
    wrapper.appendChild(input);
    container.appendChild(wrapper);
  });
}

async function encodeConfiguration(url) {
  const container = document.getElementById("config-display");
  if (!container) return;

  const inputs = container.querySelectorAll("[data-param-id]");
  const values = {};

  inputs.forEach((input) => {
    const paramId = input.dataset.paramId;
    const paramType = input.dataset.paramType;

    let value;
    if (paramType === "enum") {
      value = input.value;
    } else if (paramType === "boolean") {
      value = input.checked;
    } else if (paramType === "quantity") {
      const units = input.dataset.units || "mm";
      value = `${input.value}_${units}`;
    }

    values[paramId] = value;
  });

  const res = await fetch("/api/config/encode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, values }),
  });
  const data = await res.json();
  alert("Encoded configuration:\n" + data.encodedId);
}
