PYTHON ?= python3
ifneq ($(wildcard .venv/bin/python),)
PYTHON := .venv/bin/python
endif

IVERILOG ?= iverilog
VVP      ?= vvp
RTL      := rtl/rate_divider.v rtl/sar_fsm.v rtl/sar_adc_digital.v
TB_DIR   := tb/rtl

.PHONY: all rtl-test spice-test pdk-test waves mitbih layout-digital layout-analog layout-top gds tt-gds tt-magic lvs clean

all: rtl-test

rtl-test: rtl-div rtl-adc rtl-timing rtl-sweep rtl-tt

rtl-div:
	$(IVERILOG) -g2012 -o /tmp/tb_rate_divider $(RTL) $(TB_DIR)/tb_rate_divider.v
	$(VVP) /tmp/tb_rate_divider

rtl-adc:
	$(IVERILOG) -g2012 -o /tmp/tb_sar_adc_digital $(RTL) $(TB_DIR)/tb_sar_adc_digital.v
	$(VVP) /tmp/tb_sar_adc_digital

rtl-timing:
	$(IVERILOG) -g2012 -o /tmp/tb_sar_timing $(RTL) $(TB_DIR)/tb_sar_timing.v
	$(VVP) /tmp/tb_sar_timing

rtl-sweep:
	$(IVERILOG) -g2012 -o /tmp/tb_sar_sweep $(RTL) $(TB_DIR)/tb_sar_sweep.v
	$(VVP) /tmp/tb_sar_sweep

rtl-tt:
	$(IVERILOG) -g2012 -o /tmp/tb_tt_um_sar_adc $(RTL) rtl/sar_adc_analog.v rtl/tt_um_davidbroughsmyth_sar_adc.v $(TB_DIR)/tb_tt_um_sar_adc.v
	$(VVP) /tmp/tb_tt_um_sar_adc

pdk-test:
	. layout/env.sh >/dev/null; $(PYTHON) tb/spice/run_pdk_tests.py

spice-test:
	$(PYTHON) tb/spice/run_spice_tests.py

waves:
	$(PYTHON) sim/run_sar_tests.py --waves --mitbih

mitbih:
	$(PYTHON) sim/run_sar_tests.py --mitbih --network

layout-digital:
	bash layout/openlane/run_openlane.sh

layout-analog:
	bash layout/magic/run_magic.sh layout/magic/sar_adc_analog_gencell.tcl

tt-magic:
	bash layout/magic/run_magic.sh layout/magic/tt_tile.tcl

layout-top:
	$(PYTHON) layout/build_gds.py

gds: layout-top tt-gds
	@ls -l layout/gds/*.gds gds/*.gds lef/*.lef

tt-gds:
	$(PYTHON) layout/build_tt_gds.py

lvs:
	bash layout/netgen/run_lvs.sh

clean:
	rm -f /tmp/tb_rate_divider /tmp/tb_sar_adc_digital /tmp/tb_sar_timing /tmp/tb_sar_sweep
	rm -rf results/*.png results/*.csv results/*.txt
