export const sampleLogs = [
  {
    id: "missing-dependency",
    title: "Missing dependency",
    logs: `[CI] Installing dependencies...
[CI] Running tests...
Traceback (most recent call last):
  File "/app/main.py", line 4, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
ERROR: Job failed: exit code 1`
  },
  {
    id: "docker-build-failure",
    title: "Docker build failure",
    logs: `Step 7/10 : RUN npm run build
 ---> Running in 7e2a4f1c24b0
> frontend@1.0.0 build
> vite build

src/App.jsx:12:19: error: Could not resolve "axios"
failed to solve: process "/bin/sh -c npm run build" did not complete successfully: exit code: 1
ERROR: Docker image build failed`
  },
  {
    id: "timeout-error",
    title: "Timeout error",
    logs: `[Pipeline] Deploying service to staging...
[Pipeline] Waiting for readiness probe...
ERROR: deployment exceeded its progress deadline
Readiness probe failed: Get "http://10.0.0.18:8080/health": context deadline exceeded
FAILED: rollout status check timed out after 600 seconds`
  }
]

