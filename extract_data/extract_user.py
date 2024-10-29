import requests
import csv
import time
from typing import List, Set, Dict, Any, Optional

class GitHubContributors:
    def __init__(self, token: str, organization: str, start_date: str, end_date: str, output_csv: str):
        """
        Initializes the class with GitHub authentication credentials and other parameters.

        Args:
            token (str): The GitHub authentication token.
            organization (str): The GitHub organization.
            start_date (str): Start date in ISO 8601 format.
            end_date (str): End date in ISO 8601 format.
            output_csv (str): The name of the output CSV file.
        """
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
        }
        self.organization = organization
        self.start_date = start_date
        self.end_date = end_date
        self.output_csv = output_csv

    def get_repositories(self) -> List[str]:
        """
        Retrieves the list of repositories from the organization.

        Returns:
            List[str]: A list of repository names.
        """
        repos = []
        url = f'https://api.github.com/orgs/{self.organization}/repos'
        while url:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            repos.extend(response.json())
            url = response.links.get('next', {}).get('url')
        return [repo['name'] for repo in repos]

    def get_commits(self, repo: str) -> List[Dict[str, Any]]:
        """
        Retrieves the list of commits from a specific repository.

        Args:
            repo (str): The repository name.

        Returns:
            List[Dict[str, Any]]: A list of commits.
        """
        commits = []
        url = f'https://api.github.com/repos/{self.organization}/{repo}/commits'
        params = {
            'since': self.start_date,
            'until': self.end_date,
            'per_page': 100,
        }
        while url:
            attempts = 0
            success = False
            while attempts < 2 and not success:
                try:
                    response = requests.get(url, headers=self.headers, params=params)
                    response.raise_for_status()
                    commits.extend(response.json())
                    url = response.links.get('next', {}).get('url')
                    success = True
                except requests.exceptions.RequestException as e:
                    attempts += 1
                    print(f"Error fetching commits from repository {repo}: {e}")
                    print(f"Retrying ({attempts}/2)...")
                    time.sleep(5)
                    if attempts == 2:
                        print("Max retries reached. Skipping to the next repository.")
                        url = None
        return commits

    @staticmethod
    def get_contributors(commits: List[Dict[str, Any]]) -> Set[str]:
        """
        Retrieves the list of contributors from the commit list.

        Args:
            commits (List[Dict[str, Any]]): A list of commits.

        Returns:
            Set[str]: A set of contributor usernames.
        """
        contributors = set()
        for commit in commits:
            if commit['author']:  
                contributors.add(commit['author']['login'])
        return contributors

    def save_to_csv(self, contributors: Set[str]):
        """
        Saves the list of contributors to a CSV file.

        Args:
            contributors (Set[str]): A set of contributor usernames.
        """
        with open(self.output_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['User'])
            for contributor in contributors:
                writer.writerow([contributor])
        print(f'Successfully written to {self.output_csv}')

    def run(self):
        """
        Runs the complete process of retrieving contributors and saving them to a CSV.
        """
        all_contributors = set()
        repositories = self.get_repositories()
        for repo in repositories:
            print(f'Processing repository: {repo}')
            commits = self.get_commits(repo)
            contributors = self.get_contributors(commits)
            all_contributors.update(contributors)
        self.save_to_csv(all_contributors)

if __name__ == '__main__':
    token = 'token'
    organization = 'organization'
    start_date = '2017-01-01T00:00:00Z'
    end_date = '2024-07-01T23:59:59Z'
    output_csv = 'output_users.csv'

    github_contributors = GitHubContributors(token, organization, start_date, end_date, output_csv)
    github_contributors.run()
