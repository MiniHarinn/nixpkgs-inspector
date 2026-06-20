from __future__ import annotations

import os
from typing import Protocol

from github import Auth, Github

from .model import PR_CLOSED, PR_MERGED, PR_OPEN, PullRequest


class GitHubReader(Protocol):
    def referencing_prs(self, repo: str, issue_number: int) -> list[PullRequest]: ...


class PyGithubReader:
    def __init__(self, token: str | None = None):
        token = token or os.environ.get("GITHUB_TOKEN")
        self._gh = Github(auth=Auth.Token(token) if token else None)

    def referencing_prs(self, repo: str, issue_number: int) -> list[PullRequest]:
        issue = self._gh.get_repo(repo).get_issue(issue_number)

        # cross-referenced timeline events whose source is a PR
        state_of: dict[int, str] = {}
        for ev in issue.get_timeline():
            if ev.event != "cross-referenced" or ev.source is None:
                continue
            src = ev.source.issue
            if src is None or src.pull_request is None:
                continue
            if src.pull_request.merged_at is not None:
                state = PR_MERGED
            elif src.state == "open":
                state = PR_OPEN
            else:
                state = PR_CLOSED
            state_of[src.number] = state

        return [PullRequest(number=n, state=state_of[n]) for n in sorted(state_of)]
