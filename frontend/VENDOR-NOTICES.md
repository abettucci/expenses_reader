# Bundled browser libraries

The deployed static bundle (`app.bundle.js`) includes the following libraries. Their license notices are retained in the bundle.

- fflate 0.8.3 — MIT
- Mozilla PDF.js 5.4.624 — Apache-2.0
- esbuild 0.28.2 — MIT (build-time bundler)

`pdf.worker.mjs` is the matching PDF.js worker and is served from the same deployment. Uploaded statements are parsed in the browser and are not sent to a server.
