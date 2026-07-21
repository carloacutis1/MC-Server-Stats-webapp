# api_project
Observability stack for Minecraft server


1. Pick your stack and scaffold the project. Choose a language/framework (Python + FastAPI or Node + Express are the common resume picks), make a GitHub repo, and get a "hello world" endpoint running locally. Getting the boring skeleton working first makes everything after feel incremental.

2. Build the event ingestion piece. This is basically the script from earlier, repurposed: something tails the Minecraft log, parses joins/leaves/starts/stops, and instead of sending a notification directly, it POSTs the event to your API. Now your API has a data source.

3. Add a database and store the events. Stand up Postgres (or even SQLite to start — totally fine), design a couple of tables (events, players, maybe sessions), and have the ingestion endpoint write to it. This is where playtime and history become possible.

4. Build the read endpoints. GET /players/online, GET /events, GET /players/{name}/playtime — the fun part, because now querying your API returns real data about your real server.

5. Add notifications as a feature of the API. Move the ntfy/Discord/SMS logic into the API: when an event comes in, the API decides who to notify. A POST /webhooks endpoint for registering notification targets makes it feel like a real product.

6. Add auth. API keys are enough — a header check middleware. This is a small step but it's the one interviewers ask about, so don't skip it.

7. Deploy it on your Ubuntu box. Run it as a systemd service or in Docker, sitting alongside the Minecraft server. Now it's live 24/7, which is what lets you say "running in production" with a straight face.

8. Polish for the resume. A good README with an architecture diagram, some tests, maybe GitHub Actions running them on push. This step is disproportionately valuable relative to effort — the README is what a hiring manager actually looks at.
