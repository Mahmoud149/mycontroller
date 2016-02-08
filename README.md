###Ryu Controller to implement controller,which  prints out SPF table, between the switches, on any PacketIn Components like advertising or change in network topology.
###Algorithm:
<ul>
<li>Controller continously collects data on all switches and ports connected.</li> 
<li>Controller runs LLDP checks on all and any topology changes.</li> 
<li>Right after any new LLDP updates parsed an SPF algorithm (Dijkstra, Bellman-Ford,or any other) is run on the data.</li>     
<li>SPF output is stored as well as printed out.</li>
</ul>


###Reference 
1)Simple implementation of floyd-warhsall algorithm in Python 
https://gist.github.com/Ceasar/2474603

2)Class Notes mycontroller4.py from MyDrive
https://www.dropbox.com/sh/9473n90i6o8e5of/AABvnngHL-HDfdu1k74ospY_a?dl=0


