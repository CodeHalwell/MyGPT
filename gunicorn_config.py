import os
import multiprocessing
from datetime import datetime

# Server socket
bind = "0.0.0.0:5000"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120  # Increased timeout for long-running requests
keepalive = 5

# Logging
logformat = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'gunicorn_process'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (configure in production if needed)
keyfile = None
certfile = None

# Security headers
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Additional security settings
forwarded_allow_ips = '*'
proxy_allow_ips = '*'
proxy_protocol = True

# Error handling
capture_output = True
enable_stdio_inheritance = True

def worker_exit(server, worker):
    """Log worker exit"""
    server.log.info(f'Worker exited (pid: {worker.pid})')

def worker_abort(worker):
    """Log worker abort"""
    worker.log.info(f'Worker aborted (pid: {worker.pid})')

def on_starting(server):
    """Log server start"""
    server.log.info('Gunicorn server is starting')

def on_exit(server):
    """Log server exit"""
    server.log.info('Gunicorn server is shutting down')

def post_worker_init(worker):
    """Initialize worker"""
    worker.log.info(f'Worker initialized (pid: {worker.pid})')
