import os
import re
from rich.table import Table
from rich.console import Console
from rich.text import Text

class Workout:
    def __init__(self):
        self.blocks = []  # list of block‐dicts
        self.clipboard = None      # for copy/paste
        self.ftp = None  


    def add_block(self, block_type, **params):
        """
        block_type: "steady", "warmup", "cooldown", or "interval"
        steady expects:   zone, duration, power
        warmup/cooldown: power_start, power_end, duration (in seconds)
        interval:        power1, dur1, power2, dur2, reps
        """
        blk = {"type": block_type}
        if block_type == "steady":
            blk["zone"]     = params["zone"].upper()
            blk["duration"] = params["duration"]
            blk["power"]    = params["power"]
        elif block_type in ("warmup","cooldown"):
            blk["power_start"] = params["power_start"]
            blk["power_end"]   = params["power_end"]
            blk["duration"]    = params["duration"]
        elif block_type == "interval":
            blk["power1"] = params["power1"]
            blk["dur1"]   = params["dur1"]
            blk["power2"] = params["power2"]
            blk["dur2"]   = params["dur2"]
            blk["reps"]   = params["reps"]
        else:
            raise ValueError(f"Unknown block type: {block_type}")
        self.blocks.append(blk)

    def edit_block(self, index, zone=None, duration=None, power=None):
        block = self.blocks[index]
        if zone: block["zone"] = zone.upper()
        if duration: block["duration"] = duration
        if power: block["power"] = power

    def delete_block(self, index):
        self.blocks.pop(index)

    def display(self, console: Console):
        table = Table(title="🏁 Zwift Workout Timeline")
        table.add_column("Index")
        table.add_column("Zone")
        table.add_column("Duration")
        table.add_column("Power (W)")
        for i, b in enumerate(self.blocks):
            color = self._zone_color(b["zone"])
            table.add_row(str(i), f"[{color}]{b['zone']}[/{color}]", b["duration"], str(b["power"]))
        console.print(table)

    def export(self, filepath, name="Custom Workout"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(self.to_zwo(name=name))


    def to_zwo(self, name="Custom Workout"):
        def to_sec(d):
            # if stored as int, just return it; else strip non-digits
            return d if isinstance(d, int) else int(re.sub(r"[^\d]", "", d))

        def ratio(p):
            return round(p / self.ftp, 8) if (self.ftp and self.ftp > 0) else 0

        lines = []
        lines.append("<workout_file>")
        lines.append(f"  <name>{name}</name>")
        lines.append("  <description></description>")
        lines.append("  <sportType>bike</sportType>")
        lines.append("  <tags/>")
        lines.append("  <workout>")

        for b in self.blocks:
            btype = b.get("type", "steady")

            if btype == "steady":
                dur = to_sec(b["duration"])
                p_ratio = ratio(b["power"])
                lines.append(
                    f'    <SteadyState Duration="{dur}" Power="{p_ratio}" pace="0"/>'
                )

            elif btype == "warmup":
                dur = to_sec(b["duration"])
                low = ratio(b["power_start"])
                high = ratio(b["power_end"])
                lines.append(
                    f'    <Warmup Duration="{dur}" PowerLow="{low}" PowerHigh="{high}" pace="0"/>'
                )

            elif btype == "cooldown":
                dur = to_sec(b["duration"])
                low = ratio(b["power_start"])
                high = ratio(b["power_end"])
                lines.append(
                    f'    <Cooldown Duration="{dur}" PowerLow="{low}" PowerHigh="{high}" pace="0"/>'
                )

            elif btype == "interval":
                reps = b["reps"]
                on_d = to_sec(b["dur1"])
                off_d = to_sec(b["dur2"])
                on_p = ratio(b["power1"])
                off_p = ratio(b["power2"])
                lines.append(
                    f'    <IntervalsT Repeat="{reps}" OnDuration="{on_d}" OffDuration="{off_d}" '
                    f'OnPower="{on_p}" OffPower="{off_p}" pace="0"/>'
                )

            else:
                # unknown type; skip or raise
                continue

        lines.append("  </workout>")
        lines.append("</workout_file>")
        return "\n".join(lines)

    def _zone_color(self, zone):
        return {
            "Z1": "green",
            "Z2": "yellow",
            "Z3": "orange1",
            "Z4": "red",
            "Z5": "magenta",
            "Z6": "blue"
        }.get(zone.upper(), "white")

    def _minutes_to_seconds(self, dur_str):
        if "min" in dur_str:
            return int(dur_str.replace("min", "")) * 60
        return int(dur_str)  # assume seconds if no "min"
