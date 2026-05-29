import os
from llm_client import analyze_diff

diff_text = """-    old_code
+    new_code"""

result = analyze_diff("test.py", diff_text)
print(result)