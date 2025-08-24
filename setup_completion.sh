#!/usr/bin/env bash

# Sales.py Command Completion Auto-Setup Script
# Automatically detects shell and OS, then installs appropriate completions

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Detect operating system
detect_os() {
    case "$(uname -s)" in
        Darwin*)    echo "macos" ;;
        Linux*)     echo "linux" ;;
        CYGWIN*)    echo "cygwin" ;;
        MINGW*)     echo "mingw" ;;
        *)          echo "unknown" ;;
    esac
}

# Detect current shell
detect_shell() {
    if [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    elif [ -n "$BASH_VERSION" ]; then
        echo "bash"
    elif [ -n "$FISH_VERSION" ]; then
        echo "fish"
    else
        # Fallback to checking SHELL environment variable
        case "$SHELL" in
            */zsh)  echo "zsh" ;;
            */bash) echo "bash" ;;
            */fish) echo "fish" ;;
            *)      echo "unknown" ;;
        esac
    fi
}

# Check if Homebrew is installed (macOS)
check_homebrew() {
    if command -v brew &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Create zsh completion script
create_zsh_completion() {
    cat > sales_completion.zsh << 'EOF'
#compdef sales.py python3\ sales.py python\ sales.py ./sales.py

_sales_py() {
    local context state line
    typeset -A opt_args

    _arguments -C \
        '(-h --help)'{-h,--help}'[Show help message]' \
        '(-d --debug)'{-d,--debug}'[Enable debug mode]' \
        '--all[Show complete detailed report]' \
        '--compare[Compare with same day last week]' \
        '--file[Save results to JSON file]:filename:_files -g "*.json"' \
        '--today[Analyze today'\''s sales]' \
        '--yesterday[Analyze yesterday'\''s sales]' \
        '--date[Specific date]:date:_dates' \
        '--range[Date range]:start date:_dates:end date:_dates' \
        '--this-month[Current month]' \
        '--last-month[Previous month]' \
        '--this-year[Current year]' \
        '--last-year[Previous year]' \
        '--this-week[Current week]' \
        '--last-week[Previous week]'
}

_dates() {
    local dates
    dates=(
        "$(date +%Y-%m-%d):today"
        "$(date -d 'yesterday' +%Y-%m-%d 2>/dev/null || date -v -1d +%Y-%m-%d):yesterday"
        "$(date -d '1 week ago' +%Y-%m-%d 2>/dev/null || date -v -1w +%Y-%m-%d):1 week ago"
        "$(date -d '1 month ago' +%Y-%m-%d 2>/dev/null || date -v -1m +%Y-%m-%d):1 month ago"
    )
    _describe 'dates' dates
}

_sales_py "$@"
EOF
}

# Create fish completion script
create_fish_completion() {
    cat > sales_completion.fish << 'EOF'
# Fish completion for sales.py

complete -c sales.py -s h -l help -d 'Show help message'
complete -c sales.py -s d -l debug -d 'Enable debug mode'
complete -c sales.py -l all -d 'Show complete detailed report'
complete -c sales.py -l compare -d 'Compare with same day last week'
complete -c sales.py -l file -d 'Save results to JSON file' -r -F
complete -c sales.py -l today -d 'Analyze today\'s sales'
complete -c sales.py -l yesterday -d 'Analyze yesterday\'s sales'
complete -c sales.py -l date -d 'Specific date' -x
complete -c sales.py -l range -d 'Date range' -x
complete -c sales.py -l this-month -d 'Current month'
complete -c sales.py -l last-month -d 'Previous month'
complete -c sales.py -l this-year -d 'Current year'
complete -c sales.py -l last-year -d 'Previous year'
complete -c sales.py -l this-week -d 'Current week'
complete -c sales.py -l last-week -d 'Previous week'

# Also complete for python invocations
complete -c python -n '__fish_seen_subcommand_from sales.py' -s h -l help -d 'Show help message'
complete -c python3 -n '__fish_seen_subcommand_from sales.py' -s h -l help -d 'Show help message'
EOF
}

# Setup completion for macOS
setup_macos() {
    local shell=$1
    
    print_info "Setting up completions for macOS with $shell shell..."
    
    case $shell in
        "zsh")
            # Create zsh completion script if it doesn't exist
            if [ ! -f "sales_completion.zsh" ]; then
                print_info "Creating zsh completion script..."
                create_zsh_completion
                print_success "Created sales_completion.zsh"
            fi
            
            # Install to user's zsh completions directory
            local zsh_completion_dir="$HOME/.local/share/zsh/site-functions"
            mkdir -p "$zsh_completion_dir"
            cp sales_completion.zsh "$zsh_completion_dir/_sales.py"
            print_success "Installed zsh completion to $zsh_completion_dir/_sales.py"
            
            # Update .zshrc if needed
            local zshrc="$HOME/.zshrc"
            if ! grep -q "fpath=(.*\.local/share/zsh/site-functions" "$zshrc" 2>/dev/null; then
                echo 'fpath=(~/.local/share/zsh/site-functions $fpath)' >> "$zshrc"
                print_success "Added completion path to ~/.zshrc"
            fi
            
            if ! grep -q "autoload -Uz compinit" "$zshrc" 2>/dev/null; then
                echo 'autoload -Uz compinit && compinit' >> "$zshrc"
                print_success "Added compinit to ~/.zshrc"
            fi
            
            print_warning "Please run 'source ~/.zshrc' or restart your terminal to enable completions"
            ;;
            
        "bash")
            if check_homebrew; then
                # Homebrew bash-completion
                print_info "Using Homebrew bash-completion..."
                
                # Check if bash-completion is installed
                if ! brew list bash-completion &>/dev/null; then
                    print_warning "bash-completion not found. Installing via Homebrew..."
                    brew install bash-completion
                fi
                
                local completion_dir="$(brew --prefix)/etc/bash_completion.d"
                mkdir -p "$completion_dir"
                cp sales_completion.bash "$completion_dir/sales.py"
                print_success "Installed bash completion to $completion_dir/sales.py"
                
                # Update .bash_profile
                local bash_profile="$HOME/.bash_profile"
                local completion_source='[ -f $(brew --prefix)/etc/bash_completion ] && . $(brew --prefix)/etc/bash_completion'
                if ! grep -q "bash_completion" "$bash_profile" 2>/dev/null; then
                    echo "$completion_source" >> "$bash_profile"
                    print_success "Added bash-completion to ~/.bash_profile"
                fi
                
                print_warning "Please run 'source ~/.bash_profile' or restart your terminal to enable completions"
            else
                # Fallback to user directory
                local completion_dir="$HOME/.local/share/bash-completion/completions"
                mkdir -p "$completion_dir"
                cp sales_completion.bash "$completion_dir/sales.py"
                print_success "Installed bash completion to $completion_dir/sales.py"
                
                # Update .bashrc
                local bashrc="$HOME/.bashrc"
                if ! grep -q "sales_completion.bash" "$bashrc" 2>/dev/null; then
                    echo "source $(pwd)/sales_completion.bash" >> "$bashrc"
                    print_success "Added completion source to ~/.bashrc"
                fi
                
                print_warning "Please run 'source ~/.bashrc' or restart your terminal to enable completions"
            fi
            ;;
            
        "fish")
            # Create fish completion script if it doesn't exist
            if [ ! -f "sales_completion.fish" ]; then
                print_info "Creating fish completion script..."
                create_fish_completion
                print_success "Created sales_completion.fish"
            fi
            
            local fish_completion_dir="$HOME/.config/fish/completions"
            mkdir -p "$fish_completion_dir"
            cp sales_completion.fish "$fish_completion_dir/sales.py.fish"
            print_success "Installed fish completion to $fish_completion_dir/sales.py.fish"
            
            print_warning "Fish completions are automatically loaded. No restart required."
            ;;
            
        *)
            print_error "Unsupported shell: $shell"
            print_info "Supported shells: zsh, bash, fish"
            return 1
            ;;
    esac
}

# Setup completion for Linux
setup_linux() {
    local shell=$1
    
    print_info "Setting up completions for Linux with $shell shell..."
    
    case $shell in
        "bash")
            local completion_dir="$HOME/.local/share/bash-completion/completions"
            mkdir -p "$completion_dir"
            cp sales_completion.bash "$completion_dir/sales.py"
            print_success "Installed bash completion to $completion_dir/sales.py"
            
            # Update .bashrc
            local bashrc="$HOME/.bashrc"
            if ! grep -q "sales_completion.bash" "$bashrc" 2>/dev/null; then
                echo "source $(pwd)/sales_completion.bash" >> "$bashrc"
                print_success "Added completion source to ~/.bashrc"
            fi
            
            print_warning "Please run 'source ~/.bashrc' or restart your terminal to enable completions"
            ;;
            
        "zsh")
            # Similar to macOS but using standard Linux paths
            if [ ! -f "sales_completion.zsh" ]; then
                print_info "Creating zsh completion script..."
                create_zsh_completion
                print_success "Created sales_completion.zsh"
            fi
            
            local zsh_completion_dir="$HOME/.local/share/zsh/site-functions"
            mkdir -p "$zsh_completion_dir"
            cp sales_completion.zsh "$zsh_completion_dir/_sales.py"
            print_success "Installed zsh completion to $zsh_completion_dir/_sales.py"
            
            local zshrc="$HOME/.zshrc"
            if ! grep -q "fpath=(.*\.local/share/zsh/site-functions" "$zshrc" 2>/dev/null; then
                echo 'fpath=(~/.local/share/zsh/site-functions $fpath)' >> "$zshrc"
                print_success "Added completion path to ~/.zshrc"
            fi
            
            print_warning "Please run 'source ~/.zshrc' or restart your terminal to enable completions"
            ;;
            
        "fish")
            if [ ! -f "sales_completion.fish" ]; then
                print_info "Creating fish completion script..."
                create_fish_completion
                print_success "Created sales_completion.fish"
            fi
            
            local fish_completion_dir="$HOME/.config/fish/completions"
            mkdir -p "$fish_completion_dir"
            cp sales_completion.fish "$fish_completion_dir/sales.py.fish"
            print_success "Installed fish completion to $fish_completion_dir/sales.py.fish"
            
            print_warning "Fish completions are automatically loaded. No restart required."
            ;;
            
        *)
            print_error "Unsupported shell: $shell"
            return 1
            ;;
    esac
}

# Main function
main() {
    echo "======================================"
    echo "  Sales.py Completion Auto-Setup"
    echo "======================================"
    echo
    
    # Check if sales.py exists
    if [ ! -f "sales.py" ]; then
        print_error "sales.py not found in current directory"
        exit 1
    fi
    
    # Check if bash completion script exists
    if [ ! -f "sales_completion.bash" ]; then
        print_error "sales_completion.bash not found in current directory"
        print_info "Please ensure you're running this script from the same directory as sales.py"
        exit 1
    fi
    
    # Detect OS and shell
    local os=$(detect_os)
    local shell=$(detect_shell)
    
    print_info "Detected OS: $os"
    print_info "Detected shell: $shell"
    echo
    
    # Run appropriate setup
    case $os in
        "macos")
            setup_macos "$shell"
            ;;
        "linux")
            setup_linux "$shell"
            ;;
        *)
            print_error "Unsupported operating system: $os"
            print_info "This script supports macOS and Linux"
            print_info "For manual setup instructions, see COMPLETION_SETUP.md"
            exit 1
            ;;
    esac
    
    echo
    print_success "Completion setup completed!"
    echo
    print_info "Test the completion by typing:"
    echo "  python3 sales.py --<TAB>"
    echo
}

# Run main function
main "$@"