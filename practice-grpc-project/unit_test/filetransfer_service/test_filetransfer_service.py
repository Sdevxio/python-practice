from test_framework.utils.consts.constants import REMOTE_LOG_PATH
from test_framework.utils.handlers.artifacts.artifacts_handler import save_to_artifacts


def test_filetransfer_service(services, test_logger):
    file_transfer = services.file_transfer("root")
    test_logger.info("Testing file transfer service...")
    tail_bytes = "204800"
    # remote_path = "/Users/admin/pro-mac-client-test-fixtures/dynamic_log_generator/dynamic_test.log"
    content = file_transfer.download_file(REMOTE_LOG_PATH, tail_bytes=tail_bytes)
    assert content is not None, "Failed to download file"
    save_to_artifacts(content, "system.log")
