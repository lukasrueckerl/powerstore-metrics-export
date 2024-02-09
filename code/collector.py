##!/usr/bin/env python3
import time
import requests
import decimal
import os
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from prometheus_client.core import GaugeMetricFamily, REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server


class PowerstoreCollector(object):

    HOST = os.environ['POWERSTORE_HOST']
    USER = os.environ['POWERSTORE_USER']
    PASS = os.environ['POWERSTORE_PASS']

    def __init__(self):
        pass

    def call_api_get (self, uri, returnToken = False):
        url = "https://"+self.HOST+uri
        req = requests.get(url, auth=HTTPBasicAuth(self.USER, self.PASS), verify = False)

        if req.status_code != 200:
            print ("UNKNOWN ERROR: Can't connect to %s failed: %s" % (url, "error"))

        result = req.json()

        if returnToken == True:
            result = req.headers['DELL-EMC-TOKEN']

        return result

    def call_api_post(self, uri, payload):
        token = self.call_api_get("/api/rest/appliance", True)
        url = "https://"+self.HOST+uri
        headers = {"DELL-EMC-TOKEN":token, "Content-Type":"application/json"}
        req = requests.post (url, data = payload, headers = headers, auth = HTTPBasicAuth(self.USER, self.PASS), verify = False)
        if req.status_code != 200:
            print ("UNKNOWN ERROR: Can't connect to %s failed: %s" % (url, "error"))
        result = req.json ()
        return result

    def round_down(value, decimals):
        with decimal.localcontext() as ctx:
            d = decimal.Decimal(value)
            ctx.rounding = decimal.ROUND_DOWN
            return round(d, decimals)

    def getPerformanceMetric(self):
        payload = '{"entity":"performance_metrics_by_cluster","entity_id":"0"}'
        apiresponse = self.call_api_post("/api/rest/metrics/generate?limit=1&select=*",payload)
        return apiresponse[-1]

    def getEthInterfaces(self):
        apiresponse = self.call_api_get("/api/rest/eth_port?select=*")
        return apiresponse

    def getFcInterfaces(self):
        apiresponse = self.call_api_get("/api/rest/fc_port?select=*")
        return apiresponse

    def getPerformanceEthInterface(id, self):
        print(id)
        payload = '{"entity":"performance_metrics_by_fe_eth_port","entity_id":"'+id+'"}'
        apiresponse = self.call_api_post("/api/rest/metrics/generate?limit=1&select=*",payload)
        return apiresponse[-1]

    def getPerformanceFcInterface(id, self):
        print(id)
        payload = '{"entity":"performance_metrics_by_fe_fc_port","entity_id":"'+id+'"}'
        apiresponse = self.call_api_post("/api/rest/metrics/generate?limit=1&select=*",payload)
        return apiresponse[-1]

    def collect(self):

        perfMetric = self.getPerformanceMetric()
        eth_interfaces = self.getEthInterfaces()
        fc_interfaces = self.getFcInterfaces()

        for eth_interface in eth_interfaces:
            if eth_interface["is_link_up"] == True:
                id = eth_interface['id']
                print(id)
                port_data = PowerstoreCollector.getPerformanceEthInterface(str(id),self)

                g = GaugeMetricFamily("powerstore_interface_"+(eth_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_bytes_out", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_ethernet"], float(port_data["bytes_tx_ps"]))
                yield g

                g = GaugeMetricFamily("powerstore_interface_"+(eth_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_bytes_in", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_ethernet"], float(port_data["bytes_rx_ps"]))
                yield g

                g = GaugeMetricFamily("powerstore_interface_"+(eth_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_pakets_out", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_ethernet"], float(port_data["pkt_tx_ps"]))
                yield g

                g = GaugeMetricFamily("powerstore_interface_"+(eth_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_pakets_in", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_ethernet"], float(port_data["pkt_rx_ps"]))
                yield g

        for fc_interface in fc_interfaces:
            if fc_interface["is_link_up"] == True:
                id = fc_interface['id']
                print(id)
                port_data = PowerstoreCollector.getPerformanceFcInterface(str(id),self)

                g = GaugeMetricFamily("powerstore_interface_"+(fc_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_avg_latency", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_fc"], float(port_data["avg_latency"]))
                yield g

                g = GaugeMetricFamily("powerstore_interface_"+(fc_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_avg_read_latency", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_fc"], float(port_data["avg_read_latency"]))
                yield g
                
                g = GaugeMetricFamily("powerstore_interface_"+(fc_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_avg_write_latency", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_fc"], float(port_data["avg_write_latency"]))
                yield g
                
                g = GaugeMetricFamily("powerstore_interface_"+(fc_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_dumps_per_second", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_fc"], float(port_data["dumped_frames_ps"]))
                yield g
                
                g = GaugeMetricFamily("powerstore_interface_"+(fc_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_total_bandwidth", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_fc"], float(port_data["total_bandwidth"]))
                yield g
                
                g = GaugeMetricFamily("powerstore_interface_"+(fc_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_read_bandwidth", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_fc"], float(port_data["read_bandwidth"]))
                yield g
                
                g = GaugeMetricFamily("powerstore_interface_"+(fc_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_write_bandwidth", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_fc"], float(port_data["write_bandwidth"]))
                yield g

                g = GaugeMetricFamily("powerstore_interface_"+(fc_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_total_iops", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_fc"], float(port_data["total_iops"]))
                yield g
                
                g = GaugeMetricFamily("powerstore_interface_"+(fc_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_read_iops", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_fc"], float(port_data["read_iops"]))
                yield g
                
                g = GaugeMetricFamily("powerstore_interface_"+(fc_interface['name'].replace("-","_")).replace("powerstore-interface-BaseEnclosure-","")+"_write_iops", 'Help text', labels=['instance'])
                g.add_metric(["powerstore_fc"], float(port_data["write_iops"]))
                yield g

        g = GaugeMetricFamily("powerstore_total_bandwidth", 'Help text', labels=['instance'])
        g.add_metric(["powerstore"], float(perfMetric["total_bandwidth"]))
        yield g

        g = GaugeMetricFamily("powerstore_read_bandwidth", 'Help text', labels=['instance'])
        g.add_metric(["powerstore"], float(perfMetric["read_bandwidth"]))
        yield g

        g = GaugeMetricFamily("powerstore_write_bandwidth", 'Help text', labels=['instance'])
        g.add_metric(["powerstore"], float(perfMetric["write_bandwidth"]))
        yield g

        g = GaugeMetricFamily("powerstore_iosize", 'Help text', labels=['instance'])
        g.add_metric(["powerstore"], float(perfMetric["avg_io_size"]))
        yield g

        g = GaugeMetricFamily("powerstore_iops", 'Help text', labels=['instance'])
        g.add_metric(["powerstore"], float(perfMetric["total_iops"]))
        yield g

        g = GaugeMetricFamily("powerstore_read_iops", 'Help text', labels=['instance'])
        g.add_metric(["powerstore"], float(perfMetric["read_iops"]))
        yield g

        g = GaugeMetricFamily("powerstore_write_iops", 'Help text', labels=['instance'])
        g.add_metric(["powerstore"], float(perfMetric["write_iops"]))
        yield g

        g = GaugeMetricFamily("powerstore_latency", 'Help text', labels=['instance'])
        g.add_metric(["powerstore"], float(perfMetric["avg_latency"]))
        yield g

        g = GaugeMetricFamily("powerstore_read_latency", 'Help text', labels=['instance'])
        g.add_metric(["powerstore"], float(perfMetric["avg_read_latency"]))
        yield g

        g = GaugeMetricFamily("powerstore_write_latency", 'Help text', labels=['instance'])
        g.add_metric(["powerstore"], float(perfMetric["avg_write_latency"]))
        yield g

if __name__ == '__main__':
    start_http_server(8123)
    REGISTRY.register(PowerstoreCollector())
    while True:
        time.sleep(20)
