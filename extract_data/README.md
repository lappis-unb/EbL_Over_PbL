## GitHub Contributor Data Extraction

This repository contains two scripts for extracting and analyzing GitHub user data from a specific organization.

### Overview

The scripts utilize the GitHub API to gather information about contributors and their activity within an organization. The process involves two main steps: retrieving a list of contributors and collecting detailed data for each contributor.

### Setup

Requirements:
- Python 3.6+
- Install dependencies:
  ```bash
  pip install requests
  ```
- A GitHub personal access token with access to the organization's repositories.

### Scripts

#### GitHub Contributors Script (extract_user.py)

- Purpose: Fetches a list of contributors from the specified organization's repositories within a given date range.
- Output: Saves the list of unique contributors to a CSV file.
- Steps:
    - Retrieves all repositories in the organization.
    - Gathers commit data for each repository.
    - Extracts unique contributor usernames.
    - Saves the results to a CSV file.

#### GitHub User Data Script (extract_contribution.py)
- Purpose: Collects detailed contribution data for each user, including contributions, repositories, primary language, and contribution types.
- Output: Saves user data to a CSV file.
- Steps:
    - Reads the list of users from the input CSV.
    - Uses GraphQL API to fetch user data for each year since 2017.
    - Aggregates total contributions, monthly statistics, and contribution types.
    - Saves the results to the output CSV.

### Usage

- Run extract_user.py to generate a list of contributors:
    - Update the script with your GitHub token, organization name, date range, and output file.

- Run extract_contribution.py to collect detailed information for each contributor:
    - Update the script with your GitHub token, input CSV (from the first script), and output CSV file.

