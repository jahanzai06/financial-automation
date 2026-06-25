# AI Financial Automation System

A premium dashboard for tracking personal financial transactions parsed via Gemini AI.

## Getting Started (Local Development)

1. Clone or download this project.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
4. Run the application:
   ```bash
   python main.py
   ```
5. Open http://localhost:8000 on your computer.

---

## Deploying to the Cloud (Accessing from Mobile)

To access this application from your mobile phone even when your laptop is turned off, you can deploy it to a cloud provider like **Render** or **Railway**.

### Step 1: Push to GitHub

1. Open your terminal in this directory and initialize Git:
   ```bash
   git init
   ```
2. Stage and commit the files (your local `.env` and `ledger.db` will be ignored automatically due to `.gitignore`):
   ```bash
   git add .
   ```
3. Commit the changes:
   ```bash
   git commit -m "Initial commit for cloud deployment"
   ```
4. Go to [GitHub](https://github.com), create a new **Private** repository.
5. Follow the GitHub instructions to link and push your local repository:
   ```bash
   git remote add origin https://github.com/your-username/your-repo-name.git
   git branch -M main
   git push -u origin main
   ```

---

### Step 2: Deploy to Render (Option A - Free Tier)

1. Go to [Render](https://render.com) and sign up/log in.
2. Click **New** -> **Web Service**.
3. Connect your GitHub account and select your repository.
4. Set the following settings:
   - **Environment**: `Docker` (it will automatically build using the included `Dockerfile`)
   - **Region**: Select the closest region to you.
5. In **Environment Variables** (under Advanced):
   - Add Key: `GEMINI_API_KEY`, Value: *Your Gemini API Key*
6. **Setting up Persistent Storage (Crucial so you don't lose data)**:
   - Render's free tier has an ephemeral filesystem. If your service restarts, your SQLite database (`ledger.db`) resets.
   - To prevent this, scroll down to **Disk** (in the advanced settings).
   - Click **Add Disk**:
     - **Name**: `ledger-db-disk`
     - **Mount Path**: `/data`
     - **Size**: `1 GiB` (more than enough for SQLite)
   - Add another Environment Variable to redirect the database path to the disk:
     - Add Key: `DATABASE_PATH`, Value: `/data/ledger.db`
7. Click **Create Web Service**. Once deployed, Render will provide a public URL (e.g., `https://your-app.onrender.com`) that you can open on your phone!

---

### Step 3: Deploy to Railway (Option B - Simple & Quick Setup)

1. Go to [Railway.app](https://railway.app) and sign up/log in.
2. Click **New Project** -> **Deploy from GitHub repo** and select your repository.
3. Once the service is created, go to **Variables**:
   - Add `GEMINI_API_KEY` = *Your Gemini API Key*
4. Go to **Settings** -> **Public Networking**:
   - Click **Generate Domain** to get a public URL for your phone.
5. **Setting up Persistent Storage**:
   - Go to your project canvas, click **+ New** -> **Volume** (creates a persistent disk).
   - Mount this Volume to your service at `/data`.
   - Go to **Variables** and add: `DATABASE_PATH` = `/data/ledger.db`
