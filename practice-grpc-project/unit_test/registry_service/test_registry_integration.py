"""
Integration tests for Registry service with real gRPC services.

Tests agent lookup, agent listing, registry functionality, and error handling
using actual gRPC connections and agent registry operations.
"""

import pytest


class TestRegistryServiceIntegration:
    """Integration tests for Registry service with real gRPC services."""

    def test_registry_service_availability(self, services):
        """Test that Registry service is available in both contexts."""
        # Test root context registry service (most common usage)
        root_registry = services.registry("root")
        assert root_registry is not None
        
        # Test user context registry service  
        user_registry = services.registry("admin")
        assert user_registry is not None

    def test_registry_service_connection_handling(self, services):
        """Test Registry service connection handling."""
        registry_service = services.registry("root")
        
        # Test basic service properties
        assert registry_service.client_name == "root"
        assert registry_service.logger is not None
        
        # Service should have stub available after connection
        assert registry_service.stub is not None
        
        # Test expected methods exist
        assert hasattr(registry_service, 'get_agent')
        assert hasattr(registry_service, 'list_agents')
        assert callable(registry_service.get_agent)
        assert callable(registry_service.list_agents)

    def test_registry_service_list_agents(self, services):
        """Test Registry service agent listing functionality."""
        registry_service = services.registry("root")
        
        # Test listing all agents
        agents = registry_service.list_agents()
        
        # Should return a list (might be empty if no agents registered)
        assert isinstance(agents, list)
        
        # If agents exist, verify structure
        for agent in agents:
            assert isinstance(agent, dict)
            assert "username" in agent
            assert "uid" in agent  
            assert "port" in agent
            assert "timestamp" in agent
            
            # Types should be correct
            assert isinstance(agent["username"], str)
            assert isinstance(agent["uid"], int)
            assert isinstance(agent["port"], int)
            assert isinstance(agent["timestamp"], int)
            
            # Values should be reasonable
            assert len(agent["username"]) > 0
            assert agent["uid"] >= 0
            assert agent["port"] > 0
            assert agent["timestamp"] > 0

    def test_registry_service_get_agent_existing(self, services):
        """Test Registry service agent lookup for existing agents."""
        registry_service = services.registry("root")
        
        # First, get list of agents to test with actual registered agents
        agents = registry_service.list_agents()
        
        if agents:
            # Test getting an existing agent
            existing_agent = agents[0]
            username = existing_agent["username"]
            
            agent_info = registry_service.get_agent(username)
            
            # Should return the agent info
            assert agent_info is not None
            assert isinstance(agent_info, dict)
            assert agent_info["username"] == username
            assert agent_info["uid"] == existing_agent["uid"]
            assert agent_info["port"] == existing_agent["port"]
            assert agent_info["timestamp"] == existing_agent["timestamp"]
        else:
            # No agents registered - that's a valid state
            print("No agents currently registered in registry")

    def test_registry_service_get_agent_nonexistent(self, services):
        """Test Registry service agent lookup for non-existent agents."""
        registry_service = services.registry("root")
        
        # Test getting a non-existent agent
        nonexistent_user = "nonexistent_user_12345"
        agent_info = registry_service.get_agent(nonexistent_user)
        
        # Should return None for non-existent agent
        assert agent_info is None

    def test_registry_service_current_session_integration(self, services):
        """Test Registry service integration with current session."""
        registry_service = services.registry("root")
        
        # Get current user from services
        current_user = services.get_current_user()
        
        if current_user:
            # Look up current user in registry
            agent_info = registry_service.get_agent(current_user)
            
            if agent_info:
                # Current user should be registered as an agent
                assert agent_info["username"] == current_user
                assert isinstance(agent_info["port"], int)
                assert agent_info["port"] > 0
                
                # Port should match user context port (50052 typically)
                expected_port = 50052  # User agent port
                assert agent_info["port"] == expected_port or agent_info["port"] > 50000
                
            else:
                # Current user might not be registered as agent - that's OK
                print(f"Current user '{current_user}' not found in agent registry")


class TestRegistryServiceRobustness:
    """Tests for Registry service robustness and edge cases."""

    def test_registry_service_error_handling(self, services):
        """Test Registry service error handling."""
        registry_service = services.registry("root")
        
        # Test with various edge case inputs
        test_usernames = [
            "",                    # Empty string
            " ",                   # Whitespace
            "user_with_long_name_that_probably_does_not_exist_in_system",  # Long name
            "user!@#$%",          # Special characters
            "123456",             # Numeric username
        ]
        
        for username in test_usernames:
            # Should handle all cases gracefully without crashing
            result = registry_service.get_agent(username)
            # Result should be None (not found) or valid dict
            assert result is None or isinstance(result, dict)

    def test_registry_service_multiple_calls(self, services):
        """Test Registry service handles multiple sequential calls."""
        registry_service = services.registry("root")
        
        # Make multiple calls to test service stability
        results = []
        for i in range(3):
            agents = registry_service.list_agents()
            results.append(agents)
        
        # All calls should return lists
        for result in results:
            assert isinstance(result, list)
        
        # Results should be consistent (agents shouldn't change rapidly)
        if results[0]:  # If we have agents
            # Agent count should be relatively stable
            counts = [len(result) for result in results]
            assert max(counts) - min(counts) <= 1  # Allow for 1 agent difference

    def test_registry_service_context_differences(self, services):
        """Test Registry service behavior across different contexts."""
        root_registry = services.registry("root")
        user_registry = services.registry("admin")
        
        # Both should be functional
        root_agents = root_registry.list_agents()
        user_agents = user_registry.list_agents()
        
        # Both should return lists
        assert isinstance(root_agents, list)
        assert isinstance(user_agents, list)
        
        # Results might be the same (both contexts access same registry)
        # This is implementation dependent - both outcomes are valid

    def test_registry_service_agent_validation(self, services):
        """Test Registry service agent data validation."""
        registry_service = services.registry("root")
        
        agents = registry_service.list_agents()
        
        for agent in agents:
            # Username validation
            assert isinstance(agent["username"], str)
            assert len(agent["username"]) > 0
            assert not agent["username"].isspace()
            
            # UID validation (should be valid system UID)
            assert isinstance(agent["uid"], int)
            assert agent["uid"] >= 0  # UIDs are non-negative
            
            # Port validation (should be valid port number)
            assert isinstance(agent["port"], int)
            assert 1 <= agent["port"] <= 65535  # Valid port range
            
            # Timestamp validation (should be reasonable timestamp)
            assert isinstance(agent["timestamp"], int)
            assert agent["timestamp"] > 0
            # Should be within reasonable time range (not too old/future)
            import time
            current_time = int(time.time())
            assert abs(current_time - agent["timestamp"]) < 86400 * 7  # Within a week


class TestRegistryServiceConfiguration:
    """Tests for Registry service configuration and setup."""

    def test_registry_service_logger_configuration(self, services):
        """Test Registry service logger is properly configured."""
        root_registry = services.registry("root")
        user_registry = services.registry("admin")
        
        # Both should have logger configured
        assert root_registry.logger is not None
        assert user_registry.logger is not None
        
        # Logger names should reflect the context
        assert hasattr(root_registry.logger, 'name')
        assert hasattr(user_registry.logger, 'name')

    def test_registry_service_client_names(self, services):
        """Test Registry service client name configuration."""
        root_registry = services.registry("root")
        user_registry = services.registry("admin")
        
        assert root_registry.client_name == "root"
        assert user_registry.client_name == "admin"

    def test_registry_service_stub_configuration(self, services):
        """Test Registry service stub configuration."""
        registry_service = services.registry("root")
        
        # Should have RegistryServiceStub
        assert registry_service.stub is not None
        
        # Should have the expected gRPC methods
        expected_methods = ['GetAgent', 'ListAgents']
        for method_name in expected_methods:
            assert hasattr(registry_service.stub, method_name)
            assert callable(getattr(registry_service.stub, method_name))

    def test_registry_service_integration_with_session_manager(self, services):
        """Test Registry service integration with session manager."""
        # Test that registry service works alongside other services
        registry_service = services.registry("root")
        command_service = services.command("root")
        
        # Both should be available
        assert registry_service is not None
        assert command_service is not None
        
        # Test that they work independently
        agents = registry_service.list_agents()
        cmd_result = command_service.run_command("echo 'registry test'")
        
        assert isinstance(agents, list)
        assert cmd_result is not None

    def test_registry_service_host_attribute(self, services):
        """Test Registry service host attribute if used."""
        registry_service = services.registry("root")
        
        # Host attribute exists (might be None)
        assert hasattr(registry_service, 'host')
        
        # If set, should be string
        if registry_service.host is not None:
            assert isinstance(registry_service.host, str)
            assert len(registry_service.host) > 0


class TestRegistryServiceSessionBootstrapping:
    """Tests for Registry service role in session bootstrapping."""

    def test_registry_service_agent_discovery(self, services):
        """Test Registry service for agent discovery during session bootstrap."""
        registry_service = services.registry("root")
        
        # Get all registered agents
        agents = registry_service.list_agents()
        
        # For each agent, verify discovery pattern
        for agent in agents:
            username = agent["username"]
            port = agent["port"]
            
            # Should be able to look up agent by username
            discovered_agent = registry_service.get_agent(username)
            assert discovered_agent is not None
            assert discovered_agent["port"] == port
            
            # Port should be in user agent range
            assert port >= 50052  # User agents typically start at 50052

    def test_registry_service_session_consistency(self, services):
        """Test Registry service consistency with current session."""
        registry_service = services.registry("root")
        
        # Get expected user from config
        expected_user = services.expected_user
        
        # Look up in registry
        agent_info = registry_service.get_agent(expected_user)
        
        if agent_info:
            # If registered, should have valid port
            assert isinstance(agent_info["port"], int)
            assert agent_info["port"] > 0
            
            # Should match expected user
            assert agent_info["username"] == expected_user
        
        # Either way is valid - user might not be registered as agent