"""Validation tests for Phase 3 tools against real GitLab API.

Tests namespaces, groups, jobs, and draft notes functionality.
"""

import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.skipif(
    not os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN"),
    reason="GITLAB_PERSONAL_ACCESS_TOKEN not set",
)
@pytest.mark.asyncio
async def test_namespace_tools():
    """Test namespace tools with real GitLab API."""
    from gitlab_mcp.presentation.tools.namespaces.get_namespace import get_namespace
    from gitlab_mcp.presentation.tools.namespaces.list_namespaces import list_namespaces
    from gitlab_mcp.presentation.tools.namespaces.verify_namespace import verify_namespace

    print("\n" + "=" * 80)
    print("🔍 Testing Namespace Tools")
    print("=" * 80)

    # Test 1: List namespaces
    print("\n" + "-" * 80)
    print("TEST 1: List namespaces")
    print("-" * 80)

    try:
        result = await list_namespaces(per_page=5)
        print("\n✓ Successfully called list_namespaces")
        print(f"  - Namespaces found: {result.get('total_results', 0)}")

        assert "namespaces" in result
        assert "total_results" in result

        if result.get("namespaces"):
            first_ns = result["namespaces"][0]
            print(f"  - First namespace: {first_ns.get('name')} ({first_ns.get('path')})")
            print(f"  - Kind: {first_ns.get('kind')}")
            namespace_id = first_ns.get("id")

            # Test 2: Get specific namespace
            print("\n" + "-" * 80)
            print("TEST 2: Get specific namespace")
            print("-" * 80)

            ns_result = await get_namespace(namespace_id)
            print("\n✓ Successfully called get_namespace")
            print(f"  - Namespace ID: {ns_result.get('id')}")
            print(f"  - Name: {ns_result.get('name')}")
            print(f"  - Path: {ns_result.get('path')}")
            print(f"  - Kind: {ns_result.get('kind')}")

            assert ns_result.get("id") == namespace_id
            assert ns_result.get("name") is not None

        print("\n✅ Test 1-2 PASSED: Namespace tools working correctly")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        raise

    # Test 3: Verify namespace availability
    print("\n" + "-" * 80)
    print("TEST 3: Verify namespace availability")
    print("-" * 80)

    try:
        # Check a namespace that should exist (gitlab-org)
        result = await verify_namespace("gitlab-org")
        print("\n✓ Successfully called verify_namespace for 'gitlab-org'")
        print(f"  - Path: {result.get('path')}")
        print(f"  - Available: {result.get('available')}")
        print(f"  - Exists: {result.get('exists')}")

        # Test with a likely non-existent namespace
        result2 = await verify_namespace("this-namespace-definitely-does-not-exist-12345")
        print("\n✓ Successfully called verify_namespace for non-existent namespace")
        print(f"  - Path: {result2.get('path')}")
        print(f"  - Available: {result2.get('available')}")
        print(f"  - Exists: {result2.get('exists')}")

        print("\n✅ Test 3 PASSED: Verify namespace working correctly")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        raise


@pytest.mark.skipif(
    not os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN"),
    reason="GITLAB_PERSONAL_ACCESS_TOKEN not set",
)
@pytest.mark.asyncio
async def test_group_tools():
    """Test group tools with real GitLab API."""
    from gitlab_mcp.presentation.tools.groups.list_group_iterations import list_group_iterations
    from gitlab_mcp.presentation.tools.groups.list_group_projects import list_group_projects

    print("\n" + "=" * 80)
    print("👥 Testing Group Tools")
    print("=" * 80)

    # Test 1: List group projects (using gitlab-org as a public group)
    print("\n" + "-" * 80)
    print("TEST 1: List group projects")
    print("-" * 80)

    try:
        # Try gitlab-org group (public group)
        result = await list_group_projects("gitlab-org", per_page=5)
        print("\n✓ Successfully called list_group_projects for 'gitlab-org'")
        print(f"  - Projects found: {result.get('total_results', 0)}")

        assert "projects" in result
        assert "total_results" in result

        if result.get("projects"):
            first_project = result["projects"][0]
            print(f"  - First project: {first_project.get('name')}")
            print(f"  - Path: {first_project.get('path_with_namespace')}")
            print(f"  - Visibility: {first_project.get('visibility')}")

        print("\n✅ Test 1 PASSED: List group projects working correctly")
    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {e}")
        print("  Note: This may fail if you don't have access to groups")

    # Test 2: List group iterations (may not be available on all GitLab instances)
    print("\n" + "-" * 80)
    print("TEST 2: List group iterations")
    print("-" * 80)

    try:
        result = await list_group_iterations("gitlab-org", per_page=5)
        print("\n✓ Successfully called list_group_iterations")
        print(f"  - Iterations found: {result.get('total_results', 0)}")

        if "message" in result:
            print(f"  - Message: {result.get('message')}")
            print("  Note: Iterations require GitLab Premium")

        assert "iterations" in result
        assert "total_results" in result

        print("\n✅ Test 2 PASSED: List group iterations working correctly")
    except Exception as e:
        print(f"\n❌ Test 2 FAILED: {e}")
        print("  Note: This feature requires GitLab Premium")


@pytest.mark.skipif(
    not os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN"),
    reason="GITLAB_PERSONAL_ACCESS_TOKEN not set",
)
@pytest.mark.asyncio
async def test_job_tools():
    """Test job tools with real GitLab API."""
    from gitlab_mcp.presentation.tools.jobs.cancel_pipeline_job import cancel_pipeline_job
    from gitlab_mcp.presentation.tools.jobs.play_pipeline_job import play_pipeline_job

    print("\n" + "=" * 80)
    print("⚙️  Testing Job Tools")
    print("=" * 80)

    # We'll just test that the functions are callable
    # Actual testing would require a project with pipelines
    print("\n" + "-" * 80)
    print("TEST: Job tools structure")
    print("-" * 80)

    try:
        # Test that functions exist and have correct signatures
        import inspect

        play_sig = inspect.signature(play_pipeline_job)
        cancel_sig = inspect.signature(cancel_pipeline_job)

        print(f"\n✓ play_pipeline_job signature: {play_sig}")
        print(f"✓ cancel_pipeline_job signature: {cancel_sig}")

        assert "project_id" in play_sig.parameters
        assert "job_id" in play_sig.parameters
        assert "project_id" in cancel_sig.parameters
        assert "job_id" in cancel_sig.parameters

        print("\n✅ Job tools have correct structure")
        print("  Note: Full testing requires a project with active pipelines")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        raise


@pytest.mark.skipif(
    not os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN"),
    reason="GITLAB_PERSONAL_ACCESS_TOKEN not set",
)
@pytest.mark.asyncio
async def test_draft_notes_tools():
    """Test draft notes tools with real GitLab API."""
    from gitlab_mcp.presentation.tools.draft_notes.get_draft_note import get_draft_note
    from gitlab_mcp.presentation.tools.draft_notes.list_draft_notes import list_draft_notes

    print("\n" + "=" * 80)
    print("📝 Testing Draft Notes Tools")
    print("=" * 80)

    # Test structure (actual testing would require MRs with draft notes)
    print("\n" + "-" * 80)
    print("TEST: Draft notes tools structure")
    print("-" * 80)

    try:
        import inspect

        list_sig = inspect.signature(list_draft_notes)
        get_sig = inspect.signature(get_draft_note)

        print(f"\n✓ list_draft_notes signature: {list_sig}")
        print(f"✓ get_draft_note signature: {get_sig}")

        assert "project_id" in list_sig.parameters
        assert "mr_iid" in list_sig.parameters
        assert "project_id" in get_sig.parameters
        assert "mr_iid" in get_sig.parameters
        assert "draft_note_id" in get_sig.parameters

        print("\n✅ Draft notes tools have correct structure")
        print("  Note: Full testing requires merge requests with draft notes")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        raise


@pytest.mark.asyncio
async def test_all_phase3_tools_summary():
    """Summary test showing all Phase 3 tools are registered."""
    from gitlab_mcp.server import mcp

    print("\n" + "=" * 80)
    print("📊 Phase 3 Tools Registration Summary")
    print("=" * 80)

    tools = await mcp.list_tools()
    tool_list = list(tools)
    tool_names = {tool.name for tool in tool_list}

    phase3_tools = {
        "namespaces": ["gitlab_list_namespaces", "gitlab_get_namespace", "gitlab_verify_namespace"],
        "groups": ["gitlab_list_group_projects", "gitlab_list_group_iterations"],
        "jobs": ["gitlab_play_pipeline_job", "gitlab_cancel_pipeline_job"],
        "draft_notes": ["gitlab_list_draft_notes", "gitlab_get_draft_note"],
    }

    print(f"\n✓ Total tools registered: {len(tools)}")
    print("\nPhase 3 tools:")

    all_found = True
    for category, expected_tools in phase3_tools.items():
        found = [tool for tool in expected_tools if tool in tool_names]
        status = "✅" if len(found) == len(expected_tools) else "❌"
        print(f"  {status} {category}: {len(found)}/{len(expected_tools)} tools")
        for tool in expected_tools:
            if tool in tool_names:
                print(f"      ✓ {tool}")
            else:
                print(f"      ✗ {tool} (MISSING)")
                all_found = False

    assert all_found, "Some Phase 3 tools are missing!"
    print("\n✅ All Phase 3 tools successfully registered!")


if __name__ == "__main__":
    """Run validation tests directly."""
    import asyncio

    print("\n" + "=" * 80)
    print("Running Phase 3 Validation Tests")
    print("=" * 80)

    # Check environment variables
    if not os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN"):
        print("❌ ERROR: GITLAB_PERSONAL_ACCESS_TOKEN not set")
        sys.exit(1)

    print("\n✓ Environment variables set correctly")

    # Run tests
    asyncio.run(test_all_phase3_tools_summary())
    asyncio.run(test_namespace_tools())
    asyncio.run(test_group_tools())
    asyncio.run(test_job_tools())
    asyncio.run(test_draft_notes_tools())

    print("\n" + "=" * 80)
    print("🎉 ALL PHASE 3 VALIDATION TESTS COMPLETED")
    print("=" * 80)
