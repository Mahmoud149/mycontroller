from collections import defaultdict as ddict
from ryu.base import app_manager as Manager
from ryu.controller import handler
from ryu.controller.handler  import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.ofproto import ofproto_v1_3 as ofp13
from ryu.ofproto import ofproto_v1_3_parser as parser13
from ryu.lib.packet import packet
from ryu.controller import ofp_event
from ryu.lib.packet import packet,arp, ether_types, ethernet as eth
from ryu.lib.packet import lldp
from ryu.ofproto.ether import ETH_TYPE_LLDP
from ryu.ofproto import ether as ethertypes
from ryu.lib import hub
import random


class MyController(Manager.RyuApp):
	OFP_VERSIONS = [ofp13.OFP_VERSION]
    	DEF_PRI = 100
    	DEF_TIMEOUT = 30
	

	def __init__(self, *args, **kwargs):
        	super(MyController, self).__init__(*args, **kwargs)  # Mandatory
        	  # Inherits Dict
        	#self.stats_requester_thread = hub.spawn(self._port_stats_requester)
		self.state=Topology()
		self.P_DOWN=(None,None)
        	self.P_EDGE=(1234,1234)
		self.edge_port=ddict(dict)
		self._threads=hub.spawn(self._monitor)
		self.source=None
		self.destination=None
		self.change=None	
		

	@handler.set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER, DEAD_DISPATCHER])
	def _state_change_handler(self, ev):
       		 datapath = ev.datapath
       		 if ev.state == MAIN_DISPATCHER:
            		if not datapath.id in self.state.datapaths:
	                	self.logger.debug('register datapath: %016x', datapath.id)
                		self.state.datapaths[datapath.id] = datapath
        	 elif ev.state == DEAD_DISPATCHER:
            		if datapath.id in self.state.datapaths:
                		self.logger.debug('unregister datapath: %016x', datapath.id)
                		del self.state.datapaths[datapath.id]

    	def _monitor(self):
			
	            	for dp in self.state.datapaths.values():
        	        	msg=parser13.OFPPortDescStatsRequest(dp)
				dp.send_msg(msg)
				print'STATS REQUESTED---------------',dp.id
				self.change=True
            		hub.sleep(2)
			#self.dijkstra(self.edge_port,self.source,self.destination)


    	def adj(self,g):
    		vertices = g.keys()
    		dist = {}
    		for i in vertices:
        		dist[i] = {}
        		for j in vertices:
            			try:
                			dist[i][j] = g[i][j]
            			except KeyError:
                # the distance from a node to itself is 0
                			if i == j:
                    				dist[i][j] = 0
                # the distance from a node to an unconnected node is infinity
                			else:
                    				dist[i][j] = float('inf')
    		return dist
	def fw(self,g):
    		vertices = g.keys()

    		d = dict(g)  # copy g
    		for k in vertices:
        		for i in vertices:
            			for j in vertices:
                			d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    		return d


	@handler.set_ev_cls(ofp_event.EventOFPSwitchFeatures,handler.CONFIG_DISPATCHER)
        def default_behaviour(self,ev):

                switch = ev.msg.datapath
        # ADD THE SWITCH
              #  self.switches[switch.id] = switch

        # Build a default rule
                actions_controller = [parser13.OFPActionOutput(ofp13.OFPP_CONTROLLER)]
                instr = [ parser13.OFPInstructionActions(
                        ofp13.OFPIT_APPLY_ACTIONS,
                        actions_controller) ]
        # Send it
                self.send_new_flow(switch=switch, instr=instr, priority=0, timeout=0)

        # Override any LLDP flows
                match = parser13.OFPMatch(eth_type=ether_types.ETH_TYPE_LLDP)
                self.send_new_flow(switch=switch, instr=instr, priority=5000, timeout=0, match=match)

        # Request port status
                msg = parser13.OFPPortDescStatsRequest(switch)
		switch.send_msg(msg)
		#self.state.fun_print()
        def send_new_flow(self,
                      switch,
                      out_port=ofp13.OFPP_FLOOD,
                      match=parser13.OFPMatch(),
                      instr=[],
                      priority=DEF_PRI,
                      timeout=DEF_TIMEOUT,
                      buffer_id=ofp13.OFP_NO_BUFFER):

                msg = parser13.OFPFlowMod(match=match,
                                datapath=switch,
                                instructions=instr,
                                idle_timeout=timeout,
                                priority=priority,
                                buffer_id=buffer_id)
                switch.send_msg(msg)
	
	@handler.set_ev_cls(ofp_event.EventOFPPacketIn,handler.MAIN_DISPATCHER)
        def packet_in_unknown(self,ev):
                msg=ev.msg
                dp=msg.datapath
                ofp=dp.ofproto
                eth_frame=msg.data
                parsed=packet.Packet(eth_frame)
                ether_header=parsed.get_protocols(eth.ethernet)[0]
                dst=ether_header.dst
                src=ether_header.src
                in_p=msg.match['in_port']
                if ether_header.ethertype==ether_types.ETH_TYPE_LLDP:
                        
                        lldp_header=parsed.get_protocols(lldp.lldp)[0]
			
                        self.parse_lldp(dp,in_p,lldp_header)
                        #self._threads.append(hub.spawn(self._port_status()))
                        #self._threads.append(hub.spawn(self.paramter_coll())
                        return
                #Now get the Id of the switch and port/-on which we recieved the packet
		
                self.state.mac_tables[dp.id][src]=in_p
				
#               print self.mac_tables

                #SEND Where??
                if dst in self.state.mac_tables[dp.id]:
                        out_port=self.state.mac_tables[dp.id][dst]
                else:
                        out_port=ofp13.OFPP_FLOOD
                action=[parser13.OFPActionOutput(out_port)]
                inst=[parser13.OFPInstructionActions(ofp13.OFPIT_APPLY_ACTIONS,action)]

                if out_port !=ofp13.OFPP_FLOOD:
                        match=parser13.OFPMatch(eth_dst=dst)
                        if ev.msg.buffer_id!=ofp13.OFP_NO_BUFFER:
                                self.add_flow_entry(dp,match,msg.buffer_id,inst)
                                return
                        else:
                                buffer_id=None
                                self.add_flow_entry(dp,match,buffer_id,inst)
                data=None
                if msg.buffer_id==ofp13.OFP_NO_BUFFER:
                        data=msg.data
                out=parser13.OFPPacketOut(datapath=dp,buffer_id=msg.buffer_id,in_port=msg.match['in_port'],actions=action,data=data)
                dp.send_msg(out)
		
	
	def parse_lldp(self, switch, in_port, lldp_header):
         	global objectlist
              	tlv_chassis = lldp_header.tlvs[0]
                tlv_port = lldp_header.tlvs[1]
                peer_dpid = int(tlv_chassis.chassis_id)
                peer_port = int(tlv_port.port_id)
		print "*********************************"
                print "RECV LLDP: ", switch.id, in_port, "<-", peer_dpid, peer_port
		print"*********************************"
                self.state.switchports[switch.id][in_port] = (peer_dpid, peer_port)
	 	#print '-----------receive LLDP-------'
		print'Switch_Port Entry  Updated ', self.state.switchports
		#print "------------------\n"
		self.edge(switch.id,peer_dpid)
		if self.change==True:
			print'------------------------------'
			print 'SHORTEST PATH CALS',self.fw(self.adj(self.edge_port))
			print '-------------------------------'
	

	def send_lldp_out(self,p,port_no):
                e=eth.ethernet(dst=lldp.LLDP_MAC_NEAREST_BRIDGE,src=lldp.LLDP_MAC_NEAREST_BRIDGE,ethertype=ether_types.ETH_TYPE_LLDP)
                pkt=packet.Packet()
                pkt.add_protocol(e)
                l=lldp.lldp(tlvs=[
                         lldp.ChassisID(subtype=lldp.ChassisID.SUB_LOCALLY_ASSIGNED,
                                        chassis_id=str(p.id)),
                         lldp.PortID(subtype=lldp.PortID.SUB_LOCALLY_ASSIGNED,
                                     port_id=str(port_no)),
                         lldp.TTL(ttl=5),
                         lldp.End()
                         ])
                pkt.add_protocol(l)
                pkt.serialize()
                data=pkt.data
                print "Sednd LLdp:",p.id,port_no
                out=parser13.OFPPacketOut(datapath=p,buffer_id=ofp13.OFP_NO_BUFFER,in_port=ofp13.OFPP_CONTROLLER,actions=[parser13.OFPActionOutput(port_no)],data=data)
                p.send_msg(out)
	def add_flow_entry(self,datapath,match,buffer_id,inst):
                        ofp =datapath.ofproto
                        ofp_parser=datapath.ofproto_parser
                        priority=32768
                        #match=ofp_parser.OFPMatch(eth_dst=dst)
                        if buffer_id:

                                req=ofp_parser.OFPFlowMod(datapath=datapath,buffer_id=buffer_id,priority=priority,match=match,instructions=inst)
                        else:
                                req=ofp_parser.OFPFlowMod(datapath=datapath,prioroty=priority,match=match,instructions=inst)
                        datapath.send_msg(req)
	


	@handler.set_ev_cls(ofp_event.EventOFPPortStatus, handler.MAIN_DISPATCHER)
        def port_status_handler(self,ev):
                msg=ev.msg
                dp=msg.datapath
                p=ev.msg.desc
		self._monitor()
                if p.state==1:
                        peer_id,peer_port=self.state.switchports[dp.id].setdefault(p.port_no,self.P_DOWN)
                        self.state.switchports[ev.msg.datapath.id][p.port_no]=self.P_DOWN
                        print dp.id,'portno->',p.port_no,'Status Changed'
			self.source=dp.id
			self.destination=peer_id
                        if peer_id !=None and peer_port!=None:
                                self.state.switchports[peer_id][peer_port]=self.P_DOWN
				del self.edge_port[dp.id][peer_id]
				del self.edge_port[peer_id][dp.id]
				print'After Edge_port delete, -->{switch_id:{peer_id:weight}}',self.edge_port
#				try:
#					hub.spawn(self.dijkstra(self.edge_port,dp.id,len(self.edge_port)-1))
#				except:
#					print 'lol'
                elif p.state==0:
			print 'Port Up'
			peer_id,peer_port=self.state.switchports[dp.id].setdefault(p.port_no,self.P_EDGE)
                        self.state.switchports[dp.id][p.port_no]=self.P_EDGE
			self.source=dp.id
			self.destination=peer_id
                        self.send_lldp_out(dp,p.port_no)
#		self._monitor()
	@handler.set_ev_cls(ofp_event.EventOFPPortDescStatsReply, handler.MAIN_DISPATCHER)
        def port_desc_stats_reply_handler(self, ev):
                ports = []
#		self.source=ev.msg.datapath.id
#		self.destination=p.peer
                #hub.spawn(self.dijkstra(self.edge_port,ev.msg.datapath.id,len(self.edge_port)-1))
		#self.dijkstra(self.edge_port,self.source,self.destination)
                for p in ev.msg.body:
                        if p.state==1:
                                state=self.P_DOWN
                        else:
                                state=self.P_EDGE
                        if p.port_no != ofp13.OFPP_CONTROLLER and p.port_no != ofp13.OFPP_LOCAL:
                                self.state.switchports[ev.msg.datapath.id][p.port_no] = state
                                self.send_lldp_out(ev.msg.datapath, p.port_no)
		
				#self.source=ev.msg.datapath.id
				#print self.source
				#print self.destination
				#if len(self.edge_port)>=2:
				#	self.dijkstra(self.edge_port,self.source,self.destination)
					
	def edge(self,src,dst):
		
		for key, port in self.state.switchports.iteritems():

                               for port_no ,states in port.iteritems():
					
                                           if states==self.P_EDGE or states==self.P_DOWN:
							
                                                     	 pass
                                           else:
                                                      	 self.edge_port[key][states[0]]=random.randint(1,9)
		print 'DATA STRUCTURE FOR  Directed Graph -->{switch_id:{peer_id:weight}} '
		print self.edge_port

class Topology(dict):
    """ Stores all topology related information and
    some useful utility functions"""
    def __init__(self):
        # Self is a dict for {DPID => DP_OBJ}
        self.switchports=ddict(dict)
	self.mac_tables=ddict(dict)
    	self.datapaths={}
