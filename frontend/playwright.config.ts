import { defineConfig } from "@playwright/test";

// End-to-end run on its own ports and a throwaway database, so it never touches dev data.
const API_PORT = 8011;
const WEB_PORT = 3011;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  use: { baseURL: `http://localhost:${WEB_PORT}`, channel: "chrome", headless: true },
  webServer: [
    {
      command: `rm -f e2e.db && DATABASE_URL=sqlite:///./e2e.db CORS_ORIGINS=http://localhost:${WEB_PORT} .venv/bin/uvicorn app.main:app --port ${API_PORT}`,
      cwd: "../backend",
      url: `http://localhost:${API_PORT}/health`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `NEXT_PUBLIC_API_URL=http://localhost:${API_PORT} npx next dev --turbopack -p ${WEB_PORT}`,
      url: `http://localhost:${WEB_PORT}`,
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
