#!/bin/bash
app="turquoise"
docker build -t ${app}:latest .
docker run -d -p 5000:5000 \
  --name=${app} \
  -v $PWD:/app ${app}
