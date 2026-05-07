#!/usr/bin/env python3
"""Send arbitrary waveform batches to Red Pitaya and read acquired data over SCPI.

This is useful as a PC-side data exchange loop: each input row is sent as an
arbitrary output waveform, the Red Pitaya output is triggered, and one ADC buffer
is read back.
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np

try:
    import redpitaya_scpi as scpi
except ImportError:
    import scpi


VALID_DECIMATIONS = {1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048,
                     4096, 8192, 16384, 32768, 65536}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Send arbitrary waveform data to a Red Pitaya output and read back "
            "ADC data repeatedly over SCPI."
        )
    )
    parser.add_argument("rp_ip", help="Red Pitaya IP address or hostname")
    parser.add_argument(
        "input_file",
        help="Input waveform data file. Use .npy or CSV. A 2D file is treated as batches.",
    )
    parser.add_argument(
        "--output-file",
        default="fpga_exchange_results.csv",
        help="CSV file for acquired results. Default: fpga_exchange_results.csv",
    )
    parser.add_argument(
        "--gen-channel",
        type=int,
        choices=(1, 2),
        default=1,
        help="Fast output channel for arbitrary waveform generation. Default: 1",
    )
    parser.add_argument(
        "--acq-channel",
        type=int,
        choices=(1, 2),
        default=1,
        help="ADC input channel to read. Default: 1",
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=1000.0,
        help="Arbitrary waveform repetition frequency in Hz. Default: 1000",
    )
    parser.add_argument(
        "--amplitude",
        type=float,
        default=1.0,
        help="Output peak amplitude scale in V. Default: 1.0",
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="Output DC offset in V. Default: 0.0",
    )
    parser.add_argument(
        "--decimation",
        type=int,
        default=1,
        help="Acquisition decimation. Default: 1",
    )
    parser.add_argument(
        "--trigger-delay",
        type=int,
        default=0,
        help="Acquisition trigger delay in samples. Default: 0",
    )
    parser.add_argument(
        "--settle-time",
        type=float,
        default=0.01,
        help="Seconds to wait after triggering before reading ADC data. Default: 0.01",
    )
    parser.add_argument(
        "--loops",
        type=int,
        default=1,
        help="Number of passes through all batches. 0 means run until Ctrl+C. Default: 1",
    )
    parser.add_argument(
        "--leave-output-on",
        action="store_true",
        help="Leave the generator output enabled when the script exits.",
    )
    return parser.parse_args()


def validate_args(args):
    if args.frequency <= 0.0:
        raise ValueError("--frequency must be greater than 0 Hz")
    if not 0.0 <= args.amplitude <= 1.0:
        raise ValueError("--amplitude must be in the range 0 to 1 V")
    if not -1.0 <= args.offset <= 1.0:
        raise ValueError("--offset must be in the range -1 to 1 V")
    if args.offset + args.amplitude > 1.0 or args.offset - args.amplitude < -1.0:
        raise ValueError("--offset +/- --amplitude must stay within about +/-1 V")
    if args.decimation not in VALID_DECIMATIONS:
        raise ValueError(f"--decimation must be one of {sorted(VALID_DECIMATIONS)}")
    if args.settle_time < 0.0:
        raise ValueError("--settle-time must be >= 0")
    if args.loops < 0:
        raise ValueError("--loops must be >= 0")


def load_batches(input_file):
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {path}")

    if path.suffix.lower() == ".npy":
        data = np.load(path)
    else:
        data = np.loadtxt(path, delimiter=",")

    data = np.asarray(data, dtype=float)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    if data.ndim != 2:
        raise ValueError("Input data must be 1D or 2D")
    if data.shape[1] < 2:
        raise ValueError("Each waveform batch must contain at least two samples")
    if np.any(data < -1.0) or np.any(data > 1.0):
        raise ValueError("Waveform samples must be normalized to the range -1 to 1")

    return data


def waveform_to_scpi(samples):
    return "{" + ",".join(f"{sample:.7g}" for sample in samples) + "}"


def parse_adc_buffer(response):
    cleaned = response.strip("{}\n\r ").replace("  ", "")
    if not cleaned:
        return np.array([], dtype=float)
    return np.array([float(value) for value in cleaned.split(",")], dtype=float)


def send(rp_s, command):
    rp_s.tx_txt(command)


def configure_generator(rp_s, channel, frequency, amplitude, offset):
    prefix = f"SOUR{channel}"
    send(rp_s, "GEN:RST")
    send(rp_s, f"{prefix}:FUNC ARBITRARY")
    send(rp_s, f"{prefix}:FREQ:FIX {frequency}")
    send(rp_s, f"{prefix}:VOLT {amplitude}")
    send(rp_s, f"{prefix}:VOLT:OFFS {offset}")
    send(rp_s, f"OUTPUT{channel}:STATE ON")


def send_waveform_batch(rp_s, channel, samples):
    prefix = f"SOUR{channel}"
    send(rp_s, f"{prefix}:TRAC:DATA:DATA {waveform_to_scpi(samples)}")
    send(rp_s, f"{prefix}:TRig:INT")


def acquire_adc_buffer(rp_s, channel, decimation, trigger_delay, settle_time):
    send(rp_s, "ACQ:RST")
    send(rp_s, "ACQ:DATA:FORMAT ASCII")
    send(rp_s, "ACQ:DATA:UNITS VOLTS")
    send(rp_s, f"ACQ:DEC {decimation}")
    send(rp_s, f"ACQ:TRIG:DLY {trigger_delay}")
    send(rp_s, "ACQ:START")
    send(rp_s, "ACQ:TRIG NOW")
    time.sleep(settle_time)
    send(rp_s, f"ACQ:SOUR{channel}:DATA?")
    return parse_adc_buffer(rp_s.rx_txt())


def write_result(writer, loop_index, batch_index, acquired):
    row = {
        "loop": loop_index,
        "batch": batch_index,
        "sample_count": len(acquired),
        "mean_v": float(np.mean(acquired)) if len(acquired) else "",
        "min_v": float(np.min(acquired)) if len(acquired) else "",
        "max_v": float(np.max(acquired)) if len(acquired) else "",
        "samples_v": " ".join(f"{sample:.7g}" for sample in acquired),
    }
    writer.writerow(row)


def disable_output(rp_s, channel):
    send(rp_s, f"OUTPUT{channel}:STATE OFF")


def close_connection(rp_s):
    close = getattr(rp_s, "close", None)
    if callable(close):
        close()


def main():
    args = parse_args()

    try:
        validate_args(args)
        batches = load_batches(args.input_file)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    rp_s = scpi.scpi(args.rp_ip)
    fieldnames = ["loop", "batch", "sample_count", "mean_v", "min_v", "max_v", "samples_v"]

    try:
        configure_generator(
            rp_s,
            args.gen_channel,
            args.frequency,
            args.amplitude,
            args.offset,
        )

        print(
            f"Loaded {batches.shape[0]} batch(es), {batches.shape[1]} samples each. "
            f"Writing acquired data to {args.output_file}"
        )

        with open(args.output_file, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            loop_index = 0
            while args.loops == 0 or loop_index < args.loops:
                for batch_index, batch in enumerate(batches):
                    send_waveform_batch(rp_s, args.gen_channel, batch)
                    acquired = acquire_adc_buffer(
                        rp_s,
                        args.acq_channel,
                        args.decimation,
                        args.trigger_delay,
                        args.settle_time,
                    )
                    write_result(writer, loop_index, batch_index, acquired)
                    csv_file.flush()
                    print(
                        f"loop={loop_index} batch={batch_index} "
                        f"acquired_samples={len(acquired)}"
                    )
                loop_index += 1

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        if not args.leave_output_on:
            disable_output(rp_s, args.gen_channel)
            print(f"OUT{args.gen_channel} disabled.")
        close_connection(rp_s)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
