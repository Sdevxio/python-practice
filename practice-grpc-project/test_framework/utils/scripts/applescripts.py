

LOG_OUT_USER_APPLESCRIPT = '''
tell application "System Events"
    tell process "Finder"
        click menu bar item 1 of menu bar 1
        delay 1
        -- Find and click the Log Out menu item (may include username)
        set menuItems to menu items of menu 1 of menu bar item 1 of menu bar 1
        repeat with menuItem in menuItems
            if name of menuItem contains "Log Out" then
                click menuItem
                exit repeat
            end if
        end repeat
        
        delay 1
        
        -- Handle confirmation dialog - look for "Log Out" button and click it
        repeat 10 times
            try
                -- Check for dialog window
                if exists window 1 then
                    -- Look for "Log Out" button in the dialog
                    if exists button "Log Out" of window 1 then
                        click button "Log Out" of window 1
                        exit repeat
                    end if
                end if
                -- Check for sheet dialog
                if exists sheet 1 of window 1 then
                    if exists button "Log Out" of sheet 1 of window 1 then
                        click button "Log Out" of sheet 1 of window 1
                        exit repeat
                    end if
                end if
            on error
                -- Continue if no dialog found yet
            end try
            delay 0.5
        end repeat
    end tell
end tell
'''