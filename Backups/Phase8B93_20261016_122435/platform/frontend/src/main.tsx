import React from "react";
import { createRoot } from "react-dom/client";
import AuthRoot from "./auth/AuthRoot";
import "./style.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthRoot />
  </React.StrictMode>,
);
