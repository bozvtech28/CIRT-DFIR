import type { AccountInfo, PublicClientApplication } from "@azure/msal-browser";
import { getEntraApiScope } from "./entraConfig";

/**
 * Acquires an API access token silently for an existing signed-in account.
 * This helper never accepts a token or role from caller-controlled input.
 * It does not initiate interactive sign-in and does not call the API itself.
 */
export async function acquireEntraApiAccessToken(
  instance: PublicClientApplication
): Promise<string> {
  const account: AccountInfo | null =
    instance.getActiveAccount() ?? instance.getAllAccounts()[0] ?? null;

  if (!account) {
    throw new Error("Sign-in is required before requesting an API access token.");
  }

  const result = await instance.acquireTokenSilent({
    account,
    scopes: [getEntraApiScope()],
  });

  if (!result.accessToken || !result.accessToken.trim()) {
    throw new Error("Microsoft Entra returned no usable API access token.");
  }

  return result.accessToken;
}
