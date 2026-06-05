import os

# Content for profile and .env
profile_content = """# InternMailer Profile
name: "Anamay Tripathy"
email: "tripathy.anamay23@gmail.com"
title: "Software Engineering Intern"
location: "India"
phone: "+1-XXX-XXX-XXXX"
linkedin_url: "linkedin.com/in/anamay-tripathy"
github_url: "github.com/Flamechargerr"
calendar_link: "https://cal.com/anamay"
target_roles: ["Software Engineering Intern", "SDE Intern", "Backend Developer"]
target_locations: ["India", "Remote"]
experience_summary: "Passionate software engineer focused on automation and AI."
skills: ["Python", "JavaScript", "Flask", "React", "AI/ML", "Automation"]
"""

# Try to create files from WITHIN this process
paths = {
    'data_recovery/owned_profile.yaml': profile_content,
    'data_recovery/.env.owned': 'RESTORED=true'
}

print("SHADOW INITIALIZATION START")
print("===========================")

for path, content in paths.items():
    try:
        with open(path, 'w') as f:
            f.write(content)
        print(f"✅ Created: {path}")
        # Verify read immediately
        with open(path, 'r') as f:
            read_back = f.read(10)
            print(f"   Read Back: SUCCESS ('{read_back}...')")
    except Exception as e:
        print(f"❌ Failed: {path} - {e}")

print("===========================")
print("SHADOW INITIALIZATION COMPLETE")
