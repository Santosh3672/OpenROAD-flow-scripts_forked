utl::set_metrics_stage "ECO_view_{}"
source $::env(SCRIPTS_DIR)/load.tcl
load_design 7_eco.v 6_final.sdc "Starting ECO"
read_def -floorplan_initialize $::env(RESULTS_DIR)/7_eco.def

source $::env(PDN_TCL)
pdngen

if { [info exists ::env(POST_PDN_TCL)] && [file exists $::env(POST_PDN_TCL)] } {
  source $::env(POST_PDN_TCL)
}

# Check all supply nets
set block [ord::get_db_block]
foreach net [$block getNets] {
    set type [$net getSigType]
    if {$type == "POWER" || $type == "GROUND"} {
# Temporarily disable due to CI issues
#        puts "Check supply: [$net getName]"
#        check_power_grid -net [$net getName]
    }
}

read_spef $::env(RESULTS_DIR)/6_final.spef

report_units
report_units_metric
source $::env(SCRIPTS_DIR)/report_metrics.tcl
report_metrics "ECO final" false false


write_db $::env(RESULTS_DIR)/7_2_eco.odb
write_sdc $::env(RESULTS_DIR)/7_eco.sdc

report_power
report_tns
report_wns
