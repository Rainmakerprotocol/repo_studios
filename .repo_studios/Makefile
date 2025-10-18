PYTHON ?= python3

.PHONY: studio-render-views
studio-render-views:
	$(PYTHON) scripts/render_inventory_views.py

.PHONY: studio-validate-inventory
studio-validate-inventory:
	$(PYTHON) scripts/validate_inventory.py

studio-check-inventory-health: studio-render-views
	$(PYTHON) scripts/check_inventory_health.py
