# Self-Hosting Ollama (optional, for your own practice)

This is for learners who want to run their **own** Ollama on a machine or VM and reach
it over the network or VPN in their free time. It is optional. The labs also run fully
offline against the bundled `mock-ollama` (see [START_HERE.md](START_HERE.md) Step 3b),
and in the cyberlab they use the shared GPU VM.

## The usual problem: "address already in use"

If `ollama serve` fails with "address already in use," an Ollama process is already
listening on `127.0.0.1:11434` (localhost only), which is why it is not reachable from
other machines. You do not start a second copy; you make the existing service listen on
a reachable interface.

## Recommended: set OLLAMA_HOST via systemd

```bash
sudo systemctl edit ollama
```

Add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Verify it now listens on all interfaces (you want `0.0.0.0:11434`, not `127.0.0.1:11434`):

```bash
ss -ltnp | grep 11434
```

Test from another machine on the same VPN or network:

```bash
curl http://<server-ip>:11434/api/tags
```

You should see your installed models, including `llama3.1:8b`.

## Manual alternative (no systemd)

Stop the running service first, then start it bound to all interfaces:

```bash
sudo systemctl stop ollama          # or find the process: sudo lsof -i :11434
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

## Security: bind to the VPN, not the whole internet

Prefer exposing Ollama only on the private/VPN interface rather than on every
interface. For example, bind to the private IP:

```ini
Environment="OLLAMA_HOST=<your-private-ip>:11434"
```

And make sure the host firewall or cloud security group allows TCP `11434` **only from
your VPN subnet**, never `0.0.0.0/0`. Ollama has no authentication, so anyone who can
reach the port can use the model.

## Point the labs at your Ollama

In your `.env`, set the host-side model endpoint to your server:

```
OLLAMA_HOST=http://<your-server-ip>:11434
```

Then confirm the labs can reach it:

```bash
python3 common/ollama_client.py --health
python3 scripts/verify_env.py
```
