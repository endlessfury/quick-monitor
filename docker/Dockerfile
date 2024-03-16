FROM ubuntu:noble

RUN apt update && apt install python3 -y && apt install jq -y && apt install curl -y && apt install nginx -y

EXPOSE 80/tcp
WORKDIR /root
CMD ["/bin/bash","-c","/root/script.sh"]
USER root

COPY generatehtml.py /root/generatehtml.py
COPY script.sh /root/script.sh
RUN chmod u+x /root/script.sh
