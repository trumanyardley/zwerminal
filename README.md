# Zwerminal CLI 🌀

A powerful command-line interface for creating custom Zwift workouts with an intuitive terminal experience. Build structured training sessions with zones, intervals, ramps, and export them directly to `.zwo` format for use in Zwift.

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-cross--platform-lightgrey.svg)

## ✨ Features

- **Interactive CLI**: Rich terminal interface with colored output and formatted tables
- **Zone-based Training**: Define workouts using training zones (Z1-Z6) with automatic power calculations
- **Multiple Block Types**: Support for steady-state, warmup/cooldown ramps, and complex intervals
- **FTP Integration**: Set your Functional Threshold Power for automatic zone-to-power conversion
- **Copy & Paste**: Duplicate workout segments with built-in clipboard functionality
- **Live Preview**: Real-time workout timeline with color-coded zones
- **Zwift Export**: Generate `.zwo` files compatible with Zwift's workout format
- **Flexible Editing**: Edit existing blocks with zone, duration, and power modifications

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Required packages: `rich`

### Installation

```bash
git clone https://github.com/trumanyardley/zwerminal.git
cd zwerminal
pip install rich
```

### Usage

```bash
python main.py
```

## 📋 Command Reference

### Basic Setup
```bash
ftp 250                    # Set your FTP to 250 watts
```

### Adding Workout Blocks

#### Steady-State Blocks
```bash
add Z2 10min              # 10 minutes in Zone 2
add Z4 5:30               # 5 minutes 30 seconds in Zone 4
add 200 15min             # 15 minutes at 200 watts (auto-detects zone)
```

#### Ramp Blocks (Warmup/Cooldown)
```bash
add warmup 100 200 10min   # Ramp from 100W to 200W over 10 minutes
add cooldown 250 150 5min  # Ramp from 250W to 150W over 5 minutes
```

#### Interval Blocks
```bash
add interval 300 4min 150 2min 5    # 5 x (4min @ 300W, 2min @ 150W)
```

### Editing and Management
```bash
preview                   # Display current workout timeline
copy 2 4                  # Copy blocks 2-4 to clipboard
paste                     # Paste clipboard blocks
edit 0 -zone Z3          # Change block 0 to Zone 3
edit 1 -time 8min        # Change block 1 duration to 8 minutes
edit 2 -power 275        # Change block 2 power to 275W
delete 3                 # Remove block 3
```

### Export
```bash
export my_workout.zwo     # Export to workouts/my_workout.zwo
```

## 🎯 Training Zones

Zwerminal uses standard cycling power zones based on your FTP:

| Zone | % of FTP | Description |
|------|----------|-------------|
| Z1   | <60%     | Active Recovery |
| Z2   | 60-75%   | Endurance |
| Z3   | 76-90%   | Tempo |
| Z4   | 91-105%  | Lactate Threshold |
| Z5   | 106-120% | VO2 Max |
| Z6   | >120%    | Anaerobic Capacity |

## 📊 Example Workout

Here's how to create a classic VO2 Max interval session:

```bash
> ftp 250
> add warmup 100 200 10min
> add Z2 5min
> add interval 275 3min 150 3min 5
> add Z2 5min
> add cooldown 200 100 10min
> preview
```

This creates:
- 10-minute warmup (100W → 200W)
- 5 minutes Z2 preparation
- 5 x 3min VO2 intervals (275W) with 3min recovery (150W)
- 5 minutes Z2 cool-down preparation
- 10-minute cooldown (200W → 100W)

## 🎨 Visual Timeline

The workout timeline uses color-coding for easy visualization:

- **Grey**: Z1 (Recovery)
- **Blue**: Z2 (Endurance)  
- **Green**: Z3 (Tempo)
- **Yellow**: Z4 (Threshold)
- **Orange**: Z5 (VO2 Max)
- **Red**: Z6 (Anaerobic)

## 📁 File Structure

```
zwerminal/
├── main.py              # Main CLI application
├── workout.py           # Workout class and ZWO export logic
├── workouts/            # Generated .zwo files (created automatically)
└── README.md           # This file
```

## 🔧 Advanced Usage

### Duration Formats
Multiple duration formats are supported:
- `10min` - 10 minutes
- `5:30` - 5 minutes 30 seconds  
- `300s` - 300 seconds
- `90` - 90 seconds (when no unit specified)

### Auto Zone Detection
When you specify power without a zone, Zwerminal automatically calculates the appropriate training zone based on your FTP.

### Clipboard Operations
Use `copy` and `paste` to duplicate workout segments:
```bash
copy 1 3      # Copy blocks 1, 2, and 3
paste         # Add copies to end of workout
paste         # Add another set (can paste multiple times)
```

## 🐛 Troubleshooting

**"Set FTP first" error**: You need to set your FTP before adding zone-based blocks:
```bash
ftp 250
```

**Invalid duration format**: Use supported formats like `10min`, `5:30`, or `300s`

**Unknown zone error**: Use zones Z1 through Z6 only

## 🤝 Contributing

Contributions are welcome! Here are some ways to contribute:

- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Inspired by the need for flexible Zwift workout creation
- Thanks to the cycling and developer communities

## 📧 Support

If you encounter any issues or have questions:

- Open an issue on GitHub
- Check the command reference above
- Use the built-in `help` command in the CLI

---

**Happy training!** 🚴‍♂️💨