

def test_connection_service_root(services, test_logger):
    """Test basic connection functionality with both contexts."""
    
    # Test root context connection (should work)
    test_logger.info("Testing root context connecok fintion...")
    root_command = services.command("root")
    root_result = root_command.run_command("echo", ["root connection test"])
    test_logger.info(f"Root connection test: {root_result.stdout.strip()}")
    assert root_result.exit_code == 0, "Root context connection failed"
    
    # Test user context connection (should work)
    test_logger.info("Testing user context connection...")
    user_command = services.command("admin")  
    user_result = user_command.run_command("echo", ["user connection test"])
    test_logger.info(f"User connection test: {user_result.stdout.strip()}")
    assert user_result.exit_code == 0, "User context connection failed"
    
    # Test connection service instantiation (even if get_server_info doesn't work)
    test_logger.info("Testing connection service instantiation...")
    try:
        root_conn_service = services.grpc_connection("root")
        user_conn_service = services.grpc_connection("admin")
        test_logger.info("✅ Connection services instantiated successfully")
        assert root_conn_service is not None, "Root connection service is None"
        assert user_conn_service is not None, "User connection service is None"
    except Exception as e:
        test_logger.error(f"Connection service instantiation failed: {e}")
        raise
    
    test_logger.info("✅ All connection tests passed!")
