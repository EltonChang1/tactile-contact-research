"""Numerical starter code from the user-provided refined implementation guide."""


from pathlib import Path
import re

RECORD_NAME = re.compile(
    r"^(?P<surface_id>\d+)_(?P<direction_deg>\d+)_(?P<speed_mm_s>\d+)_"
    r"(?P<force_mN>\d+)_(?P<repeat_id>\d+)\.parquet$"
)

def parse_record_name(path):
    match = RECORD_NAME.fullmatch(Path(path).name)
    if match is None:
        raise ValueError(f"Unrecognized sensor filename: {Path(path).name}")
    row = {k: int(v) for k, v in match.groupdict().items()}
    if row["direction_deg"] not in range(0, 360, 45):
        raise ValueError("Unexpected direction")
    if row["speed_mm_s"] not in [20, 30, 40, 50, 60]:
        raise ValueError("Unexpected speed")
    if row["force_mN"] not in [500, 1000]:
        raise ValueError("Unexpected nominal load")
    if row["repeat_id"] not in [0, 1]:
        raise ValueError("Unexpected repeat")
    row["nominal_force_N"] = row["force_mN"] / 1000.0
    row["recording_id"] = Path(path).stem
    return row
