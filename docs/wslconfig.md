# WSL2 Resource Limits

Follow this guide if Docker Desktop on Windows is consuming too much RAM via `VmmemWSL` while running the project stack.

## 1. Prerequisites
- Windows 10/11 with WSL2 and Docker Desktop (WSL backend) installed.
- Administrative PowerShell or CMD when editing config files outside your Windows profile.

## 2. Create or Update `.wslconfig`
1. Open PowerShell (no elevation required) and run:
	```powershell
	notepad $env:USERPROFILE\.wslconfig
	```
2. Paste or adjust the sample configuration:
	```ini
	[wsl2]
	memory=6GB          # Cap total RAM available to all WSL distros
	processors=4        # Optional: limit CPU cores exposed to WSL
	swap=2GB            # Optional: reduce or disable swap (swap=0)
	localhostForwarding=true
	```
	Adjust the values to suit your hardware (leave headroom for Windows; 6–8 GB works well for this project).

## 3. Apply the Settings
Run the following to restart WSL:
```powershell
wsl --shutdown
```
Docker Desktop will restart its Linux VM the next time you launch it and will respect the new limits.

## 4. Verify Resource Caps
- Open Task Manager → Performance → Memory and confirm that `VmmemWSL` stays near the configured ceiling.
- Inside a WSL shell, run `free -h` to see the limited memory reported to Linux.

## 5. Optional Project Tweaks
- `docker compose down` when you finish development sessions to free resources immediately.
- Consider adding `mem_limit` settings to `docker-compose.yml` for additional container-level guardrails if needed.

## 6. Troubleshooting
- Containers failing with `Out of memory` errors? Increase the `memory` value or adjust Postgres settings.
- No effect after editing `.wslconfig`? Make sure you saved the file under your Windows user profile and ran `wsl --shutdown`.
- Sharing machines? Each developer should apply these steps on their own profile; the repo cannot enforce them automatically.
