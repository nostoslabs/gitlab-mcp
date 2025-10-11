#!/usr/bin/env python3
"""End-to-end test script for GitLab MCP Server.

This script tests the MCP server with real GitLab API calls.
"""

import asyncio
import os
import sys

from gitlab_mcp.presentation.tools.issues.my_issues import my_issues
from gitlab_mcp.presentation.tools.namespaces.list_namespaces import list_namespaces
from gitlab_mcp.presentation.tools.projects.get_project import get_project
from gitlab_mcp.presentation.tools.projects.list_projects import list_projects
from gitlab_mcp.presentation.tools.projects.search_projects import search_projects
from gitlab_mcp.presentation.tools.users.list_users import list_users


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


async def test_list_projects():
    """Test listing projects."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 1: List Projects{Colors.RESET}")
    try:
        result = await list_projects(owned=True, per_page=5)

        if "projects" in result:
            print(f"{Colors.GREEN}✓ Successfully listed projects{Colors.RESET}")
            print(f"  Found {result.get('total_results', 0)} projects")

            if result["projects"]:
                first_project = result["projects"][0]
                print(
                    f"  First project: {first_project.get('name')} (ID: {first_project.get('id')})"
                )
                return True, first_project.get("id")
        else:
            print(f"{Colors.RED}✗ No projects in response{Colors.RESET}")
            return False, None

    except Exception as e:
        print(f"{Colors.RED}✗ Failed: {str(e)}{Colors.RESET}")
        return False, None


async def test_get_project(project_id):
    """Test getting a specific project."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 2: Get Specific Project{Colors.RESET}")
    try:
        result = await get_project(project_id)

        if "id" in result:
            print(f"{Colors.GREEN}✓ Successfully retrieved project{Colors.RESET}")
            print(f"  Name: {result.get('name')}")
            print(f"  Path: {result.get('path_with_namespace')}")
            print(f"  Visibility: {result.get('visibility')}")
            return True
        else:
            print(f"{Colors.RED}✗ Invalid response format{Colors.RESET}")
            return False

    except Exception as e:
        print(f"{Colors.RED}✗ Failed: {str(e)}{Colors.RESET}")
        return False


async def test_search_projects():
    """Test searching projects."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 3: Search Projects{Colors.RESET}")
    try:
        result = await search_projects("gitlab", per_page=3)

        if "projects" in result:
            print(f"{Colors.GREEN}✓ Successfully searched projects{Colors.RESET}")
            print(f"  Found {result.get('total_results', 0)} results")
            return True
        else:
            print(f"{Colors.RED}✗ No projects in response{Colors.RESET}")
            return False

    except Exception as e:
        print(f"{Colors.RED}✗ Failed: {str(e)}{Colors.RESET}")
        return False


async def test_my_issues():
    """Test listing user's issues."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 4: My Issues{Colors.RESET}")
    try:
        result = await my_issues(state="all", per_page=5)

        if "issues" in result:
            print(f"{Colors.GREEN}✓ Successfully listed my issues{Colors.RESET}")
            print(f"  Found {result.get('total_results', 0)} issues")
            return True
        else:
            print(f"{Colors.RED}✗ No issues in response{Colors.RESET}")
            return False

    except Exception as e:
        print(f"{Colors.RED}✗ Failed: {str(e)}{Colors.RESET}")
        return False


async def test_list_users():
    """Test listing users."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 5: List Users{Colors.RESET}")
    try:
        result = await list_users(per_page=3)

        if "users" in result:
            print(f"{Colors.GREEN}✓ Successfully listed users{Colors.RESET}")
            print(f"  Found {result.get('total_results', 0)} users")
            return True
        else:
            print(f"{Colors.RED}✗ No users in response{Colors.RESET}")
            return False

    except Exception as e:
        print(f"{Colors.RED}✗ Failed: {str(e)}{Colors.RESET}")
        return False


async def test_list_namespaces():
    """Test listing namespaces."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 6: List Namespaces{Colors.RESET}")
    try:
        result = await list_namespaces(per_page=5)

        if "namespaces" in result:
            print(f"{Colors.GREEN}✓ Successfully listed namespaces{Colors.RESET}")
            print(f"  Found {result.get('total_results', 0)} namespaces")
            return True
        else:
            print(f"{Colors.RED}✗ No namespaces in response{Colors.RESET}")
            return False

    except Exception as e:
        print(f"{Colors.RED}✗ Failed: {str(e)}{Colors.RESET}")
        return False


async def main():
    """Run all end-to-end tests."""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}GitLab MCP Server - End-to-End Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")

    # Check environment
    token = os.environ.get("GITLAB_PERSONAL_ACCESS_TOKEN")
    if not token:
        print(f"{Colors.RED}✗ GITLAB_PERSONAL_ACCESS_TOKEN not set{Colors.RESET}")
        return 1

    api_url = os.environ.get("GITLAB_API_URL", "https://gitlab.com/api/v4")
    print(f"\n{Colors.YELLOW}Configuration:{Colors.RESET}")
    print(f"  API URL: {api_url}")
    print(f"  Token: {'*' * 20}{token[-4:]}")

    # Run tests
    results = []

    # Test 1: List projects (also get a project ID for test 2)
    success, project_id = await test_list_projects()
    results.append(("List Projects", success))

    # Test 2: Get specific project (if we got a project ID)
    if project_id:
        success = await test_get_project(project_id)
        results.append(("Get Project", success))
    else:
        print(f"\n{Colors.YELLOW}⊘ Skipping Get Project test (no project ID){Colors.RESET}")
        results.append(("Get Project", None))

    # Test 3: Search projects
    success = await test_search_projects()
    results.append(("Search Projects", success))

    # Test 4: My issues
    success = await test_my_issues()
    results.append(("My Issues", success))

    # Test 5: List users
    success = await test_list_users()
    results.append(("List Users", success))

    # Test 6: List namespaces
    success = await test_list_namespaces()
    results.append(("List Namespaces", success))

    # Print summary
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")

    passed = sum(1 for _, s in results if s is True)
    failed = sum(1 for _, s in results if s is False)
    skipped = sum(1 for _, s in results if s is None)

    for test_name, success in results:
        if success is True:
            print(f"  {Colors.GREEN}✓{Colors.RESET} {test_name}")
        elif success is False:
            print(f"  {Colors.RED}✗{Colors.RESET} {test_name}")
        else:
            print(f"  {Colors.YELLOW}⊘{Colors.RESET} {test_name} (skipped)")

    print(f"\n{Colors.BOLD}Results: {Colors.GREEN}{passed} passed{Colors.RESET}, ", end="")
    if failed > 0:
        print(f"{Colors.RED}{failed} failed{Colors.RESET}, ", end="")
    else:
        print(f"{failed} failed, ", end="")
    print(f"{Colors.YELLOW}{skipped} skipped{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")

    # Return exit code
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
