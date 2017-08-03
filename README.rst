

Monitoring-Integration
=======================


Functionalities
----------------

- Create a new dashboard in Grafana


Environment Setup
-----------------

#. Clone the monitoring-integration repository

    ::

        $ git clone https://github.com/Tendrl/monitoring-integration.git
	$ cd monitoring-integration


**Note :**

      All the commands mentioned below are run as a regular user that has ``sudo``
      privileges.
      These commands are assumed to be run from a single directory, which
      contains the code of monitoring-integration.

#. Install python pip


   https://pip.pypa.io/en/stable/installing/


#. Install python dependencies

    ::

        $ python setup.py install


#. Install Grafana


    http://docs.grafana.org/installation/


#. Configure grafana for anonymous login.

    ::

        $ cp etc/grafana/grafana.ini /etc/grafana/.

    .. note::

       	  This will overwrite present grafana.ini.

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

  If configuration file is not present.

    ::

        $ cp etc/tendrl/monitoring-integration/monitoring-integration.conf.yaml.sample
          /etc/tendrl/monitoring-integration/monitoring-integration.conf.yaml
	  
  Default dashboards that are to be created in grafana are present under

  ' /etc/tendrl/monitoring-integration/grafana/dashboards/ '

  If the dashboards are not present.

    ::

        $ mkdir /etc/tendrl/monitoring-integration/grafana
        $ mkdir /etc/tendrl/monitoring-integration/grafana/dashboards
        $ cp etc/tendrl/monitoring-integration/grafana/dashboards/* 
          /etc/tendrl/monitoring-integration/grafana/dashboards/.


* **Development setup**

  * Create a json file in /etc/tendrl/monitoring-integration/grafana/dashboards/ and provide json
    for the dashboard that is to be created.

  * Provide the file-name of the json file created in above step under "dashboards"
    in /etc/tendrl/monitoring-integration/monitoring-integration.conf.yaml.

  * Make one of the dashboards listed under "dashboards" as home_dashboard.

  * Provide grafana instance's credential under "credentials" in monitoring-integration.conf.yaml file

  * Provide name of datasource to be created in grafana under "datasource_name" in
    monitoring-integration.conf.yaml file

  * Make sure a datasource with same name as given in monitoring-integration.conf.yaml file
    doesnot exist in grafana.

  * By default true is passed under "isDefault" in monitoring-integration.conf.yaml
    to set the datasource as the default datasource in grafana.

  * Follow the commands provided below to run __init__.py file to create dashboards and datasource
    in grafana.

    ::

        $ cd tendrl/monitoring_integration/
        $ python __init__.py	
