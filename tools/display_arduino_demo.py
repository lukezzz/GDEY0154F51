#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from gdey0154f51 import GDEY0154F51, PinConfig, SpiConfig
from gdey0154f51.constants import BUFFER_SIZE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Display an Arduino demo .h buffer on GDEY0154F51 via Raspberry Pi"
    )
    parser.add_argument(
        "--header",
        default="GDEM0154F51H_Arduino/Ap_29demo.h",
        help="Path to Arduino demo header file",
    )
    parser.add_argument(
        "--no-sleep", action="store_true", help="Do not enter deep sleep after refresh"
    )
    parser.add_argument(
        "--fast-update",
        action="store_true",
        help="Use Arduino fast full-update initialization sequence",
    )

    parser.add_argument("--spi-bus", type=int, default=0)
    parser.add_argument("--spi-device", type=int, default=0)
    parser.add_argument("--spi-speed", type=int, default=2_000_000)
    parser.add_argument(
        "--manual-cs",
        action="store_true",
        help="Use GPIO-managed CS instead of spidev hardware chip select",
    )

    parser.add_argument("--pin-rst", type=int, default=17)
    parser.add_argument("--pin-dc", type=int, default=25)
    parser.add_argument("--pin-cs", type=int, default=8)
    parser.add_argument("--pin-busy", type=int, default=24)
    parser.add_argument(
        "--busy-active-low",
        action="store_true",
        help="Treat BUSY=0 as ready (some board revisions use inverted polarity)",
    )
    parser.add_argument(
        "--no-busy-auto-fallback",
        action="store_true",
        help="Disable automatic BUSY polarity fallback after timeout",
    )

    return parser.parse_args()


def load_demo_buffer(header_path: Path) -> bytes:
    text = header_path.read_text(encoding="utf-8", errors="ignore")
    hex_bytes = re.findall(r"0X([0-9A-Fa-f]{2})", text)
    if len(hex_bytes) < BUFFER_SIZE:
        raise ValueError(
            f"header contains only {len(hex_bytes)} bytes, need at least {BUFFER_SIZE}"
        )
    return bytes(int(v, 16) for v in hex_bytes[:BUFFER_SIZE])


def main() -> None:
    args = parse_args()
    header_path = Path(args.header)

    if not header_path.exists():
        raise FileNotFoundError(f"header file not found: {header_path}")

    demo_buffer = load_demo_buffer(header_path)

    pins = PinConfig(
        rst=args.pin_rst, dc=args.pin_dc, cs=args.pin_cs, busy=args.pin_busy
    )
    spi = SpiConfig(
        bus=args.spi_bus,
        device=args.spi_device,
        max_speed_hz=args.spi_speed,
        mode=0,
        use_hardware_cs=not args.manual_cs,
    )

    epd = GDEY0154F51.from_rpi(
        pin_config=pins,
        spi_config=spi,
        busy_ready_level=0 if args.busy_active_low else 1,
        busy_auto_fallback=not args.no_busy_auto_fallback,
    )
    try:
        epd.display_demo_buffer(
            demo_buffer,
            auto_sleep=not args.no_sleep,
            fast_update=args.fast_update,
        )
        print(f"display refresh complete from: {header_path}")
    finally:
        epd.close()


if __name__ == "__main__":
    main()
