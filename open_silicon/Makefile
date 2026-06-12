# SPDX-FileCopyrightText: 2026 Project Moonshot
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

BLOCKS = user_project_wrapper

# OpenLane Configuration
OPENLANE_TAG ?= 2023.05.01
OPENLANE_IMAGE_NAME ?= efabless/openlane:$(OPENLANE_TAG)

# The physical build command
.PHONY: harden
harden:
	@echo "==================================================================="
	@echo " PROJECT MOONSHOT: Physical Tape-Out Process Initiated             "
	@echo "==================================================================="
	@echo " Starting OpenLane Flow for $(BLOCKS)..."
	@echo " This will synthesize the RTL, floorplan the die, place the cells,"
	@echo " route the interconnects, and generate the physical GDSII file."
	@echo "==================================================================="
	docker run -it -v $(PWD):/project -w /project $(OPENLANE_IMAGE_NAME) \
		flow.tcl -design openlane -tag moonshot_physical_build

.PHONY: clean
clean:
	rm -rf openlane/runs/moonshot_physical_build
