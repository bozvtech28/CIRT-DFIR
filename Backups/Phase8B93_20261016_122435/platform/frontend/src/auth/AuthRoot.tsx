import { useEffect, useState } from "react";
import { MsalProvider, useMsal } from "@azure/msal-react";
import type { PublicClientApplication } from "@azure/msal-browser";
import App from "../App";
import {
  entraConfigurationErrors,
  getEntraApiScope,
  isEntraConfigured,
} from "./entraConfig";
import { initializeMsal } from "./msalInstance";

function AuthenticationControls() {
  const { instance, accounts, inProgress } = useMsal();
  const account = instance.getActiveAccount() ?? accounts[0] ?? null;
  const [actionError, setActionError] = useState("");

  async function signIn() {
    setActionError("");
    try {
      await instance.loginRedirect({ scopes: [getEntraApiScope()] });
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Sign-in could not start.");
    }
  }

  async function signOut() {
    setActionError("");
    try {
      await instance.logoutRedirect({ account });
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Sign-out could not start.");
    }
  }

  return (
    <section
      style={{
        padding: "12px 20px",
        borderBottom: "1px solid #d5dce5",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px",
        flexWrap: "wrap",
      }}
      aria-label="Microsoft Entra authentication"
    >
      <div>
        <strong>Microsoft Entra authentication</strong>
        <div role="status" aria-live="polite">
          {inProgress !== "none"
            ? "Authentication in progress…"
            : account
              ? `Signed in: ${account.username}`
              : "Not signed in. Sign in to request protected API data."}
        </div>
        {actionError && <p role="alert">{actionError}</p>}
      </div>
      {account ? (
        <button type="button" onClick={() => void signOut()} disabled={inProgress !== "none"}>
          Sign out
        </button>
      ) : (
        <button type="button" onClick={() => void signIn()} disabled={inProgress !== "none"}>
          Sign in with Microsoft
        </button>
      )}
    </section>
  );
}

function AuthenticatedApplication() {
  return (
    <>
      <AuthenticationControls />
      <App />
    </>
  );
}

export default function AuthRoot() {
  const [client, setClient] = useState<PublicClientApplication | null>(null);
  const [initializationError, setInitializationError] = useState("");

  useEffect(() => {
    let mounted = true;

    if (isEntraConfigured) {
      void initializeMsal()
        .then((initializedClient) => {
          if (mounted) setClient(initializedClient);
        })
        .catch((error: unknown) => {
          if (mounted) {
            setInitializationError(
              error instanceof Error ? error.message : "MSAL initialization failed."
            );
          }
        });
    }

    return () => {
      mounted = false;
    };
  }, []);

  if (!isEntraConfigured) {
    return (
      <>
        <section role="status" style={{ padding: 16, borderBottom: "1px solid #d5dce5" }}>
          <strong>Authentication not configured</strong>
          <ul>
            {entraConfigurationErrors.map((message) => <li key={message}>{message}</li>)}
          </ul>
          <p>Live Entra sign-in is disabled until approved settings are supplied.</p>
          <p>Do not treat demonstration data as authenticated incident data.</p>
        </section>
        <App />
      </>
    );
  }

  if (initializationError) {
    return <section role="alert" style={{ padding: 16 }}>
      Microsoft Entra initialization failed: {initializationError}
    </section>;
  }

  if (!client) {
    return <section role="status" style={{ padding: 16 }}>
      Initializing Microsoft Entra authentication…
    </section>;
  }

  return (
    <MsalProvider instance={client}>
      <AuthenticatedApplication />
    </MsalProvider>
  );
}
