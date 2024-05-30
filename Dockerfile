FROM python:3-alpine
RUN apk update
RUN apk upgrade
RUN apk add git

# Get and build ngn/k
RUN apk add make
RUN apk add clang
RUN git clone https://codeberg.org/ngn/k.git
RUN cd k && make CC=clang-17

# Get and run Mesh Spreadsheet backend server
RUN pip install websockets
RUN git clone https://github.com/chrispsn/mesh-spreadsheet.git
WORKDIR /mesh-spreadsheet
RUN echo "PATH_NGN_K_BINARY = \"/k/k\"" > vars.py
RUN echo "PATH_TEMP_SHEET = \"tempsheet.k\"" >> vars.py
CMD python server.py
