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
### Use of Multi-threshold voltage cells in the design
 In Asap7 library there are three types of standard cells in terms of threshold voltage they are  
 i. R: Cells with regular Vt  <br />
 ii. L: low Vt cells <br />
 iii. SL: Super low Vt cells <br />
 In terms of delay R > L > SL, hence SL cells are faster than L cells which are faster than R cell. With this the delay of the datapath will be reduced allowing us to meet STA with low time period or high frequency. 

But it comes at the cost of power. SL cells consume more than 10times the power consumed by R cells. To avoid having a high power consumption chip for high frequency operation, I am planning to use R and L cells having low  power consumption during Synthesis stage and then after synthesis at the later part replace L or R cells with SL cells on failing paths to have positive WNS. THis way the dewsign will be timing clean with less number of SL cells.

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
```
set_global_routing_layer_adjustment layer adjustment
```
For example if we set adjustment for M2 as 0.5 it will reduce the routing resources of M2 layer by 50% now the tool will try to do routing on other layer. Default script blocks 50% of all signal routing. I added a fastroute.tcl script which blocks more routing resources for lower layer and less for higher layer thereby spreading routing among all layers.

## Conclusion


## Reference

