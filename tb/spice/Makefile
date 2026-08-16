NGSPICE ?= ngspice
ROOT    := ../..

.PHONY: all dac sh cmp sar

all: dac sh cmp sar

dac:
	$(NGSPICE) -b -o /tmp/tb_r2r_dac.log tb_r2r_dac.spice
	@grep -E "v\\(vout\\)|Error|error" /tmp/tb_r2r_dac.log | tail -5

sh:
	$(NGSPICE) -b -o /tmp/tb_sample_hold.log tb_sample_hold.spice
	@grep -E "droop|v_track|v_hold|Error|error" /tmp/tb_sample_hold.log | tail -10

cmp:
	$(NGSPICE) -b -o /tmp/tb_comparator.log tb_comparator.spice
	@grep -E "comp_p|Error|error" /tmp/tb_comparator.log | tail -8

sar:
	$(NGSPICE) -b -o /tmp/tb_sar_loop.log tb_sar_loop.spice
	@grep -E "SAR_CODE|code|Error|error" /tmp/tb_sar_loop.log | tail -15
