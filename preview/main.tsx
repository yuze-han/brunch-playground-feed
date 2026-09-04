import React from "react"
import ReactDOM from "react-dom/client"
import Playground from "../figma/Playground"
import "./styles.css"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <main className="preview-shell">
      <Playground />
    </main>
  </React.StrictMode>,
)
