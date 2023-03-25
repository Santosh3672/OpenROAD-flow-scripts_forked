# Openroad Flow PPA improvement
## Introduction
This repo is related to Openroad 7nn  [contest](https://jenkins.openroad.tools/buildStatus/icon?job=OpenROAD-flow-scripts-Public%2Fpublic_tests_all%2Fmaster). Here I am targetting problem statement A of achieving best performance with zero DRC and timig violation.
Following are the details:
### Design selected: Ibex
### Process node: Asap7 7nm

In this repo I will be discussing the modification in flow performed to increase frequency of the design while at the same time ensuring that these methods had no major impact on Power and area. Thus achieving improvement in PPA. Some methods like PDN strategy change have helped us to improve runtime, that is also discussed here. 

## Content
Following are the modification in the flow that I have performed:
 ### Use of Multi-threshold voltage cells in the design
 ### Using higher layer for power ground routing during floorplan stage. 
