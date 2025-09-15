# Production Gunicorn configuration for AWS App Runner
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv('WORKERS', '2'))

# Worker processes
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'tadaro-investment-bot'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = 'appuser'
group = 'appgroup'
preload_app = True

# SSL (handled by AWS App Runner)
forwarded_allow_ips = '*'
proxy_allow_ips = '*'