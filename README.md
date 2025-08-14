# FinalProjectCode

Gesture-Based Drone Control Using IR Sensors

This project explores the application of a gesture-based control system using infrared (IR) sensors and a Raspberry Pi Pico 2W. By interpreting gestures in real time, the user is able to position a drone without relying on a conventional remote. The code provided in this repository is used as follows:

ir.py - Initializes and calibrates analog IR sensors (at ADC pins) and sets a baseline to adapt to lighting conditions.
main.py - Sends client.py gesture duration and active sensor data. Takeoff/Land sequences are sensed here as well.
ml_train - Used collected data from analog IR sensors to train different ML models and save the model of choice.
takeoff_client.py - Receives data from main.py, interprets data, and identifies gesture using saved ML model. Sends PX4 SITL drone simulator commands to visualize drone movements.
