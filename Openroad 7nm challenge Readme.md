# Openroad Flow PPA improvement
This repo documents the work done during Openroad 7nm design [contest](https://jenkins.openroad.tools/buildStatus/icon?job=OpenROAD-flow-scripts-Public%2Fpublic_tests_all%2Fmaster). 
## Table of content
- [Introduction](#introduction)
- [Solutions tried](#solutions-tried)
  - [Use of Multi-threshold voltage cells in the design](#use-of-multi-threshold-voltage-cells-in-the-design)
  - [Using higher layer for power ground routing during floorplan stage](#Using higher layer for power ground routing during floorplan stage)
- [Conclusion](#conclusion)
- [Reference](#reference)
## Introduction
This repo is related to Openroad 7nn  [contest](https://jenkins.openroad.tools/buildStatus/icon?job=OpenROAD-flow-scripts-Public%2Fpublic_tests_all%2Fmaster). Here I am targetting problem statement A of achieving best performance with zero DRC and timig violation.
Following are the details:
### Design selected: Ibex
### Process node: Asap7 7nm

In this repo I will be discussing the modification in flow performed to increase frequency of the design while at the same time ensuring that these methods had no major impact on Power and area. Thus achieving improvement in PPA. Some methods like PDN strategy change have helped us to improve runtime, that is also discussed here. 

## Solutions tried
Following are the modification in the flow that I have performed:
### Use of Multi-threshold voltage cells in the design
 In Asap7 library there are three types of standard cells in terms of threshold voltage they are  
 i. R: Cells with regular Vt  
 ii. L: low Vt cells
 iii. SL: Super low Vt cells
 In terms of delay R > L > SL, hence SL cells are faster than L cells which are faster than R cell. With this the delay of the datapath will be reduced allowing us to meet STA with low time period or high frequency. 

But it comes at the cost of power. SL cells consume more than 10times the power consumed by R cells. To avoid having a high power consumption chip for high frequency operation, I am planning to use R and L cells having low  power consumption during Synthesis stage and then after synthesis at the later part replace L or R cells with SL cells on failing paths to have positive WNS. THis way the dewsign will be timing clean with less number of SL cells.

### Using higher layer for power ground routing during floorplan stage
During the routing stage of Ibex on Asap7 node the total runtime was more than 45 min where during detailed routing the tool was clkeaning DRC. 
In global_route.tcl M2-M7 layers are being used for routing and 50% of it is being used for signal routing. 
I see that the PDN script uses M5 and M6 layers while Asap7 node allows us to route till M9 layer, so I changed the PDN layers from M5-M6 to M7-M8. In doing so the M5 and M6 layers can now accomodate more signal routing hence the detail routing tool now runs faster due to less congestion. 
With this strategy of PDN routing I allocated 10% more space for M3-M6 and now the runtime reduces to 30 minutes.

## Conclusion


## Reference

