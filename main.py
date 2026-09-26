from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="GitHub Actions Log Extractor")

GITHUB_API_URL = "https://api.github.com"

@app.get("/")
async def serve_index():
    if not os.path.exists("index.html"):
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse("index.html")

@app.get("/repos")
async def get_user_repos():
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise HTTPException(status_code=401, detail="GitHub token not configured in .env")
        
    headers = await get_github_headers(github_token)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch repos for the authenticated user, sorted by most recently updated
            repos_url = f"{GITHUB_API_URL}/user/repos"
            params = {"sort": "updated", "per_page": 100}
            
            response = await client.get(repos_url, headers=headers, params=params)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Failed to fetch repositories: {response.text}"
                )
                
            repos_data = response.json()
            
            # Return a simplified list of repositories
            repos = [
                {
                    "full_name": repo["full_name"],
                    "owner": repo["owner"]["login"],
                    "name": repo["name"]
                }
                for repo in repos_data
            ]
            
            return {"repos": repos}
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Network error while connecting to GitHub: {str(exc)}")

async def get_github_headers(token: str) -> Dict[str, str]:
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

@app.get("/logs/{owner}/{repo}/failed")
async def get_failed_logs(
    owner: str, 
    repo: str, 
    token: Optional[str] = Header(None, description="GitHub Personal Access Token (can also use GITHUB_TOKEN in .env)"),
    limit: int = Query(5, description="Number of recent failed runs to fetch")
):
    """
    Fetches the logs for recent failed GitHub Actions workflow runs for a specific repository.
    """
    github_token = token or os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise HTTPException(status_code=401, detail="GitHub token not provided in header or .env")
        
    headers = await get_github_headers(github_token)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Fetch recent workflow runs (no status filter so we can check if it's fixed)
            runs_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs"
            params = {"per_page": 50}
            
            runs_response = await client.get(runs_url, headers=headers, params=params)
        
        if runs_response.status_code != 200:
            raise HTTPException(
                status_code=runs_response.status_code, 
                detail=f"Failed to fetch workflow runs: {runs_response.text}"
            )
            
        runs_data = runs_response.json()
        all_runs = runs_data.get("workflow_runs", [])
        
        # Track the latest run for each workflow to see if it's currently failing
        latest_workflow_runs = {}
        for run in all_runs:
            w_id = run["workflow_id"]
            if w_id not in latest_workflow_runs:
                latest_workflow_runs[w_id] = run
                
        # Filter down to workflows where the *latest* run is a failure
        currently_failing_runs = [
            run for run in latest_workflow_runs.values() 
            if run.get("conclusion") == "failure"
        ]
        
        # Limit the results
        failed_runs = currently_failing_runs[:limit]
        
        if not failed_runs:
            return {"message": "All workflows are currently passing! No unresolved failures found. 🎉"}
            
        results = []
        
        # 2. For each failed run, get the jobs
        for run in failed_runs:
            run_id = run["id"]
            run_name = run["name"]
            
            jobs_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
            jobs_response = await client.get(jobs_url, headers=headers)
            
            if jobs_response.status_code != 200:
                continue
                
            jobs_data = jobs_response.json()
            failed_jobs = [job for job in jobs_data.get("jobs", []) if job.get("conclusion") == "failure"]
            
            for job in failed_jobs:
                job_id = job["id"]
                job_name = job["name"]
                
                # 3. Get logs for the failed job
                logs_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
                
                # The logs endpoint often redirects to a temporary URL containing the raw text
                logs_response = await client.get(logs_url, headers=headers, follow_redirects=True)
                
                log_content = None
                if logs_response.status_code == 200:
                    log_content = logs_response.text
                else:
                    log_content = f"Failed to fetch logs. Status: {logs_response.status_code}"
                
                results.append({
                    "run_id": run_id,
                    "run_name": run_name,
                    "job_id": job_id,
                    "job_name": job_name,
                    "logs": log_content
                })
                
        return {"extracted_logs": results}
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Network error while connecting to GitHub: {str(exc)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
