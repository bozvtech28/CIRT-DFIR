import type { Configuration } from "@azure/msal-browser";

const tenantId = (import.meta.env.VITE_ENTRA_TENANT_ID ?? "").trim();
const clientId = (import.meta.env.VITE_ENTRA_CLIENT_ID ?? "").trim();
const apiScope = (import.meta.env.VITE_ENTRA_API_SCOPE ?? "").trim();
const redirectUri = (import.meta.env.VITE_ENTRA_REDIRECT_URI ?? "").trim();

function isPlaceholder(value: string): boolean {
  return !value ||
    value.includes("REPLACE_WITH_APPROVED") ||
    value.includes("YOUR_TENANT") ||
    value.includes("YOUR_CLIENT");
}

function isGuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

export const entraConfigurationErrors: string[] = [];

if (isPlaceholder(tenantId) || !isGuid(tenantId)) {
  entraConfigurationErrors.push("An approved Entra tenant ID is required.");
}

if (isPlaceholder(clientId) || !isGuid(clientId)) {
  entraConfigurationErrors.push("An approved SPA application client ID is required.");
}

if (
  isPlaceholder(apiScope) ||
  !/^(api:\/\/|https:\/\/)[^\s]+$/.test(apiScope)
) {
  entraConfigurationErrors.push("An approved API access scope is required.");
}

if (isPlaceholder(redirectUri)) {
  entraConfigurationErrors.push("An approved redirect URI is required.");
} else {
  try {
    const redirect = new URL(redirectUri);
    const isLocalDevelopment =
      redirect.protocol === "http:" &&
      ["localhost", "127.0.0.1"].includes(redirect.hostname);

    if (redirect.protocol !== "https:" && !isLocalDevelopment) {
      entraConfigurationErrors.push(
        "Redirect URI must use HTTPS except for localhost development."
      );
    }
  } catch {
    entraConfigurationErrors.push("Redirect URI must be a valid absolute URL.");
  }
}

export const isEntraConfigured = entraConfigurationErrors.length === 0;

export function getEntraConfiguration(): Configuration {
  if (!isEntraConfigured) {
    throw new Error(
      "Microsoft Entra sign-in is not configured. An administrator-approved configuration is required."
    );
  }

  return {
    auth: {
      clientId,
      authority: `https://login.microsoftonline.com/${tenantId}`,
      redirectUri,
      postLogoutRedirectUri: redirectUri,
    },
    cache: {
      cacheLocation: "sessionStorage",
    },
  };
}

export function getEntraApiScope(): string {
  if (!isEntraConfigured) {
    throw new Error("Microsoft Entra API scope is not configured.");
  }

  return apiScope;
}
