#!/usr/bin/env bash

# NOTE Update the Version: parameter in the spec file and save it before
# NOTE running this script.
#
# This script will download and vendor both the python-proton-vpn-local-agent/Cargo.toml
# and the local_agent_rs/Cargo.toml files in order that everything both crates
# require is vendorered for the build, this is the mess that is cargo/rust.
#
# Upload both the local-agent-rs.tar.gz source tarball and the
# local-agent-rs-%{version}-vendor.tar.xz to the abf file store.

DownloadSource () {
	local FILENAME=$( basename $1 )
	if  [ ! -f "./${FILENAME}"  ]; then
		printf "${FILENAME} does not exist in package directory. \nAttempting to download..\n"
		if curl -o /dev/null -sfL -r 0-0 "${1}"; then
			printf "File exists on remote, downloading..\n"
			curl -o "${FILENAME}" -L $1
		else
			printf "URI/Archive: $FILENAME does not exist on remote server. \nCheck package Name or oname define in spec file.\n\n"
			exit 0
		fi
else
	printf "${FILENAME} exists in package directory, skipping download attempt.\n"
fi
}

#Get the package source URL from the spec file
PACKAGE_SRC=$(awk -F " " '/^Source:|^Source0:/ {print $2}' *.spec)
# Get version and defined oname from spec file
VERSION=$(awk -F ":" '/Version/ {print $2}' python-proton-vpn-local-agent.spec)
# Remove leading and trailing whitespace from VERSION
VERSION="${VERSION#"${VERSION%%[![:space:]]*}"}"
VERSION="${VERSION%"${VERSION##*[![:space:]]}"}"
ONAME=$(awk -F " " '/%define oname/ {print $3}' python-proton-vpn-local-agent.spec)

PACKAGE_NAME=$(awk -F ":" '/Name/ {print $2}' *.spec)
# Remove leading and trailing whitespace from PACKAGE
PACKAGE_NAME="${PACKAGE_NAME#"${PACKAGE_NAME%%[![:space:]]*}"}"
PACKAGE_NAME="${PACKAGE_NAME%"${PACKAGE_NAME##*[![:space:]]}"}"

PACKAGE_SRC=$(echo ${PACKAGE_SRC} | sed -e 's,\%{oname},'${ONAME}',g')
PACKAGE_SRC=$(echo ${PACKAGE_SRC} | sed -e 's,\%{version},'${VERSION}',g')
echo $PACKAGE_SRC

DownloadSource ${PACKAGE_SRC}

tar -xf ${ONAME}-${VERSION}.tar.gz

cd ./${ONAME}-${VERSION}/python-proton-vpn-local-agent

printf "Creating vendor archive: $ONAME-$VERSION-vendor.tar.xz \n"
# vendor the crate and its dependency crate
cargo vendor  -s ../local_agent_rs/Cargo.toml
# archive the vendor dir into the spec file root
tar -cJf ../../$ONAME-$VERSION-vendor.tar.xz ./vendor
printf "Completed creating archive: $ONAME-$VERSION-vendor.tar.xz \n"
# remove the vendor folder and contents generated during vendoring
# if you need to see what is vendored look inside the archive.
rm -rf ./vendor
