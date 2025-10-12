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

## 5. Ensuring docker closes properly

- When Docker is opened on a Windows systems or opens during start (dockers can Auto Start). It starts WSL (Window System Linux), running a program that's visible in task manager called `VmmemWSL`.
- This program can take up alot of memory and can still run when docker is closed, sometimes `VmmemWSL` won't end and `wsl --shutdown` won't end the task. 
- This is because Docker is still running even when the app is closed, to properly close docker;

```powershell
	1. Open task mangaer and search 'docker' in processor
	2. Right click on "Docker desktop backend" and click end task
	3. Then do the same on the Docker Desktop
	4. Then open powershell and use: wsl --shutdown
```
This will allow docker to properly close and close any other instances of WSL.

## 6. Optional Project Tweaks
- `docker compose down` when you finish development sessions to free resources immediately.
- Consider adding `mem_limit` settings to `docker-compose.yml` for additional container-level guardrails if needed.

## 7. Troubleshooting
- Containers failing with `Out of memory` errors? Increase the `memory` value or adjust Postgres settings.
- No effect after editing `.wslconfig`? Make sure you saved the file under your Windows user profile and ran `wsl --shutdown`.
- Sharing machines? Each developer should apply these steps on their own profile; the repo cannot enforce them automatically.
