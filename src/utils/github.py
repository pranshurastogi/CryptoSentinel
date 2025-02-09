import os
import requests
from urllib.parse import urlparse
from langchain_openai import ChatOpenAI  # new recommended import

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Ensure your credentials are set
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("Please set the GITHUB_TOKEN environment variable with your GitHub personal access token.")

# Set headers for GitHub API requests
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def parse_github_url(url: str) -> dict:
    """
    Parses a GitHub URL.
    - If the URL has one path segment (e.g. "github.com/username"),
      it returns {"type": "user", "username": ...}.
    - If it has at least two segments (e.g. "github.com/username/repo"),
      it returns {"type": "repo", "username": ..., "repo": ...}.
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    print('I am inside parse_github_url')
    if len(path_parts) == 1:
        print('I am inside parse_github_url',path_parts[0])

        return {"type": "user", "username": path_parts[0]}
    elif len(path_parts) >= 2:
        print('I am inside parse_github_url',path_parts[0], path_parts[1])

        return {"type": "repo", "username": path_parts[0], "repo": path_parts[1]}
    else:
        raise ValueError("Invalid GitHub URL format.")

def fetch_user_data(username: str) -> dict:
    """
    Fetches user details and repository metrics:
      - GET /users/{username} for overall user details.
      - GET /users/{username}/repos for repo details (up to 100 repos).
    Aggregates total stars and forks.
    """
    print('I am inside fetch_user_data')
    user_url = f"https://api.github.com/users/{username}"
    r = requests.get(user_url, headers=HEADERS)
    if r.status_code != 200:
        raise Exception(f"Error fetching user data: {r.text}")
    user_data = r.json()
    
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    r_repos = requests.get(repos_url, headers=HEADERS)
    if r_repos.status_code != 200:
        raise Exception(f"Error fetching repositories: {r_repos.text}")
    repos_data = r_repos.json()
    
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos_data)
    num_repos = len(repos_data)
    print('I am inside fetch_user_data',{
        "followers": user_data.get("followers", 0),
        "public_repos": user_data.get("public_repos", 0),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "repos_count": num_repos
    })

    
    return {
        "followers": user_data.get("followers", 0),
        "public_repos": user_data.get("public_repos", 0),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "repos_count": num_repos
    }

def fetch_repo_data(username: str, repo: str) -> dict:
    """
    Fetches repository details from GET /repos/{username}/{repo}.
    """
    print('I am inside fetch_repo_data')

    url = f"https://api.github.com/repos/{username}/{repo}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        raise Exception(f"Error fetching repository data: {r.text}")
    repo_data = r.json()
    print('I am inside fetch_repo_data',{
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "watchers": repo_data.get("watchers_count", 0),
        "open_issues": repo_data.get("open_issues_count", 0)
    })

    return {
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "watchers": repo_data.get("watchers_count", 0),
        "open_issues": repo_data.get("open_issues_count", 0)
    }

def rate_user_activity(metrics: dict) -> str:
    """
    Uses the ChatOpenAI model to produce a rating (1-10) and explanation for a GitHub user.
    """
    print('I am inside rate_user_activity')

    template = (
        "You are a GitHub rating assistant. Given the following metrics for a GitHub user:\n\n"
        "- Followers: {followers}\n"
        "- Number of Public Repositories: {public_repos}\n"
        "- Total Stars across Repositories: {total_stars}\n"
        "- Total Forks across Repositories: {total_forks}\n\n"
        "Provide a rating on a scale of 1 to 10 for the user's overall GitHub presence, "
        "along with a brief explanation."
    )
    prompt_text = template.format(**metrics)
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    response = llm(prompt_text)
    print('I am inside rate_user_activity',response)

    return response

def rate_repo_activity(metrics: dict) -> str:
    """
    Uses the ChatOpenAI model to produce a rating (1-10) and explanation for a GitHub repository.
    """
    print('I am inside rate_repo_activity')
    template = (
        "You are a GitHub rating assistant. Given the following metrics for a GitHub repository:\n\n"
        "- Stars: {stars}\n"
        "- Forks: {forks}\n"
        "- Watchers: {watchers}\n"
        "- Open Issues: {open_issues}\n\n"
        "Provide a rating on a scale of 1 to 10 for the repository's popularity and activity, "
        "along with a brief explanation."
    )
    prompt_text = template.format(**metrics)
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    response = llm(prompt_text)
    print('I am inside rate_repo_activity',response)

    return response

# def main():
#     github_url = input("Enter a GitHub URL: ").strip()
#     resource = parse_github_url(github_url)
    
#     if resource["type"] == "user":
#         print(f"Fetching data for GitHub user: {resource['username']}")
#         user_metrics = fetch_user_data(resource["username"])
#         print("User Metrics:")
#         print(user_metrics)
#         rating = rate_user_activity(user_metrics)
#         print("\nUser Rating and Explanation:")
#         print(rating)
#     elif resource["type"] == "repo":
#         print(f"Fetching data for repository: {resource['username']}/{resource['repo']}")
#         repo_metrics = fetch_repo_data(resource["username"], resource["repo"])
#         print("Repository Metrics:")
#         print(repo_metrics)
#         rating = rate_repo_activity(repo_metrics)
#         print("\nRepository Rating and Explanation:")
#         print(rating)
#     else:
#         print("Unsupported GitHub URL format.")

# if __name__ == "__main__":
#     main()
