/* Vérification par capture avant un rendu long.
   Charge la composition, place la tête de lecture à l'instant demandé,
   applique la visibilité des .clip comme le fait le moteur, et
   photographie l'écran. Trente secondes ici évitent d'en perdre quatre-vingt-dix.

   Usage : node shot.cjs 0.9 2.6 9.0 …            (secondes)
           node shot.cjs --dir=/chemin 0.9 2.6    (dossier de sortie) */
const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const EXE = process.env.PUPPETEER_EXECUTABLE_PATH || "/opt/pw-browsers/chromium";

(async () => {
  const args = process.argv.slice(2);
  const dirArg = args.find((a) => a.startsWith("--dir="));
  const out = dirArg ? dirArg.slice(6) : path.join(__dirname, "shots");
  const times = args.filter((a) => !a.startsWith("--")).map(Number);
  if (!times.length) { console.error("aucun instant demandé"); process.exit(1); }
  fs.mkdirSync(out, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: EXE,
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--font-render-hinting=none"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 2160, height: 3840, deviceScaleFactor: 1 });
  await page.goto("file://" + path.join(__dirname, "index.html"),
                  { waitUntil: "networkidle0" });
  await page.evaluate(() => document.fonts.ready);

  for (const t of times) {
    await page.evaluate((t) => {
      // Visibilité des clips : le moteur n'affiche que ceux dont la
      // fenêtre temporelle contient l'instant courant.
      document.querySelectorAll(".clip").forEach((el) => {
        const s = parseFloat(el.dataset.start || "0");
        const d = parseFloat(el.dataset.duration || "0");
        el.style.visibility = t >= s && t < s + d ? "visible" : "hidden";
      });
      window.__timelines.main.seek(t, false);
    }, t);
    const f = path.join(out, `t${String(t).replace(".", "_")}.png`);
    await page.screenshot({ path: f });
    console.log("→", f);
  }
  await browser.close();
})();
