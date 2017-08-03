

Monitoring-Integration
=======================

Functionalities
----------------

- Create a new dashboard in Grafana


Prerequisites
--------------

* Grafana instance is set-up and running on the server node.

* Graphite instance is set-up and running on the same server node.

* Monitoring-Integration is installed on same server node.


Usage Details
--------------

**Note :**

  Configuration file monitoring-integration.conf.yaml needed by monitoring-integration
  is present under
 
  ' /etc/tendrl/monitoring-integration/'
 
 Default dashboards that are to be created in grafana are present under

  ' /etc/tendrl/monitoring-integration/grafana/dashboards/ '	  

* **Restart server to load new configurations**

  * service grafana-server restart
  
  * service httpd restart


* **Development setup**

  * Create a json file in /etc/tendrl/monitoring-integration/grafana/dashboards/ and provide json
    for the dashboard that is to be created.

  * Provide the file-name of the json file created in above step under "dashboards"
    in /etc/tendrl/monitoring-integration/monitoring-integration.conf.yaml.

  * Make one of the dashboards listed under "dashboards" as home_dashboard.

  * Provide grafana instance's credential under "credentials" in monitoring-integration.conf.yaml file

  * Provide name of datasource to be created in grafana under "datasource_name" in
    monitoring-integration.conf.yaml file
    
  * Provide host ip-address of datasource to be created in grafana under "datasource_host" in
    monitoring-integration.conf.yaml file
    
    **Note**
        Please provide the ip of the server node where graphite is installed.
	[ Do not provide localhost or 127.0.0.1 ]

  * Make sure a datasource with same name as given in monitoring-integration.conf.yaml file
    doesnot exist in grafana.

  * By default true is passed under "isDefault" in monitoring-integration.conf.yaml
    to set the datasource as the default datasource in grafana.

  * Run monitoring-integration

    ::

        $ tendrl-monitoring-integration
