# Created by Yossy on 2025/06/04

import subprocess

packages = [
    'streamlit',
    'PySide6',
    'pandas',
    'numpy'
]

def install_pakcages():

    # Upgrade pip
    subprocess.run((['python', '-m', 'pip', 'install', '--upgrade', 'pip']))

    # Install packages
    for pkg in packages:
        subprocess.run((['python', '-m', 'pip', 'install', pkg]))

if __name__ == '__main__':
    install_pakcages()