# Use the official ESP-IDF image
FROM espressif/idf:v5.2.2

# Set ESP-IDF path
ENV IDF_PATH="/opt/esp/idf/"

WORKDIR "/"

COPY src/ /src/

RUN git clone https://github.com/earlephilhower/mklittlefs.git && \
  cd mklittlefs && \
  git submodule update --init && \
  make dist && \
  ./mklittlefs --version

RUN cd mklittlefs && \
  mkdir -p ~/fs && \
  cp /src/*.py ~/fs/ && \
  ./mklittlefs -c ~/fs -b 4096 -p 256 -s 0x200000 /fs.bin


CMD ["/bin/bash"]
