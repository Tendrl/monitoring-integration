Monitoring-Integration
=======================

Installation Details
--------------------

The following steps outlines the procedure to install monitoring-intregration component.

**Note :**

  All the commands mentioned below are run as a regular user that has ``sudo``
  privileges.


1) **Conifgure Graphite**


   ::

     $ /usr/lib/python2.7/site-packages/graphite/manage.py syncdb 
       --noinput chown apache:apache /var/lib/graphite-web/graphite.db



2) **Installing Monitoring-Integration**


   **Note**
    
     Make sure tendrl repositories are enabled.
     https://github.com/Tendrl/documentation/wiki/Tendrl-Package-Installation-Reference

   ::
    
         $ yum install tendrl-monitoring-integration



3) **Start/Restart server to load new configurations**


* Enable and start carbon-cache service

  ::

      $ systemctl enable carbon-cache
      $ systemctl start carbon-cache


* Start grafana server
  
  ::

      $ systemctl daemon-reload
      $ systemctl enable grafana-server.service
      $ systemctl start grafana-server

  
* Restart httpd

  ::

      $ systemctl restart httpd


4) **Configuring Monitoring-Integration**


* Open monitoring-integration.conf.yaml:

  ::
   
      $ vi /etc/tendrl/monitoring-integration/monitoring-integration.conf.yaml 

* Update datasource_host with IP of graphite server:

  ::
  
      datasource_host = <IP of graphite server>

  **Note** :
    
      Do not provide localost or 127.0.0.1.



5) **Running Monitoring-Integration**


* Run monitoring-integration

  ::

      $ tendrl-monitoring-integration



6) **Open Grafana**


* Open the following URL in the browser

  ::

     http://<IP of the server>:3000
