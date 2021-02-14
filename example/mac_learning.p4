/* -*- P4_16 -*- */
#include <core.p4>
// #include <psa.p4>
#include <v1model.p4>

#include <headers.p4>

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/



struct metadata {
}

struct headers {
    ethernet_t ethernet;
}


struct mac_digest {
	macAddr_t smac;
	egressSpec_t ingress_port;
}


/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            default : accept;
        }
    }

}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }

	action mac_forward(egressSpec_t port) {
		standard_metadata.egress_spec = port;
	}

	action multicast_forward(bit<16> mcast_grp) {
		standard_metadata.mcast_grp = mcast_grp;
	}

	action noop () { /* Nothing to do */ }

	action send_digest() {
		digest<mac_digest>(1, {
			hdr.ethernet.srcAddr, 
			standard_metadata.ingress_port
		});
	}


	table smac_table {
		key = {
			hdr.ethernet.srcAddr: exact;
		}
		actions = {
			send_digest;
			noop;
		}
		default_action = send_digest();
		size = 4096;
		support_timeout = true;
	}


	table dmac_table {
		key = {
			hdr.ethernet.dstAddr: exact;
		}
		actions = {
			mac_forward;
			multicast_forward;
			drop;
		}
		size = 1024;
		default_action = drop;
	}



    apply {
        if (hdr.ethernet.isValid()) {
			smac_table.apply();
			dmac_table.apply();	

			/* 	This could be done in the dmac table with either a static or
				loaded entry */
			// if (hdr.ethernet.dstAddr == 0xffffffffffff) {
			// 	mac_broadcast();
			// } 
			// else {
			// 	dmac_table.apply();	
			// }
		}
	}
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    action drop() {
        mark_to_drop(standard_metadata);
    }

    apply {
        // Prune multicast packet to ingress port to preventing loop
        if (standard_metadata.egress_port == standard_metadata.ingress_port) {
            drop();
		}
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
		/* We can't use conditionals in a deparser. This means that we are
		   unable to conditionally output headers directly. However, if the 
		   frame is set as invalid, it won't be outputted, even if emit is
		   called
		*/
        packet.emit(hdr.ethernet);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
	MyParser(),
	MyVerifyChecksum(),
	MyIngress(),
	MyEgress(),
	MyComputeChecksum(),
	MyDeparser()
) main; 