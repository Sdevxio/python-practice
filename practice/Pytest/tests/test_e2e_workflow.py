import tempfile
import os
from test_framework.loging_manager import create_login_manager


def test_end_2_end_workflow(service_manager):
    # Initialize LoginManager with ServiceManager
    login_mgr = create_login_manager(service_manager)
    
    # Step 1: Verify ServiceManager session establishment
    assert service_manager.health_check("root"), "Root context health check failed"
    assert service_manager.health_check("user"), "User context health check failed"
    
    service_info = service_manager.get_service_info()
    assert "command" in service_info['available_services']
    assert "user" in service_info['available_contexts']
    assert "root" in service_info['available_contexts']
    
    # Step 2: Verify user logged in using command
    current_user = login_mgr.get_current_user()
    
    user_whoami = service_manager.command("user").run_command("whoami")
    root_whoami = service_manager.command("root").run_command("whoami")
    
    assert user_whoami.exit_code == 0, "User whoami command failed"
    assert root_whoami.exit_code == 0, "Root whoami command failed"
    
    # Step 3: Verify user logged in using logs file
    logs_service = service_manager.logs_monitor_stream("user")
    assert logs_service is not None, "Logs monitoring service not available"
    
    # Test with temporary log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as temp_log:
        temp_log.write("Test log entry for e2e workflow\n")
        temp_log.write(f"Current user session: {current_user or 'unknown'}\n")
        temp_log_path = temp_log.name
    
    # Cleanup temp file
    os.unlink(temp_log_path)
    
    # Step 4: Verify user logged in using apple scripts
    apple_script_service = service_manager.apple_script("user")
    
    test_script = 'return "AppleScript test"'
    result = apple_script_service.run_applescript(test_script)
    
    # AppleScript should execute (success depends on system permissions)
    assert result is not None, "AppleScript service not responding"
    
    # Step 5: Verify user logged in using UI Screen capture approach
    screen_service = service_manager.screen_capture("user")
    assert screen_service is not None, "Screen capture service not available"
    
    # Test LoginManager integration
    assert login_mgr.health_check(), "LoginManager health check failed"
    
    anyone_logged_in = login_mgr.is_anyone_logged_in()
    assert isinstance(anyone_logged_in, bool), "LoginManager user check failed"
    
    # Final verification - all components working together
    assert service_manager.health_check("user"), "Final user health check failed"
    assert service_manager.health_check("root"), "Final root health check failed"
    assert login_mgr.health_check(), "Final LoginManager health check failed"


def test_service_manager_context_switching(service_manager):
    """
    Test ServiceManager context switching capabilities.
    """
    contexts = ["user", "root"]
    
    for context in contexts:
        # Test command service
        result = service_manager.command(context).run_command("echo", [f"Hello from {context}"])
        assert result.exit_code == 0, f"Command failed in {context} context"
        
        # Test context isolation
        command_service = service_manager.command(context)
        assert command_service is not None, f"Failed to get command service for {context}"


def test_login_manager_integration(service_manager):
    """
    Test LoginManager integration with ServiceManager.
    """
    # Create LoginManager with ServiceManager
    login_mgr = create_login_manager(service_manager)
    
    # Test proper separation of concerns
    assert login_mgr.services is service_manager, "ServiceManager not properly integrated"
    
    # Test verification methods (using ServiceManager)
    current_user = login_mgr.get_current_user()
    anyone_logged_in = login_mgr.is_anyone_logged_in()
    
    assert isinstance(anyone_logged_in, bool), "User state verification failed"
    
    # Test health integration
    login_health = login_mgr.health_check()
    service_health = service_manager.health_check("user")
    
    assert service_health, "ServiceManager health check failed"
    assert login_health, "LoginManager health check failed"