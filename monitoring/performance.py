"""
Performance Monitoring
Track application performance metrics and identify bottlenecks
"""

import time
import functools
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import request, g
import threading

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self, max_records=1000):
        self.max_records = max_records
        self.request_times = deque(maxlen=max_records)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'max_time': 0,
            'min_time': float('inf'),
            'errors': 0
        })
        self.slow_queries = deque(maxlen=100)
        self.error_log = deque(maxlen=100)
        self._lock = threading.Lock()
    
    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record a request's performance metrics"""
        with self._lock:
            # Record general request timing
            self.request_times.append({
                'timestamp': datetime.utcnow(),
                'endpoint': endpoint,
                'method': method,
                'duration': duration,
                'status_code': status_code
            })
            
            # Update endpoint statistics
            key = f"{method} {endpoint}"
            stats = self.endpoint_stats[key]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], duration)
            stats['min_time'] = min(stats['min_time'], duration)
            
            if status_code >= 400:
                stats['errors'] += 1
            
            # Log slow requests
            if duration > 2.0:  # Slower than 2 seconds
                self.slow_queries.append({
                    'timestamp': datetime.utcnow(),
                    'endpoint': endpoint,
                    'method': method,
                    'duration': duration,
                    'status_code': status_code
                })
                
                logger.warning(f"Slow request: {method} {endpoint} took {duration:.2f}s")
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            # Filter recent requests
            recent_requests = [
                req for req in self.request_times
                if req['timestamp'] > cutoff_time
            ]
            
            if not recent_requests:
                return {'error': 'No requests in the specified time period'}
            
            # Calculate statistics
            durations = [req['duration'] for req in recent_requests]
            error_count = sum(1 for req in recent_requests if req['status_code'] >= 400)
            
            # Top slowest endpoints
            endpoint_times = defaultdict(list)
            for req in recent_requests:
                key = f"{req['method']} {req['endpoint']}"
                endpoint_times[key].append(req['duration'])
            
            slowest_endpoints = []
            for endpoint, times in endpoint_times.items():
                if times:  # Ensure times is not empty
                    avg_time = sum(times) / len(times)
                    slowest_endpoints.append({
                        'endpoint': endpoint,
                        'avg_duration': round(avg_time, 3),
                        'request_count': len(times),
                        'max_duration': round(max(times), 3)
                    })
            
            slowest_endpoints.sort(key=lambda x: x['avg_duration'], reverse=True)
            
            return {
                'period_hours': hours,
                'total_requests': len(recent_requests),
                'error_count': error_count,
                'error_rate': round((error_count / len(recent_requests)) * 100, 2),
                'average_response_time': round(sum(durations) / len(durations), 3),
                'max_response_time': round(max(durations), 3),
                'min_response_time': round(min(durations), 3),
                'slow_requests': len([d for d in durations if d > 2.0]),
                'slowest_endpoints': slowest_endpoints[:5],
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_endpoint_stats(self) -> Dict[str, Any]:
        """Get detailed statistics for all endpoints"""
        with self._lock:
            stats = {}
            for endpoint, data in self.endpoint_stats.items():
                stats[endpoint] = {
                    'requests': data['count'],
                    'avg_time': round(data['avg_time'], 3),
                    'max_time': round(data['max_time'], 3),
                    'min_time': round(data['min_time'] if data['min_time'] != float('inf') else 0, 3),
                    'total_time': round(data['total_time'], 3),
                    'errors': data['errors'],
                    'error_rate': round((data['errors'] / data['count']) * 100, 2) if data['count'] > 0 else 0
                }
            
            return {
                'endpoints': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent slow queries"""
        with self._lock:
            recent_slow = list(self.slow_queries)[-limit:]
            return [{
                'timestamp': sq['timestamp'].isoformat(),
                'endpoint': sq['endpoint'],
                'method': sq['method'],
                'duration': round(sq['duration'], 3),
                'status_code': sq['status_code']
            } for sq in recent_slow]

class MetricsCollector:
    """Collect and aggregate various application metrics"""
    
    def __init__(self):
        self.api_call_counts = defaultdict(int)
        self.api_call_times = defaultdict(list)
        self.user_activity = defaultdict(int)
        self.feature_usage = defaultdict(int)
        self._lock = threading.Lock()
    
    def record_api_call(self, api_name: str, duration: float, success: bool = True):
        """Record an external API call"""
        with self._lock:
            self.api_call_counts[f"{api_name}_{'success' if success else 'error'}"] += 1
            self.api_call_times[api_name].append(duration)
            
            # Keep only recent times (last 100)
            if len(self.api_call_times[api_name]) > 100:
                self.api_call_times[api_name] = self.api_call_times[api_name][-100:]
    
    def record_user_activity(self, user_id: int, activity_type: str):
        """Record user activity"""
        with self._lock:
            self.user_activity[f"user_{user_id}_{activity_type}"] += 1
    
    def record_feature_usage(self, feature_name: str):
        """Record feature usage"""
        with self._lock:
            self.feature_usage[feature_name] += 1
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        with self._lock:
            stats = {}
            
            # Group by API name
            apis = set()
            for key in self.api_call_counts.keys():
                api_name = key.rsplit('_', 1)[0]  # Remove _success or _error suffix
                apis.add(api_name)
            
            for api in apis:
                success_count = self.api_call_counts.get(f"{api}_success", 0)
                error_count = self.api_call_counts.get(f"{api}_error", 0)
                total_count = success_count + error_count
                
                avg_time = 0
                if api in self.api_call_times and self.api_call_times[api]:
                    avg_time = sum(self.api_call_times[api]) / len(self.api_call_times[api])
                
                stats[api] = {
                    'total_calls': total_count,
                    'successful_calls': success_count,
                    'failed_calls': error_count,
                    'success_rate': round((success_count / total_count) * 100, 2) if total_count > 0 else 0,
                    'average_response_time': round(avg_time, 3)
                }
            
            return stats
    
    def get_feature_stats(self) -> Dict[str, Any]:
        """Get feature usage statistics"""
        with self._lock:
            sorted_features = sorted(self.feature_usage.items(), key=lambda x: x[1], reverse=True)
            return {
                'total_features': len(sorted_features),
                'most_used_features': sorted_features[:10],
                'feature_usage': dict(self.feature_usage)
            }

def monitor_performance(f):
    """Decorator to monitor function performance"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            
            # Record successful execution
            function_name = f.__name__
            metrics_collector.record_feature_usage(function_name)
            
            if duration > 1.0:  # Log slow functions
                logger.info(f"Function {function_name} took {duration:.2f}s")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Function {f.__name__} failed after {duration:.2f}s: {str(e)}")
            raise
    
    return decorated_function

def monitor_api_call(api_name: str):
    """Decorator to monitor external API calls"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_api_call(api_name, duration, success)
        
        return decorated_function
    return decorator

def track_api_performance(endpoint_name: str):
    """Decorator to track API endpoint performance"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                result = f(*args, **kwargs)
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                return result
            except Exception as e:
                status_code = 500
                logger.error(f"API endpoint {endpoint_name} failed: {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                method = getattr(request, 'method', 'GET') if 'request' in globals() else 'GET'
                performance_monitor.record_request(endpoint_name, method, duration, status_code)
                metrics_collector.record_feature_usage(endpoint_name)
        
        return decorated_function
    return decorator

# Global instances
performance_monitor = PerformanceMonitor()
metrics_collector = MetricsCollector()