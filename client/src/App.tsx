import { useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";

function App() {
  const [count, setCount] = useState(0);
  const [status, setStatus] = useState<string | null>(null);

  async function onClick() {
    const req = await (await fetch("/api")).json();
    setStatus(req);
  }

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
      </div>
      <button onClick={onClick}>Run health check</button>
      {status ? (
        <>
          <pre>{JSON.stringify(status)}</pre>
          <button onClick={() => setStatus(null)}>Clear</button>
        </>
      ) : null}
    </>
  );
}

export default App;
