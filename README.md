#Run -->> saini2.py 
#8->Shortest Path First calcs(using floyd-warhsall)

    Success condition: Controller prints out SPF table, between the switches, on any PacketIn
    Components: Adv. Python.
    Algorithm: - Controller continously collects data on all switches and ports connected. - Controller runs LLDP checks     on all and any topology changes. - Right after any new LLDP updates parsed an SPF algorithm (Dijkstra, Bellman-Ford,     or any other) is run on the data. - SPF output is stored as well as printed out.

#Reference 
1)Simple implementation of floyd-warhsall algorithm in Python 
https://gist.github.com/Ceasar/2474603

2)Class Notes mycontroller4.py from MyDrive
https://www.dropbox.com/sh/9473n90i6o8e5of/AABvnngHL-HDfdu1k74ospY_a?dl=0


