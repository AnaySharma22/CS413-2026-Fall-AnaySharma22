(() => {
  const RPC_URL = "/rpc";
  const BATCH = 8;

  const els = {
    board: document.getElementById("board"),
    status: document.getElementById("status"),
    size: document.getElementById("size"),
    speed: document.getElementById("speed"),
    speedLabel: document.getElementById("speed-label"),
    start: document.getElementById("start"),
    step: document.getElementById("step"),
    play: document.getElementById("play"),
    pause: document.getElementById("pause"),
    nextSolution: document.getElementById("next-solution"),
    reset: document.getElementById("reset"),
    solutions: document.getElementById("solutions"),
    events: document.getElementById("events"),
    streamState: document.getElementById("stream-state"),
    error: document.getElementById("error"),
    log: document.getElementById("log"),
  };

  const state = {
    streamId: null,
    size: 8,
    board: [],
    highlight: null,
    queue: [],
    done: false,
    playing: false,
    seekingSolution: false,
    timer: null,
    solutionCount: 0,
    eventCount: 0,
    fetching: false,
  };

  function rpc(method, params, id = Date.now()) {
    return fetch(RPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method, params, id }),
    }).then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const body = await response.json();
      if (body.error) {
        const detail = body.error.data ? ` ${JSON.stringify(body.error.data)}` : "";
        throw new Error(`${body.error.message}${detail}`);
      }
      return body.result;
    });
  }

  function showError(message) {
    els.error.hidden = !message;
    els.error.textContent = message || "";
  }

  function setStatus(text) {
    els.status.textContent = text;
  }

  function setControls() {
    const open = Boolean(state.streamId);
    els.start.disabled = open;
    els.size.disabled = open;
    els.step.disabled = !open || state.done || state.playing;
    els.play.disabled = !open || state.done;
    els.pause.disabled = !open || !state.playing;
    els.nextSolution.disabled = !open || state.done || state.playing;
    els.reset.disabled = !open;
    els.play.setAttribute("aria-pressed", state.playing ? "true" : "false");
    els.pause.setAttribute("aria-pressed", state.playing ? "false" : "true");
    els.streamState.textContent = !open ? "closed" : state.done ? "done" : "open";
    els.solutions.textContent = String(state.solutionCount);
    els.events.textContent = String(state.eventCount);
  }

  function renderBoard() {
    const size = state.size;
    els.board.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
    els.board.replaceChildren();
    for (let row = 0; row < size; row += 1) {
      for (let col = 0; col < size; col += 1) {
        const cell = document.createElement("div");
        cell.className = `cell ${(row + col) % 2 === 0 ? "light" : "dark"}`;
        cell.dataset.row = String(row);
        cell.dataset.col = String(col);
        if (state.board[row] === col) {
          const mark = document.createElement("span");
          mark.className = "queen";
          mark.textContent = "♛";
          cell.appendChild(mark);
        }
        if (
          state.highlight &&
          state.highlight.row === row &&
          state.highlight.column === col
        ) {
          cell.classList.add(state.highlight.kind);
        }
        if (state.highlight && state.highlight.kind === "solution-glow") {
          if (state.board[row] === col) cell.classList.add("solution-glow");
        }
        els.board.appendChild(cell);
      }
    }
  }

  function logEvent(event) {
    const item = document.createElement("li");
    item.className = event.event;
    if (event.event === "solution") {
      item.textContent = `solution ${JSON.stringify(event.board)}`;
    } else if (event.event === "done") {
      item.textContent = "done — search complete";
    } else {
      item.textContent = `${event.event} r${event.row} c${event.column} ${JSON.stringify(event.board)}`;
    }
    els.log.prepend(item);
    while (els.log.children.length > 80) {
      els.log.removeChild(els.log.lastChild);
    }
  }

  function applyEvent(event) {
    state.eventCount += 1;
    logEvent(event);
    if (event.event === "done") {
      state.done = true;
      state.highlight = null;
      state.playing = false;
      state.seekingSolution = false;
      setStatus(`Search complete. ${state.solutionCount} solution(s).`);
      setControls();
      renderBoard();
      return;
    }
    if (event.board) state.board = event.board.slice();
    if (event.event === "solution") {
      state.solutionCount += 1;
      state.highlight = { kind: "solution-glow" };
      state.seekingSolution = false;
      setStatus(`Solution ${state.solutionCount}: ${JSON.stringify(event.board)}`);
    } else {
      state.highlight = {
        kind: event.event,
        row: event.row,
        column: event.column,
      };
      setStatus(`${event.event} at row ${event.row}, column ${event.column}`);
    }
    setControls();
    renderBoard();
  }

  async function fillQueue() {
    if (!state.streamId || state.done || state.fetching || state.queue.length > 0) {
      return;
    }
    state.fetching = true;
    try {
      const result = await rpc("queens.next", {
        stream_id: state.streamId,
        limit: BATCH,
      });
      state.queue.push(...result.events);
      if (result.done && result.events.length === 0) {
        state.done = true;
        setStatus(`Search complete. ${state.solutionCount} solution(s).`);
        state.playing = false;
        setControls();
      }
      showError("");
    } catch (error) {
      state.playing = false;
      state.seekingSolution = false;
      showError(String(error.message || error));
      setStatus("RPC failure. Fix the service or press Reset.");
      setControls();
    } finally {
      state.fetching = false;
    }
  }

  async function stepOnce() {
    if (!state.streamId || state.done) return false;
    await fillQueue();
    if (state.queue.length === 0) return false;
    applyEvent(state.queue.shift());
    return true;
  }

  async function playLoop() {
    if (!state.playing) return;
    const delay = Number(els.speed.value);
    const advanced = await stepOnce();
    if (!state.playing) return;
    if (!advanced) {
      state.playing = false;
      setControls();
      return;
    }
    if (state.seekingSolution) {
      const last = els.log.firstChild;
      if (last && (last.classList.contains("solution") || last.classList.contains("done"))) {
        state.playing = false;
        state.seekingSolution = false;
        setControls();
        return;
      }
    }
    state.timer = window.setTimeout(playLoop, delay);
  }

  async function start() {
    showError("");
    state.size = Number(els.size.value);
    state.board = [];
    state.highlight = null;
    state.queue = [];
    state.done = false;
    state.playing = false;
    state.seekingSolution = false;
    state.solutionCount = 0;
    state.eventCount = 0;
    els.log.replaceChildren();
    try {
      const result = await rpc("queens.open", { size: state.size });
      state.streamId = result.stream_id;
      setStatus(`Stream open (size ${result.size}). Press Step or Play.`);
      setControls();
      renderBoard();
    } catch (error) {
      showError(String(error.message || error));
      setControls();
    }
  }

  async function reset() {
    window.clearTimeout(state.timer);
    state.playing = false;
    state.seekingSolution = false;
    const id = state.streamId;
    state.streamId = null;
    state.queue = [];
    state.board = [];
    state.highlight = null;
    state.done = false;
    if (id) {
      try {
        await rpc("queens.close", { stream_id: id });
      } catch (_) {
        /* already gone */
      }
    }
    setStatus("Idle. Press Start to open a stream.");
    showError("");
    setControls();
    renderBoard();
  }

  els.speed.addEventListener("input", () => {
    els.speedLabel.textContent = els.speed.value;
  });
  els.start.addEventListener("click", start);
  els.step.addEventListener("click", () => {
    stepOnce();
  });
  els.play.addEventListener("click", () => {
    if (!state.streamId || state.done) return;
    state.playing = true;
    state.seekingSolution = false;
    setControls();
    playLoop();
  });
  els.pause.addEventListener("click", () => {
    state.playing = false;
    state.seekingSolution = false;
    window.clearTimeout(state.timer);
    setControls();
  });
  els.nextSolution.addEventListener("click", () => {
    if (!state.streamId || state.done) return;
    state.playing = true;
    state.seekingSolution = true;
    setControls();
    playLoop();
  });
  els.reset.addEventListener("click", reset);

  state.size = Number(els.size.value);
  renderBoard();
  setControls();
})();
