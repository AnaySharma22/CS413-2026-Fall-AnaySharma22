const editor = document.querySelector("#editor");
const status = document.querySelector("#status");
const loadMenu = document.querySelector("#load-menu");
const fileInput = document.querySelector("#file");
const sourceName = document.querySelector("#source-name");
const revisionNode = document.querySelector("#revision");
const resultMeta = document.querySelector("#result-meta");
const resultNode = document.querySelector("#result");

const toolIds = ["lint", "interpret", "typecheck", "compile"];
let appliedSource = "";
let appliedName = "Manual input";
let inFlight = false;
let examples = {};
let lastState = {
  name: "",
  source: "",
  revision: 0,
  busy: false,
  artifact: null,
  result: null,
};

function dirty() {
  return editor.value !== appliedSource;
}

function setStatus(text) {
  status.textContent = text;
}

function render(state) {
  lastState = state;
  if (!dirty()) {
    editor.value = state.source;
    appliedSource = state.source;
  }
  if (state.revision && !dirty()) {
    appliedName = state.name;
    sourceName.textContent = state.name;
  } else if (!state.revision && !dirty()) {
    sourceName.textContent = "none";
  }
  revisionNode.textContent = String(state.revision);
  if (state.result) {
    resultMeta.textContent =
      "Action: " + state.result.operation +
      ". Revision: " + state.result.revision +
      ". Outcome: " + state.result.outcome + ".";
    resultNode.textContent = state.result.text;
  } else {
    resultMeta.textContent = "No result.";
    resultNode.textContent = "";
  }
  const locked = dirty() || inFlight || state.busy;
  loadMenu.disabled = locked;
  fileInput.disabled = locked;
  editor.disabled = inFlight || state.busy;
  document.querySelector("#apply").disabled = !dirty() || inFlight || state.busy;
  document.querySelector("#discard").disabled = !dirty() || inFlight || state.busy;
  for (const id of toolIds) {
    document.querySelector("#" + id).disabled = locked || state.revision === 0;
  }
  document.querySelector("#execute").disabled = true;
  if (inFlight || state.busy) {
    setStatus("Working. Controls are paused until this operation finishes.");
  } else if (dirty()) {
    setStatus("Unapplied edits. Apply or discard them before loading source or running tools.");
  } else if (state.revision === 0) {
    setStatus("Idle. Apply source before running tools.");
  } else {
    setStatus("Idle. Source revision " + state.revision + " is applied.");
  }
}

async function readJson(response) {
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }
  return payload;
}

async function refresh() {
  const response = await fetch("/api/state");
  render(await readJson(response));
}

async function applySource(text, name) {
  inFlight = true;
  render(lastState);
  setStatus("Working. Applying source.");
  let errorText = "";
  try {
    const response = await fetch("/api/source", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: text, name: name }),
    });
    const state = await readJson(response);
    appliedSource = state.source;
    editor.value = state.source;
    render(state);
  } catch (error) {
    errorText = error.message + " The previous applied source is unchanged.";
  } finally {
    inFlight = false;
  }
  await refresh();
  if (errorText) {
    setStatus(errorText);
  }
}

async function runTool(operation) {
  inFlight = true;
  render(lastState);
  setStatus("Working: " + operation + ".");
  let errorText = "";
  try {
    const response = await fetch("/api/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operation: operation, editor: editor.value }),
    });
    render(await readJson(response));
  } catch (error) {
    errorText = error.message;
  } finally {
    inFlight = false;
  }
  await refresh();
  if (errorText) {
    setStatus(errorText);
  }
}

loadMenu.addEventListener("change", async () => {
  const choice = loadMenu.value;
  loadMenu.value = "";
  if (!choice || loadMenu.disabled) {
    return;
  }
  if (choice === "file") {
    fileInput.click();
    return;
  }
  if (choice === "manual") {
    editor.value = "";
    appliedName = "Manual input";
    await refresh();
    sourceName.textContent = "Manual input";
    return;
  }
  editor.value = examples[choice] || "";
  await applySource(editor.value, choice);
});

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  fileInput.value = "";
  if (!file) {
    return;
  }
  const bytes = new Uint8Array(await file.arrayBuffer());
  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch (error) {
    setStatus("The file is not valid UTF-8. The applied source was not changed.");
    return;
  }
  editor.value = text;
  await applySource(text, file.name);
});

editor.addEventListener("input", () => refresh());

document.querySelector("#apply").addEventListener("click", () => {
  applySource(editor.value, appliedName);
});

document.querySelector("#discard").addEventListener("click", async () => {
  editor.value = appliedSource;
  await refresh();
});

for (const id of toolIds) {
  document.querySelector("#" + id).addEventListener("click", () => runTool(id));
}

fetch("/api/examples")
  .then((response) => response.json())
  .then((payload) => {
    examples = payload;
    return refresh();
  })
  .catch((error) => setStatus(error.message));
