# Red Pitaya Tools for Cold Atoms Experiments

This repository contains **C-based control and acquisition programs** developed for use with
**Red Pitaya** hardware in **cold atoms**, **laser spectroscopy**, and **quantum optics** experiments.  
The tools included here were originally developed for real AMO laboratory systems (laser locking,
AOM ramping, photodiode-triggered sequences).

All programs use the official Red Pitaya C API (`redpitaya/rp.h`) and are designed to run directly
on the Red Pitaya board or via remote compilation.

---

# 📂 Repository Structure

```

redpitaya-cold-atoms-tools/
│
├── src/
│   ├── continuous_ramp/
│   │   ├── continuous_ramp.c
│   │   └── Makefile
│   │
│   └── laser_lock_pid/
│       ├── laser_lock_pid.c
│       └── Makefile
│
├── docs/
│   └── images
│
└── examples

````

---

# 🔧 **1. continuous_ramp — Controlled Amplitude & Offset Ramp Generator**

**Folder:** `src/continuous_ramp/`  
**File:** `continuous_ramp.c`

This tool generates a **continuous waveform** on Red Pitaya Channel 1 and performs a **ramp of amplitude
and DC offset** after detecting a threshold crossing on the input channel.  
It is intended for:

- adiabatic laser intensity ramps  
- AOM RF amplitude ramps  
- controlled turn-on/off sequences  
- experiments requiring trigger-synchronized amplitude shaping like in second stage cooling of cold Sr experiment.

## **Features**
✔ Selectable waveform: triangle, sine, ramp up, ramp down  
✔ Threshold-based triggering via ADC  
✔ Smooth amplitude decay using configurable time constants  
✔ DC offset ramping linked to amplitude  
✔ Continuous looping operation  

---

## **Build Instructions**

From inside this folder:

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

This generates a 7 kHz sine wave, waits for a threshold crossing, then ramps amplitude down.

---

# 🔧 **2. laser_lock_pid — Laser Locking with Peak Detection and PID Feedback**

**Folder:** `src/laser_lock_pid/`
**File:** `laser_lock_pid.c`

This program implements a **laser locking system** using Red Pitaya:

1. Generates a scanning waveform (e.g., for a scanning cavity).
2. Acquires photodiode data from an ADC channel.
3. Detects **one or more spectral peaks** using derivatives & thresholds.
4. Computes frequency/position **error** to user-provided setpoints.
5. Applies **PID feedback** via analog outputs to stabilize a laser.

This reflects real AMO lab control logic for:

* scanning transfer cavity locking for slave lasers to a master laser
* saturated absorption locking
* double locking via relative peak spacing

---

## **Features**

✔ External or internal trigger-based acquisition
✔ Peak detection using derivative filtering
✔ Absolute and relative peak-position locking
✔ Two-channel PID feedback (e.g., AOM + piezo)
✔ Optional live plotting using gnuplot
✔ Safety limits to prevent DC output over/underflow

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

General form:

```bash
./laser_lock_pid <delay> <pause> <set0> <Kp0> <Ki0> <Dc0> [<set1> <Kp1> <Ki1> <Dc1> <loop>]
```

### **Argument Description**

| Argument                    | Meaning                                                      |
| --------------------------- | ------------------------------------------------------------ |
| `delay`                     | Trigger delay in samples                                     |
| `pause`                     | Wait time after trigger before reading buffer (µs)           |
| `set0`                      | Desired index of first peak                                  |
| `Kp0`, `Ki0`                | PID gains for first feedback channel                         |
| `Dc0`                       | Initial DC value of analog output 0                          |
| `set1`, `Kp1`, `Ki1`, `Dc1` | (optional) second lock channel using relative peak positions |
| `loop`                      | Number of cycles (0 or omitted → infinite)                   |

### **Example**

```bash
./laser_lock_pid 8192 90000 350 0.001 0.0005 0.5
```

or double locking:

```bash
./laser_lock_pid 8192 90000 350 0.001 0.0005 0.5  720 0.002 0.0001 0.0  0
```

---

# 🧰 **Requirements**

* Red Pitaya STEMlab board (125-14 / 122-16 or similar)
* Red Pitaya C API installed (`rp.h`)
* GCC
* Optional: `gnuplot` for live plotting

---

# 📜 License

This project is released under the **MIT License**.
See the file: **[LICENSE](LICENSE)**.

---
