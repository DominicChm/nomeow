#!/bin/bash

sudo apt update
sudo apt install -y python3-pip libportaudio2 cmake
pip install -r requirements.txt

sudo tee /etc/systemd/system/nomeow.service <<EOF
[Unit]
Description=Run nomeow
After=network.target

[Service]
Type=simple
User=$(logname)
WorkingDirectory=$(pwd)
ExecStart=/bin/python3 -u main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable nomeow
sudo systemctl start nomeow


