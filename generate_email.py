import json
import sys
import os
sys.path.append('src')
from jinja2 import Template
from azure_ai_client import generate_with_azure_ai

# Sample HTML email template
HTML_TEMPLATE = '''
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta charset="UTF-8">
    <title>Research Internship Inquiry</title>
</head>
<body style="margin: 0; padding: 0; background-color: #ffffff; font-family: 'Times New Roman'; line-height: 1.5; color: #000000;">

    <div style="max-width: 700px; margin: 30px auto; background: #ffffff; padding: 40px 45px; border: 1px solid #e0e0e0;">

        <div style="text-align: center; margin-bottom: 25px; border-bottom: 2px solid #000000; padding-bottom: 15px;">
            <h1 style="margin: 0; font-size: 18px; font-weight: bold;">RESEARCH INTERNSHIP INQUIRY</h1>
        </div>

        <p style="margin: 0 0 20px 0; font-size: 16px;">Dear Prof. {{ professor_name }},</p>
        <p style="margin: 0 0 20px 0; font-size: 16px;">I hope this message finds you well.</p>

        <p style="margin: 0 0 30px 0; font-size: 16px;">My name is <strong>Anamay Tripathy</strong>, a third-year B.Tech student in Data Science & Engineering at <strong>MIT Manipal, India</strong>. I am writing to express my sincere interest in joining your research group as a research intern.</p>

        <h2 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; border-bottom: 1px solid #000000; padding-bottom: 5px;">Why Your Work Resonates with Me</h2>
        <p style="margin: 0 0 15px 0; font-size: 16px;">Your pioneering contributions to <strong>{{ research_area }}</strong> have deeply influenced my academic vision. {{ resonation_text }}</p>

        <h2 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; border-bottom: 1px solid #000000; padding-bottom: 5px;">Technical Background & Fit</h2>
        <p style="margin: 0 0 15px 0; font-size: 16px;">{{ technical_fit_text }}</p>

        <p style="margin: 0 0 15px 0; font-size: 16px;">I am available for internships in <strong>Winter 2025</strong> or <strong>Summer 2026</strong>, and welcome <strong>remote or on-site</strong>, <strong>funded or volunteer</strong> opportunities. I've attached my <strong>CV</strong> and would be grateful for the opportunity to discuss how my background and interests align with your ongoing projects.</p>

        <p style="margin: 0 0 25px 0; font-size: 16px;">Thank you for your time and consideration.</p>

        <h2 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; border-bottom: 1px solid #000000; padding-bottom: 5px;">Contact Information</h2>
        <p style="margin: 0; font-size: 16px; line-height: 1.4;">
            📧 <a href="mailto:tripathy.anamay23@gmail.com" style="color: #000000; text-decoration: underline;">tripathy.anamay23@gmail.com</a><br>
            📞 <a href="tel:+919877454747" style="color: #000000; text-decoration: underline;">+91-9877454747</a><br>
            🌐 <a href="https://anamay.vercel.app" style="color: #000000; text-decoration: underline;">anamay.vercel.app</a> |
            <a href="https://github.com/Flamechargerr" style="color: #000000; text-decoration: underline;">github.com/Flamechargerr</a>
        </p>

        <div style="margin-top: 30px; border-top: 1px solid #000000; padding-top: 20px;">
            <p style="margin: 0 0 8px 0; font-size: 16px;">Warm regards,</p>
            <p style="margin: 0; font-size: 16px; font-weight: bold;">Anamay Tripathy</p>
            <p style="margin: 0; font-size: 16px; font-style: italic;">B.Tech Data Science & Engineering, MIT Manipal</p>
        </div>
    </div>
</body>
</html>
'''


def generate_personalized_email(professor_name, research_area):
    """
    Generate a personalized email for a given professor using Azure AI and template.
    """
    # Use Azure AI for personalization
    prompts = [
        f"Describe why someone would find working in the area of {research_area} so compelling based on the latest research and real-world applications.",
        "Summarize how technical experience in relevant domains would appeal to a professor in {research_area}."
    ]
    resonation_text = generate_with_azure_ai(prompts[0])
    technical_fit_text = generate_with_azure_ai(prompts[1])

    # Render the HTML template with personalized content
    template = Template(HTML_TEMPLATE)
    return template.render(professor_name=professor_name, research_area=research_area,
                           resonation_text=resonation_text, technical_fit_text=technical_fit_text)

# Example usage
generated_email = generate_personalized_email("Prof. Barbara Liskov", "distributed systems and programming languages")
print(generated_email)
# Save to file
with open("personalized_email_output.html", "w", encoding="utf-8") as f:
    f.write(generated_email)
