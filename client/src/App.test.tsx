import { render, screen } from "@testing-library/react";

import App from "./App";

describe("App", () => {
  it("App renders expected text", () => {
    render(<App />);
    expect(screen.getByText("DIBBs eCR Refiner")).toBeInTheDocument();
  });
});
