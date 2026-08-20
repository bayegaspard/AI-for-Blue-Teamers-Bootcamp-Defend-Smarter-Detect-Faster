FROM debian:bookworm-slim
# Attacker toolbox for Module 2 (detection) and Module 5 (capstone).
# Lightweight alternative to the full Kali VM so the lab runs anywhere.
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      hydra nmap curl ca-certificates sshpass python3 python3-requests iputils-ping netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/attacks
COPY scripts/ /opt/attacks/
COPY wordlists/ /opt/attacks/wordlists/
RUN chmod +x /opt/attacks/*.sh || true
# Keep the container alive so students can `docker exec` into it.
CMD ["sleep", "infinity"]
