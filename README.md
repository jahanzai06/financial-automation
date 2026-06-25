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

### Step 2: Create a Free PostgreSQL Database

1. Sign up at [Neon.tech](https://neon.tech) or [Supabase.com](https://supabase.com) (both offer a generous 100% free database plan).
2. Create a new project/database.
3. Copy the database connection string (looks like `postgresql://user:password@host/dbname`).

---

### Step 3: Deploy to Render (100% Free)

1. Go to [Render](https://render.com) and sign up/log in.
2. Click **New** -> **Web Service**.
3. Connect your GitHub account and select the `financial-automation` repository.
4. Set the following settings:
   - **Environment**: `Docker` (it will automatically build using the included `Dockerfile`)
   - **Region**: Select the closest region to you.
   - **Instance Type**: Select the **Free** tier.
5. In **Environment Variables** (under Advanced):
   - Add Key: `GEMINI_API_KEY`, Value: `your_actual_gemini_api_key`
   - Add Key: `DATABASE_URL`, Value: `your_postgres_connection_string` (pasted from Step 2)
6. Click **Deploy Web Service**. Once built, Render will give you a public URL (e.g., `https://your-app.onrender.com`) which you can open on your phone!

---

### Step 4: Deploy to Railway (Alternative Option)

1. Go to [Railway.app](https://railway.app) and sign up.
2. Click **New Project** -> **Deploy from GitHub repo** and select your repository.
3. Go to the **Variables** tab and add:
   - `GEMINI_API_KEY` = `your_actual_gemini_api_key`
   - `DATABASE_URL` = `your_postgres_connection_string` (pasted from Step 2)
4. Go to **Settings** -> **Public Networking** and click **Generate Domain** to get a public URL for your phone.
