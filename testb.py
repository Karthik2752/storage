import sys, types

cgi = types.ModuleType("cgi")
cgi.parse_header = lambda x: (x, {})
sys.modules["cgi"] = cgi

from googletrans import Translator
print("✅ googletrans imported successfully!")
