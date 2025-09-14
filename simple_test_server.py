#!/usr/bin/env python3
"""
Simple Test Server - No Dependencies Required
Tests investment bot functionality without Flask/pandas dependencies
"""

import http.server
import socketserver
import json
import urllib.parse
from datetime import datetime
import webbrowser
import threading
import time

PORT = 8080

class InvestmentBotTestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard':
            self.serve_dashboard()
        elif self.path.startswith('/api/'):
            self.handle_api_request()
        elif self.path == '/test-status':
            self.serve_status()
        else:
            self.serve_404()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            self.serve_404()
    
    def serve_dashboard(self):
        """Serve the testing dashboard"""
        html_content = self.get_dashboard_html()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', len(html_content))
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def handle_api_request(self):
        """Handle API requests with mock responses"""
        path = self.path
        method = self.command
        
        # Parse the path
        if '/api/management/quality/' in path:
            response = self.get_management_quality_response()
        elif '/api/shareholder-value/' in path:
            response = self.get_shareholder_value_response()
        elif '/api/macro-integration/' in path:
            response = self.get_macro_integration_response()
        elif '/api/advisory/risk-assessment' in path:
            response = self.get_risk_assessment_response()
        elif '/api/advisory/portfolio-construction' in path:
            response = self.get_portfolio_construction_response()
        elif '/api/advisory/fiduciary-advice' in path:
            response = self.get_fiduciary_advice_response()
        else:
            response = {'status': 'error', 'message': 'API endpoint not found'}
        
        # Send JSON response
        json_response = json.dumps(response, indent=2)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(json_response))
        self.end_headers()
        self.wfile.write(json_response.encode())
    
    def get_management_quality_response(self):
        """Mock management quality analysis response"""
        return {
            'status': 'success',
            'symbol': '2222.SR',
            'analysis_date': datetime.now().isoformat(),
            'management_analysis': {
                'overall_score': 87.2,
                'leadership_stability': 'Stable',
                'governance_score': 88.0,
                'performance_delivery': 78.0,
                'key_strengths': [
                    'Strong governance framework',
                    'Stable leadership team',
                    'Transparent reporting practices'
                ],
                'key_concerns': [
                    'High executive compensation',
                    'Limited board diversity'
                ],
                'turnover_analysis': {
                    'executive_turnover_rate': 12.0,
                    'board_independence': 85.0,
                    'recent_changes': ['CEO appointment in 2023']
                }
            },
            'source': 'test_server',
            'message': '✅ Phase 3 Management Analysis - Test Server Response'
        }
    
    def get_shareholder_value_response(self):
        """Mock shareholder value tracking response"""
        return {
            'status': 'success',
            'symbol': '2222.SR',
            'analysis_date': datetime.now().isoformat(),
            'shareholder_value_metrics': {
                'value_creation_score': 82.3,
                'peer_ranking': 'Quartile 2',
                'total_shareholder_return': {
                    '1_year': '8.5%',
                    '3_year': '12.3%',
                    '5_year': '15.8%'
                },
                'dividend_analysis': {
                    'current_yield': '4.2%',
                    'growth_rate': '6.8%',
                    'consistency_score': '95%'
                },
                'capital_allocation': {
                    'overall_score': '82/100',
                    'buyback_effectiveness': '75%',
                    'buyback_yield': '1.2%'
                },
                'value_drivers': [
                    'Strong dividend growth',
                    'Effective capital allocation'
                ],
                'value_destroyers': [
                    'High leverage in challenging periods'
                ]
            },
            'source': 'test_server',
            'message': '✅ Phase 3 Shareholder Value Tracking - Test Server Response'
        }
    
    def get_macro_integration_response(self):
        """Mock macro integration response"""
        return {
            'status': 'success',
            'symbol': '2222.SR',
            'analysis_date': datetime.now().isoformat(),
            'macro_environment': {
                'current_factors': {
                    'saudi_policy_rate': '5.50%',
                    'inflation_rate': '2.8%',
                    'gdp_growth': '4.1%',
                    'oil_price': '$85/bbl',
                    'consumer_confidence': 108.5
                },
                'economic_cycle': 'expansion'
            },
            'sector_analysis': {
                'sector': 'energy',
                'interest_rate_sensitivity': -0.2,
                'gdp_correlation': 0.7,
                'current_cycle_position': 'expansion',
                'recommended_allocation': 'overweight'
            },
            'valuation_adjustment': {
                'base_valuation': 100.0,
                'macro_adjusted_valuation': 108.0,
                'adjustment_breakdown': {
                    'interest_rate_impact': 2.0,
                    'inflation_impact': 1.0,
                    'currency_impact': 0.0,
                    'risk_premium_impact': 5.0
                },
                'confidence_level': '85%'
            },
            'source': 'test_server',
            'message': '✅ Phase 3 Macro Integration - Test Server Response'
        }
    
    def get_risk_assessment_response(self):
        """Mock risk assessment response"""
        return {
            'status': 'success',
            'assessment_date': datetime.now().isoformat(),
            'risk_profile': {
                'risk_score': '6/10',
                'risk_category': 'moderate',
                'volatility_tolerance': '12.0%',
                'drawdown_tolerance': '10.0%',
                'time_horizon': '20 years',
                'liquidity_needs': 'medium',
                'investment_experience': 'intermediate',
                'financial_capacity': 'medium',
                'behavioral_biases': ['loss_aversion', 'recency_bias']
            },
            'investment_goals': [{
                'goal_id': 'retirement',
                'name': 'Retirement Planning',
                'target_amount': 'SAR 3,000,000',
                'time_horizon': '20 years',
                'priority': 'high',
                'risk_tolerance': 'moderate'
            }],
            'source': 'test_server',
            'message': '✅ Phase 4 Risk Assessment - Test Server Response'
        }
    
    def get_portfolio_construction_response(self):
        """Mock portfolio construction response"""
        return {
            'status': 'success',
            'construction_date': datetime.now().isoformat(),
            'portfolio_recommendation': {
                'strategic_allocation': {
                    'saudi_equity': '45.0%',
                    'saudi_bonds': '25.0%',
                    'international_equity': '20.0%',
                    'real_estate': '8.0%',
                    'cash_equivalents': '2.0%'
                },
                'expected_metrics': {
                    'annual_return': '8.2%',
                    'volatility': '14.5%',
                    'sharpe_ratio': '0.45',
                    'max_drawdown_estimate': '12.0%'
                },
                'specific_securities': [
                    {
                        'symbol': '2222.SR',
                        'name': 'Saudi Aramco',
                        'asset_class': 'saudi_equity',
                        'allocation': '15.0%',
                        'selection_criteria': 'High quality energy company with strong fundamentals'
                    },
                    {
                        'symbol': '1180.SR',
                        'name': 'Al Rajhi Bank',
                        'asset_class': 'saudi_equity',
                        'allocation': '10.0%',
                        'selection_criteria': 'Leading Islamic bank with consistent performance'
                    }
                ],
                'rebalancing_strategy': {
                    'frequency': 'quarterly',
                    'monitoring_triggers': [
                        'Asset allocation drift >5%',
                        'Significant market volatility',
                        'Changes in client risk profile'
                    ]
                }
            },
            'source': 'test_server',
            'message': '✅ Phase 4 Portfolio Construction - Test Server Response'
        }
    
    def get_fiduciary_advice_response(self):
        """Mock comprehensive fiduciary advice response"""
        return {
            'status': 'success',
            'advice_date': datetime.now().isoformat(),
            'fiduciary_advice': {
                'executive_summary': {
                    'client_risk_profile': 'moderate',
                    'primary_goals': ['Retirement Planning'],
                    'recommended_allocation': {
                        'saudi_equity': '45.0%',
                        'saudi_bonds': '25.0%',
                        'international_equity': '20.0%',
                        'real_estate': '8.0%',
                        'cash': '2.0%'
                    },
                    'expected_annual_return': '8.2%',
                    'next_review_date': '2025-03-12'
                },
                'risk_assessment': {
                    'risk_score': '6/10',
                    'risk_category': 'moderate',
                    'time_horizon': '20 years',
                    'liquidity_needs': 'medium'
                },
                'implementation_plan': {
                    'investment_timeline': 'Implement over 3 months',
                    'dollar_cost_averaging': 'Recommended for large positions',
                    'tax_optimization': 'Prioritize tax-advantaged accounts'
                },
                'monitoring_framework': {
                    'review_frequency': 'Quarterly',
                    'rebalancing_triggers': ['5% allocation drift', 'Life changes'],
                    'performance_benchmarks': ['TASI Index', 'Custom benchmark']
                }
            },
            'fiduciary_disclosures': [
                'This advice is provided in a fiduciary capacity',
                'Past performance does not guarantee future results',
                'All investments carry risk of loss'
            ],
            'action_items': [
                'Review and approve recommended allocation',
                'Begin implementation according to timeline',
                'Schedule quarterly review meeting'
            ],
            'source': 'test_server',
            'message': '✅ Phase 4 Complete Fiduciary Advice - Test Server Response'
        }
    
    def serve_status(self):
        """Serve system status"""
        status = {
            'server': 'Simple Test Server',
            'status': 'operational',
            'timestamp': datetime.now().isoformat(),
            'features_available': [
                'Phase 3: Management Quality Analysis',
                'Phase 3: Shareholder Value Tracking', 
                'Phase 3: Macro Integration',
                'Phase 4: Risk Assessment',
                'Phase 4: Portfolio Construction',
                'Phase 4: Fiduciary Advice'
            ],
            'note': 'This is a test server providing mock responses for demonstration'
        }
        
        json_response = json.dumps(status, indent=2)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', len(json_response))
        self.end_headers()
        self.wfile.write(json_response.encode())
    
    def serve_404(self):
        """Serve 404 page"""
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>404 - Page Not Found</h1><p><a href="/">Go to Dashboard</a></p>')
    
    def get_dashboard_html(self):
        """Generate the testing dashboard HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Bot - Simple Test Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { color: #2c3e50; margin: 0; }
        .header p { color: #7f8c8d; margin-top: 10px; }
        .alert { background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin-bottom: 30px; color: #0c5460; }
        .section { margin-bottom: 40px; }
        .section h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .test-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .test-card { background: #fff; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .test-card h3 { color: #2c3e50; margin-top: 0; }
        .test-button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; transition: background 0.3s; }
        .test-button:hover { background: #2980b9; }
        .test-button.phase3 { background: #e74c3c; }
        .test-button.phase3:hover { background: #c0392b; }
        .test-button.phase4 { background: #9b59b6; }
        .test-button.phase4:hover { background: #8e44ad; }
        .results { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; min-height: 100px; }
        .result-item { background: white; border-left: 4px solid #3498db; margin: 10px 0; padding: 15px; border-radius: 4px; }
        .result-item.success { border-color: #27ae60; }
        .result-item.error { border-color: #e74c3c; }
        .timestamp { color: #7f8c8d; font-size: 0.9em; float: right; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
        .status-online { background: #27ae60; }
        .json-response { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 0.9em; max-height: 300px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Investment Bot - Simple Test Dashboard</h1>
            <p>Dependency-free testing interface for Phase 3 & 4 functionality</p>
        </div>

        <div class="alert">
            <strong>📡 Test Server Status:</strong> 
            <span class="status-indicator status-online"></span>
            Simple test server operational - providing mock responses for all Phase 3 & 4 APIs
        </div>

        <div class="section">
            <h2>🧪 Quick Tests</h2>
            <div style="text-align: center; margin: 20px 0;">
                <button class="test-button" onclick="runAllTests()">🚀 Test All APIs</button>
                <button class="test-button phase3" onclick="testPhase3()">📊 Test Phase 3</button>
                <button class="test-button phase4" onclick="testPhase4()">🤖 Test Phase 4</button>
                <button class="test-button" onclick="checkStatus()">⚡ Server Status</button>
            </div>
        </div>

        <div class="section">
            <h2>🔧 API Endpoint Testing</h2>
            <div class="test-grid">
                <div class="test-card">
                    <h3>Phase 3: Management & Governance</h3>
                    <p>Advanced management quality and governance analysis</p>
                    <button class="test-button phase3" onclick="testAPI('GET', '/api/management/quality/2222')">Management Quality</button>
                    <button class="test-button phase3" onclick="testAPI('GET', '/api/shareholder-value/2222')">Shareholder Value</button>
                    <button class="test-button phase3" onclick="testAPI('GET', '/api/macro-integration/2222')">Macro Integration</button>
                </div>

                <div class="test-card">
                    <h3>Phase 4: AI Fiduciary Advisor</h3>
                    <p>Professional investment advisory services</p>
                    <button class="test-button phase4" onclick="testAPI('POST', '/api/advisory/risk-assessment')">Risk Assessment</button>
                    <button class="test-button phase4" onclick="testAPI('POST', '/api/advisory/portfolio-construction')">Portfolio Construction</button>
                    <button class="test-button phase4" onclick="testAPI('POST', '/api/advisory/fiduciary-advice')">Fiduciary Advice</button>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Test Results</h2>
            <div id="results" class="results">
                <p style="text-align: center; color: #7f8c8d;">Test results will appear here...</p>
            </div>
        </div>
    </div>

    <script>
        function addResult(title, status, message, data = null) {
            const results = document.getElementById('results');
            const timestamp = new Date().toLocaleTimeString();
            const statusClass = status === 'success' ? 'success' : status === 'error' ? 'error' : '';
            
            const resultHtml = `
                <div class="result-item ${statusClass}">
                    <strong>${title}</strong>
                    <span class="timestamp">${timestamp}</span>
                    <p>${message}</p>
                    ${data ? `<div class="json-response">${JSON.stringify(data, null, 2)}</div>` : ''}
                </div>
            `;
            
            results.innerHTML = resultHtml + results.innerHTML;
        }

        function testAPI(method, endpoint) {
            addResult(`API Test: ${method} ${endpoint}`, 'info', 'Sending request...');
            
            fetch(endpoint, {
                method: method,
                headers: {'Content-Type': 'application/json'}
            })
            .then(response => response.json())
            .then(data => {
                addResult(
                    `✅ ${method} ${endpoint}`,
                    'success',
                    data.message || 'API request successful',
                    data
                );
            })
            .catch(error => {
                addResult(
                    `❌ ${method} ${endpoint}`,
                    'error',
                    `Request failed: ${error.message}`
                );
            });
        }

        function testPhase3() {
            addResult('Phase 3 Test Suite', 'info', 'Testing all Phase 3 endpoints...');
            setTimeout(() => testAPI('GET', '/api/management/quality/2222'), 100);
            setTimeout(() => testAPI('GET', '/api/shareholder-value/2222'), 500);
            setTimeout(() => testAPI('GET', '/api/macro-integration/2222'), 1000);
        }

        function testPhase4() {
            addResult('Phase 4 Test Suite', 'info', 'Testing all Phase 4 endpoints...');
            setTimeout(() => testAPI('POST', '/api/advisory/risk-assessment'), 100);
            setTimeout(() => testAPI('POST', '/api/advisory/portfolio-construction'), 500);
            setTimeout(() => testAPI('POST', '/api/advisory/fiduciary-advice'), 1000);
        }

        function runAllTests() {
            addResult('Complete Test Suite', 'info', 'Running comprehensive tests for all APIs...');
            setTimeout(() => testPhase3(), 100);
            setTimeout(() => testPhase4(), 2000);
        }

        function checkStatus() {
            testAPI('GET', '/test-status');
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            addResult(
                '🎉 Simple Test Dashboard Loaded',
                'success',
                'Dashboard initialized successfully. All Phase 3 & 4 APIs ready for testing.',
            );
        });
    </script>
</body>
</html>
        '''

def start_server():
    """Start the test server"""
    try:
        with socketserver.TCPServer(("", PORT), InvestmentBotTestHandler) as httpd:
            print(f"\n🚀 Simple Investment Bot Test Server")
            print(f"=" * 50)
            print(f"✅ Server running on: http://localhost:{PORT}")
            print(f"📊 Dashboard URL: http://localhost:{PORT}/dashboard")
            print(f"🔧 Status Check: http://localhost:{PORT}/test-status")
            print(f"=" * 50)
            print(f"📝 Features Available:")
            print(f"  • Phase 3: Management Quality Analysis")
            print(f"  • Phase 3: Shareholder Value Tracking")
            print(f"  • Phase 3: Macro Integration")
            print(f"  • Phase 4: Risk Assessment")
            print(f"  • Phase 4: Portfolio Construction")
            print(f"  • Phase 4: Fiduciary Advice")
            print(f"=" * 50)
            print(f"🌐 Opening browser...")
            
            # Open browser automatically
            def open_browser():
                time.sleep(1)
                webbrowser.open(f'http://localhost:{PORT}')
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            print(f"\n⏳ Server ready! Press Ctrl+C to stop...")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n\n✅ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print(f"💡 Try a different port or check if port {PORT} is busy")

if __name__ == "__main__":
    start_server()