module.exports = {
  apps: [{
    name: 'vps-bot-manager',
    script: './main.py',
    interpreter: '/usr/bin/python3',
    autorestart: true,
    max_restarts: 5,
    min_uptime: '10s',
    env: {
      PYTHONUNBUFFERED: '1'
    },
    log_file: './logs/manager-out.log',
    error_file: './logs/manager-error.log',
    out_file: './logs/manager-out.log'
  }]
};
