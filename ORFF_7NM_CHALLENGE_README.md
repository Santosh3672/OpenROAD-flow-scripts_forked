# Openroad Flow PPA improvement
This repo documents the work done during Openroad 7nm design [contest](https://jenkins.openroad.tools/buildStatus/icon?job=OpenROAD-flow-scripts-Public%2Fpublic_tests_all%2Fmaster). 
## Table of content
- [Introduction](#introduction)
- [Solutions tried](#solutions-tried)
  - [Use of Multi-threshold voltage cells in the design](#use-of-multi-threshold-voltage-cells-in-the-design)
  - [Using higher layer for power ground routing during floorplan stage](#Using-higher-layer-for-PDN-stripes-to-have-better-signal-routing)
- [Conclusion](#conclusion)
- [Reference](#reference)
## Introduction
This repo is related to Openroad 7nn  [contest](https://www.openroaddesigncontest.org/). Here I am targetting problem statement A of achieving best performance with zero DRC and timig violation.
Following are the details:
### Design selected: Ibex
### Process node: Asap7 7nm

In this repo I will be discussing the modification in flow performed to increase frequency of the design while at the same time ensuring that these methods had no major impact on Power and area. Thus achieving improvement in PPA. Some methods like PDN strategy change have helped us to improve runtime, that is also discussed here. <br />

## Solutions tried
Following are the modification in the flow that I have performed:
### Use of Multi-Vt based ECO in the existing flow for higher performance
 In Asap7 library there are three types of standard cells in terms of threshold voltage they are   <br />
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;i. R: Cells with regular Vt  <br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ii. L: low Vt cells <br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;iii. SL: Super low Vt cells <br />
 For any particular cell the LEF of its R,L and SL cells have same domension and pin shape/orientation.
 In terms of delay R > L > SL, hence SL cells are faster than L cells which are faster than R cell. With this the delay of the datapath will be reduced allowing us to meet STA with low time period or high frequency. 

But it comes at the cost of power. SL cells consume more than 10times the power consumed by R cells.L cells are however somewhat in between R and SL they are faster than R cells but their power consumption is not that high like a SL cell. Hence a planned usage of these L and SL cell is important else the high performance will be obtained at the cost of extremely high power consumption. <br />
In this solution I have used R and L cells having low power consumption during Synthesis stage and then on the final DB replace L or R cells with SL or L cells on failing paths to have positive WNS. This way the design will be timing clean with less number of SL cells. <br />
The timing report present in the floorplan stage is very pessimistic as they have very large negative slack, the WNS and TNS of various stage of Ibex implementation at 1400ps clock period is tabulated below. <br />

| **Stage** | **WNS(ps)** | **TNS(ps)** |
| --------- | ----------- | ----------- |
| Floorplan | 2648.74     | 4390727.5   |
| Place     | 15.69       | 325.24      |
| cts       | 116.79      | 3888.48     |
| Route     | 116.79      | 3888.48     |
| Final     | 106.54      | 1160.48     |
  
From the above table following observation can be made: <br />
i. In floorplan we are not reading DEF file hence the timing is determined from knowledge of RTL which is highly pessimistic. <br />
ii. After placement without clock tree defined the WNS is least due to absence of skew.<br />
iii. After CTS the timing is now more realistic.<br />

If we try to synthesize a high frequency design by allowing faster(standard cell) standard cell, it will consider the pessimistic timing report as we have seen in floorplan and try to over-optimize the design. This will cause the design to have very high leakage power. <br />
To avoid these issues I have developed an ECO engine that checks the timing report from logs and based on that it will swap slow cells on timing critical paths with fast L or SL cells to make them timing clean. The usage of the engine on OpenROAD flow is shown in figure below.<br />

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/ECO%20flow.drawio.png" />
<p align='center'>Multi Vt ECO flow</p>
</p>
The ECO engine is pyhon based, first it parses the log file of 7_1_eco.log and search for violating paths. From those paths it extracts the datapath delay, analyses and finds list of gates that can be swapped to met constraints.  <br />
The script also incorporates those changes in the .v & .def file by updating them and dumps updated ones with a new name. Currently there are no command that swaps  cell in the openROAD tool, if that feature is available the ECO engine can dump a file containing list of changes that can be read by openROAD and write_def/ write_verilog command can be used to generate def and verilog files respectively. <br />

Details of all the modification and steps performed for the ECO is mendioned below:<br />
i. First all the Vt variant cells (R, L and SL) are read in merged.lib file and any cell not required(say L or SL) can be blocked by setting "dont_use: true" through DONT_USE variable in config file.<br />
ii. For higher frequency design R and L cells are enabled, but SL cells are blocked for synthesis.<br />
iii. L variant of Adder, Buffer and CTS buffers are used, since they have large delay. <br />
<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/Design_config.JPG" />
<p align='center'>Design config snippet</p>
</p>
Note: The cells that we enable for synthesis and additional cells that we unblock for ECO will have a big impact on PPA of our design. In our case if we had disabled most of the L cells for ECO and enable them during the ECO then the power consumption of the chip would be low but delay would be higher. It would require more effort on ECO stage <br /> 
iv. The whole flow is run till the Final stage. <br />
v. Then a a new merged_eco.lib will be generated that removes the "dont_use: true" on the cells we want to enable for ECO(set through ENABLE_ECO variable). <br />
vi. It si followed by the ECO task which has three parts. <br />
    a. 7_1_eco task: First the verilog file from 6_final task and regular merged.lib file are read using load.tcl file, then DEF and SPEF file are read to generate physical and parasitic information. Now failing paths are reported using report_checks command, which are dumped on log file.<br />
    b. ECO_engine: Then the ECO engine parses through the log file of 7_1_eco.log file and extracts the timing reports. Based on this reports it will analyze and look for cells that can be swapped to improve timing. Then it reads the existing .v and def from 6_final task, swaps those cells and update them in a new file 7_eco.v/def.<br />
    c. 7_2_eco task: It reads the ECO generated verilog file and merged_eco.lib through load.tcl. Then new def file and 6_final.spef are read(since routing are not affected, swapped cells are exact replica as we are only swapping same cells with different Vt). With all the collaterals loaded timings and power informations are reported to check effectiveness of ECO and whether additional ECO iterations are required.<br />
 <p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/ECO%20iterative%20flow.drawio.png" />
<p align='center'>Iterative ECO flow</p>
</p>   

The proposed ECO engine requires multiple iterations to resolve all timing iterations. Since it takes the timing informations from log file as input its performance depends on how many failed paths are covered on that report and the parameters being set in the script. The iterative ECO flow is mentioned in below figure: <br />
<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/ECO_task_makefile.JPG" />
<p align='center'>Snippet of ECO makefile command</p>
</p>
NOTE: For automating the task the newly generated .v and .def files are renamed to 6_final.v and .def (using make save_eco) respectively since the ECO task takes input from 6_final. To avoid loosing original 6_final files user can do 'make copy_final'. <br />
Commands required to do a new iteration of ECO:<br />
#use this to save 6_final.v nad def file.<br />
```console
copy_final <br />
save_eco <br />
clean_eco <br />
eco <br />
```
Last 3 commands are clubbed in a single command "eco_iter".<br />

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/ECO_iter_makefile.JPG" />
<p align='center'>Snippet of makefile command for ECO iterations</p>
</p>

#### Result with ECO:
Design implemented: Ibex at Asap7node
Clock period: 1400ps (714.286 MHz)
Experiment 1:
Variants of Std cell enabled for Yosys: RVT and LVT
Variants of Adder and DFF used: LVT
Pre ECO:
  Power: 1.67e-2
  WNS: -115.39
  TNS: -1718.13
  Design area: 2479u^2
 After ECO:
 Number of ECO iterations: 6
      Power(10^-2W), WNS(ps), TNS(ps)
Iter1: 1.68, 49.84, 275.17
Iter2: 1.68,  18.72,  76.01
Iter3: 1.68,  15.00,  41.01
Iter4: 1.68,     5.24,   6.58
Iter5: 1.68, 2.18, 2.18
Iter6: 1.68, 0, 0
  
Experiment 2:
Variants of Std cell enabled for Yosys: RVT, LVT and SLVT
Variants of Adder and DFF used: LVT
Pre ECO:
  Power 1.82e-2
  WNS: 149.21
  TNS: 1752.8
  Design area: 2479u^2
  After ECO:
  Number of ECO iterations: Did not converge
      Power(10^-2W), WNS(ps), TNS(ps)
Iter1: 1.82, 76.09,  311.75
Iter2: 1.82,  40.78, 103.39
Iter3: 1.82,  30.47,  41.06
Iter4: 1.82,  29.82, 38.17
Iter5: 1.82,  29.84, 38.25
Experiment 3:
Variants of Std cell enabled for Yosys: RVT, LVT and SLVT
Variants of Adder and DFF used: RVT
Pre ECO:
  Power 1.78e-2
  WNS: 73.64
  TNS: 1566.26
  Design area: 2479u^2
 Number of ECO iterations: 2
      Power(10^-2W), WNS(ps), TNS(ps)
Iter1: 1.78, 15.00, 46.77
Iter2: 1.78,  0,      0


Experiment 4:
Variant of Std cells enabled for Yosys: RVT
Variant of adder and DFF used: RVT
Pre ECO:
  Power 1.78e-2
  WNS: 80.25
  TNS: 1365.28
  Design area: 2478u^2
  Number of ECO iterations: 3
      Power(10^-2W), WNS(ps), TNS(ps)
Iter1: 1.78, 10.12,  13.55
Iter2: 1.78,  0.96,  0.96
Iter3: 1.65,  8.32,  18.71
Iter4: 1.65,     0,      0
### Using higher layer for PDN stripes to have better signal routing
For ASAP7 there are 9 metal layers and signal routing is enabled on M2-M7. The PDN is generated for M1, M2 and M5-M6. M1 and M2 are rails which are used to power the VDD and VSS pins of std cells. While M5 and M6 are the stripes at higher layer used to improve rebustness of grid to have better IR/EM profile. <br />
Problem faced: For large design like Ibex the detail routing had longest runtime among all other tasks.
During detail routing the tool will do routing in the 0th and measure the DRCs then it will clean the DRCs in next iterations. 
Till all DRCs are cleaned the iterations will continue.
So the runtime of detail routing depends upon two factors: Size of the design and Initial DRC present in the design. 

Solution tried: In this solution I tried to reduce the initial DRCs in the design by moving the PDN stripes to higher layer M7-M8 from existing M5-M6 layer, since most of the signal routing is done on lower layers freeing M5 and M6 layer for signal layer reduces congestion by a great extent. 

Note: Since M2 is horizontal layer the stripe above it has to be vertical layer thats why I had to choose M7-M8, since M7 is vertical.

<p float="left">
<img src="https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/PDN/PDN_script_default.JPG" alt="MarineGEO circle logo" style="height: 300px; width:500px;"/>
  <img src="https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/PDN/PDN_script_Updated.JPG" alt="MarineGEO circle logo" style="height: 300px; width:500px;"/>
  <p align="center">Fig.1: a. Default PDN script b. Updated PDN script <p />
</p>
Also I observed that lower metal layers(M2-M4) had more signal routes than higher layer(M5-M7)(Fig1).<br />

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/PDN/0th_iter_old_PDN.JPG" />
<p align='center'>Fig2: DRC count and layer wise usage with default flow </p>
</p>
To avoid congestion there is a command set_global_routing_layer_adjustment which sets routing resources adjustment in signal routing.<br />

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **set_global_routing_layer_adjustment layer adjustment** <br />
For example if we set adjustment for M2 as 0.5 it will reduce the routing resources of M2 layer by 50% now the tool will try to do routing on other layer. Default script blocks 50% of all signal routing. I added a fastroute.tcl script which blocks more routing resources for lower layer and less for higher layer thereby spreading routing among all layers.

<p float="left">
<img src="https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/PDN/default_fastroute_script.JPG" alt="MarineGEO circle logo" style="height: 120px; width:500px;"/>
  <img src="https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/PDN/updated_fastroute_script.JPG" alt="MarineGEO circle logo" style="height: 120px; width:500px;"/>
  <p align="center">Fig.3: a. Default fastroute script when FASTROUTE_TCL variable is not defined b. Updated fastroute.tcl script <p />
</p>

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/PDN/0th_iter_new_PDN_with_fastroute_1.JPG" />
<p align='center'>Fig4: DRC count and layer wise usage with updated PDN and fastroute script</p>
</p>

Comparing it with the default flow there are less DRC after 0th iteration (16348 to 15387) and runtime of 0th iteration reduced from 4min 47 sec to 3min 27sec. 

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/PDN/total_runtime_old_PDN_1.JPG" />
  </p>
<p align='center'>Fig5. a: Total runtime with default script</p>

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/PDN/total_runtime_new_PDN_with_fastroute_2.JPG" />
<p align='center'>Fig5. b: Total runtime with updated PDN and fastroute script</p>
</p>

In overall the runtime reduced from 20min 25sec(1225sec) to 16min 48sec(1008sec) a reduction of ~ 18% runtime is achieved by reducing initial DRC of detail route stage.
## Conclusion


## Reference

