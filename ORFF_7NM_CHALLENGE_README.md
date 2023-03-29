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

In this repo I will be discussing the modification in flow performed to increase frequency of the design while at the same time ensuring that these methods had no major impact on Power and area. Thus achieving improvement in PPA. Some methods like PDN strategy change have helped us to improve runtime, that is also discussed here. 

## Solutions tried
Following are the modification in the flow that I have performed:
### Use of Multi-Vt based ECO in the existing flow
 In Asap7 library there are three types of standard cells in terms of threshold voltage they are  
 i. R: Cells with regular Vt  <br />
 ii. L: low Vt cells <br />
 iii. SL: Super low Vt cells <br />
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

Details of all the modification and steps performed for the ECO is mendioned below:<br />
i. First all the R, L and SL cells are read in merged.lib file and any cell we want to block will be blocked by setting "dont_use: true" through DONT_USE variable in config file.<br />
ii. For higher frequency design R and L cells are enabled, i.e. apart from default list of dont_use keyword an additional &ast;_SL is added blocking all SL cells.<br />
iii.asd

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

