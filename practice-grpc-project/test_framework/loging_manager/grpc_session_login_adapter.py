"""
GrpcSessionManager to LoginManager Adapter

This adapter provides a clean interface between LoginManager and GrpcSessionManager,
exposing only the necessary methods that LoginManager actually uses.

Purpose:
- Clean separation of concerns
- Minimal interface (only what's needed)
- Makes any GrpcSessionManager compatible with LoginManager
- Follows adapter pattern principles
"""


class GrpcSessionLoginAdapter:
    """
    Adapter that makes GrpcSessionManager compatible with LoginManager.
    
    This adapter exposes ONLY the methods that LoginManager actually uses:
    - command() - For user verification (get_logged_in_users)
    - apple_script() - For AppleScript logout operations  
    - health_check() - For connection verification
    
    Why these specific methods?
    1. command("root") - LoginManager needs to check current user state
    2. apple_script("user") - LoginManager needs to execute logout AppleScript
    3. health_check() - LoginManager verifies gRPC connectivity before operations
    
    Usage:
        session_mgr = GrpcSessionManager("station1")
        session_mgr.setup_user("admin")
        
        adapter = GrpcSessionLoginAdapter(session_mgr)
        login_mgr = create_login_manager(service_manager=adapter)
    """
    
    def __init__(self, grpc_session_manager):
        """
        Initialize the adapter with a GrpcSessionManager.
        
        Args:
            grpc_session_manager: Any GrpcSessionManager instance
        """
        self.session_mgr = grpc_session_manager
        
    def command(self, context: str):
        """
        Get command service for the specified context.
        
        LoginManager uses this for:
        - get_logged_in_users() - Check current user state
        - run_command() - Execute verification commands
        
        Args:
            context: "root" for system-level verification operations
            
        Returns:
            CommandServiceClient for the specified context
        """
        return self.session_mgr.command(context)
    
    def apple_script(self, context: str):
        """
        Get AppleScript service for the specified context.
        
        LoginManager uses this for:
        - run_applescript(LOG_OUT_USER_APPLESCRIPT) - Execute logout
        
        Args:
            context: Usually "user" for user-level AppleScript operations
            
        Returns:
            AppleScriptServiceClient for the specified context
        """
        return self.session_mgr.apple_script(context)
    
    def health_check(self, context: str) -> bool:
        """
        Perform health check for the specified context.
        
        LoginManager uses this to:
        - Verify gRPC connectivity before login/logout operations
        - Ensure services are available
        
        Args:
            context: "root" or username to check connectivity
            
        Returns:
            True if context is healthy and connected
        """
        return self.session_mgr.health_check(context)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"GrpcSessionLoginAdapter({self.session_mgr})"


def create_login_adapter(grpc_session_manager) -> GrpcSessionLoginAdapter:
    """
    Factory function to create a LoginManager adapter.
    
    This provides a clean, consistent way to create adapters and can be extended
    with validation or configuration in the future.
    
    Args:
        grpc_session_manager: GrpcSessionManager instance to adapt
        
    Returns:
        Adapter that makes the session manager compatible with LoginManager
        
    Example:
        session_mgr = GrpcSessionManager("station1")
        session_mgr.setup_user("admin")
        
        adapter = create_login_adapter(session_mgr)
        login_mgr = create_login_manager(service_manager=adapter)
    """
    return GrpcSessionLoginAdapter(grpc_session_manager)