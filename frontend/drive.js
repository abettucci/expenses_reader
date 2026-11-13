// Google Drive read-only access for statement import.
// Uses Google Identity Services in the browser: no client secret and no backend.
// The access token lives only in memory and is discarded on page refresh.

// OAuth Web client ID from Google Cloud Console (not a secret).
// Its authorized JavaScript origins must include https://expenses-reader.vercel.app
// (and http://localhost:<port> for local tests).
export const GOOGLE_CLIENT_ID = "364424801820-55db8m0j7aija70oce7th4i747hnuq4b.apps.googleusercontent.com";

const DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly";
const GIS_SRC = "https://accounts.google.com/gsi/client";
const MAX_BYTES = 15 * 1024 * 1024;
const SOURCE_MIME_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
];

let tokenClient = null;
let accessToken = "";
let tokenExpiresAt = 0;
let pending = null;

function loadGis() {
  if (window.google?.accounts?.oauth2) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = GIS_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("No se pudo cargar el servicio de Google."));
    document.head.append(script);
  });
}

function ensureTokenClient() {
  if (tokenClient) return;
  tokenClient = window.google.accounts.oauth2.initTokenClient({
    client_id: GOOGLE_CLIENT_ID,
    scope: DRIVE_SCOPE,
    callback: (response) => {
      if (!pending) return;
      const { resolve, reject } = pending;
      pending = null;
      if (response.error) {
        reject(new Error(response.error));
        return;
      }
      accessToken = response.access_token;
      tokenExpiresAt = Date.now() + (Number(response.expires_in) || 3600) * 1000 - 60_000;
      resolve(accessToken);
    },
    error_callback: (error) => {
      if (!pending) return;
      const { reject } = pending;
      pending = null;
      reject(new Error(error?.type || "popup_failed"));
    },
  });
}

function getToken() {
  if (accessToken && Date.now() < tokenExpiresAt) return Promise.resolve(accessToken);
  return new Promise((resolve, reject) => {
    pending = { resolve, reject };
    tokenClient.requestAccessToken({ prompt: accessToken ? "" : "consent" });
  });
}

async function driveGet(url, token) {
  const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw new Error(`Google Drive respondió ${response.status}.`);
  return response;
}

async function listStatementFiles(token) {
  const mimeQuery = SOURCE_MIME_TYPES.map((type) => `mimeType='${type}'`).join(" or ");
  const params = new URLSearchParams({
    q: `(${mimeQuery}) and trashed=false`,
    orderBy: "modifiedTime desc",
    pageSize: "25",
    fields: "files(id,name,mimeType,size)",
  });
  const data = await (await driveGet(`https://www.googleapis.com/drive/v3/files?${params}`, token)).json();
  return data.files || [];
}

async function downloadStatementFile(file, token) {
  if (Number(file.size) > MAX_BYTES) throw new Error("Ese archivo supera 15 MB.");
  const response = await driveGet(
    `https://www.googleapis.com/drive/v3/files/${encodeURIComponent(file.id)}?alt=media`,
    token,
  );
  const blob = await response.blob();
  return new File([blob], file.name, { type: file.mimeType });
}

function renderFileList(files, token, { onFile, notify }) {
  const container = document.getElementById("drive-files");
  if (!container) return;
  container.replaceChildren();
  container.hidden = false;

  if (!files.length) {
    const empty = document.createElement("p");
    empty.className = "upload-help";
    empty.textContent = "No encontré PDF ni Excel .xlsx en tu Google Drive.";
    container.append(empty);
    return;
  }

  for (const file of files) {
    const button = document.createElement("button");
    button.className = "source-option integration-option";
    button.type = "button";
    const label = document.createElement("span");
    const name = document.createElement("strong");
    name.textContent = file.name;
    label.append(name);
    button.append(label);
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        const downloaded = await downloadStatementFile(file, token);
        container.hidden = true;
        await onFile(downloaded);
      } catch (error) {
        notify(error.message || "No se pudo descargar el archivo de Drive.");
        button.disabled = false;
      }
    });
    container.append(button);
  }
}

export async function openDriveFiles({ onFile, notify }) {
  if (!GOOGLE_CLIENT_ID) {
    notify("Google Drive todavía no está configurado: falta el Client ID.");
    return;
  }
  try {
    await loadGis();
    ensureTokenClient();
    const token = await getToken();
    const files = await listStatementFiles(token);
    const status = document.querySelector("#drive-option .source-soon");
    if (status) status.textContent = "Conectado";
    renderFileList(files, token, { onFile, notify });
  } catch (error) {
    notify(
      error.message === "popup_closed" || error.message === "popup_failed"
        ? "Se cerró la ventana de Google antes de conectar."
        : "No pude conectar con Google Drive. Probá de nuevo.",
    );
  }
}
