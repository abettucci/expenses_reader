import { copyFile, mkdir, rm } from "node:fs/promises";

const outputDirectory = new URL("./dist/", import.meta.url);
await rm(outputDirectory, { recursive: true, force: true });
await mkdir(outputDirectory, { recursive: true });

for (const file of ["index.html", "styles.css"]) {
  await copyFile(new URL(`./${file}`, import.meta.url), new URL(`./dist/${file}`, import.meta.url));
}

await copyFile(new URL("./app.bundle.js", import.meta.url), new URL("./dist/app.js", import.meta.url));
await copyFile(new URL("./pdf.worker.mjs", import.meta.url), new URL("./dist/pdf.worker.mjs", import.meta.url));
