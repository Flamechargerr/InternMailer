"""
InternMailer - Windows Service Installer
Runs JARVIS as Windows background service (survives terminal close)
"""

import os
import sys
import subprocess

def create_task_scheduler_service():
    """
    Create Windows Task Scheduler entry to run JARVIS on startup
    and keep it running even if terminal closes
    """
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    jarvis_path = os.path.join(script_dir, 'jarvis_mode.py')
    python_exe = sys.executable
    
    # Create VBS script to run Python without showing window
    vbs_script = f"""Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d {script_dir} && {python_exe} jarvis_mode.py --start", 0, False
Set WshShell = Nothing
"""
    
    vbs_path = os.path.join(script_dir, 'run_jarvis_hidden.vbs')
    with open(vbs_path, 'w') as f:
        f.write(vbs_script)
    
    # Create PowerShell script to register Task
    ps_script = f'''
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "{vbs_path}"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings $settings

Register-ScheduledTask -TaskName "InternMailer_JARVIS" -InputObject $task -Force
Write-Host "✅ JARVIS registered as Windows service!"
Write-Host "   Will run on startup and restart on failure"
Write-Host "   You can now close laptop - JARVIS keeps running!"
'''
    
    ps_path = os.path.join(script_dir, 'install_service.ps1')
    with open(ps_path, 'w') as f:
        f.write(ps_script)
    
    print("📦 Installing JARVIS as Windows Service...")
    print("   (Requires Administrator privileges)")
    
    # Run PowerShell script
    try:
        subprocess.run(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_path],
            check=True,
            shell=True
        )
        print("\n✅ SUCCESS! JARVIS is now a Windows service!")
        print("\n🎯 What changed:")
        print("   ✅ JARVIS runs on Windows startup automatically")
        print("   ✅ JARVIS survives terminal/Antigravity close")
        print("   ✅ JARVIS restarts automatically if it crashes")
        print("   ✅ You can close laptop (sleep mode) - JARVIS resumes on wake")
        
        print("\n📋 To manage:")
        print("   Start:  Task Scheduler → InternMailer_JARVIS → Run")
        print("   Stop:   Task Scheduler → InternMailer_JARVIS → End")
        print("   Remove: Task Scheduler → InternMailer_JARVIS → Delete")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to install: {e}")
        print("\n⚠️ Run this as Administrator:")
        print(f"   Right-click PowerShell → Run as Administrator")
        print(f"   Then run: python install_windows_service.py")
        return False

def uninstall_service():
    """Remove JARVIS from Task Scheduler"""
    try:
        subprocess.run(
            ['schtasks', '/Delete', '/TN', 'InternMailer_JARVIS', '/F'],
            check=True
        )
        print("✅ JARVIS service removed")
    except:
        print("❌ Service not found or already removed")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Install JARVIS as Windows Service')
    parser.add_argument('--install', action='store_true', help='Install as service')
    parser.add_argument('--uninstall', action='store_true', help='Remove service')
    
    args = parser.parse_args()
    
    if args.uninstall:
        uninstall_service()
    elif args.install:
        create_task_scheduler_service()
    else:
        print("""
🔧 JARVIS Windows Service Installer

PROBLEM: JARVIS stops when you close laptop/terminal

SOLUTION: Install as Windows service

Commands:
  python install_windows_service.py --install    # Install (run as Admin)
  python install_windows_service.py --uninstall  # Remove

After install:
  ✅ JARVIS runs on startup
  ✅ Survives terminal close
  ✅ Survives laptop sleep
  ✅ Auto-restarts on crash

NOTE: Requires Administrator privileges
        """)
