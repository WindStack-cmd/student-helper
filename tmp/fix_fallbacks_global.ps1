$pagesDir = "c:\Users\DELL\OneDrive\Desktop\webzip (2)\webzip\pages"
$files = Get-ChildItem "$pagesDir\*.html" | Select-Object -ExpandProperty Name

foreach ($f in $files) {
    if ($f -eq "login.html") { continue }
    
    $path = Join-Path $pagesDir $f
    $content = Get-Content $path -Raw -Encoding UTF8
    
    # Flexible replacement for different possible whitespace or minor variations
    $pattern = 'const name = user.first_name\s*\|\|\s*user.name\s*\|\|\s*"User";'
    $replacement = 'const name = user.first_name || user.name || (user.email ? user.email.split("@")[0] : "User");'
    
    # Check if the pattern exists
    if ($content -match $pattern) {
        $content = [regex]::replace($content, $pattern, $replacement)
        # Also check for this variant without "const" if it exists
        $content = $content -replace 'name = user.first_name \|\| user.name \|\| "User"', 'name = user.first_name || user.name || (user.email ? user.email.split("@")[0] : "User")'
        
        Set-Content $path $content -Encoding UTF8 -NoNewline
        Write-Output "Fixed fallback in: $f"
    }
}

Write-Output "Global fallback update complete."
