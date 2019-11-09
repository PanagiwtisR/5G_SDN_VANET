#!/usr/bin/python

import time
import os

from mininet.log import setLogLevel, info
from mininet.node import RemoteController
from mn_wifi.cli import CLI_wifi
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mininet.term import makeTerm, cleanUpScreens
from mn_wifi.wmediumdConnector import interference


class InbandController( RemoteController ):

    def checkListening( self ):
        "Overridden to do nothing."
        return


def topology():

    os.system('service network-manager stop')

    "Create a network."
    net = Mininet_wifi(controller=InbandController,
                       link=wmediumd,
                       wmediumd_mode=interference
                       )

    ip_c0 = '10.0.0.101'
    ip_c1 = '10.0.0.102'
    ip_c2 = '10.0.0.103'
    ip_c3 = '10.0.0.104'

    info("*** Creating nodes\n")
    cars = []
    car1 = net.addStation('car1', mac='02:00:00:00:00:01',
                          position='130,180,0') #, active_scan=1)

    car2 = net.addStation('car2', mac='02:00:00:00:00:02',
                          position='230,220,0') #, active_scan=1)

    car3 = net.addStation('car3', mac='02:00:00:00:00:03',
                          position='420,200,0') #, active_scan=1)

    car4 = net.addStation('car4', mac='02:00:00:00:00:04',
                          position='420,150,0') #, active_scan=1)

    car5 = net.addStation('car5', mac='02:00:00:00:00:05',
                          position='408,150,0') #, active_scan=1)

    car6 = net.addStation('car6', mac='02:00:00:00:00:05',
                          position='410,250,0') #, active_scan=1)
    cars.append(car1)
    cars.append(car2)
    cars.append(car3)
    cars.append(car4)
    cars.append(car5)
    cars.append(car6)


    enb1 = net.addAccessPoint('enb1', mac='00:00:00:00:00:01', ssid="handover",
                             mode="g", channel="1", datapath='user',
                             passwd='123456789a', encrypt='wpa2', ieee80211r='yes',
                             mobility_domain='a1b2', dpid='1',
                             position='150,200,0', inband=True)

    enb2 = net.addAccessPoint('enb2', mac='00:00:00:00:00:02', ssid="handover",
                             mode="g", channel="1", datapath='user',
                             passwd='123456789a', encrypt='wpa2', ieee80211r='yes',
                             mobility_domain='a1b2', dpid='2',
                             position='250,200,0', color='r', inband=True)

    enb3 = net.addAccessPoint('enb3', mac='00:00:00:00:00:03', ssid="handover",
                             mode="g", channel="1", datapath='user',
                             passwd='123456789a', encrypt='wpa2', ieee80211r='yes',
                             mobility_domain='a1b2', dpid='3',
                             position='320,200,0', inband=True)

    backbone1 = net.addSwitch('backbone1', mac='00:00:00:00:00:04', dpid='4',
                              datapath='user', inband=True)
    server = net.addHost('server', ip='10.0.0.100/8')

    h1 = net.addHost('h1', ip=ip_c0)
    h2 = net.addHost('h2', ip=ip_c1)
    h3 = net.addHost('h3', ip=ip_c2)
    h4 = net.addHost('h4', ip=ip_c3)

    c0 = net.addController('c0', controller=InbandController,
                           port=6690, ip=ip_c0)
    c1 = net.addController('c1', controller=InbandController,
                           port=6691, ip=ip_c1)
    c2 = net.addController('c2', controller=InbandController,
                           port=6692, ip=ip_c2)
    c3 = net.addController('c3', controller=InbandController,
                           port=6693, ip=ip_c3)
    net.setPropagationModel(model="logDistance", exp=3.4)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    #c0.plot(position='50,80,0')
    #c1.plot(position='110,80,0')
    #c2.plot(position='130,80,0')
    #backbone1.plot(position='110,30,0')
    #server1.plot(position='110,10,0')

    info("*** Associating Stations\n")
    net.addLink(backbone1, enb1)
    net.addLink(backbone1, enb2)
    net.addLink(backbone1, enb3,bw=20, delay='5ms',loss=5)
    net.addLink(backbone1, server)
    net.addLink(h1, enb1)
    net.addLink(h2, enb2)
    net.addLink(h3, enb3)
    net.addLink(h4, backbone1)

    net.plotGraph(max_x=500, max_y=500)

    info("*** Starting network\n")
    net.build()
    enb1.start([c0])
    enb2.start([c1])
    enb3.start([c2])
    backbone1.start([c3])

    makeTerm(h1, cmd="bash -c 'cd ryu && ./run.sh h1;'")
    makeTerm(h2, cmd="bash -c 'cd ryu && ./run.sh h2;'")
    makeTerm(h3, cmd="bash -c 'cd ryu && ./run.sh h3;'")
    makeTerm(h4, cmd="bash -c 'cd ryu && ./run.sh h4;'")

    time.sleep(3)

    enb1.cmd('sysctl net.ipv4.ip_forward=1')
    enb2.cmd('sysctl net.ipv4.ip_forward=1')
    enb3.cmd('sysctl net.ipv4.ip_forward=1')
    backbone1.cmd('sysctl net.ipv4.ip_forward=1')

    enb1.cmd('ifconfig enb1-eth3 10.0.0.201')
    enb2.cmd('ifconfig enb2-eth3 10.0.0.202')
    enb3.cmd('ifconfig enb3-eth3 10.0.0.203')
    backbone1.cmd('ifconfig backbone1-eth5 10.0.0.204')

    enb1.cmd('route add 10.0.0.101 dev enb1-eth3')
    enb2.cmd('route add 10.0.0.102 dev enb2-eth3')
    enb3.cmd('route add 10.0.0.103 dev enb3-eth3')
    backbone1.cmd('route add 10.0.0.104 dev backbone1-eth5')

    cars[0].cmd('iw dev %s-wlan0 interface '
                'add %s-mon0 type monitor'
                % (cars[0].name, cars[0].name))
    cars[0].cmd('ifconfig %s-mon0 up' % cars[0].name)

    enb1.cmd('ovs-ofctl add-flow "enb1" in_port=1,udp,tp_src=8000,actions=controller')
    enb2.cmd('ovs-ofctl add-flow "enb2" in_port=1,udp,tp_src=8000,actions=controller')
    enb3.cmd('ovs-ofctl add-flow "enb3" in_port=1,udp,tp_src=8000,actions=controller')
    backbone1.cmd('ovs-ofctl add-flow "backbone1" in_port=1,actions=output:4')
    backbone1.cmd('ovs-ofctl add-flow "backbone1" in_port=2,actions=output:4')
    backbone1.cmd('ovs-ofctl add-flow "backbone1" in_port=3,actions=output:4')


    cars[0].cmd('./%s.py &' % cars[0].name)

    currentTime = time.time()
    i = 60
    j = 0
    while j<3:
        if (time.time() - currentTime) >= i:
            currentTime = time.time()
            if j == 0:
                cars[0].setPosition('240,180,0')
            else:
                cars[0].setPosition('315,180,0')
            j+=1
        if j == 2 and (time.time() - currentTime) == 1:
            cars[0].cmd('wpa_cli -i car1-wlan0 scan')
        # force association due to better rssi
        if j == 2 and (time.time() - currentTime) == 5:
            cars[0].cmd('wpa_cli -i car1-wlan0 scan_results')
            cars[0].cmd('wpa_cli -i car1-wlan0 roam 00:00:00:00:00:03')

    info("*** Running CLI\n")
    CLI_wifi(net)

    os.system('pkill -f \"xterm -title\"')
    os.system('pkill ryu-manager')
    os.system('service network-manager start')

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()
