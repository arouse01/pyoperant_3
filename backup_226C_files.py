import subprocess
rclone_exe = r'C:\Users\tmerri03\Documents\rclone\rclone.exe'

# --- backup bird data ---
backup_files = r'C:\Users\tmerri03\Desktop\aperture-3\bird\data'
dest = r"Rstore:/as_rsch_kao_lab01$/Data/RhythmPerception/bird/data/226C/"

cmd = [
    rclone_exe,
    'sync',
    backup_files,
    dest,
    '--local-no-check-updated'
]
print("Running:", " ".join(cmd))
subprocess.run(cmd, check=True)

# --- backup daily performance ---
backup_files=r"C:\Users\tmerri03\Desktop\aperture-3\daily_analysis"
dest=r"Rstore:/as_rsch_kao_lab01$/Data/RhythmPerception/data/raw_from_226C/"

script_file = r'C:\Users\tmerri03\Desktop\aperture-3\daily_analysis.py'
cmd = [
    'python',
    script_file
]
subprocess.run(cmd, check=True)

cmd = [
    rclone_exe,
    'sync',
    backup_files,
    dest,
    '--local-no-check-updated'

]
print("Running:", " ".join(cmd))
subprocess.run(cmd, check=True)
