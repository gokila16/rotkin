const vscode = require("vscode");
const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFile, spawn } = require("child_process");

const URL = "http://localhost:8765";
// Claude Code hooks need a path that survives extension updates, so they run this copy.
const HOOK_SCRIPT = path.join(os.homedir(), ".rotkin", "bin", "rotkin.py");
const SETTINGS = path.join(os.homedir(), ".claude", "settings.json");
const EMOJI = { Fresh: "🎃", "Soft Spot": "🎃", Moldy: "🤢", "Fruit Flies": "🤢", Collapsing: "🤢", Dead: "💀" };
const NEWS = {
  Fresh: "Your pumpkin is fresh again. Don't ruin it.",
  "Soft Spot": "Your pumpkin has developed a soft spot.",
  Moldy: "Your pumpkin is growing mold. When did you last blink?",
  "Fruit Flies": "Fruit flies have arrived. They brought friends.",
  Collapsing: "Your pumpkin is collapsing. Go outside. Now.",
  Dead: "Your pumpkin has died. Touch grass to revive it.",
};

let server = null;

function run(cmd, args) {
  return new Promise((resolve, reject) =>
    execFile(cmd, args, (err, stdout, stderr) => (err ? reject(new Error(stderr || err.message)) : resolve(stdout.trim()))),
  );
}

// Returns the absolute path of a Python 3.8+ on this machine, or null.
async function findPython() {
  const check = "import sys; assert sys.version_info >= (3, 8); print(sys.executable)";
  for (const cmd of ["python3", "python"]) {
    try {
      return await run(cmd, ["-c", check]);
    } catch {}
  }
  return null;
}

function hooksInstalled() {
  try {
    return fs.readFileSync(SETTINGS, "utf8").includes("rotkin.py");
  } catch {
    return false;
  }
}

function activate(context) {
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  status.command = "rotkin.openDashboard";
  status.tooltip = "Open the Rotkin dashboard";
  status.show();
  context.subscriptions.push(status);

  if (process.platform === "win32") {
    status.text = "🎃 macOS/Linux only";
    return;
  }

  // Packaged, the Python app lives in ./python (see bundle.js). Run from the repo, it's one folder up.
  const bundled = context.asAbsolutePath("python");
  const app = fs.existsSync(bundled) ? bundled : path.join(context.extensionPath, "..");

  let view, lastStage, lastStart = 0, warnedNoPython = false;
  const python = findPython();
  const openDashboard = () => vscode.env.openExternal(vscode.Uri.parse(URL));

  async function needPython() {
    const py = await python;
    if (!py && !warnedNoPython) {
      warnedNoPython = true;
      const pick = await vscode.window.showErrorMessage("Rotkin needs Python 3.8 or newer.", "Get Python");
      if (pick) vscode.env.openExternal(vscode.Uri.parse("https://www.python.org/downloads/"));
    }
    return py;
  }

  // Start the dashboard server unless another VS Code window already runs one.
  async function startServer() {
    if (server || Date.now() - lastStart < 30000) return;
    lastStart = Date.now();
    const py = await needPython();
    if (!py) return;
    server = spawn(py, [path.join(app, "server.py")], { stdio: "ignore" });
    server.on("exit", () => (server = null));
    server.on("error", () => (server = null));
  }

  function refreshHookScript() {
    fs.mkdirSync(path.dirname(HOOK_SCRIPT), { recursive: true, mode: 0o700 });
    fs.copyFileSync(path.join(app, "rotkin.py"), HOOK_SCRIPT);
  }

  async function connect() {
    const py = await needPython();
    if (!py) return;
    try {
      refreshHookScript();
      await run(py, [path.join(app, "install.py"), HOOK_SCRIPT]);
      vscode.window.showInformationMessage("🎃 Rotkin is connected. New Claude Code sessions will feed your pumpkin.");
    } catch (err) {
      vscode.window.showErrorMessage(`Rotkin couldn't connect: ${err.message}`);
    }
  }

  async function disconnect() {
    if (!hooksInstalled()) return vscode.window.showInformationMessage("Rotkin isn't connected to Claude Code.");
    const py = await needPython();
    if (!py) return;
    try {
      await run(py, [path.join(app, "uninstall.py")]);
      vscode.window.showInformationMessage("Rotkin is disconnected. Your other hooks are untouched.");
    } catch (err) {
      vscode.window.showErrorMessage(`Rotkin couldn't disconnect: ${err.message}`);
    }
  }

  async function askToConnect() {
    if (hooksInstalled() || context.globalState.get("askedToConnect")) return;
    context.globalState.update("askedToConnect", true);
    const pick = await vscode.window.showInformationMessage(
      "Connect Rotkin to Claude Code? It adds two hooks and a status line to ~/.claude/settings.json (backed up first).",
      "Connect",
      "Not now",
    );
    if (pick === "Connect") connect();
  }

  async function poll() {
    try {
      const state = await (await fetch(URL + "/state")).json();
      status.text = `${EMOJI[state.stage]} ${Math.round(state.rot)}%`;
      if (lastStage && state.stage !== lastStage) vscode.window.showInformationMessage(NEWS[state.stage]);
      lastStage = state.stage;
      view?.webview.postMessage(state);
    } catch {
      status.text = "🎃 off";
      view?.webview.postMessage(null);
      startServer();
    }
  }

  // Keep the hooks' copy in step with this version of the extension.
  if (fs.existsSync(HOOK_SCRIPT)) refreshHookScript();
  askToConnect();

  context.subscriptions.push(
    vscode.commands.registerCommand("rotkin.openDashboard", openDashboard),
    vscode.commands.registerCommand("rotkin.connect", connect),
    vscode.commands.registerCommand("rotkin.disconnect", disconnect),
    vscode.window.registerWebviewViewProvider("rotkin.pumpkin", {
      resolveWebviewView(v) {
        view = v;
        v.webview.options = { enableScripts: true };
        v.webview.html = PAGE.replaceAll("NONCE", crypto.randomBytes(16).toString("hex"));
        v.webview.onDidReceiveMessage(openDashboard);
        poll();
      },
    }),
  );
  poll();
  const timer = setInterval(poll, 2000);
  context.subscriptions.push({ dispose: () => clearInterval(timer) });
}

const PAGE = `<!doctype html>
<html><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-NONCE'">
<style>
html, body { height: 100%; margin: 0; }
body { box-sizing: border-box; padding: 8px; overflow: hidden; display: flex; flex-direction: column; text-align: center; color: var(--vscode-foreground); font-family: var(--vscode-font-family); --mold: #9bb07a; }
.s0 { --skin: #f7821b; --skin-d: #d9620f; --skin-l: #ff9a3c; --line: #9c3f06; --stem: #5d7f2a; --leaf: #7fae3a; }
.s1 { --skin: #ec8526; --skin-d: #c96512; --skin-l: #f6993f; --line: #8d3e0a; --stem: #627a2b; --leaf: #8aa63c; }
.s2 { --skin: #d18a3c; --skin-d: #ad6a26; --skin-l: #dc9a52; --line: #7a4514; --stem: #6b6f2c; --leaf: #9c9a40; }
.s3 { --skin: #ae7f3e; --skin-d: #8c6230; --skin-l: #b98d4f; --line: #5d3f17; --stem: #6a5a2a; --leaf: #a08a42; }
.s4 { --skin: #8a7440; --skin-d: #6c5a30; --skin-l: #94804c; --line: #4a3a18; --stem: #574426; --leaf: #8a6f3c; }
.s5 { --skin: #6b6a3a; --skin-d: #55532c; --skin-l: #75744a; --line: #3b3818; --stem: #4a3a22; --leaf: #6a5432; }
/* The pumpkin takes whatever height is left, so everything fits when you resize the panel. */
.ui { flex: 1; min-height: 0; display: flex; flex-direction: column; justify-content: center; }
svg { flex: 0 1 auto; min-height: 0; width: 100%; height: auto; }
.lobe { stroke: var(--line); stroke-width: 3; }
.out { fill: var(--skin-d); } .mid { fill: var(--skin); } .top { fill: var(--skin-l); }
.stem-shape { fill: var(--stem); stroke: var(--line); stroke-width: 2.5; }
.vine { fill: none; stroke: var(--stem); stroke-width: 3.5; stroke-linecap: round; }
.leaf { fill: var(--leaf); stroke: var(--line); stroke-width: 2; }
.shadow { fill: #3a241433; transform-box: fill-box; transform-origin: center; }
.s4 .shadow { transform: scaleX(1.15); } .s5 .shadow { transform: scaleX(1.3); }
.body, .stem { transform-box: view-box; }
.body { transform-origin: 200px 344px; }
.s1 .body { transform: scale(1.02, .97); } .s2 .body { transform: scale(1.05, .93); }
.s3 .body { transform: scale(1.09, .87); } .s4 .body { transform: scale(1.17, .75) skewX(-4deg); }
.s5 .body { transform: scale(1.28, .42); }
.stem { transform-origin: 205px 150px; }
.s4 .stem { transform: rotate(-20deg); } .s5 .stem { transform: rotate(-70deg) translateY(10px); }
.soft { fill: #6b3a12; opacity: 0; } .r1 .soft { opacity: .35; } .r3 .soft { opacity: .55; }
.mold, .puddle, .flies, .stink, .extra, .ghost, .happy, .tired, .dead, .smile, .meh, .sad, .sweat { opacity: 0; }
.r2 .m2, .r3 .m3, .r4 .m4 { opacity: .92; }
.puddle { fill: var(--skin-d); stroke: var(--line); stroke-width: 2.5; }
.r4 .puddle { opacity: .35; } .r5 .puddle, .r3 .flies, .r3 .stink, .r4 .extra, .s5 .ghost { opacity: 1; }
.s0 .happy, .s1 .happy, .s2 .tired, .s3 .tired, .s4 .tired, .s5 .dead,
.s0 .smile, .s1 .meh, .s2 .meh, .s3 .sad, .s4 .sad, .s3 .sweat, .s4 .sweat { opacity: 1; }
.face path { stroke: #2b1a0e; stroke-width: 3.5; stroke-linecap: round; fill: none; }
.face .eye { fill: #2b1a0e; stroke: none; } .face .tongue { fill: #e46a6a; stroke: none; }
.face .sweat { fill: #8fd0ff; stroke: none; } .glint { fill: #fff; }
.blush { fill: #ff6b6b; opacity: .35; } .r3 .blush { opacity: 0; }
.fly { fill: #2b2118; stroke: #fffa; stroke-width: 2; }
.stink path { fill: none; stroke: #8fa35a; stroke-width: 3; stroke-linecap: round; }
.ghost .sheet { fill: #fff; stroke: #c9b9a6; stroke-width: 2; } .ghost .eye { fill: #2b1a0e; }
.stage { margin: 4px 0; font-size: 1.3em; font-weight: 600; }
.stage, .track, button { flex-shrink: 0; }
.track { height: 8px; border-radius: 4px; background: var(--vscode-input-background); overflow: hidden; }
.bar { height: 100%; background: var(--skin); }
button { width: 100%; margin-top: 8px; padding: 6px; border: 0; border-radius: 2px; cursor: pointer;
  color: var(--vscode-button-foreground); background: var(--vscode-button-background); }
.msg, .offline .ui { display: none; } .offline .msg { display: block; }
@media (max-height: 130px) { button { display: none; } }
</style></head>
<body class="offline">
<p class="msg">Waking up the pumpkin…<br>(Rotkin needs Python 3)</p>
<div class="ui">
<svg viewBox="20 85 360 290">
  <defs>
    <filter id="sketch"><feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="4"/><feDisplacementMap in="SourceGraphic" scale="3.5"/></filter>
    <radialGradient id="shine" cx=".38" cy=".28" r=".6"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <g id="spore"><circle r="12" fill="var(--mold)"/><circle r="7" cx="-4" cy="-3" fill="#c6d4a8"/><circle r="3" cx="6" cy="5" fill="#e6eed6"/><circle r="2.5" cx="10" cy="-8" fill="#c6d4a8"/></g>
  </defs>
  <ellipse class="shadow" cx="200" cy="346" rx="128" ry="13"/>
  <path class="puddle" d="M48 344 q30-22 152-18 q120-4 152 18 q6 16-40 16 q-6 12-24 4 q-60 6-176 0 q-14 10-26-2 q-44 0-38-18z"/>
  <g class="body" filter="url(#sketch)">
    <g class="stem">
      <path class="vine" d="M214 138 c20-16 44-8 40 8 c-3 12-20 11-18 1"/>
      <path class="leaf" d="M212 126 c16-26 54-28 66-12 c-22 2-40 16-66 12z"/>
      <path class="stem-shape" d="M190 152 c-6-22 0-46 22-56 l9 12 c-14 8-18 24-12 44z"/>
    </g>
    <ellipse class="lobe out" cx="126" cy="252" rx="78" ry="86"/><ellipse class="lobe out" cx="274" cy="252" rx="78" ry="86"/>
    <ellipse class="lobe mid" cx="162" cy="248" rx="70" ry="94"/><ellipse class="lobe mid" cx="238" cy="248" rx="70" ry="94"/>
    <ellipse class="lobe top" cx="200" cy="246" rx="58" ry="98"/>
    <ellipse cx="200" cy="246" rx="150" ry="96" fill="url(#shine)"/>
    <ellipse class="soft" cx="112" cy="286" rx="24" ry="17"/>
    <g class="mold m2"><use href="#spore" transform="translate(140 212)"/><use href="#spore" transform="translate(252 304) scale(.8)"/><use href="#spore" transform="translate(304 236) scale(.7)"/></g>
    <g class="mold m3"><use href="#spore" transform="translate(92 262) scale(1.2)"/><use href="#spore" transform="translate(214 182) scale(.8)"/><use href="#spore" transform="translate(172 318) scale(.9)"/></g>
    <g class="mold m4"><use href="#spore" transform="translate(128 196) scale(1.3)"/><use href="#spore" transform="translate(318 282) scale(1.1)"/><use href="#spore" transform="translate(240 330) scale(.9)"/></g>
    <g class="face">
      <ellipse class="blush" cx="162" cy="270" rx="11" ry="6"/><ellipse class="blush" cx="238" cy="270" rx="11" ry="6"/>
      <g class="happy"><ellipse class="eye" cx="178" cy="246" rx="7" ry="10"/><ellipse class="eye" cx="222" cy="246" rx="7" ry="10"/><circle class="glint" cx="180" cy="242" r="2.5"/><circle class="glint" cx="224" cy="242" r="2.5"/></g>
      <g class="tired"><path d="M168 246 h20 M212 246 h20"/><path class="eye" d="M169 247 a9 8 0 0 0 18 0z M213 247 a9 8 0 0 0 18 0z"/></g>
      <g class="dead"><path d="M170 238 l16 16 M186 238 l-16 16 M214 238 l16 16 M230 238 l-16 16"/></g>
      <path class="smile" d="M186 270 q14 14 28 0"/><path class="meh" d="M187 276 q6-5 13 0 t13 0"/><path class="sad" d="M186 282 q14-13 28 0"/>
      <g class="dead"><path d="M182 278 q18-9 36 0"/><path class="tongue" d="M202 277 q0 13 9 10 q4-3 2-11z"/></g>
      <path class="sweat" d="M252 214 q-7 11 0 15 q7-4 0-15z"/>
    </g>
  </g>
  <g class="stink"><path d="M120 150 q-8-10 0-20 q8-10 0-20"/><path d="M290 160 q-8-10 0-20 q8-10 0-20"/></g>
  <g class="flies"><circle class="fly" cx="196" cy="104" r="5"/><circle class="fly" cx="96" cy="170" r="5"/><circle class="fly" cx="318" cy="178" r="5"/>
    <g class="extra"><circle class="fly" cx="60" cy="280" r="5"/><circle class="fly" cx="262" cy="118" r="5"/></g></g>
  <g class="ghost" transform="translate(200 140)">
    <path class="sheet" d="M-22 18 v-18 a22 22 0 0 1 44 0 v18 l-7-6 -7 6 -8-6 -7 6 -8-6z"/>
    <circle class="eye" cx="-8" cy="-2" r="3"/><circle class="eye" cx="8" cy="-2" r="3"/>
  </g>
</svg>
<div class="stage" id="stage"></div>
<div class="track"><div class="bar" id="bar"></div></div>
<button id="grass">🌱 Touch Grass</button>
</div>
<script nonce="NONCE">
const api = acquireVsCodeApi();
const STAGES = ["Fresh", "Soft Spot", "Moldy", "Fruit Flies", "Collapsing", "Dead"];
window.addEventListener("message", ({ data }) => {
  if (!data) return (document.body.className = "offline");
  const i = STAGES.indexOf(data.stage);
  document.body.className = "s" + i + " " + STAGES.slice(1, i + 1).map((_, k) => "r" + (k + 1)).join(" ");
  document.getElementById("stage").textContent = data.stage + " · " + Math.round(data.rot) + "%";
  document.getElementById("bar").style.width = data.rot + "%";
});
document.getElementById("grass").onclick = () => api.postMessage("grass");
</script>
</body></html>`;

function deactivate() {
  server?.kill();
}

module.exports = { activate, deactivate };
