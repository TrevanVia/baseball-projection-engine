with open('src/App.jsx', 'r') as f:
    content = f.read()

# Remove any non-printable characters
import string
printable = set(string.printable)
cleaned = ''.join(c for c in content if c in printable or ord(c) > 127)

with open('src/App.jsx', 'w') as f:
    f.write(cleaned)

print("✓ Cleaned non-printable characters")
