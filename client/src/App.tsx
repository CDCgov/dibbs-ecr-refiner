import { useState } from "react";
import "./App.css";

function App() {
  const [eicr, setEicr] = useState("");
  const [refinedEicr, setRefinedEicr] = useState("");
  const [error, setError] = useState("");

  async function refine() {
    if (!eicr) {
      setError("Please provide an eICR XML input.");
      return;
    }
    const req = await fetch("/api/ecr", {
      body: eicr,
      method: "POST",
      headers: {
        "Content-Type": "application/xml",
      },
    });
    const result = await req.text();
    setRefinedEicr(result);
    setError("");
  }

  function onReset() {
    setRefinedEicr("");
    setError("");
  }

  return (
    <>
      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <button onClick={async () => await refine()}>Refine eICR</button>
        <button onClick={onReset}>Reset</button>
      </div>
      {error ? <p>{error}</p> : null}
      <div className="io-container">
        <div style={{ width: "50%" }}>
          <label htmlFor="input">Refined eICR:</label>
          <textarea
            name="input"
            style={{ minWidth: "100%", minHeight: "100%" }}
            onChange={(e) => {
              e.preventDefault();
              setEicr(e.target.value);
            }}
            onClick={() => setError("")}
            onBlur={() => setError("")}
          />
        </div>
        <div style={{ minWidth: "50%" }}>
          <label htmlFor="output">Unrefined eICR:</label>
          <textarea
            name="output"
            style={{ minWidth: "100%", minHeight: "100%" }}
            disabled
            value={refinedEicr}
          />
        </div>
      </div>
    </>
  );
}

export default App;
