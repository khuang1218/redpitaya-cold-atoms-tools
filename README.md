# Red Pitaya Tools for Cold Atoms Experiments

This repository contains **C and Python programs** developed for use with
**Red Pitaya** hardware in **cold atoms**, **laser spectroscopy**, and **quantum optics** experiments.  
The tools included here were originally developed for real AMO laboratory systems (laser locking,
AOM ramping, spectroscopy, and phase‐noise measurement).

All **C programs** use the official Red Pitaya C API (`redpitaya/rp.h`) and are designed to run directly
on the Red Pitaya board or via remote compilation.

All **Python programs** use SCPI communication over Ethernet via the `redpitaya_scpi` module for
remote data acquisition and control.

---

# 📂 Repository Structure

```

redpitaya-cold-atoms-tools/
│
├── src/
│   ├── sine_wave_generator/
│   │   ├── sine_wave_generator.c
│   │   └── Makefile
│   │
│   ├── continuous_ramp/
│   │   ├── continuous_ramp.c
│   │   └── Makefile
│   │
│   ├── laser_lock_pid/
│   │   ├── laser_lock_pid.c
│   │   └── Makefile
│   │
│   └── python/
│       ├── fpga_data_exchange_scpi.py
│       ├── laser_lock_scpi.py
│       ├── sine_wave_scpi.py
│       └── phase_noise_measurement.py
│
├── docs/
│   └── images
│
└── examples

````

---

# Sine Wave Generator - Fixed-Frequency FPGA Output (C)

**Folder:** `src/sine_wave_generator/`  
**File:** `sine_wave_generator.c`

This tool outputs a continuous sine wave from one Red Pitaya fast analog output.
It is intended for simple FPGA-based RF/test-signal generation where you want to set
the frequency directly from the command line.

## **Features**

* Sine waveform output on OUT1 or OUT2
* User-set frequency, amplitude, and DC offset
* Optional timed run
* Ctrl+C shutdown for continuous operation
* Output range check to avoid exceeding about +/-1 V on the fast outputs

---

## **Build Instructions**

```bash
cd src/sine_wave_generator
make
```

This generates:

```bash
sine_wave_generator
```

---

## **Usage**

```bash
./sine_wave_generator <frequency_hz> [amplitude_v] [offset_v] [channel] [duration_s]
```

### **Arguments**

| Argument       | Meaning                                      | Default |
| -------------- | -------------------------------------------- | ------- |
| `frequency_hz` | Output sine frequency in Hz                  | required |
| `amplitude_v`  | Peak amplitude in V, 0 to 1                  | 0.5 |
| `offset_v`     | DC offset in V, -1 to 1                      | 0.0 |
| `channel`      | Fast analog output channel, 1=OUT1 or 2=OUT2 | 1 |
| `duration_s`   | Run time in seconds. 0 means until Ctrl+C    | 0 |

### **Examples**

```bash
./sine_wave_generator 1000
./sine_wave_generator 7000 0.4 0.0 1
./sine_wave_generator 100000 0.2 0.1 2 10
```

---

# Sine Wave SCPI - Remote Fixed-Frequency Output (Python)

**Folder:** `src/python/`  
**File:** `sine_wave_scpi.py`

This is the Python/SCPI version of the sine generator. It controls the Red Pitaya over
Ethernet, so it can be run from a lab PC without compiling C code on the board.

## **Usage**

```bash
python sine_wave_scpi.py <rp_ip> <frequency_hz> [amplitude_v] [offset_v] [channel] [duration_s]
```

### **Examples**

```bash
python sine_wave_scpi.py 192.168.1.120 1000
python sine_wave_scpi.py 192.168.1.120 7000 0.4 0.0 1
python sine_wave_scpi.py 192.168.1.120 100000 0.2 0.1 2 10
```

By default the script disables the output when it exits. Add `--leave-on` if you want
the Red Pitaya output to keep running after the Python process finishes.

---

# FPGA Data Exchange SCPI - Send Batches and Read Results (Python)

**Folder:** `src/python/`  
**File:** `fpga_data_exchange_scpi.py`

This script sends arbitrary waveform batches to a Red Pitaya fast output and reads
one ADC buffer back after each batch. It is a PC-side data exchange loop for repeated
experiments such as sending training examples and reading measured responses.

Important limitation: this does not train a neural network inside the FPGA by itself.
For true FPGA-side training or inference, the FPGA bitstream must implement that logic.
This script provides the SCPI data-transfer layer around the existing Red Pitaya generator
and acquisition blocks.

## **Input Data**

Use a `.npy` or CSV file. A 1D file is treated as one waveform. A 2D file is treated as
multiple batches, one row per output waveform. Samples must be normalized from `-1` to `1`.

## **Usage**

```bash
python fpga_data_exchange_scpi.py <rp_ip> <input_file> [options]
```

### **Examples**

```bash
python fpga_data_exchange_scpi.py 192.168.1.120 training_batch.csv
python fpga_data_exchange_scpi.py 192.168.1.120 training_batch.npy --frequency 10000 --loops 20
python fpga_data_exchange_scpi.py 192.168.1.120 training_batch.csv --gen-channel 1 --acq-channel 2 --output-file results.csv
```

The result CSV stores one row per batch readout, including summary values and the acquired
ADC samples.

---

# 🔧 **1. continuous_ramp — Controlled Amplitude & Offset Ramp Generator (C)**

**Folder:** `src/continuous_ramp/`  
**File:** `continuous_ramp.c`

This tool generates a **continuous waveform** on Red Pitaya Channel 1 and performs a **ramp of amplitude
and DC offset** after detecting a threshold crossing on the input channel.  
It is intended for:

- adiabatic laser intensity ramps  
- AOM RF amplitude ramps  
- controlled turn-on/off sequences  
- second-stage cooling in cold strontium experiments  
- general trigger-synchronized amplitude shaping  

## **Features**
✔ Selectable waveform: triangle, sine, ramp up, ramp down  
✔ Threshold-based triggering via ADC  
✔ Smooth amplitude decay using configurable time steps  
✔ DC offset ramping linked to amplitude  
✔ Continuous looping operation in experiments  

---

## **Build Instructions**

```bash
cd src/continuous_ramp
make
````

This generates the executable:

```
continuous_ramp
```

---

## **Usage**

```bash
./continuous_ramp <start_amp> <ramp_time> <SF_dc> <frequency> <waveform_type>
```

### **Arguments**

| Argument        | Meaning                                    | Allowed Range      |
| --------------- | ------------------------------------------ | ------------------ |
| `start_amp`     | Initial amplitude                          | -1 to +1           |
| `ramp_time`     | Duration of amplitude ramp (s)             | ≥ 6 s              |
| `SF_dc`         | DC scaling factor for offset ramp          | -1 to +1           |
| `frequency`     | Output waveform frequency (Hz)             | any positive float |
| `waveform_type` | 0=triangle, 1=sine, 2=ramp up, 3=ramp down | integer 0–3        |

### **Example**

```bash
./continuous_ramp 0.5 40 0.02 7000 1
```

---

# 🔧 **2. laser_lock_pid — Laser Locking with Peak Detection and PID Feedback (C)**

**Folder:** `src/laser_lock_pid/`
**File:** `laser_lock_pid.c`

This program implements a **laser locking system** using Red Pitaya:

1. Generates a scanning waveform (e.g., transfer cavity scan).
2. Acquires photodiode data from an ADC channel.
3. Detects **one or more spectral peaks** using derivatives & thresholds.
4. Computes frequency/position **error** relative to user-defined setpoints.
5. Applies **PID feedback** via analog outputs to stabilize a laser.

This reflects real AMO lab practices such as:

* cavity‐based slave laser locking to a master laser
* saturated absorption locking
* double locking using relative peak spacing

---

## **Features**

✔ External or internal trigger-based acquisition
✔ Peak detection using derivative filtering
✔ Absolute and relative peak‐position locking
✔ Two‐channel PID feedback (e.g., piezo + AOM)
✔ Optional live plotting using gnuplot
✔ Safety limits for analog outputs

---

## **Build Instructions**

```bash
cd src/laser_lock_pid
make
```

This generates:

```
laser_lock_pid
```

---

## **Usage**

```bash
./laser_lock_pid <delay> <pause> <set0> <Kp0> <Ki0> <Dc0> [<set1> <Kp1> <Ki1> <Dc1> <loop>]
```

### **Argument Description**

| Argument                    | Meaning                                            |
| --------------------------- | -------------------------------------------------- |
| `delay`                     | Trigger delay in samples                           |
| `pause`                     | Wait time after trigger before reading buffer (µs) |
| `set0`                      | Desired index of first spectral peak               |
| `Kp0`, `Ki0`                | PID gains for first feedback channel               |
| `Dc0`                       | Initial DC output level                            |
| `set1`, `Kp1`, `Ki1`, `Dc1` | (optional) second peak & second PID loop           |
| `loop`                      | Number of cycles (0 or omitted → infinite)         |

---

# 🧪 **3. laser_lock_scpi.py — Python SCPI-Based Laser Locking (Ethernet/IP)**

**Folder:** `src/python/laser_lock_scpi.py`

This Python program performs **laser locking via SCPI over Ethernet**, allowing Red Pitaya to be controlled
remotely without SSH.

It implements:

* waveform acquisition using `ACQ:SOUR1:DATA?`
* three-peak spectroscopy detection
* real-time PID correction
* control of AOUT0 and output offsets (`SOUR:VOLT:OFFS`)
* saving of lock performance data
* plotting peak positions vs. time

### **Usage**

```bash
python laser_lock_scpi.py <rp_ip> <setpoint1> <setpoint2> <loop>
```

Example:

```bash
python laser_lock_scpi.py 192.168.1.120 500 6500 0
```

This locks:

* first peak near index 500
* second peak at relative position (6500–500)
* runs until stopped or limit conditions are triggered

### **Dependencies**

```bash
pip install numpy matplotlib
```

Plus:

* `redpitaya_scpi` Python module (Ethernet/SCPI interface)

---

# 📡 **4. phase_noise_measurement.py — FFT-Based Phase Noise & Frequency Tracking (Python)**

**Folder:** `src/python/phase_noise_measurement.py`

This program measures **phase noise and frequency fluctuations** around a carrier by:

1. Acquiring a waveform buffer via SCPI
2. Computing an FFT
3. Selecting a **narrow frequency window** around a carrier (e.g. ±1 MHz)
4. Finding the peak frequency
5. Computing frequency error
6. Applying PID feedback via analog output
7. Updating a real-time FFT plot

This is useful for:

* measuring frequency noise of RF sources
* locking a DDS/AOM frequency
* characterizing oscillator stability

### **Real-Time Plot Shows**

* FFT magnitude in selected window
* desired frequency (red dashed line)
* measured frequency (green line)

### **Safety Check**

PID output is constrained to **0–3.25 V**.
If exceeded → loop stops automatically.

---

# 🧰 **Requirements**

### Hardware

* Red Pitaya STEMlab board (125-14 / 122-16)

### For C Programs

* Red Pitaya C API installed (`rp.h`)
* GCC compiler
* (Optional) gnuplot

### For Python Programs

* Python 3
* `numpy`, `matplotlib`
* `redpitaya_scpi` SCPI/Ethernet module
* Ability to reach Red Pitaya via LAN/WiFi (`rp_s = scpi.scpi("<IP>")`)

---

# 📜 **License**

This project is released under the **MIT License**.
See the file: **[LICENSE](LICENSE)**.
