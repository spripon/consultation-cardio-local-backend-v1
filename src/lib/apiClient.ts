const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

interface RequestOptions extends RequestInit {
  // If set, body is a FormData and Content-Type is omitted automatically
}

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
