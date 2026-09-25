# GitHub Actions Log Extractor 🚀

A lightweight, modern web application built with **FastAPI** that automatically extracts and displays logs from failed GitHub Actions workflow runs. 

## ✨ Features
- **Auto-fetching Repositories:** Automatically lists all repositories accessible by your GitHub Personal Access Token.
- **Log Extraction:** Detects failed workflow jobs and pulls the raw error logs directly from the GitHub API.
- **Beautiful UI:** A clean, dark-themed frontend interface for ease of use.
- **Secure:** Uses environment variables to securely store and inject your GitHub PAT.

## 🛠️ Tech Stack
- **Backend:** Python, FastAPI, Uvicorn, HTTPX
- **Frontend:** HTML, Vanilla CSS, Vanilla JavaScript

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/github-webhook.git
cd github-webhook
```

### 2. Set up the virtual environment
```bash
python -m venv venv
```

**Activate the virtual environment:**
- **Windows:** `.\venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file from the provided example template:
```bash
cp .env.example .env
```
Open the `.env` file and paste in your GitHub Personal Access Token (PAT).
*Note: Your PAT needs `repo` scopes to read workflow runs from private repositories.*

### 5. Run the application

**Option A: Using Python directly**
Start the FastAPI development server using Uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Option B: Using Docker 🐳**
Build and run the container:
```bash
docker build -t github-actions-detective .
docker run -p 8001:8001 --env-file .env github-actions-detective
```

### 6. Usage
1. Open your browser and navigate to: **http://localhost:8001**
2. The dropdown will automatically populate with your GitHub repositories.
3. Select a repository to automatically fetch the latest failed GitHub Action logs.
4. If you want to use the API programmatically, you can view the auto-generated Swagger UI at `http://localhost:8001/docs`.

---

## 🧪 Testing
If you want to test the extractor, you can intentionally fail a GitHub Action in one of your repositories. Create a `.github/workflows/fail-test.yml` file with an `exit 1` command in the `run` step and push it to your repository. The app will detect the failure and display the crash log.
