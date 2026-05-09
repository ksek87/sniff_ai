# sniff_ai — Claude Code Notes

## Frontend build / CI

**Always commit `frontend/package-lock.json`.** Without it, `npm ci` fails or
produces a non-deterministic install. When adding or changing any frontend
dependency, regenerate the lockfile locally and commit it in the same PR:

```bash
cd frontend
npm install --legacy-peer-deps   # resolves deps and writes package-lock.json
git add package.json package-lock.json
```

**Verify the lockfile actually locks the intended versions** before committing.
For example, `ajv@6` must be the top-level resolved version (not `ajv@8`) or
`react-scripts 5` will fail with `Cannot find module 'ajv/dist/compile/codegen'`.
Check with:

```bash
node -e "const l=require('./frontend/package-lock.json'); console.log(l.packages['node_modules/ajv']?.version)"
```

Never work around a missing lockfile with `npm install` in CI, `overrides`, or
other hacks — fix the root cause and commit the lockfile.

## Deployment

- Backend: Hugging Face Spaces (Docker, port 7860), image at `ghcr.io/ksek87/sniff_ai/backend:latest`
- Frontend: GitHub Pages at `https://ksek87.github.io/sniff_ai/`
- HF Space must have `CORS_ORIGINS=https://ksek87.github.io` set or API calls from the frontend will be blocked
- GitHub Pages source must be set to **GitHub Actions** (not "Deploy from branch")
