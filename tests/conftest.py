from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pytest_collection_modifyitems(config, items):
    priority = {
        "test_lot8_to_lot9_required_mini_chain_is_declared_with_timeouts": 0,
        "test_run_required_chain_script_exists_and_uses_step_timeouts": 1,
        "test_validate_all_until_lot5_executes_without_nested_pytest": 2,
        "test_validate_all_until_lot4_executes_without_nested_pytest": 3,
    }
    items.sort(key=lambda item: (priority.get(item.name, 10), item.nodeid))
