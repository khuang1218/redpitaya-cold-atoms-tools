#!/usr/bin/env python3
"""Generate a sine wave on a Red Pitaya fast output using SCPI."""

import argparse
import sys
import time

try:
    import redpitaya_scpi as scpi
except ImportError:
    import scpi


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a sine wave on a Red Pitaya fast analog output."
    )
    parser.add_argument("rp_ip", help="Red Pitaya IP address or hostname")
    parser.add_argument("frequency_hz", type=float, help="Sine frequency in Hz")
    parser.add_argument(
        "amplitude_v",
        nargs="?",
        type=float,
        default=0.5,
        help="Peak amplitude in V, 0 to 1. Default: 0.5",
    )
    parser.add_argument(
        "offset_v",
        nargs="?",
        type=float,
        default=0.0,
        help="DC offset in V, -1 to 1. Default: 0.0",
    )
    parser.add_argument(
        "channel",
        nargs="?",
        type=int,
        default=1,
        choices=(1, 2),
        help="Output channel, 1=OUT1 or 2=OUT2. Default: 1",
    )
    parser.add_argument(
        "duration_s",
        nargs="?",
        type=float,
        default=0.0,
        help="Run time in seconds. 0 means run until Ctrl+C. Default: 0",
    )
    parser.add_argument(
        "--leave-on",
        action="store_true",
        help="Leave the output enabled when the script exits.",
    )
    return parser.parse_args()


def validate_args(args):
    if args.frequency_hz <= 0.0:
        raise ValueError("frequency_hz must be greater than 0")
    if not 0.0 <= args.amplitude_v <= 1.0:
        raise ValueError("amplitude_v must be in the range 0 to 1 V")
    if not -1.0 <= args.offset_v <= 1.0:
        raise ValueError("offset_v must be in the range -1 to 1 V")
    if args.offset_v + args.amplitude_v > 1.0 or args.offset_v - args.amplitude_v < -1.0:
        raise ValueError("offset_v +/- amplitude_v must stay within about +/-1 V")
    if args.duration_s < 0.0:
        raise ValueError("duration_s must be >= 0")


def send(rp_s, command):
    rp_s.tx_txt(command)


def configure_sine(rp_s, channel, frequency_hz, amplitude_v, offset_v):
    prefix = f"SOUR{channel}"
    send(rp_s, f"{prefix}:FUNC SINE")
    send(rp_s, f"{prefix}:FREQ:FIX {frequency_hz}")
    send(rp_s, f"{prefix}:VOLT {amplitude_v}")
    send(rp_s, f"{prefix}:VOLT:OFFS {offset_v}")
    send(rp_s, f"OUTPUT{channel}:STATE ON")
    send(rp_s, f"{prefix}:TRig:INT")


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
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    rp_s = scpi.scpi(args.rp_ip)

    try:
        configure_sine(
            rp_s,
            args.channel,
            args.frequency_hz,
            args.amplitude_v,
            args.offset_v,
        )
        print(
            f"Generating sine wave on OUT{args.channel}: "
            f"frequency={args.frequency_hz:g} Hz, "
            f"amplitude={args.amplitude_v:g} V, offset={args.offset_v:g} V"
        )

        if args.duration_s > 0.0:
            time.sleep(args.duration_s)
        else:
            print("Press Ctrl+C to stop.")
            while True:
                time.sleep(1.0)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        if not args.leave_on:
            disable_output(rp_s, args.channel)
            print(f"OUT{args.channel} disabled.")
        close_connection(rp_s)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
