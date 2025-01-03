[![</> htmx](https://raw.githubusercontent.com/bigskysoftware/htmx/master/www/static/img/htmx_logo.1.png "high power tools for HTML")](https://htmx.org)

# FastAPI/Celery WebUI For Transmission BitTorrent Client

Start:

```
uvicorn main:app --reload
```

Served at `localhost:8000`

Or reverse proxied to `<hostname>/<base route>`

```
curl -H 'Content-Type: application/json' \
      -d '{ "url":"<magnet link>"}' \
      -X POST \
      https://<hostname>/<base route>/add
```

### Transmission RPC Specification

https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md

https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html


### Docker Compose

Volumes may be removed for deployment.

If not, make sure persisted directories have appropriate permissions.

### Systemd

`sudo nano /etc/systemd/system/transmission-remote.service`

```
[Unit]
Description=transmission-remote
After=network.target

[Service]
User=<user>
Group=<group>
WorkingDirectory=/home/<user>/transmission-remote
ExecStart=/home/<user>/.pyenv/versions/3.12.8/envs/fastapi/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

`sudo nano /etc/systemd/system/transmission-celery.service`

```
[Unit]
Description=transmission-celery
After=network.target

[Service]
User=<user>
Group=<group>
WorkingDirectory=/home/<user>/transmission-celery
ExecStart=/home/<user>/.pyenv/versions/3.12.8/envs/fastapi/bin/celery -A tasks worker
Restart=always

[Install]
WantedBy=multi-user.target
```
