import pytest

pytest_plugins = ["test_framework.fixtures.fixtures"]


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """Hook to capture test outcomes for logging fixtures"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)