def test_command_service_contexts(services):
    # User context command
    result = services.command("admin").run_command("whoami")
    assert result.exit_code == 0

    # Root context command
    result = services.command("root").run_command("whoami")
    print(f"Command results: {result}")
    assert result.exit_code == 0

    # AppleScript
    script = services.apple_script("user").run_applescript('return "hello"')

