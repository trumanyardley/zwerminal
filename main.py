from workout import Workout
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
import re

console = Console()
workout = Workout()


def display_timeline():
    table = Table(title="\U0001F3C1 Zwifty Workout Timeline")
    table.add_column("Idx")
    table.add_column("Type")
    table.add_column("Zone/Info")
    table.add_column("Duration")
    table.add_column("Power")

    # Map zones to colors
    color_map = {
        "Z1": "grey",
        "Z2": "blue",
        "Z3": "green",
        "Z4": "yellow",
        "Z5": "orange1",
        "Z6": "red"
    }

    for i, b in enumerate(workout.blocks):
        btype = b.get("type", "steady")
        # --- steady blocks ---
        if btype == "steady":
            power = b["power"]
            zone  = b["zone"]
            if zone == "AUTO" and workout.ftp is not None:
                zone = power_to_zone(power)
            dur_s = parse_duration_to_seconds(b["duration"])
            dur   = f"{dur_s//60}:{str(dur_s%60).zfill(2)}"
            color = color_map.get(zone.upper(), "white")
            info = f"[{color}]{zone}[/{color}]"

        # --- ramp blocks (warmup/cooldown) ---
        elif btype in ("warmup", "cooldown"):
            p0 = b["power_start"]
            p1 = b["power_end"]
            dur_s = b["duration"]
            dur   = f"{dur_s//60}:{str(dur_s%60).zfill(2)}"
            info  = f"{p0}→{p1}"

        # --- interval blocks ---
        elif btype == "interval":
            p1, d1 = b["power1"], b["dur1"]
            p2, d2 = b["power2"], b["dur2"]
            reps    = b["reps"]
            total_s = (d1 + d2) * reps
            dur     = f"{total_s//60}:{str(total_s%60).zfill(2)}"
            info    = f"{p1}/{p2}×{reps}"

        else:
            # Fallback (shouldn't happen)
            info = ""
            dur  = ""
            power= ""
        
        table.add_row(str(i), btype, info, dur, str(power) if btype=="steady" else info)

    console.print(table)


def parse_duration_to_seconds(duration_str):
    duration_str = duration_str.strip().lower()
    if ":" in duration_str:
        parts = duration_str.split(":")
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
    if "min" in duration_str:
        return int(re.sub("[^0-9]", "", duration_str)) * 60
    if "s" in duration_str:
        return int(re.sub("[^0-9]", "", duration_str))
    return int(duration_str)


def power_to_zone(power):
    if workout.ftp is None:
        return "Z?"
    pct = (power / workout.ftp) * 100
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


def zone_to_power(zone):
    if workout.ftp is None:
        return None
    zperc = {
        "Z1": 0.55,
        "Z2": 0.65,
        "Z3": 0.80,
        "Z4": 0.95,
        "Z5": 1.10,
        "Z6": 1.25
    }.get(zone.upper(), None)
    return int(workout.ftp * zperc) if zperc is not None else None


def update_auto_powers():
    for b in workout.blocks:
        if b['zone'] in ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6"] and workout.ftp is not None:
            b['power'] = zone_to_power(b['zone'])
        elif b['zone'] == "AUTO" and workout.ftp is not None:
            b['zone'] = power_to_zone(b['power'])


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
        command = parts[0]
        args = parts[1:]

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
      Save to workouts/<filename>.zwo (prompts for workout name that will be displayed in zwift app).

  help
      Show this help message.

  exit
      Quit the app.
""")

        elif command == "ftp" and len(args) == 1:
            workout.ftp = int(args[0])
            update_auto_powers()
            console.print(f"✅ FTP set to [bold]{workout.ftp}W[/]")
            display_timeline()

        elif command == "add" and args:
            sub = args[0].lower()

            # 1) Warmup / Cooldown
            if sub in ("warmup", "cooldown") and len(args) == 4:
                p0 = int(args[1])                     # start watts
                p1 = int(args[2])                     # end watts
                dur = parse_duration_to_seconds(args[3])
                workout.add_block(sub, power_start=p0, power_end=p1, duration=dur)
                display_timeline()

            # 2) Interval: add interval p1 t1 p2 t2 reps
            elif sub == "interval" and len(args) == 6:
                p1 = int(args[1])
                t1 = parse_duration_to_seconds(args[2])
                p2 = int(args[3])
                t2 = parse_duration_to_seconds(args[4])
                reps = int(args[5])
                workout.add_block("interval",
                                  power1=p1, dur1=t1,
                                  power2=p2, dur2=t2,
                                  reps=reps)
                display_timeline()

            # 3) `add Zx time` or `add time power` or `add Zx time power`
            elif len(args) == 2 and args[0].upper().startswith("Z"):
                zone, duration_raw = args
                duration = f"{parse_duration_to_seconds(duration_raw)}s"
                if workout.ftp is not None:
                    power = zone_to_power(zone)
                    if power is not None:
                        workout.add_block("steady", zone=zone.upper(), duration=duration, power=power)
                        display_timeline()
                    else:
                        console.print("[red]Unknown zone. Use Z1-Z6.")
                else:
                    console.print("[red]Set FTP first using 'ftp [value]'")
            elif len(args) == 2:
                power, duration_raw  = args
                duration = f"{parse_duration_to_seconds(duration_raw)}s"
                workout.add_block("steady", zone="AUTO", duration=duration, power=int(power))
                display_timeline()
            else:
                console.print("[red]Invalid 'add' usage. See 'help'.")

        elif command == "copy" and len(args) == 2:
            i0, i1 = map(int, args)
            workout.clipboard = workout.blocks[i0:i1+1].copy()
            console.print(f"✅ Copied blocks {i0}–{i1}")

        elif command == "paste":
            if workout.clipboard:
                # append a shallow copy to avoid reference issues
                workout.blocks.extend(workout.clipboard.copy())
                display_timeline()
            else:
                console.print("[red]Nothing to paste. Use copy first.[/]") 

        elif command == "edit" and len(args) >= 1:
            index = int(args[0])
            flags = args[1:]
            kwargs = {}
            if "-zone" in flags and "-power" in flags:
                console.print("[red]❌ Cannot specify both -zone and -power. Choose one.")
                continue
            if "-zone" in flags:
                z_idx = flags.index("-zone")
                if z_idx + 1 < len(flags):
                    kwargs["zone"] = flags[z_idx + 1]
            if "-time" in flags:
                t_idx = flags.index("-time")
                if t_idx + 1 < len(flags):
                    kwargs["duration"] = f"{parse_duration_to_seconds(flags[t_idx + 1])}s"
            if "-power" in flags:
                p_idx = flags.index("-power")
                if p_idx + 1 < len(flags):
                    kwargs["power"] = int(flags[p_idx + 1])
            workout.edit_block(index, **kwargs)

            if "zone" in kwargs:
                update_auto_powers()
            elif "power" in kwargs and workout.ftp is not None:
                workout.blocks[index]["zone"] = power_to_zone(workout.blocks[index]["power"])
            pass

            display_timeline()

        elif command == "delete" and len(args) == 1:
            workout.delete_block(int(args[0]))
            display_timeline()
            pass
        elif command == "preview":
            display_timeline()

        elif command == "export" and len(args) >= 1:
            import os
            os.makedirs("workouts", exist_ok=True)
            filename = args[0]
            default_name = os.path.splitext(filename)[0]
            workout_name = Prompt.ask("🏷  Enter workout name for Zwift", default=default_name)
            filepath = f"workouts/{filename}"
            workout.export(filepath, name=workout_name)
            console.print(f"\n💾 Exported to workouts/{filename} as '{workout_name}'")
            pass

        else:
            console.print("[red]⚠️ Unknown command. Type 'help' for options.[/]")

    console.print("\n[bold green]Goodbye![/]")


if __name__ == "__main__":
    repl()
