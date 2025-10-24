#!/bin/bash
#
# Jarvis Function Inventory System - Production Rollout Script
# Phase 5: Automated rollout to all major directories
#
# Usage: ./rollout_inventory_system.sh [--dry-run]
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
DRY_RUN=false
JARVIS_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--dry-run]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Show what would be done without making changes"
            echo "  --help       Show this help message"
            exit 0
            ;;
    esac
done

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BOLD}${BLUE}================================================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}================================================================${NC}"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"
    
    local all_good=true
    
    # Check we're in Jarvis root
    if [ ! -f "$JARVIS_ROOT/Makefile" ]; then
        log_error "Not in Jarvis root directory (Makefile not found)"
        all_good=false
    else
        log_success "Jarvis root directory: $JARVIS_ROOT"
    fi
    
    # Check script exists
    if [ ! -f "$JARVIS_ROOT/tools/generate_inventory.py" ]; then
        log_error "generate_inventory.py not found in tools/"
        all_good=false
    else
        log_success "generate_inventory.py found"
    fi
    
    # Check Makefile has index target
    if ! grep -q "^index:" "$JARVIS_ROOT/Makefile"; then
        log_error "Makefile doesn't have 'index' target"
        all_good=false
    else
        log_success "Makefile has 'index' target"
    fi
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        local py_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python version: $py_version"
    else
        log_error "Python 3 not found"
        all_good=false
    fi
    
    if [ "$all_good" = false ]; then
        log_error "Prerequisites not met. Aborting."
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Define directories to index
# Customize this array based on your Jarvis structure
DIRECTORIES=(
    "modules"
    "agents"
    "services"
    "tools"
)

# Detect existing directories
detect_directories() {
    log_section "Detecting Directories to Index"
    
    local found_dirs=()
    
    for dir in "${DIRECTORIES[@]}"; do
        if [ -d "$JARVIS_ROOT/$dir" ]; then
            # Check if it contains Python files
            if find "$JARVIS_ROOT/$dir" -name "*.py" -type f | head -1 | grep -q .; then
                log_success "Found: $dir (contains Python files)"
                found_dirs+=("$dir")
            else
                log_warning "Found: $dir (but no Python files, skipping)"
            fi
        else
            log_warning "Not found: $dir (directory doesn't exist, skipping)"
        fi
    done
    
    if [ ${#found_dirs[@]} -eq 0 ]; then
        log_error "No directories with Python files found"
        exit 1
    fi
    
    # Update DIRECTORIES with only found dirs
    DIRECTORIES=("${found_dirs[@]}")
    
    echo ""
    log_info "Will index ${#DIRECTORIES[@]} directories:"
    for dir in "${DIRECTORIES[@]}"; do
        echo "  - $dir"
    done
}

# Generate index for a directory
generate_index() {
    local dir=$1
    
    log_info "Indexing: $dir"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would run: make index path=$dir"
        return 0
    fi
    
    # Generate index
    if make -C "$JARVIS_ROOT" index path="$dir" 2>&1 | tee /tmp/index_${dir//\//_}.log; then
        log_success "✅ Successfully indexed: $dir"
        
        # Verify output exists
        local folder_name=$(basename "$dir")
        local index_file="$JARVIS_ROOT/$dir/${folder_name}_index/${folder_name}_index.json"
        
        if [ -f "$index_file" ]; then
            local file_size=$(du -h "$index_file" | cut -f1)
            log_info "   Index file: $file_size"
            
            # Extract some stats
            local total_files=$(python3 -c "import json; f=open('$index_file'); d=json.load(f); print(d['metadata']['total_files'])")
            local total_functions=$(python3 -c "import json; f=open('$index_file'); d=json.load(f); print(d['metadata']['total_functions'])")
            log_info "   Files: $total_files, Functions: $total_functions"
        else
            log_warning "   Index file not found at expected location"
        fi
        
        return 0
    else
        log_error "❌ Failed to index: $dir"
        cat /tmp/index_${dir//\//_}.log
        return 1
    fi
}

# Generate all indices
generate_all_indices() {
    log_section "Generating Function Indices"
    
    local success_count=0
    local fail_count=0
    
    for dir in "${DIRECTORIES[@]}"; do
        if generate_index "$dir"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
        echo ""
    done
    
    log_info "Summary: $success_count succeeded, $fail_count failed"
    
    if [ $fail_count -gt 0 ]; then
        log_warning "Some indices failed to generate"
        return 1
    fi
    
    return 0
}

# Show git status
show_git_status() {
    log_section "Git Status"
    
    log_info "Checking for new/modified index files..."
    echo ""
    
    # Find all index directories
    local index_dirs=$(find "$JARVIS_ROOT" -type d -name "*_index" 2>/dev/null)
    
    if [ -z "$index_dirs" ]; then
        log_warning "No index directories found"
        return
    fi
    
    # Show git status for index files
    git -C "$JARVIS_ROOT" status --short -- "*_index/" 2>/dev/null || true
    
    echo ""
    log_info "To commit indices, run:"
    echo "  git add *_index/"
    echo "  git commit -m \"chore: add/update function inventories\""
}

# Commit indices to git
commit_indices() {
    log_section "Committing Indices to Git"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would commit all *_index/ directories"
        return 0
    fi
    
    # Check if there are changes
    if ! git -C "$JARVIS_ROOT" status --short -- "*_index/" | grep -q .; then
        log_info "No changes to commit"
        return 0
    fi
    
    # Show what will be committed
    log_info "Changes to be committed:"
    git -C "$JARVIS_ROOT" status --short -- "*_index/"
    echo ""
    
    # Ask for confirmation
    read -p "Commit these changes? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git -C "$JARVIS_ROOT" add "*_index/"
        git -C "$JARVIS_ROOT" commit -m "chore: add function inventories for major modules

- Generated indices for: ${DIRECTORIES[*]}
- Indices provide fast function lookup for AI assistants
- Part of Phase 5 production rollout"
        
        log_success "✅ Indices committed to git"
        return 0
    else
        log_info "Skipping commit (you can commit manually later)"
        return 0
    fi
}

# Update project documentation
update_documentation() {
    log_section "Documentation Recommendations"
    
    echo "Consider updating the following documentation:"
    echo ""
    echo "1. README.md - Add section about function indices:"
    echo "   ## Function Inventory System"
    echo "   "
    echo "   Generate structural indices for AI assistance:"
    echo "   \`\`\`bash"
    echo "   make index path=modules"
    echo "   \`\`\`"
    echo ""
    echo "2. copilot_standards_project.md (if exists) - Add workflow:"
    echo "   - Regenerate indices before major refactoring"
    echo "   - Command: make index path=<folder>"
    echo "   - Commit indices with code changes"
    echo ""
    echo "3. Project protocols - Reference inventory system"
    echo ""
}

# Print summary
print_summary() {
    log_section "Rollout Complete"
    
    log_success "✅ Function Inventory System is now in production!"
    echo ""
    echo "What was done:"
    echo "  ✅ Validated prerequisites"
    echo "  ✅ Generated indices for ${#DIRECTORIES[@]} directories"
    echo "  ✅ Verified output files"
    echo ""
    echo "Next steps:"
    echo "  1. Commit indices to git (if not already done)"
    echo "  2. Update project documentation"
    echo "  3. Integrate into daily workflow"
    echo "  4. Start using with Copilot"
    echo ""
    echo "Workflow integration:"
    echo "  - Before major work: make index path=<folder>"
    echo "  - After code changes: make index path=<folder>"
    echo "  - Commit indices: git add *_index/ && git commit"
    echo ""
    echo "For usage help: make index-help"
    echo "For documentation: docs/INDEX_USAGE.md"
    echo ""
}

# Main execution
main() {
    log_section "Jarvis Function Inventory System - Phase 5 Rollout"
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "Running in DRY-RUN mode (no changes will be made)"
        echo ""
    fi
    
    # Execute rollout steps
    check_prerequisites
    detect_directories
    
    if ! generate_all_indices; then
        log_error "Some indices failed to generate"
        log_info "You can manually fix issues and re-run this script"
        exit 1
    fi
    
    show_git_status
    
    if [ "$DRY_RUN" = false ]; then
        echo ""
        read -p "Would you like to commit indices now? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            commit_indices
        fi
    fi
    
    update_documentation
    print_summary
    
    exit 0
}

# Run main
main
