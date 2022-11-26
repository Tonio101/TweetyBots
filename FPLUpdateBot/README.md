## FPL Updates

TODO

## Systemd Service

Process controlled and supervised by systemd.

```bash
sudo cp twitterbot.service /etc/systemd/system/
sudo systemctl start twitterbot.service
sudo systemctl status twitterbot.service
```

After confirming that things are working, enable the service to<br>
automatically start the process at start up.

```bash
sudo systemctl enable twitterbot.service
```
