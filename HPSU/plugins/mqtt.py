#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# config inf conf_file (defaults):
# [MQTT]
# BROKER = localhost
# PORT = 1883
# USERNAME = 
# PASSWORD = 
# CLIENTNAME = rotex_hpsu
# PREFIX = rotex

import configparser
import requests
import sys
import os
import threading
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt


def make_client(client_id):
    try:
        return mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except (AttributeError, TypeError, ValueError):
        return mqtt.Client(client_id)


_client_lock = threading.Lock()
_client = None


def _shared_client(clientname, brokerhost, brokerport, username, password):
    # export() is instantiated fresh per job cycle, so a per-instance
    # connection would reconnect every time (previously even once per
    # value within pushValues()); reuse one process-wide connection.
    global _client
    with _client_lock:
        if _client is None:
            client = make_client(clientname)
            if username:
                client.username_pw_set(username, password=password)
            client.enable_logger()
            client.reconnect_delay_set(min_delay=1, max_delay=30)
            client.connect_async(brokerhost, port=brokerport)
            client.loop_start()
            _client = client
        return _client


class export():
    hpsu = None

    def __init__(self, hpsu=None, logger=None, config_file=None):
        self.hpsu = hpsu
        self.logger = logger
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if os.path.isfile(self.config_file):
            self.config.read(self.config_file)
        else:
            sys.exit(9)

        # MQTT hostname or IP
        if self.config.has_option('MQTT', 'BROKER'):
            self.brokerhost = self.config['MQTT']['BROKER']
        else:
            self.brokerhost = 'localhost'

        # MQTT broker port
        if self.config.has_option('MQTT', 'PORT'):
            self.brokerport = int(self.config['MQTT']['PORT'])
        else:
            self.brokerport = 1883

        # MQTT client name
        if self.config.has_option('MQTT', 'CLIENTNAME'):
            self.clientname = self.config['MQTT']['CLIENTNAME']
        else:
            self.clientname = 'rotex'
        # MQTT Username
        if self.config.has_option('MQTT', 'USERNAME'):
            self.username = self.config['MQTT']['USERNAME']
        else:
            self.username = None
            print("Username not set!!!!!")

        #MQTT Password
        if self.config.has_option('MQTT', "PASSWORD"):
            self.password = self.config['MQTT']['PASSWORD']
        else:
            self.password="None"

        #MQTT Prefix
        if self.config.has_option('MQTT', "PREFIX"):
            self.prefix = self.config['MQTT']['PREFIX']
        else:
            self.prefix = ""

        #MQTT QOS
        if self.config.has_option('MQTT', "QOS"):
            self.qos = self.config['MQTT']['QOS']
        else:
            self.qos = "0"

        self.client = _shared_client(self.clientname, self.brokerhost, self.brokerport, self.username, self.password)

    
        
    #def on_publish(self,client,userdata,mid):
    #   print("data published, mid: " + str(mid) + "\n")
    #    pass


    def pushValues(self, vars=None):
        for r in vars:
            if self.prefix:
                topic = self.prefix + "/" + r['name']
            else:
                topic = r['name']
            self.client.publish(topic, payload=r['resp'], qos=int(self.qos))

       



   
