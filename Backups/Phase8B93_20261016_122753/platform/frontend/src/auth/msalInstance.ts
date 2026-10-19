import { PublicClientApplication } from "@azure/msal-browser";
import { getEntraConfiguration, isEntraConfigured } from "./entraConfig";

let instance: PublicClientApplication | null = null;
let initialization: Promise<PublicClientApplication> | null = null;

export function getMsalInstance(): PublicClientApplication {
  if (!isEntraConfigured) {
    throw new Error("Microsoft Entra is not configured.");
  }

  if (!instance) {
    instance = new PublicClientApplication(getEntraConfiguration());
  }

  return instance;
}

export function initializeMsal(): Promise<PublicClientApplication> {
  if (!initialization) {
    initialization = (async () => {
      const client = getMsalInstance();
      await client.initialize();

      const redirectResult = await client.handleRedirectPromise();
      if (redirectResult?.account) {
        client.setActiveAccount(redirectResult.account);
      } else if (!client.getActiveAccount()) {
        const accounts = client.getAllAccounts();
        if (accounts.length === 1) {
          client.setActiveAccount(accounts[0]);
        }
      }

      return client;
    })().catch((error: unknown) => {
      initialization = null;
      throw error;
    });
  }

  return initialization;
}
