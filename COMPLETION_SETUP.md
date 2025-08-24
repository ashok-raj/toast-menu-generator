# Sales.py Command Completion Setup

This directory contains shell completion scripts for the `sales.py` command to enable tab completion of command-line options across different shells and operating systems.

## Automatic Setup (Recommended for macOS)

### Quick Auto-Setup
```bash
# Run the auto-setup script (detects your shell and OS automatically)
./setup_completion.sh
```

This script will:
- Automatically detect your shell (bash, zsh, fish)
- Install completions in the correct location for your macOS version
- Handle both Intel and Apple Silicon Macs
- Set up completions for the current user without requiring sudo

## Manual Installation

### Option 1: Temporary (Current Session Only)
```bash
# Load the completion script in your current terminal session
source sales_completion.bash
```

### Option 2: Permanent Installation

#### For macOS Users:

**Zsh (Default on macOS Catalina+):**
```bash
# Add to your ~/.zshrc
mkdir -p ~/.local/share/zsh/site-functions
cp sales_completion.zsh ~/.local/share/zsh/site-functions/_sales.py
echo 'fpath=(~/.local/share/zsh/site-functions $fpath)' >> ~/.zshrc
echo 'autoload -Uz compinit && compinit' >> ~/.zshrc
source ~/.zshrc
```

**Bash with Homebrew:**
```bash
# Install bash-completion if not already installed
brew install bash-completion

# Add completion script
mkdir -p $(brew --prefix)/etc/bash_completion.d
cp sales_completion.bash $(brew --prefix)/etc/bash_completion.d/sales.py

# Ensure bash-completion is loaded in ~/.bash_profile
echo '[ -f $(brew --prefix)/etc/bash_completion ] && . $(brew --prefix)/etc/bash_completion' >> ~/.bash_profile
source ~/.bash_profile
```

**Fish Shell:**
```bash
# Copy to fish completions directory
mkdir -p ~/.config/fish/completions
cp sales_completion.fish ~/.config/fish/completions/sales.py.fish
```

#### For Linux Users:
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

### Test Commands
```bash
# Test option completion
python3 sales.py --<TAB>

# Test date completion
python3 sales.py --date <TAB>

# Test file completion
python3 sales.py --file <TAB>

# Test range completion
python3 sales.py --range <TAB>

# Test with comparison
python3 sales.py --today --compare<TAB>
```

## Troubleshooting

### macOS Issues

**Zsh completions not working:**
```bash
# Check if your fpath includes the completion directory
echo $fpath | grep -q "\.local/share/zsh/site-functions" && echo "✓ Path found" || echo "✗ Path missing"

# Manually reload completions
autoload -Uz compinit && compinit

# Check if completion function is loaded
which _sales.py
```

**Bash completions not working:**
```bash
# Check if bash-completion is loaded
type _init_completion &>/dev/null && echo "✓ bash-completion loaded" || echo "✗ bash-completion not loaded"

# For Homebrew users, ensure bash-completion is in PATH
brew --prefix bash-completion

# Manually source the completion
source sales_completion.bash
```

**Fish completions not working:**
```bash
# Check fish completions directory
ls -la ~/.config/fish/completions/ | grep sales

# Reload fish completions
fish -c "fish_update_completions"
```

### General Issues

**Permission errors:**
- Ensure the setup script is executable: `chmod +x setup_completion.sh`
- Don't run the setup script with sudo unless specifically installing system-wide

**Multiple shells:**
- If you use multiple shells, run the setup script from each shell environment
- The script will detect the current shell and install appropriate completions

**Virtual environments:**
- Completions work regardless of virtual environment
- The script name `sales.py` is what triggers completion, not the Python path

## Files Created

After running the setup, you'll have these completion files:

- `sales_completion.bash` - Bash completion script (original)
- `sales_completion.zsh` - Zsh completion script (auto-generated)  
- `sales_completion.fish` - Fish completion script (auto-generated)
- `setup_completion.sh` - Auto-setup script for macOS and Linux

## Support

For issues with completion setup:
1. Try the manual installation method for your specific shell
2. Check that the completion scripts exist in the current directory
3. Verify your shell configuration files (.bashrc, .zshrc, etc.) are properly sourced
4. Restart your terminal or source your shell configuration manually