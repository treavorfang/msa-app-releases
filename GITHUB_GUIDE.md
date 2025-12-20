# GitHub Guide: Professional "Private Code" Setup

To keep your source code 100% private but still allow users to get updates, we use a **Two-Repo Strategy**.

## 1. The Setup (Do this now)

### A. Make your Code Private

1.  Go to your repository: [github.com/treavorfang/msa-desktop](https://github.com/treavorfang/msa-desktop).
2.  Click the **Settings** tab.
3.  Scroll down to the **Danger Zone** at the bottom.
4.  Click **Change visibility** -> **Make private**.
    - _Your code is now hidden from the public!_

### B. Create a Public "Releases" Repo

1.  Click the **[+]** icon (top right) -> **New repository**.
2.  Name it: **`msa-app-releases`**.
3.  Set it to **Public**.
    - _This repo will contain NO code, only your installer files._

---

## 2. Daily Workflow

### To Save your Code (Private)

Just run your usual commands to push to `msa-desktop`:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

### To Send an Update (Public)

When you have a new version (e.g., `v1.0.4`):

1.  Go to the **`msa-app-releases`** repo on GitHub.
2.  Click **Releases** -> **Create a new release**.
3.  Set the Tag to `v1.0.4`.
4.  **Upload the EXE or DMG installer** as an asset.
5.  **Publish**.
    - _The app will check THIS repo for updates, while your code stays safe in the private one._

---

## ⚠️ Important Note

In your `src/app/config/config.py`, the `GITHUB_REPO_PUBLIC` is set to `msa-app-releases`. This is what the app uses to check for new files. Never put your code in the public repo!
