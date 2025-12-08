"""
InternMailer - Quick Launch Script
Run: python run.py
"""
import sys
import os

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║               INTERNMAILER - QUICK LAUNCHER                  ║
╠══════════════════════════════════════════════════════════════╣
║  1. Send to 10 Professors                                    ║
║  2. Send to 10 Recruiters                                    ║
║  3. Send to 20 (10 each)                                     ║
║  4. Open Dashboard                                           ║
║  5. View Status                                              ║
║  6. Custom Campaign                                          ║
║  0. Exit                                                     ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    choice = input("Select option [1-6]: ").strip()
    
    if choice == "1":
        print("\n🎓 Sending to 10 Professors...")
        os.system("python system.py --count 10")
    
    elif choice == "2":
        print("\n🏢 Sending to 10 Recruiters...")
        os.system("python system.py --hr --count 10")
    
    elif choice == "3":
        print("\n📧 Sending to 20 contacts (10 professors + 10 recruiters)...")
        os.system("python system.py --count 10")
        os.system("python system.py --hr --count 10")
    
    elif choice == "4":
        print("\n📊 Opening Dashboard...")
        os.system("streamlit run dashboard.py")
    
    elif choice == "5":
        print("\n📈 Campaign Status:")
        import system
        vs = system.VerifiedEmailSystem()
        vs.show_status()
    
    elif choice == "6":
        mode = input("Mode (professor/hr): ").strip().lower()
        count = input("Number of emails: ").strip()
        
        if mode in ["hr", "corporate", "recruiter"]:
            os.system(f"python system.py --hr --count {count}")
        else:
            os.system(f"python system.py --count {count}")
    
    elif choice == "0":
        print("Goodbye!")
        sys.exit(0)
    
    else:
        print("Invalid option")

if __name__ == "__main__":
    main()
