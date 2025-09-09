import os
import re
from rich.table import Table
from rich.console import Console
from rich.text import Text

class Workout:
    def __init__(self):
        self.blocks = []  # list of block‐dicts
        self.clipboard = []  # Initialize as empty list instead of None
        self.ftp = None  

    def add_block(self, block_type, **params):
        """
        Add a workout block 
        block_type: "steady", "warmup", "cooldown", or "interval"
        steady expects:   zone, duration, power
        warmup/cooldown: power_start, power_end, duration (in seconds)
        interval:        power1, dur1, power2, dur2, reps
        """
        if not block_type or block_type not in ["steady", "warmup", "cooldown", "interval"]:
            raise ValueError(f"Invalid block type: {block_type}")
            
        blk = {"type": block_type}
        
        try:
            if block_type == "steady":
                blk["zone"] = str(params.get("zone", "Z1")).upper()
                blk["duration"] = str(params.get("duration", "0s"))
                blk["power"] = int(params.get("power", 0))
                blk["power_mode"] = params.get("power_mode", "custom")

                
            elif block_type in ("warmup", "cooldown"):
                blk["power_start"] = int(params.get("power_start", 0))
                blk["power_end"] = int(params.get("power_end", 0))
                blk["duration"] = int(params.get("duration", 0))
                
            elif block_type == "interval":
                blk["power1"] = int(params.get("power1", 0))
                blk["dur1"] = int(params.get("dur1", 0))  
                blk["power2"] = int(params.get("power2", 0))
                blk["dur2"] = int(params.get("dur2", 0))
                blk["reps"] = int(params.get("reps", 1))
                
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid parameters for {block_type} block: {e}")
            
        self.blocks.append(blk)

    def edit_block(self, index, zone=None, duration=None, power=None):
        """Edit a block"""
        if not (0 <= index < len(self.blocks)):
            raise IndexError(f"Block index {index} out of range")
            
        block = self.blocks[index]
        
        try:
            if zone is not None:
                if zone.upper() not in ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "AUTO"]:
                    raise ValueError(f"Invalid zone: {zone}")
                block["zone"] = zone.upper()
                
            if duration is not None:
                # Validate duration format
                if isinstance(duration, str) and duration.endswith('s'):
                    dur_seconds = int(duration[:-1])
                    if dur_seconds <= 0:
                        raise ValueError("Duration must be positive")
                block["duration"] = duration
                
            if power is not None:
                power_val = int(power)
                if power_val < 0:
                    raise ValueError("Power cannot be negative")
                block["power"] = power_val
                
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid edit parameters: {e}")

    def delete_block(self, index):
        """Delete a block"""
        if not (0 <= index < len(self.blocks)):
            raise IndexError(f"Block index {index} out of range")
        self.blocks.pop(index)

    def export(self, filepath, name="Custom Workout"):
        """Export"""
        if not self.blocks:
            raise ValueError("Cannot export empty workout")
            
        if self.ftp is None or self.ftp <= 0:
            raise ValueError("FTP must be set before exporting")
            
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(filepath)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                
            with open(filepath, "w", encoding='utf-8') as f:
                f.write(self.to_zwo(name=name))
        except (OSError, IOError) as e:
            raise IOError(f"Failed to write file {filepath}: {e}")

    def to_zwo(self, name="Custom Workout"):
        """Generate ZWO"""
        if self.ftp is None or self.ftp <= 0:
            raise ValueError("FTP must be set to generate ZWO file")
            
        def to_sec(d):
            """Convert duration to seconds with validation"""
            if isinstance(d, int):
                return max(0, d)  # Ensure non-negative
            if isinstance(d, str):
                # Strip 's' suffix and convert
                duration_str = d.rstrip('s')
                try:
                    return max(0, int(duration_str))
                except ValueError:
                    return 0
            return 0

        def ratio(p):
            """Convert power to FTP ratio with validation"""
            try:
                power_val = float(p)
                if power_val < 0:
                    power_val = 0
                return round(power_val / self.ftp, 6)
            except (ValueError, TypeError, ZeroDivisionError):
                return 0.0

        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append("<workout_file>")
        lines.append(f"  <name>{self._escape_xml(name)}</name>")
        lines.append("  <description></description>")
        lines.append("  <sportType>bike</sportType>")
        lines.append("  <tags/>")
        lines.append("  <workout>")

        for i, b in enumerate(self.blocks):
            try:
                btype = b.get("type", "steady")

                if btype == "steady":
                    dur = to_sec(b.get("duration", 0))
                    if dur <= 0:
                        continue  # Skip invalid blocks
                    p_ratio = ratio(b.get("power", 0))
                    lines.append(
                        f'    <SteadyState Duration="{dur}" Power="{p_ratio}" pace="0"/>'
                    )

                elif btype == "warmup":
                    dur = to_sec(b.get("duration", 0))
                    if dur <= 0:
                        continue
                    low = ratio(b.get("power_start", 0))
                    high = ratio(b.get("power_end", 0))
                    lines.append(
                        f'    <Warmup Duration="{dur}" PowerLow="{low}" PowerHigh="{high}" pace="0"/>'
                    )

                elif btype == "cooldown":
                    dur = to_sec(b.get("duration", 0))
                    if dur <= 0:
                        continue
                    high = ratio(b.get("power_start", 0))  # Note: reversed for cooldown
                    low = ratio(b.get("power_end", 0))
                    lines.append(
                        f'    <Cooldown Duration="{dur}" PowerLow="{low}" PowerHigh="{high}" pace="0"/>'
                    )

                elif btype == "interval":
                    reps = max(1, b.get("reps", 1))
                    on_d = to_sec(b.get("dur1", 0))
                    off_d = to_sec(b.get("dur2", 0))
                    if on_d <= 0 or off_d <= 0:
                        continue  # Skip invalid intervals
                    on_p = ratio(b.get("power1", 0))
                    off_p = ratio(b.get("power2", 0))
                    lines.append(
                        f'    <IntervalsT Repeat="{reps}" OnDuration="{on_d}" OffDuration="{off_d}" '
                        f'OnPower="{on_p}" OffPower="{off_p}" pace="0"/>'
                    )

            except Exception as e:
                # Log the error but continue processing other blocks
                print(f"Warning: Skipping block {i} due to error: {e}")
                continue

        lines.append("  </workout>")
        lines.append("</workout_file>")
        return "\n".join(lines)

    def _escape_xml(self, text):
        """Escape XML special characters"""
        if not isinstance(text, str):
            text = str(text)
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#39;"))

    def _zone_color(self, zone):
        """Get color for zone with fallback"""
        color_map = {
            "Z1": "grey",
            "Z2": "blue", 
            "Z3": "green",
            "Z4": "yellow",
            "Z5": "orange1",
            "Z6": "red",
            "AUTO": "white"
        }
        return color_map.get(str(zone).upper(), "white")

    
    def _power_to_zone(self, power):
        """Convert power to zone"""
        if self.ftp is None or self.ftp <= 0:
            return "Z?"
        
        try:
            power = float(power)
            if power < 0:
                return "Z?"
            pct = (power / self.ftp) * 100
            if pct < 60:
                return "Z1"
            elif pct < 76:
                return "Z2"
            elif pct < 90:
                return "Z3"
            elif pct < 105:
                return "Z4"
            elif pct < 119:
                return "Z5"
            else:
                return "Z6"
        except (ValueError, TypeError):
            return "Z?"

    def _zone_to_power(self, zone):
        """Convert zone to power"""
        if self.ftp is None or self.ftp <= 0:
            return None
            
        try:
            zperc = {
                "Z1": 0.55,
                "Z2": 0.65,
                "Z3": 0.80,
                "Z4": 0.95,
                "Z5": 1.10,
                "Z6": 1.25
            }.get(zone.upper(), None)
            return int(self.ftp * zperc) if zperc is not None else None
        except (ValueError, TypeError):
            return None

    def _block_seconds(self, b: dict) -> int:
        """Return block duration in seconds for any block type."""
        t = b.get("duration")
        if t is not None:
            return int(t) if isinstance(t, int) else int(re.sub(r"[^\d]", "", str(t)))

        if b["type"] == "interval":
            # Each rep has dur1 + dur2
            return (b["dur1"] + b["dur2"]) * b["reps"]
        return 0  # fallback


    def _block_avg_ratio(self, b: dict) -> float:
        """Return average FTP ratio (IF) for the block."""
        if not self.ftp:
            return 0.0

        if b["type"] == "steady":
            return b["power"] / self.ftp

        if b["type"] in ("warmup", "cooldown"):
            return (b["power_start"] + b["power_end"]) / 2 / self.ftp

        if b["type"] == "interval":
            on = b["power1"] / self.ftp
            off = b["power2"] / self.ftp
            total = (b["dur1"] + b["dur2"])
            return (on * b["dur1"] + off * b["dur2"]) / total

        return 0.0


    def total_seconds(self) -> int:
        """Sum of all block durations."""
        return sum(self._block_seconds(b) for b in self.blocks)


    def estimate_tss(self) -> float:
        """
        Approx Training Stress Score using:
            TSS = (sec * IF^2) / 36
        where IF is duration-weighted average Intensity Factor.
        """
        sec = self.total_seconds()
        if sec == 0 or not self.ftp:
            return 0.0

        # duration-weighted IF
        total_if_x_sec = sum(
            self._block_avg_ratio(b) ** 2 * self._block_seconds(b)
            for b in self.blocks
        )
        tss = total_if_x_sec / (36 * 1.0)  # 36 = 3600 sec / 100
        return round(tss, 1)