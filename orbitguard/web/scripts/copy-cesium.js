// Copy Cesium's static assets into public/ so the viewer can load workers,
// imagery (offline NaturalEarthII) and widgets CSS without a CDN or ion token.
const fs = require("fs");
const path = require("path");

const src = path.join(__dirname, "..", "node_modules", "cesium", "Build", "Cesium");
const dst = path.join(__dirname, "..", "public", "cesium");

if (!fs.existsSync(src)) {
  console.error("cesium build assets not found at", src);
  process.exit(1);
}
fs.rmSync(dst, { recursive: true, force: true });
fs.cpSync(src, dst, { recursive: true });
console.log("copied Cesium assets ->", dst);
