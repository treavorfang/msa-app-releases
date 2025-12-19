# GitHub Release Guide for MSA Updates

This guide will show you how to set up your GitHub repository so that your app's "Check for Updates" feature works correctly.

## Phase 1: Create your Repository

1.  **Sign in to GitHub**: Go to [github.com](https://github.com) and create an account if you don't have one.
2.  **New Repository**: Click the **[+]** icon at the top right -> **New repository**.
3.  **Name it**: Use the exact name we set in the code: `msa-desktop`.
4.  **Set to Public**: It must be **Public** so the app can check for updates without needing a private key.
5.  **Create**: Click **Create repository**.

## Phase 2: Upload your Code (One-time)

If your code is not yet on GitHub, run these commands in your terminal (at `/Users/studiotai/PyProject/msa`):

```bash
git init
git add .
git commit -m "Initial commit with update system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/msa-desktop.git
git push -u origin main
```

_(Replace `YOUR_USERNAME` with your actual GitHub username)_

## Phase 3: How to Publish an Update (The "Release")

When you have a new version (e.g., `1.0.4`) and you want your users to get it:

1.  **Go to your Repo**: Open `https://github.com/YOUR_USERNAME/msa-desktop` in your browser.
2.  **Releases**: On the right side, click **Releases** -> **Create a new release**.
3.  **Tag Version**: Click **Choose a tag** and type `v1.0.4` (or whatever your new version is). Then click **Create new tag**.
4.  **Title**: Give it a title, like `MSA Public Release v1.0.4`.
5.  **Description**: In the "Describe this release" box, type what has changed (e.g., "Fixed login bug"). These notes will show up in the app's Update dialog!
6.  **Upload the Installer**: Drag and drop your new `.exe` (for Windows) or `.dmg` (for macOS) into the **Assets** box at the bottom.
    - **Note**: The app looks for files ending in `.exe` or `.dmg`.
7.  **Publish**: Click the green **Publish release** button.

## ✅ DONE!

Once published, any user who clicks **Check for Updates** in their app will see your new version and can download it immediately.

---

### ⚠️ Important Configuration Match

In your `src/app/config/config.py`, make sure the `GITHUB_USER` matches your real GitHub username:

```python
GITHUB_USER = "your_actual_name" # Change this to your real GitHub username!
GITHUB_REPO = "msa-desktop"
```

If you change your username, you must update this file before building the next version!
