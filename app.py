from flask import Flask, render_template, request, jsonify
import threading
import time
from datetime import datetime
from web_search_functions import (
    search_part_number_in_system_general_limited,
    search_part_number_in_dataio,
    search_part_number_in_bpmicro
)

app = Flask(__name__)

# Store search results temporarily
search_status = {}

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_devices():
    """API endpoint to start device search"""
    try:
        data = request.get_json()
        part_number = data.get('part_number', '').strip()
        websites = data.get('websites', [])
        
        if not part_number:
            return jsonify({'error': 'Part number is required'}), 400
        
        if not websites:
            return jsonify({'error': 'At least one website must be selected'}), 400
        
        # Generate unique search ID
        search_id = f"search_{int(time.time() * 1000)}"
        
        # Initialize search status
        search_status[search_id] = {
            'status': 'running',
            'progress': 0,
            'results': [],
            'current_search': '',
            'start_time': datetime.now().isoformat()
        }
        
        # Start search in background thread
        search_thread = threading.Thread(
            target=perform_search,
            args=(search_id, part_number, websites)
        )
        search_thread.daemon = True
        search_thread.start()
        
        return jsonify({'search_id': search_id, 'status': 'started'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/<search_id>/status', methods=['GET'])
def get_search_status(search_id):
    """Get the status of a search operation"""
    if search_id not in search_status:
        return jsonify({'error': 'Search not found'}), 404
    
    return jsonify(search_status[search_id])

def perform_search(search_id, part_number, websites):
    """Perform the actual search operations in background"""
    try:
        status = search_status[search_id]
        status['current_search'] = f'Starting search for part number: {part_number}'
        
        results = []
        total_websites = len(websites)
        
        # Search System General if selected
        if 'systemgeneral' in websites:
            status['current_search'] = '🔍 Searching System General...'
            status['progress'] = (len(results) / total_websites) * 100
            
            try:
                result = search_part_number_in_system_general_limited(part_number)
                if result:
                    socket_info, actual_part = result
                    results.append({
                        'website': 'System General',
                        'status': 'found',
                        'socket_info': socket_info,
                        'part_used': actual_part,
                        'modified': actual_part != part_number,
                        'chars_removed': len(part_number) - len(actual_part) if actual_part != part_number else 0
                    })
                else:
                    results.append({
                        'website': 'System General',
                        'status': 'not_found',
                        'socket_info': None,
                        'part_used': part_number,
                        'modified': False,
                        'chars_removed': 0
                    })
            except Exception as e:
                results.append({
                    'website': 'System General',
                    'status': 'error',
                    'error': str(e),
                    'socket_info': None,
                    'part_used': part_number,
                    'modified': False,
                    'chars_removed': 0
                })
        
        # Search DataIO if selected
        if 'dataio' in websites:
            status['current_search'] = '🔍 Searching DataIO...'
            status['progress'] = (len(results) / total_websites) * 100
            
            try:
                result = search_part_number_in_dataio(part_number)
                if result:
                    socket_info, actual_part = result
                    results.append({
                        'website': 'DataIO',
                        'status': 'found',
                        'socket_info': socket_info,
                        'part_used': actual_part,
                        'modified': actual_part != part_number,
                        'chars_removed': len(part_number) - len(actual_part) if actual_part != part_number else 0
                    })
                else:
                    results.append({
                        'website': 'DataIO',
                        'status': 'not_found',
                        'socket_info': None,
                        'part_used': part_number,
                        'modified': False,
                        'chars_removed': 0
                    })
            except Exception as e:
                results.append({
                    'website': 'DataIO',
                    'status': 'error',
                    'error': str(e),
                    'socket_info': None,
                    'part_used': part_number,
                    'modified': False,
                    'chars_removed': 0
                })
        
        # Search BPMicro if selected
        if 'bpmicro' in websites:
            status['current_search'] = '🔍 Searching BPMicro...'
            status['progress'] = (len(results) / total_websites) * 100
            
            try:
                result = search_part_number_in_bpmicro(part_number)
                if result:
                    socket_info, actual_part = result
                    results.append({
                        'website': 'BPMicro',
                        'status': 'found',
                        'socket_info': socket_info,
                        'part_used': actual_part,
                        'modified': actual_part != part_number,
                        'chars_removed': len(part_number) - len(actual_part) if actual_part != part_number else 0
                    })
                else:
                    results.append({
                        'website': 'BPMicro',
                        'status': 'not_found',
                        'socket_info': None,
                        'part_used': part_number,
                        'modified': False,
                        'chars_removed': 0
                    })
            except Exception as e:
                results.append({
                    'website': 'BPMicro',
                    'status': 'error',
                    'error': str(e),
                    'socket_info': None,
                    'part_used': part_number,
                    'modified': False,
                    'chars_removed': 0
                })
        
        # Update final status
        status['status'] = 'completed'
        status['progress'] = 100
        status['results'] = results
        status['current_search'] = 'Search completed!'
        status['end_time'] = datetime.now().isoformat()
        
        # Check if any results were found
        found_results = [r for r in results if r['status'] == 'found']
        status['summary'] = {
            'total_searched': len(results),
            'found_count': len(found_results),
            'has_results': len(found_results) > 0
        }
        
    except Exception as e:
        status['status'] = 'error'
        status['error'] = str(e)
        status['current_search'] = f'Error: {str(e)}'

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # use Render’s PORT or fallback to 5000 locally
    app.run(debug=True, host='0.0.0.0', port=port)

