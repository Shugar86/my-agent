import os
try:
    import git
except ImportError:
    git = None
try:
    from github import Github
except ImportError:
    Github = None


def git_clone(repo_url: str, dest_dir: str = None) -> dict:
    if git is None:
        return {"error": "gitpython not installed"}
    try:
        if dest_dir is None:
            dest_dir = os.path.join("output", repo_url.split("/")[-1].replace(".git", ""))
        repo = git.Repo.clone_from(repo_url, dest_dir)
        return {"path": dest_dir, "branch": str(repo.active_branch)}
    except Exception as e:
        return {"error": str(e)}


def git_status(repo_path: str = ".") -> dict:
    if git is None:
        return {"error": "gitpython not installed"}
    try:
        repo = git.Repo(repo_path)
        return {
            "branch": str(repo.active_branch),
            "modified": [i.a_path for i in repo.index.diff(None)],
            "staged": [i.a_path for i in repo.index.diff("HEAD")] if repo.head.is_valid() else [],
            "untracked": repo.untracked_files,
            "clean": not repo.is_dirty(),
        }
    except Exception as e:
        return {"error": str(e)}


def github_list_issues(token: str, repo: str, state: str = "open") -> dict:
    if Github is None:
        return {"error": "PyGithub not installed"}
    try:
        from github import Auth
        auth = Auth.Token(token)
        g = Github(auth=auth)
        r = g.get_repo(repo)
        issues = r.get_issues(state=state)
        return {
            "issues": [{"number": i.number, "title": i.title, "state": i.state,
                        "url": i.html_url, "created": str(i.created_at)} for i in issues[:20]],
            "total": issues.totalCount,
        }
    except Exception as e:
        return {"error": str(e)}


def github_create_issue(token: str, repo: str, title: str, body: str = "") -> dict:
    if Github is None:
        return {"error": "PyGithub not installed"}
    try:
        from github import Auth
        auth = Auth.Token(token)
        g = Github(auth=auth)
        r = g.get_repo(repo)
        issue = r.create_issue(title=title, body=body)
        return {"number": issue.number, "url": issue.html_url, "state": issue.state}
    except Exception as e:
        return {"error": str(e)}


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="git_clone",
        description="Clone a git repository to local disk.",
        parameters={"type": "object", "properties": {
            "repo_url": {"type": "string"},
            "dest_dir": {"type": "string"},
        }},
        execute_fn=lambda repo_url="", dest_dir=None: git_clone(repo_url, dest_dir),
    )
    registry.register(
        name="git_status",
        description="Show git status of a local repository (branch, modified, staged, untracked).",
        parameters={"type": "object", "properties": {
            "repo_path": {"type": "string"},
        }},
        execute_fn=lambda repo_path=".": git_status(repo_path),
    )
    registry.register(
        name="github_list_issues",
        description="List issues from a GitHub repository.",
        parameters={"type": "object", "properties": {
            "token": {"type": "string"},
            "repo": {"type": "string"},
            "state": {"type": "string"},
        }},
        execute_fn=lambda token="", repo="", state="open": github_list_issues(token, repo, state),
    )
    registry.register(
        name="github_create_issue",
        description="Create a new issue on a GitHub repository.",
        parameters={"type": "object", "properties": {
            "token": {"type": "string"},
            "repo": {"type": "string"},
            "title": {"type": "string"},
            "body": {"type": "string"},
        }},
        execute_fn=lambda token="", repo="", title="", body="": github_create_issue(token, repo, title, body),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["git_clone", "git_status", "github_list_issues", "github_create_issue"]:
        registry.unregister(name)
