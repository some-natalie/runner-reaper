#!/usr/bin/env python3
"""
This file holds the main function that does all the things.

Inputs:
- GitHub API endpoint (assumes github.com if not specified or run within GHES/GHAE)
- PAT of appropriate scope (assumes the workflow token if not specified)
- Report scope ("enterprise", "organization", "repository")
- Enterprise slug OR organization name OR repository name

Outputs:
- Nothing really, it removes your offline runners
"""

# Import modules
import requests
import os

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


# Define functions
def get_runners(api_endpoint, runner_scope, scope_name, github_pat):
    """
    Get the list of runners
    """
    # Set base url by scope
    if runner_scope == "repository":
        base_url = "{}/repos/{}/actions/runners".format(api_endpoint, scope_name)
    elif runner_scope == "organization":
        base_url = "{}/orgs/{}/actions/runners".format(api_endpoint, scope_name)
    elif runner_scope == "enterprise":
        base_url = "{}/enterprises/{}/actions/runners".format(api_endpoint, scope_name)
    else:
        print("Invalid runner scope")
        return

    # Set headers
    headers = {
        "Authorization": "token {}".format(github_pat),
        "Accept": "application/vnd.github.v3+json",
    }

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


def delete_runners(api_endpoint, runner_scope, scope_name, github_pat, runner_list):
    """
    Delete the offline runners
    """
    # Set base url by scope
    if runner_scope == "repository":
        base_url = "{}/repos/{}/actions/runners".format(api_endpoint, scope_name)
    elif runner_scope == "organization":
        base_url = "{}/orgs/{}/actions/runners".format(api_endpoint, scope_name)
    elif runner_scope == "enterprise":
        base_url = "{}/enterprises/{}/actions/runners".format(api_endpoint, scope_name)
    else:
        print("Invalid runner scope")
        return

    # Set headers
    headers = {
        "Authorization": "token {}".format(github_pat),
        "Accept": "application/vnd.github.v3+json",
    }

    for i in runner_list:
        if i["status"] == "offline":
            url = base_url + "/{}".format(i["id"])
            response = requests.delete(url, headers=headers)
            if response.status_code == 204:
                print("Deleted runner {}".format(i["name"]))


# Do the thing!
if __name__ == "__main__":
    runner_list = get_runners(api_endpoint, runner_scope, scope_name, github_pat)
    delete_runners(api_endpoint, runner_scope, scope_name, github_pat, runner_list)
