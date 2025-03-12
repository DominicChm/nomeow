# NoMeow
This project is born of many rude awakenings at the hand of a roommate's cat in the middle of the night.

# Install
Run this command in the home directory of a raspberry pi:
`git clone https://github.com/DominicChm/nomeow.git && cd nomeow && bash install.sh`

# Circuitry
NoMeow pulses `GPIO19` to dispense a beep. This GPIO should be connected to an N-Channel MOSFET which powers on some kind of ultrasonic beeper. For testing you can also use an LED. 

## How it works
NoMeow uses YAMNet to detect meows between the hours of 12 and 10 local time using a USB microphone. If one is detected, it triggers a GPIO which should be wired through a MOSFET to an ultrasonic dog trainer or pest repeller. This project is written for an RPI Zero 2w, but will probably work on any rpi. It probably won't on any derivatives.