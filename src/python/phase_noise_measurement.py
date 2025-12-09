# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 16:32:26 2024

@author: balsant
"""

import numpy as np
import matplotlib.pyplot as plt
import scpi as scpi
import time

# Constants
CENTER_FREQ = 0  # 100 MHz
FREQ_WINDOW = 1e5  # ±1 MHz
SAMPLE_RATE = 31.250e6  # 250 MS/s
DESIRED_FREQ = 0  # Desired frequency in Hz
#WINDOW_LENGTH_SAMPLES = int(5e-6 * SAMPLE_RATE)  # 5 microseconds of data

# PID Parameters
kp = 0.00000001  # Proportional gain
ki = 0.00000001  # Integral gain
kd = 0.000000005  # Derivative gain
integral = 0
previous_error = 0

# Initialize SCPI connection
rp_s = scpi.scpi('169.254.121.63')
rp_s.tx_txt('ACQ:DEC 8')

# Set up the plot once
plt.ion()  # Turn on interactive mode
fig, ax = plt.subplots(figsize=(10, 5))
line1, = ax.plot([], [], 'b-', label='Focused FFT')
desired_line = ax.axvline(x=DESIRED_FREQ, color='r', linestyle='--', label='Desired Frequency (100 MHz)')
measured_line = ax.axvline(x=DESIRED_FREQ, color='g', linestyle=':', label='Measured Frequency')
plt.title('Focused FFT around 100 MHz')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.legend()

# Continuous operation
try:
    while True:
        rp_s.tx_txt('ACQ:RST')
        rp_s.tx_txt('ACQ:START')
        rp_s.tx_txt('ACQ:TRIG NOW')  # Trigger immediately
        
        pause_time = 75e-6  # 75 microseconds
        time.sleep(pause_time)
        
        # Get data from Red Pitaya
        rp_s.tx_txt('ACQ:SOUR1:DATA?')
        buff_string = rp_s.rx_txt()
        buff = np.array(list(map(float, buff_string.strip('{}\n\r').replace("  ", "").split(','))))

        # Perform FFT
        fft_result = np.fft.fft(buff)
        freqs = np.fft.fftfreq(len(buff), 1 / SAMPLE_RATE)

        # Focus on the frequency range around 100 MHz ±1 MHz
        mask = (freqs > (CENTER_FREQ - FREQ_WINDOW)) & (freqs < (CENTER_FREQ + FREQ_WINDOW))
        focused_freqs = freqs[mask]
        focused_fft = np.abs(fft_result[mask])

        # Find the peak within the focused range
        peak_idx = np.argmax(focused_fft)
        measured_freq = focused_freqs[peak_idx]
        frequency_error = measured_freq - DESIRED_FREQ

        # Update plot
        line1.set_data(focused_freqs, focused_fft)
        measured_line.set_xdata([measured_freq, measured_freq])
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw()
        fig.canvas.flush_events()

        # PID Calculation
        integral += frequency_error
        derivative = frequency_error - previous_error
        output = kp * frequency_error + ki * integral + kd * derivative
        previous_error = frequency_error

        # Ensure output voltage is within 0-3.25V
        if output < 0 or output > 3.25:
            print(f"Error: PID output voltage out of range or too large error to correct: {output:.4f} V")
            break  # Exit the loop
        
        print(f"Measured Frequency: {measured_freq/1e6:.6f} MHz")
        print(f"Frequency Error: {frequency_error:.4f} Hz")
        print(f"PID Output (Voltage Adjustment): {output:.4f} V")
        
        #time.sleep(0.001)  # Small delay for stability and to reduce CPU load

except KeyboardInterrupt:
    print("Stopped by user.")

# Close connection
rp_s.close()
plt.ioff()
plt.close()

# -*- coding: utf-8 -*-
# """
# Created on Fri Jun  7 16:32:26 2024
# Alternate version
# @author: balsant
# """

# import numpy as np
# import matplotlib.pyplot as plt
# import scpi as scpi
# import time

# # Constants
# CENTER_FREQ = 100e6  # 100 MHz
# FREQ_WINDOW = 2e6  # ±1 MHz
# SAMPLE_RATE = 250e6  # 250 MS/s
# DESIRED_FREQ = 100e6  # Desired frequency in Hz
# WINDOW_LENGTH_SAMPLES = int(5e-6 * SAMPLE_RATE)  # 5 microseconds of data

# # PID Parameters
# kp = 0.00000001  # Proportional gain
# ki = 0.00000001  # Integral gain
# kd = 0.000000005  # Derivative gain
# integral = 0
# previous_error = 0

# # Initialize SCPI connection
# rp_s = scpi.scpi('169.254.121.63')
# rp_s.tx_txt('ACQ:DEC 1')

# # Set up the plot once
# plt.ion()  # Turn on interactive mode
# fig, ax = plt.subplots(figsize=(10, 5))
# line1, = ax.plot([], [], 'b-', label='Focused FFT')
# desired_line = ax.axvline(x=DESIRED_FREQ, color='r', linestyle='--', label='Desired Frequency (100 MHz)')
# measured_line = ax.axvline(x=DESIRED_FREQ, color='g', linestyle=':', label='Measured Frequency')
# plt.title('Focused FFT around 100 MHz')
# plt.xlabel('Frequency (Hz)')
# plt.ylabel('Magnitude')
# plt.legend()

# # Continuous operation
# try:
#     while True:
#         rp_s.tx_txt('ACQ:RST')
#         rp_s.tx_txt('ACQ:START')
#         rp_s.tx_txt('ACQ:TRIG NOW')  # Trigger immediately
        
#         pause_time = 75e-6  # 75 microseconds
#         time.sleep(pause_time)
        
#         # Get data from Red Pitaya
#         rp_s.tx_txt('ACQ:SOUR1:DATA?')
#         buff_string = rp_s.rx_txt()
#         buff = np.array(list(map(float, buff_string.strip('{}\n\r').replace("  ", "").split(','))))

#         # Perform FFT
#         fft_result = np.fft.fft(buff)
#         freqs = np.fft.fftfreq(len(buff), 1 / SAMPLE_RATE)

#         # Focus on the frequency range around 100 MHz ±1 MHz
#         mask = (freqs > (CENTER_FREQ - FREQ_WINDOW)) & (freqs < (CENTER_FREQ + FREQ_WINDOW))
#         focused_freqs = freqs[mask]
#         focused_fft = np.abs(fft_result[mask])

#         # Find the peak within the focused range
#         peak_idx = np.argmax(focused_fft)
#         measured_freq = focused_freqs[peak_idx]
#         frequency_error = measured_freq - DESIRED_FREQ

#         # Update plot
#         line1.set_data(focused_freqs, focused_fft)
#         measured_line.set_xdata([measured_freq, measured_freq])
#         ax.relim()
#         ax.autoscale_view()
#         fig.canvas.draw()
#         fig.canvas.flush_events()

#         # PID Calculation
#         integral += frequency_error
#         derivative = frequency_error - previous_error
#         output = kp * frequency_error + ki * integral + kd * derivative
#         previous_error = frequency_error

#         # Ensure output voltage is within 0-3.25V
#         if output < 0 or output > 3.25:
#             print(f"Error: PID output voltage out of range or too large error to correct: {output:.4f} V")
#             break  # Exit the loop
        
#         print(f"Measured Frequency: {measured_freq/1e6:.6f} MHz")
#         print(f"Frequency Error: {frequency_error:.4f} Hz")
#         print(f"PID Output (Voltage Adjustment): {output:.4f} V")
        
#         #time.sleep(0.001)  # Small delay for stability and to reduce CPU load

# except KeyboardInterrupt:
#     print("Stopped by user.")

# # Close connection
# rp_s.close()
# plt.ioff()
# plt.close()
