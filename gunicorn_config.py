import os
import multiprocessing
from datetime import datetime

# Server socket
bind = "0.0.0.0:3000"  # Standard Replit port

# Worker processes - optimized for Replit's environment
workers = 2  # Optimized for Replit's environment
worker_class = 'gevent'  # For better async support
worker_connections = 1000
timeout = 120  # Increased timeout for long-running requests
keepalive = 5

# Performance tuning
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30

# Logging
logformat = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Proxy settings for Replit
forwarded_allow_ips = '*'
proxy_protocol = False
proxy_allow_ips = '*'

# Security headers
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Event handlers
def when_ready(server):
    """Log when server is ready"""
    server.log.info(f'Gunicorn server is ready. Listening at: {bind}')

def on_starting(server):
    """Log server start"""
    server.log.info('Gunicorn server is starting up')

def on_reload(server):
    """Log server reload"""
    server.log.info('Gunicorn server is reloading')

def on_exit(server):
    """Log server exit"""
    server.log.info('Gunicorn server is shutting down')

def worker_int(worker):
    """Log worker interrupt"""
    worker.log.info(f'Worker interrupted (pid: {worker.pid})')

def worker_abort(worker):
    """Log worker abort"""
    worker.log.info(f'Worker aborted (pid: {worker.pid})')

def pre_fork(server, worker):
    """Pre-fork logging"""
    server.log.info(f'Pre-forking worker (pid: {os.getpid()})')

def post_fork(server, worker):
    """Post-fork logging"""
    server.log.info(f'Worker forked (pid: {worker.pid})')

def worker_exit(server, worker):
    """Log worker exit"""
    server.log.info(f'Worker exited (pid: {worker.pid})')
