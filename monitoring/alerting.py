"""
Alerting System
Monitor system health and send alerts when issues are detected
"""

import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from collections import defaultdict
import threading
import time

logger = logging.getLogger(__name__)

class AlertManager:
    """Manage system alerts and notifications"""
    
    def __init__(self, app=None):
        self.app = app
        self.alert_history = []
        self.alert_cooldowns = defaultdict(datetime)  # Prevent spam
        self.cooldown_period = timedelta(minutes=30)  # 30 minutes between same alerts
        self._lock = threading.Lock()
        
        # Alert thresholds
        self.thresholds = {
            'response_time': 5.0,  # seconds
            'error_rate': 10.0,    # percentage
            'memory_usage': 85.0,  # percentage
            'disk_usage': 90.0,    # percentage
            'cpu_usage': 80.0,     # percentage
            'api_failure_rate': 20.0  # percentage
        }
    
    def check_and_alert(self, health_status: Dict[str, Any], performance_data: Dict[str, Any]):
        """Check system status and send alerts if necessary"""
        alerts_to_send = []
        
        # Check overall health
        if health_status.get('overall_status') != 'healthy':
            alert = self._create_health_alert(health_status)
            if self._should_send_alert(alert['type']):
                alerts_to_send.append(alert)
        
        # Check specific components
        checks = health_status.get('checks', {})
        
        # Database alerts
        if 'database' in checks and not checks['database'].get('healthy'):
            alert = self._create_database_alert(checks['database'])
            if self._should_send_alert(alert['type']):
                alerts_to_send.append(alert)
        
        # API services alerts
        if 'api_services' in checks and not checks['api_services'].get('healthy'):
            alert = self._create_api_alert(checks['api_services'])
            if self._should_send_alert(alert['type']):
                alerts_to_send.append(alert)
        
        # Resource alerts
        if 'memory' in checks and not checks['memory'].get('healthy'):
            alert = self._create_memory_alert(checks['memory'])
            if self._should_send_alert(alert['type']):
                alerts_to_send.append(alert)
        
        if 'disk_space' in checks and not checks['disk_space'].get('healthy'):
            alert = self._create_disk_alert(checks['disk_space'])
            if self._should_send_alert(alert['type']):
                alerts_to_send.append(alert)
        
        # Performance alerts
        if performance_data:
            perf_alerts = self._check_performance_alerts(performance_data)
            for alert in perf_alerts:
                if self._should_send_alert(alert['type']):
                    alerts_to_send.append(alert)
        
        # Send all alerts
        for alert in alerts_to_send:
            self._send_alert(alert)
    
    def _create_health_alert(self, health_status: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert for general health issues"""
        status = health_status.get('overall_status', 'unknown')
        failed_checks = health_status.get('failed_checks', 0)
        total_checks = health_status.get('total_checks', 0)
        
        return {
            'type': 'system_health',
            'severity': 'critical' if status == 'unhealthy' else 'warning',
            'title': f'System Health: {status.upper()}',
            'message': f'{failed_checks} out of {total_checks} health checks failed',
            'details': health_status,
            'timestamp': datetime.utcnow()
        }
    
    def _create_database_alert(self, db_check: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert for database issues"""
        return {
            'type': 'database_error',
            'severity': 'critical',
            'title': 'Database Connection Failed',
            'message': db_check.get('error', 'Unknown database error'),
            'details': db_check,
            'timestamp': datetime.utcnow()
        }
    
    def _create_api_alert(self, api_check: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert for API service issues"""
        healthy_apis = api_check.get('healthy_apis', 0)
        total_apis = api_check.get('total_apis', 0)
        
        return {
            'type': 'api_services',
            'severity': 'warning',
            'title': 'External API Services Issues',
            'message': f'{healthy_apis}/{total_apis} APIs are operational',
            'details': api_check,
            'timestamp': datetime.utcnow()
        }
    
    def _create_memory_alert(self, memory_check: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert for memory issues"""
        used_percent = memory_check.get('used_percent', 0)
        available_gb = memory_check.get('available_gb', 0)
        
        return {
            'type': 'high_memory',
            'severity': 'warning',
            'title': 'High Memory Usage',
            'message': f'Memory usage at {used_percent}% ({available_gb}GB available)',
            'details': memory_check,
            'timestamp': datetime.utcnow()
        }
    
    def _create_disk_alert(self, disk_check: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert for disk space issues"""
        used_percent = disk_check.get('used_percent', 0)
        free_gb = disk_check.get('free_gb', 0)
        
        return {
            'type': 'low_disk_space',
            'severity': 'critical' if used_percent > 95 else 'warning',
            'title': 'Low Disk Space',
            'message': f'Disk usage at {used_percent}% ({free_gb}GB free)',
            'details': disk_check,
            'timestamp': datetime.utcnow()
        }
    
    def _check_performance_alerts(self, performance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for performance-related alerts"""
        alerts = []
        
        # High error rate
        error_rate = performance_data.get('error_rate', 0)
        if error_rate > self.thresholds['error_rate']:
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'warning',
                'title': 'High Error Rate',
                'message': f'Error rate is {error_rate}% (threshold: {self.thresholds["error_rate"]}%)',
                'details': performance_data,
                'timestamp': datetime.utcnow()
            })
        
        # Slow response times
        avg_response = performance_data.get('average_response_time', 0)
        if avg_response > self.thresholds['response_time']:
            alerts.append({
                'type': 'slow_response',
                'severity': 'warning',
                'title': 'Slow Response Times',
                'message': f'Average response time is {avg_response}s (threshold: {self.thresholds["response_time"]}s)',
                'details': performance_data,
                'timestamp': datetime.utcnow()
            })
        
        return alerts
    
    def _should_send_alert(self, alert_type: str) -> bool:
        """Check if we should send this alert (respects cooldown)"""
        with self._lock:
            last_sent = self.alert_cooldowns.get(alert_type)
            if last_sent is None or datetime.utcnow() - last_sent > self.cooldown_period:
                self.alert_cooldowns[alert_type] = datetime.utcnow()
                return True
            return False
    
    def _send_alert(self, alert: Dict[str, Any]):
        """Send alert via configured channels"""
        with self._lock:
            # Add to alert history
            self.alert_history.append(alert)
            if len(self.alert_history) > 100:  # Keep last 100 alerts
                self.alert_history = self.alert_history[-100:]
        
        # Log alert
        severity = alert['severity'].upper()
        logger.error(f"ALERT [{severity}] {alert['title']}: {alert['message']}")
        
        # Send email if configured
        if self.app and self._is_email_configured():
            self._send_email_alert(alert)
        
        # Could add other notification channels here (Slack, Discord, etc.)
    
    def _is_email_configured(self) -> bool:
        """Check if email is properly configured"""
        return all([
            self.app.config.get('MAIL_SERVER'),
            self.app.config.get('MAIL_USERNAME'),
            self.app.config.get('MAIL_PASSWORD')
        ])
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send alert via email"""
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.app.config['MAIL_USERNAME']
            msg['To'] = self.app.config.get('ALERT_EMAIL', self.app.config['MAIL_USERNAME'])
            msg['Subject'] = f"[Investment Bot Alert] {alert['title']}"
            
            # Email body
            body = self._format_alert_email(alert)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.app.config['MAIL_SERVER'], self.app.config['MAIL_PORT'])
            if self.app.config.get('MAIL_USE_TLS'):
                server.starttls()
            
            server.login(self.app.config['MAIL_USERNAME'], self.app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Alert email sent: {alert['title']}")
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
    
    def _format_alert_email(self, alert: Dict[str, Any]) -> str:
        """Format alert as HTML email"""
        severity_color = {
            'critical': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8'
        }.get(alert['severity'], '#6c757d')
        
        return f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {severity_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h2 style="margin: 0;">{alert['title']}</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Severity: {alert['severity'].upper()}</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; border-top: none;">
                    <h3>Alert Details</h3>
                    <p><strong>Message:</strong> {alert['message']}</p>
                    <p><strong>Timestamp:</strong> {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <p><strong>Type:</strong> {alert['type']}</p>
                </div>
                
                <div style="background-color: white; padding: 20px; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 8px 8px;">
                    <h4>System Information</h4>
                    <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; font-size: 12px;">
{self._format_details(alert.get('details', {}))}
                    </pre>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #6c757d; font-size: 12px;">
                    <p>Investment Bot Monitoring System</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _format_details(self, details: Dict[str, Any], indent: int = 0) -> str:
        """Format details dict as readable text"""
        lines = []
        prefix = "  " * indent
        
        for key, value in details.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self._format_details(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}: [{len(value)} items]")
            else:
                lines.append(f"{prefix}{key}: {value}")
        
        return "\\n".join(lines)
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            recent_alerts = [
                {
                    'type': alert['type'],
                    'severity': alert['severity'],
                    'title': alert['title'],
                    'message': alert['message'],
                    'timestamp': alert['timestamp'].isoformat()
                }
                for alert in self.alert_history
                if alert['timestamp'] > cutoff_time
            ]
        
        return recent_alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert status"""
        with self._lock:
            total_alerts = len(self.alert_history)
            
            # Count by severity
            severity_counts = defaultdict(int)
            type_counts = defaultdict(int)
            
            for alert in self.alert_history[-50:]:  # Last 50 alerts
                severity_counts[alert['severity']] += 1
                type_counts[alert['type']] += 1
        
        return {
            'total_alerts': total_alerts,
            'severity_breakdown': dict(severity_counts),
            'type_breakdown': dict(type_counts),
            'most_common_alerts': sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'last_alert': self.alert_history[-1]['timestamp'].isoformat() if self.alert_history else None
        }

# Global instance
alert_manager = AlertManager()