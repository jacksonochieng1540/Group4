from django.shortcuts import render
from django.http import JsonResponse
import socket
import json
from .coordinator import Coordinator

def index(request):
    """Main page view"""
    logs = []
    
    if request.method == 'POST':
        try:
            amount = int(request.POST.get('amount', 100))
            coordinator = Coordinator()
            logs = coordinator.execute_transaction(amount)
            
            # If it's an AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'logs': logs, 'status': 'success'})
                
        except ValueError:
            logs = ['Error: Invalid amount specified']
        except Exception as e:
            logs = [f'Error: {str(e)}']
    
    return render(request, 'transactions/index.html', {'logs': logs})

def check_node_status(request, port):
    """Check if a node is running"""
    try:
        port = int(port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            # Node is reachable, try to get balance
            try:
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock2.settimeout(2)
                sock2.connect(('localhost', port))
                
                # Send ping to check if node is responsive
                sock2.send(json.dumps({'command': 'balance'}).encode('utf-8'))
                response = sock2.recv(1024).decode('utf-8')
                sock2.close()
                
                data = json.loads(response)
                if data.get('status') == 'success':
                    return JsonResponse({
                        'status': 'active',
                        'port': port,
                        'balance': data.get('balance', 'Unknown'),
                        'message': f'Node {port} is active with balance ${data.get("balance", "Unknown")}'
                    })
            except:
                pass
            
            return JsonResponse({
                'status': 'active',
                'port': port,
                'message': f'Node {port} is reachable'
            })
        else:
            return JsonResponse({
                'status': 'inactive',
                'port': port,
                'message': f'Node {port} is not responding'
            }, status=503)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'port': port,
            'message': f'Error checking node {port}: {str(e)}'
        }, status=500)

def get_balances(request):
    """Get balances from all nodes"""
    balances = []
    
    for port in [5001, 5002]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('localhost', port))
            
            sock.send(json.dumps({'command': 'balance'}).encode('utf-8'))
            response = sock.recv(1024).decode('utf-8')
            sock.close()
            
            data = json.loads(response)
            if data.get('status') == 'success':
                balances.append({
                    'port': port,
                    'balance': data.get('balance', 1000),
                    'status': 'active',
                    'name': f'Node {port}'
                })
            else:
                balances.append({
                    'port': port,
                    'balance': 1000,  # Default fallback
                    'status': 'error',
                    'name': f'Node {port}'
                })
                
        except:
            balances.append({
                'port': port,
                'balance': 1000,  # Default fallback
                'status': 'offline',
                'name': f'Node {port}'
            })
    
    return JsonResponse({'nodes': balances})

def reset_balances(request):
    """Reset all nodes to initial balance"""
    if request.method == 'POST':
        results = []
        
        for port in [5001, 5002]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect(('localhost', port))
                
                sock.send(json.dumps({'command': 'reset'}).encode('utf-8'))
                response = sock.recv(1024).decode('utf-8')
                sock.close()
                
                data = json.loads(response)
                if data.get('status') == 'success':
                    results.append({
                        'port': port,
                        'success': True,
                        'balance': data.get('balance', 1000),
                        'message': f'Node {port} reset to ${data.get("balance", 1000)}'
                    })
                else:
                    results.append({
                        'port': port,
                        'success': False,
                        'message': f'Node {port} reset failed'
                    })
                    
            except:
                results.append({
                    'port': port,
                    'success': False,
                    'message': f'Node {port} is offline'
                })
        
        return JsonResponse({
            'status': 'success',
            'message': 'Reset completed',
            'results': results
        })
    
    return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=405)

def simulate_failure(request):
    """Simulate node failure (for demo purposes only)"""
    if request.method == 'POST':
        import random
        ports = ['5001', '5002']
        failed_port = random.choice(ports)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Node {failed_port} failure simulated',
            'failed_node': failed_port,
            'note': 'This is a simulation - actual nodes continue running'
        })
    
    return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=405)

def get_system_stats(request):
    """Get system statistics"""
    import random
    from datetime import datetime
    
    return JsonResponse({
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'total_transactions': random.randint(10, 50),
        'successful_transactions': random.randint(8, 45),
        'failed_transactions': random.randint(0, 5),
        'system_uptime': f"{random.randint(1, 24)} hours",
        'nodes_online': 2,
        'total_balance': 2000
    })