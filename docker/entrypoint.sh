#!/bin/sh
. /repo/docker/common

# - - sanity checks - - #
if ! mountpoint /data >/dev/null 2>&1; then
    perr "/data is not bind mounted, exiting."
fi

for mmdb in ASN City; do 
    if [ ! -f "/data/GeoLite2-${mmdb}.mmdb" ]; then
        perr "/data does not contain GeoLite2-${mmdb}.mmdb."
    fi
done

# - - hand over - - #
pinfo "setting permissions"
chown -Rh wya:wya /data
evalret

pinfo "starting wya"
exec su wya -c 'wya'
