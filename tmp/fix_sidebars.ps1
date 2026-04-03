$pagesDir = "c:\Users\DELL\OneDrive\Desktop\webzip (2)\webzip\pages"
$files = @("settings.html","notifications.html","request-help.html","help-request.html","view-requests.html","user-profile.html","change-password.html","leaderboard.html")

foreach ($f in $files) {
    $path = Join-Path $pagesDir $f
    if (!(Test-Path $path)) { Write-Output "Not found: $f"; continue }
    
    $content = Get-Content $path -Raw -Encoding UTF8
    
    # Fix sidebar-footer onclick from logout to profile navigation 
    $content = $content -replace 'class="sidebar-footer" onclick="logout\(\)"', 'class="sidebar-footer" onclick="window.location.href=''profile.html''" title="View Profile"'
    
    # Fix the sidebar-footer that has no onclick (like leaderboard)
    $content = $content -replace 'class="sidebar-footer">', 'class="sidebar-footer" onclick="window.location.href=''profile.html''" title="View Profile">'
    
    # Fix power icon to use stopPropagation
    $content = $content -replace '<i data-lucide="power"(\s+)style="color: var\(--danger-red\); width: 16px; height: 16px; margin-left: auto;"', '<i data-lucide="power" onclick="event.stopPropagation(); logout()"$1style="color: var(--danger-red); width: 16px; height: 16px; margin-left: auto; cursor: pointer;" title="Logout"'
    
    # Also handle the inline logout variant
    $content = $content -replace '<i data-lucide="power" onclick="logoutUser\(\)"(\s+)style="color: var\(--danger-red\);', '<i data-lucide="power" onclick="event.stopPropagation(); logoutUser()"$1style="color: var(--danger-red); cursor: pointer;" title="Logout"'
    
    # Replace NODE_LVL_4 with placeholder
    $content = $content -replace 'NODE_LVL_4', '...'
    
    Set-Content $path $content -Encoding UTF8 -NoNewline
    Write-Output "Fixed: $f"
}
Write-Output "Done!"
