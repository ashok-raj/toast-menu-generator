#!/usr/bin/env bash
# Bash completion for sales.py

_sales_py_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Available options for sales.py
    opts="--help -h --debug -d --all --compare --file --today --yesterday --date --range --this-month --last-month --this-year --last-year --this-week --last-week"
    
    case "${prev}" in
        --file)
            # Complete with .json files and provide suggestions
            COMPREPLY=( $(compgen -f -X '!*.json' -- ${cur}) )
            if [[ ${#COMPREPLY[@]} -eq 0 ]]; then
                # Suggest some common filename patterns
                COMPREPLY=( $(compgen -W "sales_report.json sales_summary.json" -- ${cur}) )
            fi
            return 0
            ;;
        --date)
            # Suggest date format with current date and common dates
            COMPREPLY=( $(compgen -W "$(date +%Y-%m-%d) $(date -d 'yesterday' +%Y-%m-%d) $(date -d '1 week ago' +%Y-%m-%d) $(date -d '1 month ago' +%Y-%m-%d)" -- ${cur}) )
            return 0
            ;;
        --range)
            # First argument of range - suggest date format
            if [[ ${COMP_CWORD} -eq $((${#COMP_WORDS[@]} - 1)) ]]; then
                COMPREPLY=( $(compgen -W "$(date +%Y-%m-%d) $(date -d '1 week ago' +%Y-%m-%d) $(date -d '1 month ago' +%Y-%m-%d)" -- ${cur}) )
            fi
            return 0
            ;;
        *)
            # Check if we're completing the second date for --range
            local range_idx=-1
            for ((i=0; i<${#COMP_WORDS[@]}; i++)); do
                if [[ "${COMP_WORDS[i]}" == "--range" ]]; then
                    range_idx=$i
                    break
                fi
            done
            
            if [[ $range_idx -ge 0 && $COMP_CWORD -eq $((range_idx + 2)) ]]; then
                # Second argument of range - suggest end dates
                COMPREPLY=( $(compgen -W "$(date +%Y-%m-%d) $(date -d '1 week' +%Y-%m-%d) $(date -d '1 month' +%Y-%m-%d)" -- ${cur}) )
                return 0
            fi
            ;;
    esac
    
    # Handle options starting with dash
    if [[ ${cur} == -* ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
    
    # Default to showing available options
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
}

# Register the completion function for sales.py
complete -F _sales_py_completion sales.py
complete -F _sales_py_completion python3\ sales.py
complete -F _sales_py_completion python\ sales.py
complete -F _sales_py_completion ./sales.py