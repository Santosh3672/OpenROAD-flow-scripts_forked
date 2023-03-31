export PLATFORM               = asap7

export DESIGN_NICKNAME        = ibex
export DESIGN_NAME            = ibex_core

export VERILOG_FILES         = $(sort $(wildcard ./designs/src/$(DESIGN_NICKNAME)/*.v))
export SDC_FILE              = ./designs/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc

export CORE_UTILIZATION       =  40
export CORE_ASPECT_RATIO      = 1
export CORE_MARGIN            = 2
export PLACE_DENSITY_LB_ADDON  = 0.20

export ENABLE_DPO = 0

export DFF_LIB_FILE           = $($(CORNER)_DFF_LIB_FILE)

#Additional settings for high performance (faster cells)
# LVT adders can also be used, but it will result in high power consumption
export ADDER_MAP_FILE         = $(PLATFORM_DIR)/yoSys/cells_adders_R.v
export LATCH_MAP_FILE         = $(PLATFORM_DIR)/yoSys/cells_latch_R.v
# Only one file can be read for DFF cell
export BC_DFF_LIB_FILE        = $(PLATFORM_DIR)/lib/asap7sc7p5t_SEQ_RVT_FF_nldm_220123.lib
export CTS_BUF_CELL           = BUFx4_ASAP7_75t_R


# LVT and SLVT cells are also read but their use can be restricted by adding *_SL or *_L as DONT_USE_CELLS in platform config file
export ADDITIONAL_LIBS		=$(PLATFORM_DIR)/lib/asap7sc7p5t_AO_SLVT_FF_nldm_211120.lib.gz \
				 $(PLATFORM_DIR)/lib/asap7sc7p5t_INVBUF_SLVT_FF_nldm_220122.lib.gz \
				 $(PLATFORM_DIR)/lib/asap7sc7p5t_OA_SLVT_FF_nldm_211120.lib.gz \
				 $(PLATFORM_DIR)/lib/asap7sc7p5t_SIMPLE_SLVT_FF_nldm_211120.lib.gz \
				 $(PLATFORM_DIR)/lib/asap7sc7p5t_SEQ_SLVT_FF_nldm_220123.lib \
				 $(PLATFORM_DIR)/lib/asap7sc7p5t_AO_LVT_FF_nldm_211120.lib.gz \
				 $(PLATFORM_DIR)/lib/asap7sc7p5t_INVBUF_LVT_FF_nldm_220122.lib.gz \
				 $(PLATFORM_DIR)/lib/asap7sc7p5t_OA_LVT_FF_nldm_211120.lib.gz \
				 $(PLATFORM_DIR)/lib/asap7sc7p5t_SIMPLE_LVT_FF_nldm_211120.lib.gz \
				 $(PLATFORM_DIR)/lib/asap7sc7p5t_SEQ_LVT_FF_nldm_220123.lib 

# L and SL LEF and GDS also being read
export ADDITIONAL_LEFS                  = $(PLATFORM_DIR)/lef/asap7sc7p5t_28_L_1x_220121a.lef $(PLATFORM_DIR)/lef/asap7sc7p5t_28_SL_1x_220121a.lef
export ADDITIONAL_GDS 			= $(PLATFORM_DIR)/gds/asap7sc7p5t_28_L_220121a.gds $(PLATFORM_DIR)/gds/asap7sc7p5t_28_SL_220121a.gds

# Updated fastroute tcl file
export FASTROUTE_TCL = ./designs/$(PLATFORM)/ibex/fastroute.tcl
# ENABLE_ECO_CELL, std cell with this keyword are enabled for ECO task only a new merged_eco.lib file will be generated during eco task
export ENABLE_ECO_CELL = *_SL *_L
export DONT_USE_CELLS 		= *x1p*_ASAP7* *xp*_ASAP7* SDF* ICG* DFFH* *_SL *_L
