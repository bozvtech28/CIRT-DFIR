// Uses the browser DOM RequestInfo and RequestInit types.
import { acquireEntraApiAccessToken } from "./entraToken";
import { getMsalInstance } from "./msalInstance";

/**
 * Sends a request with a freshly acquired Entra API access token.
 * No browser-supplied role or identity is treated as authorization.
 */
export async function authenticatedFetch(
  input: string | URL | Request,
  init: RequestInit = {}
): Promise<Response> {
  const token = await acquireEntraApiAccessToken(getMsalInstance());
  const headers = new Headers(init.headers);
  headers.set("Accept", headers.get("Accept") ?? "application/json");
  headers.set("Authorization", `Bearer ${token}`);

  return fetch(input, { ...init, headers });
}

