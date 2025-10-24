# Jarvis Function Inventory System - Makefile
# Phase 2: Makefile Integration
#
# Usage:
#   make index path=<folder_path>    - Generate inventory for specified folder
#   make index-help                  - Show usage instructions
#
# Examples:
#   make index path=modules/interface
#   make index path=agents/diagnostic
#   make index path=services

.PHONY: index index-help

# Main index target - requires path parameter
index:
ifndef path
	@echo "❌ Error: path parameter is required"
	@echo ""
	@echo "Usage: make index path=<folder_path>"
	@echo ""
	@echo "Examples:"
	@echo "  make index path=modules/interface"
	@echo "  make index path=agents/diagnostic"
	@echo "  make index path=services"
	@echo ""
	@echo "Run 'make index-help' for more information"
	@exit 1
endif
	@echo "🔍 Generating inventory for: $(path)"
	@python3 tools/generate_inventory.py "$(path)" || (echo "❌ Inventory generation failed" && exit 1)
	@echo ""
	@echo "✅ Inventory generation complete"

# Display help information
index-help:
	@echo "Jarvis Function Inventory System"
	@echo "================================="
	@echo ""
	@echo "DESCRIPTION:"
	@echo "  Generate function inventories for Python code directories."
	@echo "  Creates co-located JSON index with function/class metadata."
	@echo ""
	@echo "USAGE:"
	@echo "  make index path=<folder_path>"
	@echo ""
	@echo "PARAMETERS:"
	@echo "  path    Required. Full or relative path to directory to index."
	@echo ""
	@echo "EXAMPLES:"
	@echo "  make index path=modules"
	@echo "    Indexes the entire modules directory"
	@echo ""
	@echo "  make index path=modules/interface"
	@echo "    Indexes the interface module specifically"
	@echo ""
	@echo "  make index path=agents/diagnostic"
	@echo "    Indexes the diagnostic agent folder"
	@echo ""
	@echo "OUTPUT:"
	@echo "  Creates: <folder>/<folder_name>_index/<folder_name>_index.json"
	@echo ""
	@echo "  Example: modules/interface/interface_index/interface_index.json"
	@echo ""
	@echo "WORKFLOW:"
	@echo "  1. Run: make index path=<folder>"
	@echo "  2. Review generated JSON in <folder>_index/"
	@echo "  3. Commit the index to git"
	@echo "  4. Copilot uses index for fast function lookups"
	@echo ""
	@echo "NOTES:"
	@echo "  - Indices should be committed to repository"
	@echo "  - Regenerate after significant code changes"
	@echo "  - Script handles existing indices (removes and replaces)"
	@echo "  - All dependencies are Python standard library"
	@echo ""
	@echo "For verbose output, run the script directly:"
	@echo "  python3 tools/generate_inventory.py <path> -v"
