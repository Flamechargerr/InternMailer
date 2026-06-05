import os

# Files to check
files = ['.env', 'data/profile.yaml', 'campaign_results/email_tracking.db']

with open('perm_results.txt', 'w') as out:
    out.write("PERMISSION AUDIT RESULTS\n")
    out.write("========================\n")
    for f in files:
        out.write(f"\nFile: {f}\n")
        out.write(f"  Exists (os.path): {os.path.exists(f)}\n")
        try:
            with open(f, 'r') as fh:
                content = fh.read(20)
                out.write(f"  Read (fh.read): SUCCESS (Got: {repr(content)})\n")
        except Exception as e:
            out.write(f"  Read (fh.read): FAIL - {e}\n")
            
        out.write(f"  Read Access (os.access): {os.access(f, os.R_OK)}\n")
        out.write(f"  Write Access (os.access): {os.access(f, os.W_OK)}\n")

print("Audit written to perm_results.txt")
