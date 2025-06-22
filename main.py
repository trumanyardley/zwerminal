from workout import Workout
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
import re
import os

console = Console()
workout = Workout()


def display_timeline():
    if not workout.blocks:
        console.print("[yellow]No workout blocks yet. Add some blocks to see the timeline![/]")
        return
        
    table = Table(title="\U0001F3C1 Workout Timeline")
    table.add_column("Idx")
    table.add_column("Type")
    table.add_column("Zone/Info")
    table.add_column("Duration")
    table.add_column("Power")

    for i, b in enumerate(workout.blocks):
        try:
            btype = b.get("type", "steady")
            power = ""
            
            # --- steady blocks ---
            if btype == "steady":
                power = b.get("power", 0)
                zone = b.get("zone", "Z1")
                if zone == "AUTO" and workout.ftp is not None:
                    zone = workout._power_to_zone(power)
                dur_s = parse_duration_to_seconds(b.get("duration", "0s"))
                dur = f"{dur_s//60}:{str(dur_s%60).zfill(2)}"
                color = workout._zone_color(zone)
                info = f"[{color}]{zone}[/{color}]"

            # --- ramp blocks (warmup/cooldown) ---
            elif btype in ("warmup", "cooldown"):
                p0 = b.get("power_start", 0)
                p1 = b.get("power_end", 0)
                dur_s = b.get("duration", 0)
                dur = f"{dur_s//60}:{str(dur_s%60).zfill(2)}"
                info = f"{p0}→{p1}"
                power = f"{p0}-{p1}"

            # --- interval blocks ---
            elif btype == "interval":
                p1 = b.get("power1", 0)
                d1 = b.get("dur1", 0)
                p2 = b.get("power2", 0)
                d2 = b.get("dur2", 0)
                reps = b.get("reps", 1)
                total_s = (d1 + d2) * reps
                dur = f"{total_s//60}:{str(total_s%60).zfill(2)}"
                info = f"{p1}/{p2}×{reps}"
                power = f"{p1}/{p2}"

            else:
                # Fallback (shouldn't happen)
                info = "Unknown"
                dur = "0:00"
                power = "0"
            
            table.add_row(str(i), btype, info, dur, str(power))
            
        except Exception as e:
            # Handle corrupted block data gracefully
            table.add_row(str(i), "ERROR", str(e), "0:00", "0")
            console.print(f"[red]Warning: Block {i} has corrupted data: {e}[/]")

    console.print(table)


def parse_duration_to_seconds(duration_str):
    """Parse duration string to seconds"""
    if not duration_str:
        return 0
        
    try:
        duration_str = str(duration_str).strip().lower()
        
        # Handle colon format (MM:SS)
        if ":" in duration_str:
            parts = duration_str.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                if minutes < 0 or seconds < 0 or seconds >= 60:
                    raise ValueError("Invalid time format")
                return minutes * 60 + seconds
        
        # Handle minutes
        if "min" in duration_str:
            minutes = int(re.sub(r"[^0-9]", "", duration_str))
            if minutes < 0:
                raise ValueError("Duration cannot be negative")
            return minutes * 60
            
        # Handle seconds
        if "s" in duration_str:
            seconds = int(re.sub(r"[^0-9]", "", duration_str))
            if seconds < 0:
                raise ValueError("Duration cannot be negative")
            return seconds
            
        # Handle plain numbers (assume seconds)
        seconds = int(duration_str)
        if seconds < 0:
            raise ValueError("Duration cannot be negative")
        return seconds
        
    except (ValueError, AttributeError) as e:
        console.print(f"[red]Invalid duration format: '{duration_str}'. Using 0 seconds.[/]")
        return 0

def update_auto_powers():
    """Update auto powers"""
    if not workout.ftp:
        return
        
    for b in workout.blocks:
        try:
            zone = b.get('zone', '')
            if zone in ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6"] and workout.ftp is not None:
                new_power = workout._zone_to_power(zone)
                if new_power is not None:
                    b['power'] = new_power
            elif zone == "AUTO" and workout.ftp is not None:
                power = b.get('power', 0)
                b['zone'] = workout._power_to_zone(power)
        except Exception as e:
            console.print(f"[red]Error updating power for block: {e}[/]")


def validate_index(index_str, max_index):
    """Validate block index"""
    try:
        index = int(index_str)
        if index < 0 or index >= max_index:
            console.print(f"[red]Index {index} is out of range (0-{max_index-1})[/]")
            return None
        return index
    except ValueError:
        console.print(f"[red]Invalid index: '{index_str}'. Must be a number.[/]")
        return None


def validate_positive_int(value_str, name):
    """Validate positive integer input"""
    try:
        value = int(value_str)
        if value <= 0:
            console.print(f"[red]{name} must be positive, got {value}[/]")
            return None
        return value
    except ValueError:
        console.print(f"[red]Invalid {name}: '{value_str}'. Must be a positive number.[/]")
        return None


def validate_power(power_str):
    """Validate power input"""
    try:
        power = int(power_str)
        if power < 0:
            console.print(f"[red]Power cannot be negative, got {power}[/]")
            return None
        if power > 2000:  # Reasonable upper limit
            console.print(f"[red]Power seems too high: {power}W. Are you sure?[/]")
        return power
    except ValueError:
        console.print(f"[red]Invalid power: '{power_str}'. Must be a number.[/]")
        return None


def repl():
    console.print("[bold blue]Zwerminal CLI 🌀 v0.1.0[/]")
    console.print("Type 'help' to see available commands.\n")

    while True:
        try:
            cmd = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not cmd:
            continue

        parts = cmd.split()
        command = parts[0].lower()
        args = parts[1:]

        try:
            if command == "exit":
                break

            elif command == "help":
                console.print("""
[bold cyan]Available Commands:[/]
  ftp <value>
      Set your FTP in watts. All subsequent blocks use this FTP.
  
  add Zx <duration>
      Add a steady block in zone Zx (Z1–Z6) for given duration 
      (e.g. 5min, 90s, 1:30). Power is calculated from FTP.

  add <duration> <power>
      Add a steady block at the given power (watts). Zone is 
      auto-detected based on FTP.

  add warmup <startW> <endW> <duration>
      Add a ramp (warmup) from startW to endW over duration.

  add cooldown <startW> <endW> <duration>
      Add a ramp (cooldown) from startW to endW over duration.

  add interval <p1> <t1> <p2> <t2> <reps>
      Add an interval block: p1 watts for t1, p2 watts for t2, 
      repeated reps times.

  copy <start_idx> <end_idx>
      Copy blocks in the given index range [start_idx..end_idx] 
      into the clipboard.

  paste
      Paste the clipboard blocks to the end of the workout.

  edit <idx> [-zone Zx] [-time <duration>] [-power <watts>]
      Edit block at index. Cannot edit zone and power at the same time.

  delete <idx>
      Remove the block at the given index.

  preview
      Display the current workout timeline.

  export <filename.zwo>
      Save to workouts/<filename>.zwo (prompts for workout name).

  help
      Show this help message.

  exit
      Quit the app.
""")

            elif command == "ftp" and len(args) == 1:
                ftp_value = validate_positive_int(args[0], "FTP")
                if ftp_value is None:
                    continue 
                workout.ftp = ftp_value
                update_auto_powers()
                console.print(f"✅ FTP set to [bold]{workout.ftp}W[/]")
                display_timeline()

            elif command == "add" and args:
                sub = args[0].lower()

                # 1) Warmup / Cooldown
                if sub in ("warmup", "cooldown") and len(args) == 4:
                    p0 = validate_power(args[1])
                    p1 = validate_power(args[2])
                    if p0 is None or p1 is None:
                        continue
                    dur = parse_duration_to_seconds(args[3])
                    if dur == 0:
                        console.print("[red]Duration must be greater than 0[/]")
                        continue
                    if p0 >= p1 and sub == "warmup":
                        console.print("[red]Starting power cannot be greater than or equal to end power[/]")
                        continue
                    if p0 <= p1 and sub == "cooldown":
                        console.print("[red]Starting power cannot be less than or equal to end power[/]")
                        continue
                    workout.add_block(sub, power_start=p0, power_end=p1, duration=dur)
                    display_timeline()

                # 2) Interval: add interval p1 t1 p2 t2 reps
                elif sub == "interval" and len(args) == 6:
                    p1 = validate_power(args[1])
                    p2 = validate_power(args[3])
                    reps = validate_positive_int(args[5], "reps")
                    if p1 is None or p2 is None or reps is None:
                        continue
                    t1 = parse_duration_to_seconds(args[2])
                    t2 = parse_duration_to_seconds(args[4])
                    if t1 == 0 or t2 == 0:
                        console.print("[red]Interval durations must be greater than 0[/]")
                        continue
                    workout.add_block("interval",
                                      power1=p1, dur1=t1,
                                      power2=p2, dur2=t2,
                                      reps=reps)
                    display_timeline()

                # 3) `add Zx time` or `add time power`
                elif len(args) == 2:
                    if args[0].upper().startswith("Z"):
                        zone, duration_raw = args
                        if zone.upper() not in ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6"]:
                            console.print("[red]Invalid zone. Use Z1-Z6.[/]")
                            continue
                        duration_s = parse_duration_to_seconds(duration_raw)
                        if duration_s == 0:
                            console.print("[red]Duration must be greater than 0[/]")
                            continue
                        duration = f"{duration_s}s"
                        if workout.ftp is not None:
                            power = workout._zone_to_power(zone)
                            if power is not None:
                                workout.add_block("steady", zone=zone.upper(), duration=duration, power=power)
                                display_timeline()
                            else:
                                console.print("[red]Could not calculate power for zone.[/]")
                        else:
                            console.print("[red]Set FTP first using 'ftp [value]'[/]")
                    else:
                        # Assume power, duration format
                        power = validate_power(args[0])
                        if power is None:
                            continue
                        duration_s = parse_duration_to_seconds(args[1])
                        if duration_s == 0:
                            console.print("[red]Duration must be greater than 0[/]")
                            continue
                        duration = f"{duration_s}s"
                        workout.add_block("steady", zone="AUTO", duration=duration, power=power)
                        update_auto_powers()
                        display_timeline()
                else:
                    console.print("[red]Invalid 'add' usage. See 'help'.[/]")

            elif command == "copy" and len(args) == 2:
                if not workout.blocks:
                    console.print("[red]No blocks to copy[/]")
                    continue
                i0 = validate_index(args[0], len(workout.blocks))
                i1 = validate_index(args[1], len(workout.blocks))
                if i0 is None or i1 is None:
                    continue
                if i0 > i1:
                    console.print("[red]Start index must be <= end index[/]")
                    continue
                workout.clipboard = workout.blocks[i0:i1+1].copy()
                console.print(f"✅ Copied blocks {i0}–{i1}")

            elif command == "paste":
                if not workout.clipboard:
                    console.print("[red]Nothing to paste. Use copy first.[/]")
                    continue
                workout.blocks.extend([block.copy() for block in workout.clipboard])
                display_timeline()

            elif command == "edit" and len(args) >= 1:
                if not workout.blocks:
                    console.print("[red]No blocks to edit[/]")
                    continue
                index = validate_index(args[0], len(workout.blocks))
                if index is None:
                    continue
                    
                flags = args[1:]
                kwargs = {}
                
                if "-zone" in flags and "-power" in flags:
                    console.print("[red]❌ Cannot specify both -zone and -power. Choose one.[/]")
                    continue
                    
                if "-zone" in flags:
                    z_idx = flags.index("-zone")
                    if z_idx + 1 < len(flags):
                        zone = flags[z_idx + 1].upper()
                        if zone not in ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6"]:
                            console.print("[red]Invalid zone. Use Z1-Z6.[/]")
                            continue
                        kwargs["zone"] = zone
                        
                if "-time" in flags:
                    t_idx = flags.index("-time")
                    if t_idx + 1 < len(flags):
                        duration_s = parse_duration_to_seconds(flags[t_idx + 1])
                        if duration_s == 0:
                            console.print("[red]Duration must be greater than 0[/]")
                            continue
                        kwargs["duration"] = f"{duration_s}s"
                        
                if "-power" in flags:
                    p_idx = flags.index("-power")
                    if p_idx + 1 < len(flags):
                        power = validate_power(flags[p_idx + 1])
                        if power is None:
                            continue
                        kwargs["power"] = power

                if not kwargs:
                    console.print("[red]No valid edit parameters provided[/]")
                    continue
                    
                workout.edit_block(index, **kwargs)

                if "zone" in kwargs:
                    update_auto_powers()
                elif "power" in kwargs and workout.ftp is not None:
                    workout.blocks[index]["zone"] = workout._power_to_zone(workout.blocks[index]["power"])

                display_timeline()

            elif command == "delete" and len(args) == 1:
                if not workout.blocks:
                    console.print("[red]No blocks to delete[/]")
                    continue
                index = validate_index(args[0], len(workout.blocks))
                if index is None:
                    continue
                workout.delete_block(index)
                console.print(f"✅ Deleted block {index}")
                display_timeline()

            elif command == "preview":
                display_timeline()

            elif command == "export" and len(args) >= 1:
                if not workout.blocks:
                    console.print("[red]No blocks to export. Add some workout blocks first.[/]")
                    continue
                if workout.ftp is None:
                    console.print("[red]Set FTP first before exporting.[/]")
                    continue
                    
                filename = args[0]
                if not filename.endswith('.zwo'):
                    filename += '.zwo'
                    
                try:
                    os.makedirs("workouts", exist_ok=True)
                    default_name = os.path.splitext(filename)[0]
                    workout_name = Prompt.ask("🏷  Enter workout name for Zwift", default=default_name)
                    filepath = f"workouts/{filename}"
                    workout.export(filepath, name=workout_name)
                    console.print(f"\n💾 Exported to workouts/{filename} as '{workout_name}'")
                except Exception as e:
                    console.print(f"[red]Export failed: {e}[/]")

            else:
                console.print("[red]⚠️ Unknown command. Type 'help' for options.[/]")

        except Exception as e:
            console.print(f"[red]An error occurred: {e}[/]")
            console.print("[yellow]Type 'help' for available commands.[/]")

    console.print("\n[bold green]Goodbye![/]")


if __name__ == "__main__":
    repl()