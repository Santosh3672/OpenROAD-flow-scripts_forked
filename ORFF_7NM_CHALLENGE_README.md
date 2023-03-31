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

There is a command called repair_design which inserts buffers on nets to repair max slew, max capacitance and max fanout violations and on long wire to reduce delay. But it has to be performed before placement where the timing is not accurate. Due to this reason we see timing violations post routing. We can't do repair_design after routing stage as the new cells cannot be placed or routed. <br />

This is where the proposed solution of my ECO engine comes. It swaps the existing placed and routed cells with its faster variant(L or SL) having same dimension and pin layout. Since ECO is performed at the last stage of the design the turnaround time is also less. The solution automatic and requires no human intervention apart from running new iteration through make command. It aligns with the aim of OpenROAD project.<br />

If we try to synthesize a high frequency design by allowing faster(standard cell) standard cell, it will consider the pessimistic timing report as we have seen in floorplan and try to over-optimize the design. This will cause the design to have very high leakage power. <br />
To avoid these issues I have developed an ECO engine that checks the timing report from logs and based on that it will swap slow cells on timing critical paths with fast L or SL cells to make them timing clean. The usage of the engine on OpenROAD flow is shown in figure below.<br />

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/ECO%20flow.drawio.png" />
<p align='center'>Multi Vt ECO flow</p>
</p>
The ECO engine is pyhon based, first it parses the log file of 7_1_eco.log and search for violating paths. From those paths it extracts the datapath delay, analyses and finds list of gates that can be swapped to met constraints.  <br />
The script also incorporates those changes in the .v & .def file by updating them and dumps updated ones with a new name. Currently there are no command that swaps  cell in the openROAD tool, if that feature is available the ECO engine can dump a file containing list of changes that can be read by openROAD and write_def/ write_verilog command can be used to generate def and verilog files respectively. <br />

Details of all the modification and steps performed for the ECO is mendioned below:<br />
i. First all the Vt variant cells (R, L and SL) are read in merged.lib file and any cell not required for synthesis(say L or SL) can be blocked by setting "dont_use: true" through DONT_USE variable in config file.<br />
ii. For higher frequency design R and L cells are can be enabled, but SL cells need to be blocked for synthesis.<br />
iii. Similarly L variant of Adder, Buffer and CTS buffers can be used, for high performance. <br />
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
To test the effectiveness of the proposed ECO engine following experiments are performed on ibex design by changing differenc cell usage during synthesis task and performing ECO on them. <br />
Design implemented: Ibex at Asap7node <br />
Clock period: 1400ps (714.286 MHz) <br />
Default clock period in constraint.sdc: 1760 (it was timing clean then) <br />
Experiment 1:<br />
Variants of Std cell enabled for Yosys: RVT and LVT<br />
Variants of Adder and DFF used: LVT<br />
Pre ECO:<br />

| Power(10^-2W) | WNS(ps) | TNS(ps) | Design Area(um^2) |
| ------------- | ------- | ------- | ----------------- |
| 1.67          | 115.36  | 1718.13 | 2479              |
 
 <br />
 Post ECO:<br />
 Number of ECO iterations: 6<br />
 
| Iteration # | Power(10^-2W) | WNS(ps) | TNS(ps) |
| ----------- | ------------- | ------- | ------- |
| 1           | 1.68          | 49.84   | 275.17  |
| 2           | 1.68          | 18.72   | 76.01   |
| 3           | 1.68          | 15      | 41.01   |
| 4           | 1.68          | 5.24    | 6.58    |
| 5           | 1.68          | 2.18    | 2.18    |
| 6           | 1.68          | 0       | 0       |
  
Experiment 2:
Variants of Std cell enabled for Yosys: RVT, LVT and SLVT<br />
Variants of Adder and DFF used: LVT<br />
Pre ECO:<br />

| Power(10^-2W) | WNS(ps) | TNS(ps) | Design Area(um^2) |
| ------------- | ------- | ------- | ----------------- |
| 1.82          | 149.21  | 1752.8  | 2479              |

  After ECO:<br />
  Number of ECO iterations: Did not converge<br />

| Iteration # | Power(10^-2W) | WNS(ps) | TNS(ps) |
| ----------- | ------------- | ------- | ------- |
| 1           | 1.82          | 76.09   | 311.75  |
| 2           | 1.82          | 40.78   | 103.39  |
| 3           | 1.82          | 30.47   | 41.06   |
| 4           | 1.82          | 29.82   | 38.17   |
| 5           | 1.82          | 29.84   | 38.25   |

Experiment 3:<br />
Variants of Std cell enabled for Yosys: RVT, LVT and SLVT<br />
Variants of Adder and DFF used: RVT<br />
Pre ECO:<br />
  Power 1.78e-2<br />
  WNS: 73.64<br />
  TNS: 1566.26<br />
  Design area: 2479u^2<br />
 Number of ECO iterations: 2<br />
      Power(10^-2W), WNS(ps), TNS(ps)<br />
Iter1: 1.78, 15.00, 46.77<br />
Iter2: 1.78,  0,      0<br />


Experiment 4:<br />
Variant of Std cells enabled for Yosys: RVT<br />
Variant of adder and DFF used: RVT<br />
Pre ECO:<br />
  Power 1.54e^-2<br />
  WNS: 42.78<br />
  TNS: 327.89<br />
  Design area: 2514u^2<br />
  Number of ECO iterations: 4<br />
      Power(10^-2W), WNS(ps), TNS(ps)<br />
Iter1: 1.54, 20.75,  60.28<br />
Iter2: 1.54, 10.57,  10.57<br />
Iter3: 1.54,  7.51,  7.51<br />
Iter4: 1.54,     0,      0<br />

**Observation**
The worst PPA is seen in experiment 2 where all VT variant cells are allowed. There were L and SL cells which raised power consumption of chip and also due to lack of cell upsizing(swapping cell with its faster variant R->L or L->SL) opportunities ECO engine couldnt resolve all timing violation. While on other hand on Experiment 2 had the best PPA where only R cell was enabled. <br />
Apart from experiment 2 the ECO engine was succesful in resolving all the timing violation in design with the help of L and SL cells.<br />
From this we can conclude that it is better to be conservative when it comes to selecting VT of the std cells during synthesis stage and allow only R cells. The flow works best with that strategy. For SL and L cells it is better use them for ECO purposes only using on synthesis gives poor result. After final stage the ECO engine is effective in resolving remaining violations.<br />

**Best frequency achievable with this approach***
Till now I have tried with time period of 1200ps which is a frequency of 833.33MHz, PPA details before and after ECO are as follows:<br />
Cells enabled during syntehsis: RVT<br />
Time period of design: 1200ps (833.33MHz)<br />
Pre ECO: power 1.83e-2<br />
	 WNS: 171.4<br />
	 TNS: 52418.75<br />
	 Area: 2524u^2<br />
ECO number of iteration: <br />
Iter1: 1.83, 89.29, 14299.29<br />
Iter2: 1.84, 52.87,  8753.23<br />
Iter3: 1.84, 45.56,  5194.51<br />
Iter4: 1.84, 31.23,  3207.58<br />
Iter5: 1.84,21.95,   1707.65<br />
Iter6:1.85, 16.23, 1025.56<br />
Iter7:1.8513.98, 575.51<br />
Iter8:1.85, 12.02, 248.48<br />
Iter9:1.85, 10.67, 62.15<br />
Iter10: 1.85, 8.18, 8.15<br />
Iter11:1.85, 7.49,7.49<br />
Iter12:1.85, 4.68, 4.68<br />
Iter13:1.85,2.09, 2.09<br />
Iter14:1.851.42, 1.42<br />
Iter15:1.85, 0,0<br />

Last 5 iterations took long to converge a single violation because the ECO tool first prioritises R to L swap before swapping L to SL. This might cause slower convergence but saves power consumption by avoiding SL cells as much as possible. In future this feature may be modified.<br />

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/Ibex%201200ps%20pre%20ECO%20timing.JPG" />
<p align='center'>Pre ECO timning status on GUI</p>
</p>

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/Ibex%201200ps%20pre%20ECO%20PPA.JPG" />
<p align='center'>Pre ECO PPA details on GUI</p>
</p>
<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/Ibex%201200ps%20post%20ECO%20timing.JPG" />
<p align='center'>Post ECO timning status on GUI</p>
</p>
<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/Ibex%201200ps%20post%20ECO%20PPA.JPG" />
<p align='center'>Post ECO PPA details on GUI</p>
</p>
ECO iteration wise PPA snippets <br />

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/Ibex%201200ps%20ECO%20iter1.JPG" />
<p align='center'>ECO Iteration 1 snippet</p>
</p>

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/Ibex%201200ps%20ECO%20iter2.JPG" />
<p align='center'>ECO Iteration 2 snippet</p>
</p>

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/Ibex%201200ps%20ECO%20iter5.JPG" />
<p align='center'>ECO Iteration 5 snippet</p>
</p>

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/Ibex%201200ps%20ECO%20iter10.JPG" />
<p align='center'>ECO Iteration 10 snippet</p>
</p>

<p align="center">
<img src = "https://github.com/Santosh3672/OpenROAD-flow-scripts_forked/blob/master/Images/ECO/Ibex%201200ps%20ECO%20iter15.JPG" />
<p align='center'>ECO Iteration 15 snippet</p>
</p>

**Performance improvement with proposed ECO engine** <br />
There are two ways to measure the performance improvement:<br />
i. In first method we will compare the highest freqeuncy where default flow had timing clean DB with that with flow including ECO. With default flow somewhere around 1760ps which is set by default (568.182MHz) the timing was clean. If we compare our flow was able to increase frequency by around 60.8%.But in this case the design power consumption was 1.2 x 10^-2, while at 1200ps with ECO the power consumption was 1.85 x 10^-2W  54% higher.<br />
ii.To normalize other parameters as well we can compare frequency of ECO-based flow with default flow. With ECO we were able to meet 1200ps time period (833.333MHz) with default we have WNS of 171.4ps or it is timing clean at 1200+171.4 = 1371.4ps ~ frequency of 729.18MHz the design is timing clean. All other parameters like area and power are very close in this comparision. In this method the ECO based flow had 14.3% higher frequency.<br />

So, in terms of the ability of the ECO flow to raise frequency it has increase frequency of design by 60.8% with 54% higher power consumption. If we normalise other parameters also the floe is able to increase frequency of the design by 14.3%. <br />
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

