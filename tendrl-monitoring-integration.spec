Name: tendrl-monitoring-integration
Version: 1.5.3
Release: 1%{?dist}
BuildArch: noarch
Summary: Module for Tendrl Monitoring Integration
Source0: %{name}-%{version}.tar.gz
Source1: vonage-status-panel-1.0.5-0-g4ecb061.zip
License: LGPLv2+
URL: https://github.com/Tendrl/monitoring-integration

Requires: tendrl-commons
Requires: grafana
Requires: graphite-web
Requires: python-carbon
Requires: python-whisper
Requires: python-requests
Requires: python-setuptools
Requires: python-urllib3
Requires: tendrl-grafana-plugins
Requires: python-werkzeug

BuildRequires: python-setuptools
BuildRequires: systemd

%description
Python module for Tendrl to create a new dashboard in Grafana

%package -n tendrl-grafana-plugins
Summary:	Vonage plugin for tendrl-graphana
Requires:	grafana
License:        ASL 2.0
%description -n tendrl-grafana-plugins
The vonage status panel for grafana web server.

%prep
%setup
unzip %SOURCE1
mv -f Vonage* Vonage-Grafana_Status_panel

# Remove bundled egg-info
rm -rf %{name}.egg-info

%build
%{__python} setup.py build

# Support light mode better
sed -i -e 's/green/rgb(1,167,1)/g' Vonage-Grafana_Status_panel/dist/css/status_panel.css

# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
%{__python} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install -m  0755  --directory $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration
install -m  0755  --directory $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/grafana
install -m  0755  --directory $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/grafana/dashboards
install -d %{buildroot}%{_localstatedir}/lib/grafana/plugins/
install -Dm 0640 etc/tendrl/monitoring-integration/monitoring-integration.conf.yaml.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/monitoring-integration.conf.yaml
install -Dm 0640 etc/grafana/grafana.ini $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/grafana/grafana.ini
install -Dm 0644 tendrl-monitoring-integration.service $RPM_BUILD_ROOT%{_unitdir}/tendrl-monitoring-integration.service
install -Dm 0644 etc/tendrl/monitoring-integration/graphite/graphite-web.conf.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/graphite-web.conf
install -Dm 0644 etc/tendrl/monitoring-integration/graphite/carbon.conf.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/carbon.conf
install -Dm 0644 etc/tendrl/monitoring-integration/graphite/storage-schemas.conf.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/storage-schemas.conf
cp -a etc/tendrl/monitoring-integration/grafana/dashboards/*.json $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/grafana/dashboards/
cp -r Vonage-Grafana_Status_panel %{buildroot}%{_localstatedir}/lib/grafana/plugins/

%post
if [ $1 -eq 1 ] ; then
    mv /etc/carbon/carbon.conf /etc/carbon/carbon.conf.%{name}
    mv /etc/httpd/conf.d/graphite-web.conf /etc/httpd/conf.d/graphite-web.conf.%{name}
    mv /etc/carbon/storage-schemas.conf /etc/carbon/storage-schemas.conf.%{name}
    ln -s /etc/tendrl/monitoring-integration/carbon.conf /etc/carbon/carbon.conf
    ln -s /etc/tendrl/monitoring-integration/storage-schemas.conf /etc/carbon/storage-schemas.conf
    ln -s /etc/tendrl/monitoring-integration/graphite-web.conf /etc/httpd/conf.d/graphite-web.conf
    chgrp grafana /etc/tendrl/monitoring-integration/grafana/grafana.ini
fi
systemctl enable tendrl-monitoring-integration
%systemd_post tendrl-monitoring-integration.service


%preun
if [ "$1" = 0 ] ; then
    rm -fr etc/carbon/carbon.conf /etc/httpd/conf.d/graphite-web.conf /etc/carbon/storage-schemas.conf > /dev/null 2>&1
    mv /etc/carbon/carbon.conf.%{name} /etc/carbon/carbon.conf
    mv /etc/httpd/conf.d/graphite-web.conf.%{name} /etc/httpd/conf.d/graphite-web.conf
    mv /etc/carbon/storage-schemas.conf.%{name} /etc/carbon/storage-schemas.conf
fi
%systemd_preun tendrl-monitoring-integration.service

%check
py.test -v tendrl/monitoring_integration/tests || :

%files -n tendrl-grafana-plugins
%{_localstatedir}/lib/grafana/plugins/Vonage-Grafana_Status_panel

%files -f INSTALLED_FILES
%dir %{_sysconfdir}/tendrl/monitoring-integration
%doc README.rst
%license LICENSE
%config(noreplace) %{_sysconfdir}/tendrl/monitoring-integration/grafana/dashboards/*
%config(noreplace) %{_sysconfdir}/tendrl/monitoring-integration/monitoring-integration.conf.yaml
%config(noreplace) %{_sysconfdir}/tendrl/monitoring-integration/graphite-web.conf
%config(noreplace) %{_sysconfdir}/tendrl/monitoring-integration/carbon.conf
%config(noreplace) %{_sysconfdir}/tendrl/monitoring-integration/storage-schemas.conf
%config(noreplace) %{_sysconfdir}/tendrl/monitoring-integration/grafana/grafana.ini
%attr(-, root, grafana) %{_sysconfdir}/tendrl/monitoring-integration/grafana/grafana.ini
%{_unitdir}/tendrl-monitoring-integration.service


%changelog
* Thu Oct 12 2017 Rohan Kanade <rkanade@redhat.com> - 1.5.3-1
- Release tendrl-monitoring-integration 1.5.3

* Fri Sep 15 2017 Rohan Kanade <rkanade@redhat.com> - 1.5.2-1
- Release tendrl-monitoring-integration 1.5.2

* Fri Aug 25 2017 Timothy Asir Jeyasingh <tjeyasin@redhat.com> - 1.5.1-1
- Release tendrl-monitoring-integration 1.5.1

* Wed Aug 02 2017 Timothy Asir Jeyasingh <tjeyasin@redhat.com> - 0.0.1-1
- Initial build.
