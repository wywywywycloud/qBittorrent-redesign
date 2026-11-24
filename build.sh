#!/bin/sh
set -eu
jobs=${JOBS:-4}
for variant in icons desktop; do
    mkdir -p "$variant" source
    tar -xzf "$variant.tar.gz" --strip-components=1 -C "$variant"
    set --
    if [ "$(uname -s)" = Haiku ]; then
        patch -d "$variant" -p1 < haiku.patch
        sed -i 's/find_package(OpenSSL .* REQUIRED)/find_package(OpenSSL 3.0.2 MODULE REQUIRED)/' "$variant/cmake/Modules/CheckPackages.cmake"
        export LDFLAGS="-lnetwork"
        set -- "-DLibtorrentRasterbar_VERSION=$(pkg-config --modversion libtorrent-rasterbar)"
    fi
    rsync -rc --delete "$variant/" source/
    cmake -S source -B build -G Ninja -DCMAKE_BUILD_TYPE=Release \
        '-DCMAKE_CXX_FLAGS_RELEASE=-O1 -DNDEBUG' -DGUI=ON -DWEBUI=ON \
        -DTESTING=ON -DSTACKTRACE=OFF -DDBUS=OFF "$@"
    cmake --build build --target qbt_app check -j "$jobs"
    exe=$(find build -type f -name qbittorrent | head -1)
    test -n "$exe"
    QT_QPA_PLATFORM=offscreen python3 smoke.py "$exe" "$variant"
done
