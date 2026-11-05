// Copies the Python app into the extension before packaging, so the repo root stays the only source.
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const out = path.join(__dirname, "python");
fs.mkdirSync(out, { recursive: true });
for (const file of ["rotkin.py", "server.py", "dashboard.html", "install.py", "uninstall.py"]) {
  fs.copyFileSync(path.join(root, file), path.join(out, file));
}
fs.copyFileSync(path.join(root, "LICENSE"), path.join(__dirname, "LICENSE"));
console.log("Bundled the Python app into vscode/python");
