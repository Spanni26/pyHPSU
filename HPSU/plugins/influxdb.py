#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# config inf conf_file (defaults):
# [INFLUXDB]
# HOST = hostname_or_ip
# PORT = 8086
# DB_NAME = pyHPSU

import configparser
import requests
import sys
import os
import datetime
import influxdb


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

        # influxdb hostname or IP
        if self.config.has_option('INFLUXDB', 'HOST'):
            self.influxdbhost = self.config['INFLUXDB']['HOST']
        else:
            self.influxdbhost = 'localhost'

        # influxdb port
        if self.config.has_option('INFLUXDB', 'PORT'):
            self.influxdbport = int(self.config['INFLUXDB']['PORT'])
        else:
            self.influxdbport = 8086

        # influxdb db name
        if self.config.has_option('INFLUXDB', 'DB_NAME'):
            self.influxdbname = self.config['INFLUXDB']['DB_NAME']
        else:
            self.influxdbname = "pyHPSU"

        # influxdb username
        if self.config.has_option('INFLUXDB', 'USERNAME'):
            self.influxdbusername = self.config['INFLUXDB']['USERNAME']
        else:
            self.influxdbusername = None

        # influxdb password
        if self.config.has_option('INFLUXDB', 'PASSWORD'):
            self.influxdbpassword = self.config['INFLUXDB']['PASSWORD']
        else:
            self.influxdbpassword = None

    def pushValues(self, vars=None):
        # create connection
        self.client = influxdb.InfluxDBClient(
            host=self.influxdbhost,
            port=self.influxdbport,
            username=self.influxdbusername,
            password=self.influxdbpassword
        )
        # create database if it doesn't exist
        try:
            self.databases=self.client.get_list_database()
            db_found = False
            for db in self.databases:
                if db['name'] == self.influxdbname:
                    db_found = True
            if not(db_found):
                self.client.create_database(self.influxdbname)
               
        except Exception as e:
            rc = "ko"
            self.hpsu.printd("exception", "Error : Cannot connect to database: " + str(e))
            return


        self.client.switch_database(self.influxdbname)

        for dict in vars:
            if self.hpsu.command_dict[str(dict["name"])]["unit"] == "deg":
                measurement="temperature"
            elif self.hpsu.command_dict[str(dict["name"])]["unit"] == "bar":
                measurement="pressure"
            elif self.hpsu.command_dict[str(dict["name"])]["unit"] == "lh": 
                measurement="flow" 
            elif self.hpsu.command_dict[str(dict["name"])]["unit"] == "kwh":
                measurement="energy"
            else:
                measurement="status"

            try:
                value = float(dict["resp"])
            except (ValueError, TypeError):
                value = dict["resp"]
            self.value_dict=[{
                "measurement": measurement,
                "tags":{
                },
                "fields": {
                     dict["name"] : value
                    }
                }
            ]

            if self.client.write_points(self.value_dict):
                self.hpsu.printd("Notification","Wrote " + str(dict["name"]) + " to influxdb")
            


    #if __name__ == '__main__':
    #    app = influxdb()

    #    app.exec_()
