import requests
import csv
import datetime
from collections import defaultdict
from typing import Dict, Any, List

class GitHubUserData:
    def __init__(self, token: str):
        """
        Initializes the class with the GitHub authentication token.

        Args:
            token (str): The GitHub authentication token.
        """
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_user_data(self, user: str) -> Dict[str, Any]:
        """
        Retrieves GitHub user data, including contributions, repositories, and primary language.

        Args:
            user (str): The GitHub username.

        Returns:
            Dict[str, Any]: A dictionary containing contribution data, repositories, primary language, 
                            monthly contributions, and types of contributions.
        """
        total_contributions = 0
        monthly_contributions = defaultdict(int)
        contribution_types = defaultdict(int)
        start_year = 2017
        current_year = datetime.datetime.now().year

        for year in range(start_year, current_year + 1):
            from_date = f"{year}-01-01T00:00:00Z"
            to_date = f"{year}-12-31T23:59:59Z"
            user_data_for_year = self._get_user_data_for_year(user, from_date, to_date)
            
            total_contributions += user_data_for_year["contributions"]
            for month, count in user_data_for_year["monthly_contributions"].items():
                monthly_contributions[month] += count
            for key, count in user_data_for_year["contribution_types"].items():
                contribution_types[key] += count

        additional_user_data = self._get_additional_user_data(user)

        return {
            "contributions": total_contributions,
            "repositories": additional_user_data["repositories"],
            "primary_language": additional_user_data["primary_language"],
            "monthly_contributions": dict(monthly_contributions),
            "contribution_types": dict(contribution_types)
        }
    
    def _get_user_data_for_year(self, user: str, from_date: str, to_date: str) -> Dict[str, Any]:
        """
        Fetches GitHub user data for a specific year.

        Args:
            user (str): GitHub username.
            from_date (str): The start date (in ISO format) of the year to retrieve data from.
            to_date (str): The end date (in ISO format) of the year to retrieve data from.

        Returns:
            Dict[str, Any]: Parsed user contribution data for the specified year.
        """
        query = """
        query($user: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $user) {
            contributionsCollection(from: $from, to: $to) {
              contributionCalendar {
                totalContributions
                weeks {
                  contributionDays {
                    date
                    contributionCount
                  }
                }
              }
              commitContributionsByRepository {
                contributions(first: 100) {
                  totalCount
                }
              }
              pullRequestContributionsByRepository {
                contributions(first: 100) {
                  totalCount
                }
              }
              issueContributionsByRepository {
                contributions(first: 100) {
                  totalCount
                }
              }
              pullRequestReviewContributionsByRepository {
                contributions(first: 100) {
                  totalCount
                }
              }
            }
          }
        }
        """
        
        variables = {
            "user": user,
            "from": from_date,
            "to": to_date
        }
        
        url = "https://api.github.com/graphql"
        response = requests.post(url, json={'query': query, 'variables': variables}, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"Error fetching data for user {user}: {data['errors']}")
                return self._empty_user_data()
            
            user_data = data.get("data", {}).get("user", {})
            if not user_data:
                print(f"User not found or no data available: {user}")
                return self._empty_user_data()
            
            return self._parse_user_data(user_data)
        else:
            print(f"Error fetching data for user {user}: {response.status_code} {response.text}")
            return self._empty_user_data()
    
    def _get_additional_user_data(self, user: str) -> Dict[str, Any]:
        """
        Retrieves additional information about the user, such as the number of repositories
        and the primary programming language.

        Args:
            user (str): GitHub username.

        Returns:
            Dict[str, Any]: Additional user information, such as repositories and primary language.
        """
        query = """
        query($user: String!) {
          user(login: $user) {
            repositories(first: 100) {
              totalCount
              nodes {
                primaryLanguage {
                  name
                }
              }
            }
          }
        }
        """

        variables = {
            "user": user
        }

        url = "https://api.github.com/graphql"
        response = requests.post(url, json={'query': query, 'variables': variables}, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"Error fetching additional data for user {user}: {data['errors']}")
                return {"repositories": 0, "primary_language": "N/A"}
            
            user_data = data.get("data", {}).get("user", {})
            if not user_data:
                print(f"User not found or no data available: {user}")
                return {"repositories": 0, "primary_language": "N/A"}

            repositories = user_data.get("repositories", {}).get("totalCount", 0)

            languages = {}
            for repo in user_data.get("repositories", {}).get("nodes", []):
                primary_language = repo.get("primaryLanguage")
                if primary_language is not None:
                    language = primary_language.get("name")
                    if language:
                        languages[language] = languages.get(language, 0) + 1

            primary_language = max(languages, key=languages.get) if languages else "N/A"

            return {
                "repositories": repositories,
                "primary_language": primary_language
            }
        else:
            print(f"Error fetching additional data for user {user}: {response.status_code} {response.text}")
            return {"repositories": 0, "primary_language": "N/A"}


    def _parse_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses the user data obtained from the GitHub API.

        Args:
            user_data (Dict[str, Any]): Raw GitHub user data.

        Returns:
            Dict[str, Any]: Parsed user data.
        """
        contributions = user_data.get("contributionsCollection", {}).get("contributionCalendar", {}).get("totalContributions", 0)
        repositories = user_data.get("repositories", {}).get("totalCount", 0)
        
        languages = {}
        for repo in user_data.get("repositories", {}).get("nodes", []):
            primary_language = repo.get("primaryLanguage")
            if primary_language is not None:
                language = primary_language.get("name")
                if language:
                    languages[language] = languages.get(language, 0) + 1
        
        primary_language = max(languages, key=languages.get) if languages else "N/A"
        
        weekly_contributions = user_data.get("contributionsCollection", {}).get("contributionCalendar", {}).get("weeks", [])
        
        monthly_contributions = defaultdict(int)
        for week in weekly_contributions:
            for day in week.get("contributionDays", []):
                date = datetime.datetime.strptime(day["date"], "%Y-%m-%d")
                month = date.strftime("%Y-%m")
                monthly_contributions[month] += day["contributionCount"]
        
        contribution_types = {
            "commits": sum(repo["contributions"]["totalCount"] for repo in user_data.get("contributionsCollection", {}).get("commitContributionsByRepository", [])),
            "pull_requests": sum(repo["contributions"]["totalCount"] for repo in user_data.get("contributionsCollection", {}).get("pullRequestContributionsByRepository", [])),
            "issues": sum(repo["contributions"]["totalCount"] for repo in user_data.get("contributionsCollection", {}).get("issueContributionsByRepository", [])),
            "reviews": sum(repo["contributions"]["totalCount"] for repo in user_data.get("contributionsCollection", {}).get("pullRequestReviewContributionsByRepository", []))
        }
        
        return {
            "contributions": contributions,
            "repositories": repositories,
            "primary_language": primary_language,
            "monthly_contributions": dict(monthly_contributions),
            "contribution_types": contribution_types
        }

    @staticmethod
    def _empty_user_data() -> Dict[str, Any]:
        """
        Returns an empty dictionary representing a user with no data or an error.

        Returns:
            Dict[str, Any]: Empty dictionary with default values.
        """
        return {
            "contributions": 0,
            "repositories": 0,
            "primary_language": "N/A",
            "monthly_contributions": {},
            "contribution_types": {}
        }

class CSVProcessor:
    def __init__(self, input_csv: str, output_csv: str):
        """
        Initializes the class with the input and output CSV filenames.

        Args:
            input_csv (str): Name of the input CSV file.
            output_csv (str): Name of the output CSV file.
        """
        self.input_csv = input_csv
        self.output_csv = output_csv
        self._initialize_csv()

    def _initialize_csv(self):
        """
        Initializes the output CSV file with the header. 
        This method is called at the beginning to ensure the file exists and has a header.
        """
        with open(self.output_csv, mode='w', newline='') as file:
            fieldnames = ["user", "contributions", "repositories", "primary_language", "monthly_contributions", "contribution_types"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

    def read_users(self) -> List[str]:
        """
        Reads the list of GitHub users from the input CSV file.

        Returns:
            List[str]: List of GitHub usernames.
        """
        with open(self.input_csv, mode='r', newline='') as file:
            reader = csv.reader(file)
            return [row[0] for row in reader]

    def write_user_data(self, result: Dict[str, Any]):
        """
        Writes a single user's data to the output CSV file.

        Args:
            result (Dict[str, Any]): Dictionary containing the user's data.
        """
        with open(self.output_csv, mode='a', newline='') as file:  # Use 'a' to append data
            fieldnames = ["user", "contributions", "repositories", "primary_language", "monthly_contributions", "contribution_types"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            result["monthly_contributions"] = str(result["monthly_contributions"])
            result["contribution_types"] = str(result["contribution_types"])
            writer.writerow(result)

        print(f"User data for {result['user']} saved to {self.output_csv}.")


class GitHubContributorSummary:
    def __init__(self, token: str, input_csv: str, output_csv: str):
        """
        Initializes the class with the GitHub authentication token, input, and output CSV filenames.

        Args:
            token (str): GitHub authentication token.
            input_csv (str): Name of the input CSV file.
            output_csv (str): Name of the output CSV file.
        """
        self.github_user_data = GitHubUserData(token)
        self.csv_processor = CSVProcessor(input_csv, output_csv)

    def generate_summary(self):
        """
        Generates a summary of GitHub contributors' data and writes it to the output CSV file
        immediately after processing each user's data.
        """
        users = self.csv_processor.read_users()
        for user in users:
            try:
                user_data = self.github_user_data.get_user_data(user)
                result = {
                    "user": user,
                    "contributions": user_data["contributions"],
                    "repositories": user_data["repositories"],
                    "primary_language": user_data["primary_language"],
                    "monthly_contributions": user_data["monthly_contributions"],
                    "contribution_types": user_data["contribution_types"]
                }
                self.csv_processor.write_user_data(result)
            except Exception as e:
                print(f"Error processing user {user}: {e}")

if __name__ == '__main__':
    token = 'token'
    input_csv = 'output_users.csv'
    output_csv = 'output_contribution.csv'

    summary_generator = GitHubContributorSummary(token, input_csv, output_csv)
    summary_generator.generate_summary()
