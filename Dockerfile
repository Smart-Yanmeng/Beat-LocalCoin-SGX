FROM trubft:ACS

WORKDIR /app

# Use Chinese mirrors
RUN echo "deb http://mirrors.aliyun.com/debian/ bullseye main" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security bullseye-security main" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ bullseye-updates main" >> /etc/apt/sources.list

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget bison cmake flex libflint-dev libmpfr-dev \
    && rm -rf /var/lib/apt/lists/*

# Install PBC
RUN wget -q https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz -O /tmp/pbc.tar.gz && \
    cd /tmp && tar xzf pbc.tar.gz && \
    cd pbc-0.5.14 && ./configure && make -j$(nproc) && make install && \
    ldconfig && \
    rm -rf /tmp/pbc* || echo "PBC install failed, continuing..."

# Build charm
RUN git clone https://github.com/JHUISI/charm.git /tmp/charm && \
    cd /tmp/charm && \
    git reset --hard be9587ccdd4d61c591fb50728ebf2a4690a2064f && \
    sed -i 's/^CFLAGS.*/CFLAGS="-fcommon"/' configure.sh && \
    sed -i 's/^LDFLAGS.*/LDFLAGS="-fcommon"/' configure.sh && \
    ./configure.sh && \
    CFLAGS="-fcommon" LDFLAGS="-fcommon" make && \
    make install && \
    rm -rf /tmp/charm

# Cleanup
RUN apt-get purge -y wget bison cmake flex && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com && \
    pip uninstall -y pycrypto pycryptodome && \
    pip install gevent pycryptodome ecdsa cryptography gipc

ENV PYTHONPATH=/app/adaptive:$PYTHONPATH
ENV LIBRARY_PATH=/usr/local/lib:$LIBRARY_PATH
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
