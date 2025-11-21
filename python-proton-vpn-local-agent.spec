%global debug_package %{nil}
%define oname local-agent-rs
%bcond_without tests

# disable cargo tests on abf, each 'cargo test' is a separate compile by
# itself which results in the builders taking an excessive/unacceptable amount
# of time to complete package builds, they can be ran to locally check packages.
%bcond_with cargotests

# NOTE run ./cargo-vendor.sh script after obtaining new source tarball to
# NOTE vendor all the crates for both rust packages that are in the
# NOTE source tarball.

Name:		python-proton-vpn-local-agent
Version:	1.6.0
Release:	2
Source0:	https://github.com/ProtonVPN/local-agent-rs/archive/%{version}/%{oname}-%{version}.tar.gz
Source1:    %{oname}-%{version}-vendor.tar.xz
Summary:	Proton VPN local agent written in Rust
URL:		https://github.com/ProtonVPN/local-agent-rs
License:	GPL-3.0-only
Group:		System/Libraries

BuildRequires:	cargo
BuildRequires:  rust-packaging
%if %{with tests}
BuildRequires:	python
BuildRequires:	python%{pyver}dist(pytest)
BuildRequires:	python%{pyver}dist(pytest-asyncio)
%endif
Requires:	proton-vpn-local-agent = %{version}-%{release}
Provides:	python%{pyver}dist(proton-vpn-local-agent) = %{version}-%{release}

%description

%package -n proton-vpn-local-agent
Summary:	The library file for the Proton VPN local agent

%description -n proton-vpn-local-agent
The library file for the Proton VPN local agent.

%prep
%autosetup -n %{oname}-%{version} -p1 -a1
%cargo_prep -v vendor

cd %{name}
tar -zxf %{SOURCE1}
mkdir -p python-proton-vpn-local-agent/.cargo
mkdir -p local_agent_rs/.cargo

# rust packaging is an abhorrent mess, so we have to do this for each rust-
# cargo.toml location and repath the output that cargo gives us during the
# cargo vendoring run, see cargo-vendor.sh.

# vendorify the python-libpython_proton_vpn_local_agent config.toml
cat >> python-proton-vpn-local-agent/.cargo/config.toml << EOF
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "../vendor"

EOF

# vendorify the local_agent_rs config.toml
cat >> local_agent_rs/.cargo/config.toml << EOF
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "../vendor"

EOF

%build
cd %{name}
# --frozen is euivalent to using both --locked and --offline
cargo build --release --frozen
#mv target/release/libpython_proton_vpn_local_agent.so local_agent.so

%install
install -d %{buildroot}%{python_sitearch}/{proton,proton/vpn};
install -Dm 0644 %{_builddir}/%{oname}-%{version}/%{name}/target/release/libpython_proton_vpn_local_agent.so %{buildroot}/%{_libdir}/proton/local_agent.so
ln -sr %{buildroot}%{_libdir}/proton/local_agent.so  %{buildroot}%{python_sitearch}/proton/vpn/local_agent.so;

%if %{with tests}
%check
# set env variables for pytest CI
export CI=true
# set pythonpath so build lib is locatable in path
export PYTHONPATH="%{buildroot}%{python_sitearch}:${PWD}"

%if %{with cargotests}
# cargo test local_agent_rs
cd local_agent_rs
cargo test --frozen --all-features
cd ..
%endif

# test python-proton-vpn-local-agent
cd %{name}
%if %{with cargotests}
# cargo test python-proton-vpn-local-agent
cargo test --frozen --all-features
%endif

# python tests
%{__python} -m pytest tests/
%endif

%files
%dir %{python_sitearch}/proton
%dir %{python_sitearch}/proton/vpn
%{python_sitearch}/proton/vpn/local_agent.so

%files -n proton-vpn-local-agent
%dir %{_libdir}/proton
%{_libdir}/proton/local_agent.so
