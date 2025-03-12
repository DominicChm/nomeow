# NoMeow
This project is born of many rude awakenings at the hand of a roommate's cat in the middle of the night. It detects when said cat meows and pulses an ultrasonic beeper which usually gets it to stop.

# Install
Run this command in the home directory of a raspberry pi:
`git clone https://github.com/DominicChm/nomeow.git && cd nomeow && bash install.sh`

# Circuitry
NoMeow pulses `GPIO19` to dispense a beep. This GPIO should be connected to an N-Channel MOSFET which powers on some kind of ultrasonic beeper. For testing you can also use an LED. 

## How it works
NoMeow uses YAMNet to detect cat meows between the hours of 12am and 10am local time using a USB microphone. If one is detected, it triggers a GPIO which should be wired through a MOSFET to an ultrasonic dog trainer or pest repeller. This project is written for an RPI Zero 2w, but will probably work on any rpi.