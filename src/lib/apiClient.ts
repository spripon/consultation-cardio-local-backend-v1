/**
 * Client HTTP du backend local.
 *
 * Fail-closed : seule une base d'URL relative (même origine) est acceptée.
 * Toute tentative de pointer vers une origine externe est ignorée, afin
 * qu'aucune donnée patient ne puisse sortir du serveur.
 */
function resolveBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (configured && configured.startsWith("/")) {
    return configured.replace(/\/$/, "");
  }
  if (configured) {
    console.warn(
      "VITE_API_BASE_URL ignoré : seule une URL relative de même origine est autorisée.",
    );
  }
  return "/api";
}

const API_BASE_URL = resolveBaseUrl();

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Erreur ${response.status}`;
    try {
      const data = await response.json();
      message = data.detail || data.message || message;
    } catch {
      message = await response.text().catch(() => message);
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response);
}

export async function postFormData<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<T>(response);
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  return handleResponse<T>(response);
}
