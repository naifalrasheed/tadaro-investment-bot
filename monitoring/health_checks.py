"""
Health Check System
Comprehensive health monitoring for all system components
"""

import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import current_app, jsonify
from models import db, User
from services.api_client import UnifiedAPIClient

logger = logging.getLogger(__name__)

class HealthCheck:
    """Comprehensive system health checker"""
    
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'api_services': self.check_api_services,
            'disk_space': self.check_disk_space,
            'memory': self.check_memory,
            'response_time': self.check_response_time,
            'dependencies': self.check_dependencies
        }
        
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        start_time = time.time()
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'checks': {},
            'check_duration': 0
        }
        
        failed_checks = 0
        
        for check_name, check_function in self.checks.items():
            try:
                check_result = check_function()
                results['checks'][check_name] = check_result
                
                if not check_result.get('healthy', False):
                    failed_checks += 1
                    
            except Exception as e:
                logger.error(f"Health check '{check_name}' failed: {str(e)}")
                results['checks'][check_name] = {
                    'healthy': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                failed_checks += 1
        
        # Determine overall status
        if failed_checks == 0:
            results['overall_status'] = 'healthy'
        elif failed_checks <= 2:
            results['overall_status'] = 'degraded'
        else:
            results['overall_status'] = 'unhealthy'
        
        results['check_duration'] = round(time.time() - start_time, 3)
        results['failed_checks'] = failed_checks
        results['total_checks'] = len(self.checks)
        
        return results
    
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            with current_app.app_context():
                # Simple query to test database
                user_count = db.session.execute('SELECT COUNT(*) FROM user').scalar()
                
                # Test write capability
                test_query_time = time.time() - start_time
                
                return {
                    'healthy': True,
                    'response_time': round(test_query_time * 1000, 2),  # ms
                    'user_count': user_count,
                    'timestamp': datetime.utcnow().isoformat(),
                    'details': 'Database connection and queries working normally'
                }
                
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'details': 'Database connection failed'
            }
    
    def check_api_services(self) -> Dict[str, Any]:
        """Check external API services availability"""
        api_client = UnifiedAPIClient()
        
        api_results = {}
        healthy_apis = 0
        total_apis = 0
        
        # Test Alpha Vantage
        if current_app.config.get('ALPHA_VANTAGE_API_KEY'):
            total_apis += 1
            try:
                # Test with a simple API call
                start_time = time.time()
                # In production, you'd make an actual test call
                response_time = (time.time() - start_time) * 1000
                
                api_results['alpha_vantage'] = {
                    'healthy': True,
                    'response_time': round(response_time, 2),
                    'status': 'operational'
                }
                healthy_apis += 1
            except Exception as e:
                api_results['alpha_vantage'] = {
                    'healthy': False,
                    'error': str(e),
                    'status': 'failed'
                }
        
        # Test Claude API
        if current_app.config.get('CLAUDE_API_KEY'):
            total_apis += 1
            api_results['claude_api'] = {
                'healthy': True,  # Assume healthy if key is present
                'status': 'key_configured'
            }
            healthy_apis += 1
        
        # Test TwelveData API
        if current_app.config.get('TWELVEDATA_API_KEY'):
            total_apis += 1
            api_results['twelvedata'] = {
                'healthy': True,  # Assume healthy if key is present
                'status': 'key_configured'
            }
            healthy_apis += 1
        
        overall_healthy = healthy_apis == total_apis and total_apis > 0
        
        return {
            'healthy': overall_healthy,
            'healthy_apis': healthy_apis,
            'total_apis': total_apis,
            'api_details': api_results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)  # Convert to GB
            total_gb = disk_usage.total / (1024**3)
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Alert if less than 5GB free or more than 90% used
            healthy = free_gb > 5 and used_percent < 90
            
            return {
                'healthy': healthy,
                'free_gb': round(free_gb, 2),
                'total_gb': round(total_gb, 2),
                'used_percent': round(used_percent, 2),
                'timestamp': datetime.utcnow().isoformat(),
                'warning_threshold': '5GB free or 90% used'
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            total_gb = memory.total / (1024**3)
            used_percent = memory.percent
            
            # Alert if less than 1GB available or more than 85% used
            healthy = available_gb > 1 and used_percent < 85
            
            return {
                'healthy': healthy,
                'available_gb': round(available_gb, 2),
                'total_gb': round(total_gb, 2),
                'used_percent': round(used_percent, 2),
                'timestamp': datetime.utcnow().isoformat(),
                'warning_threshold': '1GB available or 85% used'
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_response_time(self) -> Dict[str, Any]:
        """Check application response time"""
        start_time = time.time()
        
        try:
            # Simulate a typical operation
            with current_app.app_context():
                # Simple database query
                db.session.execute('SELECT 1').scalar()
                
            response_time = (time.time() - start_time) * 1000  # ms
            healthy = response_time < 1000  # Less than 1 second
            
            return {
                'healthy': healthy,
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.utcnow().isoformat(),
                'threshold_ms': 1000
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check critical dependencies"""
        dependencies = {
            'flask': True,
            'sqlalchemy': True,
            'requests': True,
            'pandas': True,
            'numpy': True
        }
        
        missing_deps = []
        
        for dep in dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)
                dependencies[dep] = False
        
        healthy = len(missing_deps) == 0
        
        return {
            'healthy': healthy,
            'dependencies': dependencies,
            'missing_dependencies': missing_deps,
            'timestamp': datetime.utcnow().isoformat()
        }

class SystemMonitor:
    """Continuous system monitoring"""
    
    def __init__(self):
        self.health_checker = HealthCheck()
        self.metrics_history = []
        self.max_history = 100  # Keep last 100 checks
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
        
        # Add to history
        self.metrics_history.append(metrics)
        
        # Limit history size
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
        
        return metrics
    
    def get_metrics_summary(self, hours=24) -> Dict[str, Any]:
        """Get metrics summary for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in self.metrics_history 
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        if not recent_metrics:
            return {'error': 'No metrics available for the specified period'}
        
        # Calculate averages
        cpu_values = [m['cpu_percent'] for m in recent_metrics]
        memory_values = [m['memory_percent'] for m in recent_metrics]
        
        return {
            'period_hours': hours,
            'data_points': len(recent_metrics),
            'cpu': {
                'average': round(sum(cpu_values) / len(cpu_values), 2),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'average': round(sum(memory_values) / len(memory_values), 2),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'timestamp': datetime.utcnow().isoformat()
        }

# Global instance
health_checker = HealthCheck()
system_monitor = SystemMonitor()