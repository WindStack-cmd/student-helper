import os
import glob
import re

html_files = glob.glob(r'C:\Users\agraw\student-helper-new\webzip\pages\*.html')

js_snippet = """
    <script>
        document.addEventListener("DOMContentLoaded", () => {
            const userStr = localStorage.getItem("loggedInUser");
            if (userStr) {
                try {
                    const user = JSON.parse(userStr);
                    const name = user.first_name || user.name || "User";
                    const email = user.email || "user@system.node";
                    
                    document.querySelectorAll('.user-name').forEach(el => el.innerText = name);
                    document.querySelectorAll('.user-avatar').forEach(el => el.innerText = name.charAt(0).toUpperCase());
                    document.querySelectorAll('.user-role').forEach(el => el.innerText = email);
                } catch(e) {}
            }
        });
    </script>
</body>
"""

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # If it already has our snippet, skip
    if "document.querySelectorAll('.user-name').forEach(el => el.innerText = name);" in content:
        continue
        
    # Remove old static name retrieval snippet if it exists
    old_snippet_pattern = re.compile(r'<script>\s*const name = localStorage\.getItem\("firstName"\).*?</script>', re.DOTALL)
    content = old_snippet_pattern.sub('', content)

    # Insert our new script before </body>
    if '</body>' in content:
        content = content.replace('</body>', js_snippet)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {filepath}")
    else:
        print(f"</body> not found in {filepath}")

print("Done patching all html files.")
