Name: tendrl-monitoring-integration
Version: 1.0.0
Release: 1%{?dist}
BuildArch: noarch
Summary: Module for Tendrl Monitoring Integration
Source0: %{name}-%{version}.tar.gz
License: LGPLv2+
URL: https://github.com/Tendrl/monitoring-integration

#Requires: tendrl-commons
Requires: grafana
Requires: graphite-web
Requires: python-carbon
Requires: python-whisper
Requires: python-requests
Requires: python-maps
Requires: python-ruamel-yaml
Requires: python-setuptools
Requires: python-urllib3

BuildRequires: python-setuptools

%description
Python module for Tendrl to create a new dashboard in Grafana

%prep
%setup

# Remove bundled egg-info
rm -rf %{name}.egg-info

%build
%{__python} setup.py build

# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%install
%{__python} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install -m  0755  --directory $RPM_BUILD_ROOT%{_var}/log/tendrl/monitoring-integration
install -m  0755  --directory $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration
install -m  0755  --directory $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/grafana
install -m  0755  --directory $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/grafana/dashboards
#install -Dm 0644 monitoring-integration.service $RPM_BUILD_ROOT%{_unitdir}/monitoring-integration.service
install -Dm 0644 etc/grafana/grafana.ini $RPM_BUILD_ROOT%{_sysconfdir}/grafana/grafana.ini
install -Dm 0644 etc/tendrl/monitoring-integration/monitoring-integration.conf.yaml.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/monitoring-integration.conf.yaml
install -Dm 0644 etc/tendrl/monitoring-integration/graphite/graphite-web.conf.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/graphite-web.conf
install -Dm 0644 etc/tendrl/monitoring-integration/graphite/carbon.conf.sample $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/carbon.conf
cp -a etc/tendrl/monitoring-integration/grafana/dashboards/*.json $RPM_BUILD_ROOT%{_sysconfdir}/tendrl/monitoring-integration/grafana/dashboards/

%post
if [ $1 -eq 1 ] ; then
    mv /etc/carbon/carbon.conf /etc/carbon/carbon.conf.%{name}
    mv /etc/httpd/conf.d/graphite-web.conf /etc/httpd/conf.d/graphite-web.conf.%{name}
    ln -s /etc/tendrl/monitoring-integration/carbon.conf /etc/carbon/carbon.conf
    ln -s /etc/tendrl/monitoring-integration/graphite-web.conf /etc/httpd/conf.d/graphite-web.conf
    mv /etc/grafana/grafana.ini.rpmnew /etc/grafana/grafana.ini
fi

%pre
if [ $1 -eq 1 ] ; then
    mv /etc/grafana/grafana.ini /etc/grafana/grafana.ini.orig
fi

%preun
if [ "$1" = 0 ] ; then
    rm -fr etc/carbon/carbon.conf /etc/httpd/conf.d/graphite-web.conf > /dev/null 2>&1
    mv /etc/carbon/carbon.conf.%{name} /etc/carbon/carbon.conf
    mv /etc/httpd/conf.d/graphite-web.conf.%{name} /etc/httpd/conf.d/graphite-web.conf
    mv /etc/grafana/grafana.ini.orig /etc/grafana/grafana.ini
fi

%postun
%check
py.test -v tendrl/monitoring_integration/tests || :

%files -f INSTALLED_FILES
%dir %{_var}/log/tendrl/monitoring-integration
%dir %{_sysconfdir}/tendrl/monitoring-integration
%doc README.rst
%license LICENSE
%config(noreplace) %{_sysconfdir}/tendrl/monitoring-integration/grafana/dashboards/*
%config(noreplace) %{_sysconfdir}/tendrl/monitoring-integration/monitoring-integration.conf.yaml
%config(noreplace) %{_sysconfdir}/tendrl/monitoring-integration/graphite-web.conf
%config(noreplace) %{_sysconfdir}/tendrl/monitoring-integration/carbon.conf
%config(noreplace) %{_sysconfdir}/grafana/grafana.ini
#%{_unitdir}//monitoring-integration.service

%changelog
* Wed Aug 02 2017 Timothy Asir Jeyasingh <tjeyasin@redhat.com> - 0.0.1-1
- Initial build.
