

Monitoring-Integration
=======================


Functionalities
----------------

- Create new dashboard in Grafana


Prerequisites
-----------------

#. Install Grafana. 
   Follow the steps provided in below mentioned doc to install grafana.

    http://docs.grafana.org/installation/rpm/

Usage Details
--------------

**Note :**

  All the commands mentioned below are run as a regular user that has ``sudo``
  privileges.
      
  Configuration file monitoring-integration.conf.yaml needed by monitoring-integration
  is present under
 
  ' /etc/tendrl/monitoring-integration/'

  Default dashboards that are to be created in grafana are present under

  ' /etc/tendrl/monitoring-integration/grafana/dashboards/ '



* **Restart server to load new configurations**

  * Start grafana server
  
    ::

        $ service grafana-server start  
  
  * Restart httpd

    ::

        $ service httpd restart  

* **Installing Monitoring-Integration**

    ::
    
        $ yum install tendrl-monitoring-integration
	
   **Note**
        Make sure tendrl repositories are enabled.
	https://github.com/Tendrl/documentation/wiki/Tendrl-Package-Installation-Reference

* **Running Monitoring-Integration**

  * Provide host ip-address of datasource to be created in grafana under "datasource_host" in
    monitoring-integration.conf.yaml file
    
    **Note**
        Please provide the ip of server node where graphite is installed. Do not provide
	localost or 127.0.0.1 even if the graphite is installed on the local server.

  * Run monitoring-integration

    ::

        $ tendrl-monitoring-integration
