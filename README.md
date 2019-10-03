Auto-scaling cluster system for discord.py

IPC is optional, but requires `websockets==8.0.2`

## How to use
Replace the various token parts with your bots token, then run `launcher.py` and let the magic happen.

Example log output:
```cs
[2019-10-02 19:58:53,003 Cluster#Launcher/INFO] Hello, world!
[2019-10-02 19:58:53,096 Cluster#Launcher/INFO] Successfully got shard count of 1 ((200, 'OK'))
[2019-10-02 19:58:53,097 Cluster#Launcher/INFO] Preparing 4 clusters
[2019-10-02 19:58:53,098 Cluster#Alpha/INFO] Initialized with shard ids [0, 1, 2, 3], total shards 16
[2019-10-02 19:58:53,098 Cluster#Beta/INFO] Initialized with shard ids [4, 5, 6, 7], total shards 16
[2019-10-02 19:58:53,099 Cluster#Charlie/INFO] Initialized with shard ids [8, 9, 10, 11], total shards 16
[2019-10-02 19:58:53,100 Cluster#Delta/INFO] Initialized with shard ids [12, 13, 14, 15], total shards 16
[2019-10-02 19:58:53,100 Cluster#Launcher/INFO] Starting Cluster#Alpha
[2019-10-02 19:58:53,107 Cluster#Alpha/INFO] Process started with PID 24030
[2019-10-02 19:59:59,573 Cluster#Alpha/INFO] Process started successfully
[2019-10-02 19:59:59,574 Cluster#Launcher/INFO] Done!
[2019-10-02 19:59:59,575 Cluster#Launcher/INFO] Starting Cluster#Beta
[2019-10-02 19:59:59,588 Cluster#Beta/INFO] Process started with PID 24054
[2019-10-02 20:01:04,002 Cluster#Beta/INFO] Process started successfully
[2019-10-02 20:01:04,003 Cluster#Launcher/INFO] Done!
[2019-10-02 20:01:04,004 Cluster#Launcher/INFO] Starting Cluster#Charlie
[2019-10-02 20:01:04,017 Cluster#Charlie/INFO] Process started with PID 24083
[2019-10-02 20:02:09,205 Cluster#Charlie/INFO] Process started successfully
[2019-10-02 20:02:09,217 Cluster#Launcher/INFO] Done!
[2019-10-02 20:02:09,218 Cluster#Launcher/INFO] Starting Cluster#Delta
[2019-10-02 20:02:09,238 Cluster#Delta/INFO] Process started with PID 24106
[2019-10-02 20:03:13,711 Cluster#Delta/INFO] Process started successfully
[2019-10-02 20:03:13,713 Cluster#Launcher/INFO] Done!
[2019-10-02 20:03:13,713 Cluster#Launcher/INFO] All clusters launched
[2019-10-02 20:03:13,714 Cluster#Launcher/INFO] Startup completed in 260.7107082050061s
```
### Extra Features
> Automatically restarts clusters that died with a non-zero exit status

```cs
[2019-10-02 20:04:58,805 Cluster#Launcher/INFO] Cluster#Alpha exited with code -1
[2019-10-02 20:04:58,806 Cluster#Launcher/INFO] Restarting cluster#Alpha
[2019-10-02 20:04:58,811 Cluster#Alpha/INFO] Process started with PID 24149
[2019-10-02 20:06:03,831 Cluster#Alpha/INFO] Process started successfully
```
> Will turn off if all clusters close with exit code 0
```cs
[2019-10-02 20:07:13,901 Cluster#Launcher/INFO] Cluster#Alpha found dead
[2019-10-02 20:07:13,903 Cluster#Alpha/INFO] Shutting down with signal <Signals.SIGINT: 2>
[2019-10-02 20:07:13,903 Cluster#Launcher/INFO] Cluster#Beta found dead
[2019-10-02 20:07:13,904 Cluster#Beta/INFO] Shutting down with signal <Signals.SIGINT: 2>
[2019-10-02 20:07:13,904 Cluster#Launcher/INFO] Cluster#Charlie found dead
[2019-10-02 20:07:13,905 Cluster#Charlie/INFO] Shutting down with signal <Signals.SIGINT: 2>
[2019-10-02 20:07:13,905 Cluster#Launcher/INFO] Cluster#Delta found dead
[2019-10-02 20:07:13,905 Cluster#Delta/INFO] Shutting down with signal <Signals.SIGINT: 2>
[2019-10-02 20:07:18,911 Cluster#Launcher/WARNING] All clusters appear to be dead
[2019-10-02 20:07:18,914 Cluster#Launcher/INFO] Shutting down clusters
```

> Proper KeyboardInterrupt handling and cleanup
