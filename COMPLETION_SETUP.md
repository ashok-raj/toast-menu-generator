# Sales.py Command Completion Setup

This directory contains a bash completion script for the `sales.py` command to enable tab completion of command-line options.

## Installation

### Option 1: Temporary (Current Session Only)
```bash
# Load the completion script in your current terminal session
source sales_completion.bash
```

### Option 2: Permanent Installation

#### For User-Specific Installation:
```bash
# Copy the completion script to your bash completion directory
mkdir -p ~/.local/share/bash-completion/completions
cp sales_completion.bash ~/.local/share/bash-completion/completions/sales.py

# Or add to your ~/.bashrc file:
echo "source $(pwd)/sales_completion.bash" >> ~/.bashrc
source ~/.bashrc
```

#### For System-Wide Installation (requires sudo):
```bash
# Copy to system bash completion directory
sudo cp sales_completion.bash /usr/share/bash-completion/completions/sales.py
```

## Usage

After installation, you can use tab completion with `sales.py`:

```bash
# Complete command options
python3 sales.py --<TAB>
./sales.py --<TAB>

# Complete file names for --file option
python3 sales.py --file my_report<TAB>

# Complete date formats for --date option  
python3 sales.py --date 2025-<TAB>

# Complete date formats for --range option
python3 sales.py --range 2025-<TAB>

# Use comparison features
python3 sales.py --today --compare<TAB>
python3 sales.py --date 2025-08-15 --compare<TAB>
```

## Available Completions

The completion script provides intelligent suggestions for:

- **Command Options**: All available flags like `--today`, `--yesterday`, `--date`, `--range`, `--compare`, etc.
- **File Names**: When using `--file`, suggests existing `.json` files and common naming patterns
- **Date Formats**: When using `--date` or `--range`, suggests current date and common relative dates

## Supported Command Invocations

The completion works with various ways of calling the script:
- `sales.py`
- `./sales.py`
- `python sales.py`
- `python3 sales.py`

## Testing

To verify the completion is working:
```bash
# Type this and press TAB to see available options
python3 sales.py --
```

You should see a list of available command-line options.