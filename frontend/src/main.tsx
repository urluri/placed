import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import LabelerApp from "./LabelerApp";
import "./styles.css";

const RootApp = window.location.pathname.startsWith("/labeler") ? LabelerApp : App;

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RootApp />
  </StrictMode>,
);
