#!/usr/bin/env python3
"""
This file holds the main function that does all the things.

Inputs:
- GitHub API endpoint (assumes github.com if not specified or run within GHES/GHAE)
- PAT of appropriate scope (assumes the workflow token if not specified)
- Report scope ("enterprise", "organization", "repository")
- Enterprise slug OR organization name OR repository name
- Dry run (False if not set, True if set to literally anything)
- Substring (string to match against runner name, such as to only delete runners with "test" in the name)

Outputs:
- Nothing really, it removes your offline runners
"""

# Import modules
import requests
import os
import sys

# Read in config values
if os.environ.get("GITHUB_API_ENDPOINT") is None:
    api_endpoint = "https://api.github.com"
else:
    api_endpoint = os.environ.get("GITHUB_API_ENDPOINT")

if os.environ.get("GITHUB_PAT") is None:
    github_pat = os.environ.get("GITHUB_TOKEN")
else:
    github_pat = os.environ.get("GITHUB_PAT")

if os.environ.get("SCOPE_TYPE") is None:
    runner_scope = "repository"
else:
    runner_scope = os.environ.get("SCOPE_TYPE")

if os.environ.get("SCOPE_NAME") is None:
    scope_name = os.environ.get("GITHUB_REPOSITORY")
else:
    scope_name = os.environ.get("SCOPE_NAME")

if os.environ.get("DRY_RUN") is None:
    dry_run = False
else:
    dry_run = True

if os.environ.get("FUZZY_NAME") is None:
    substring = ""
else:
    substring = os.environ.get("FUZZY_NAME")

# Define functions
def set_url(api_endpoint, runner_scope, scope_name):
    """
    Set the URL based on the scope
    """
    if runner_scope == "repository":
        base_url = "{}/repos/{}/actions/runners".format(api_endpoint, scope_name)
    elif runner_scope == "organization":
        base_url = "{}/orgs/{}/actions/runners".format(api_endpoint, scope_name)
    elif runner_scope == "enterprise":
        base_url = "{}/enterprises/{}/actions/runners".format(api_endpoint, scope_name)
    else:
        print("Invalid runner scope")
        sys.exit(1)
    return base_url


def get_runners(base_url, headers):
    """
    Get the list of runners
    """
    # Get the list of runners
    response = requests.get(base_url, headers=headers)
    if response.status_code == 404:
        print("No runners found for {}".format(scope_name))
        print("Perhaps check the PAT permissions?")
        return []
    runner_count = response.json()["total_count"]
    runner_list = response.json()["runners"]
    while "next" in response.links.keys():
        response = requests.get(response.links["next"]["url"], headers=headers)
        for i in response.json()["runners"]:
            runner_list.append(i)

    # Make sure we have the right number of runners
    assert len(runner_list) == runner_count, "Runner count mismatch"

    # Return the list of runners
    return runner_list


def delete_runners(base_url, headers, runner_list, dry_run, substring):
    """
    Delete the offline runners
    """
    for i in runner_list:
        if i["status"] == "offline" and substring in i["name"] and dry_run == False:
            url = base_url + "/{}".format(i["id"])
            response = requests.delete(url, headers=headers)
            if response.status_code == 204:
                print("Deleted runner {}".format(i["name"]))
        elif i["status"] == "offline" and substring in i["name"] and dry_run == True:
            print("Runner {} is offline and would be deleted".format(i["name"]))


# Do the thing!
if __name__ == "__main__":
    # Set headers
    headers = {
        "Authorization": "token {}".format(github_pat),
        "Accept": "application/vnd.github.v3+json",
    }
    base_url = set_url(api_endpoint, runner_scope, scope_name)
    runner_list = get_runners(base_url, headers)
    delete_runners(base_url, headers, runner_list, dry_run, substring)
