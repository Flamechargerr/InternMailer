# 🤖 InternMailer - AI-Powered Research Email System

## Quick Start

### 1. Setup Gmail App Password
Edit `.env`:
```bash
EMAIL_ADDRESS=tripathy.anamay23@gmail.com
EMAIL_PASSWORD=your_16_digit_app_password
```

[Get Gmail App Password](https://support.google.com/accounts/answer/185833)

### 2. Run AI Campaign
```bash
python ai_email_sender.py
```

Enter how many emails to send (start with 5-10 for testing).

## What You Get

✅ **Free AI** personalization (Hugging Face - no cost)
✅ **379 European professors** from top universities
✅ **Unique emails** - no repetition or generic content
✅ **Auto-attached resume** (CV_Anamay_Modern.pdf)

## Example Email

```
Dear Professor Cristian Cadar,

I hope this email finds you well. As a Data Science Engineering 
student at MIT Manipal, I have been following your research in 
software engineering with great interest. The innovative approaches 
your group has developed align closely with my academic goals.

Your research on program analysis and testing aligns perfectly 
with my interests in applying machine learning to real-world 
problems...

My background in ML and data science, combined with hands-on 
experience at YaanBarpe (34% efficiency improvement)...
```

## Files

- `ai_email_sender.py` - Main campaign script
- `free_ai_analyzer.py` - Free AI content generator
- `data/clean_40k_professors.db` - 379 European professors
- `resumes/CV_Anamay_Modern.pdf` - Your resume

## Support

Issues? Check that:
1. Gmail app password is set correctly in `.env`
2. Resume exists at `resumes/CV_Anamay_Modern.pdf`
3. Database exists at `data/clean_40k_professors.db`
