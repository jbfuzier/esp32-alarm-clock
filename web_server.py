"""
Web Server for ESP32 Alarm Clock
Async HTTP REST API server with socket-based implementation
"""
import asyncio
try:
    import usocket as socket
    import ujson as json
except ImportError:
    import socket
    import json

import config


class AsyncHTTPServer:
    """
    Asynchronous HTTP server for REST API
    Handles all alarm, lights, and settings endpoints
    """
    
    def __init__(self, host='0.0.0.0', port=80):
        """
        Initialize HTTP server
        
        Args:
            host: Host address to bind to
            port: Port number to listen on
        """
        self.host = host
        self.port = port
        self.app = None  # Will be set to AlarmClockApp instance
        self.server_socket = None
        self.running = False
        
        # Route mapping
        self.routes = {
            ('GET', '/'): self._handle_index,
            ('GET', '/api/alarms'): self._handle_get_alarms,
            ('POST', '/api/alarms'): self._handle_post_alarm,
            ('PATCH', '/api/alarms'): self._handle_patch_alarm,
            ('DELETE', '/api/alarms'): self._handle_delete_alarm,
            ('GET', '/api/lights'): self._handle_get_lights,
            ('POST', '/api/lights'): self._handle_post_lights,
            ('GET', '/api/settings'): self._handle_get_settings,
            ('PATCH', '/api/settings'): self._handle_patch_settings,
        }
    
    def set_app(self, app):
        """
        Set the main application instance for integration
        
        Args:
            app: AlarmClockApp instance
        """
        self.app = app
    
    def _parse_request(self, request_data):
        """
        Parse HTTP request
        
        Args:
            request_data: Raw request bytes
            
        Returns:
            dict: Parsed request with method, path, headers, body
        """
        try:
            request_str = request_data.decode('utf-8')
            lines = request_str.split('\r\n')
            
            if not lines:
                return None
            
            # Parse request line
            request_line = lines[0].split()
            if len(request_line) < 3:
                return None
            
            method = request_line[0]
            path = request_line[1]
            
            # Parse headers
            headers = {}
            body_start = 0
            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            # Parse body
            body = None
            if body_start < len(lines):
                body_str = '\r\n'.join(lines[body_start:])
                if body_str:
                    try:
                        body = json.loads(body_str)
                    except (ValueError, KeyError):
                        body = body_str
            
            return {
                'method': method,
                'path': path,
                'headers': headers,
                'body': body
            }
        except Exception as e:
            print(f"Error parsing request: {e}")
            return None
    
    def _build_response(self, status_code, status_text, body=None, content_type='application/json'):
        """
        Build HTTP response
        
        Args:
            status_code: HTTP status code
            status_text: HTTP status text
            body: Response body (dict for JSON or string)
            content_type: Content type header
            
        Returns:
            str: Complete HTTP response
        """
        response = f"HTTP/1.1 {status_code} {status_text}\r\n"
        
        if body is not None:
            if content_type == 'application/json' and isinstance(body, dict):
                body_str = json.dumps(body)
            else:
                body_str = str(body)
            
            response += f"Content-Type: {content_type}\r\n"
            response += f"Content-Length: {len(body_str)}\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
            response += body_str
        else:
            response += "Connection: close\r\n"
            response += "\r\n"
        
        return response
    
    # Route handlers
    
    async def _handle_index(self, request):
        """Serve index.html"""
        try:
            with open('index.html', 'r') as f:
                content = f.read()
            return self._build_response(200, 'OK', content, 'text/html')
        except Exception as e:
            print(f"Error serving index.html: {e}")
            return self._build_response(404, 'Not Found', {'error': 'index.html not found'})
    
    async def _handle_get_alarms(self, request):
        """GET /api/alarms - Get all alarms"""
        if self.app and hasattr(self.app, 'storage'):
            alarms = self.app.storage.load_alarms()
            return self._build_response(200, 'OK', alarms)
        return self._build_response(500, 'Internal Server Error', {'error': 'Storage not available'})
    
    async def _handle_post_alarm(self, request):
        """POST /api/alarms - Create new alarm"""
        if not request.get('body'):
            return self._build_response(400, 'Bad Request', {'error': 'Request body required'})
        
        if self.app and hasattr(self.app, 'storage'):
            success, result = self.app.storage.add_alarm(request['body'])
            if success:
                return self._build_response(201, 'Created', result)
            else:
                return self._build_response(400, 'Bad Request', {'error': result})
        return self._build_response(500, 'Internal Server Error', {'error': 'Storage not available'})
    
    async def _handle_patch_alarm(self, request):
        """PATCH /api/alarms/{id} - Update alarm"""
        # Extract ID from path
        path = request['path']
        parts = path.split('/')
        if len(parts) < 4:
            return self._build_response(400, 'Bad Request', {'error': 'Alarm ID required'})
        
        try:
            alarm_id = int(parts[3])
        except ValueError:
            return self._build_response(400, 'Bad Request', {'error': 'Invalid alarm ID'})
        
        if not request.get('body'):
            return self._build_response(400, 'Bad Request', {'error': 'Request body required'})
        
        if self.app and hasattr(self.app, 'storage'):
            success, result = self.app.storage.update_alarm(alarm_id, request['body'])
            if success:
                return self._build_response(200, 'OK', result)
            else:
                return self._build_response(404, 'Not Found', {'error': result})
        return self._build_response(500, 'Internal Server Error', {'error': 'Storage not available'})
    
    async def _handle_delete_alarm(self, request):
        """DELETE /api/alarms/{id} - Delete alarm"""
        # Extract ID from path
        path = request['path']
        parts = path.split('/')
        if len(parts) < 4:
            return self._build_response(400, 'Bad Request', {'error': 'Alarm ID required'})
        
        try:
            alarm_id = int(parts[3])
        except ValueError:
            return self._build_response(400, 'Bad Request', {'error': 'Invalid alarm ID'})
        
        if self.app and hasattr(self.app, 'storage'):
            success = self.app.storage.delete_alarm(alarm_id)
            if success:
                return self._build_response(200, 'OK', {'message': 'Alarm deleted'})
            else:
                return self._build_response(404, 'Not Found', {'error': 'Alarm not found'})
        return self._build_response(500, 'Internal Server Error', {'error': 'Storage not available'})
    
    async def _handle_get_lights(self, request):
        """GET /api/lights - Get current LED state"""
        if self.app and hasattr(self.app, 'led_controller'):
            state = self.app.led_controller.get_current_state()
            return self._build_response(200, 'OK', state)
        return self._build_response(500, 'Internal Server Error', {'error': 'LED controller not available'})
    
    async def _handle_post_lights(self, request):
        """POST /api/lights - Set LED state"""
        if not request.get('body'):
            return self._build_response(400, 'Bad Request', {'error': 'Request body required'})
        
        body = request['body']
        if 'brightness' not in body or 'temperature' not in body:
            return self._build_response(400, 'Bad Request', {'error': 'brightness and temperature required'})
        
        if self.app and hasattr(self.app, 'led_controller'):
            try:
                brightness = int(body['brightness'])
                temperature = int(body['temperature'])
                await self.app.led_controller.set_color(brightness, temperature)
                state = self.app.led_controller.get_current_state()
                return self._build_response(200, 'OK', state)
            except Exception as e:
                return self._build_response(400, 'Bad Request', {'error': str(e)})
        return self._build_response(500, 'Internal Server Error', {'error': 'LED controller not available'})
    
    async def _handle_get_settings(self, request):
        """GET /api/settings - Get current settings"""
        if self.app and hasattr(self.app, 'storage'):
            settings = self.app.storage.load_settings()
            return self._build_response(200, 'OK', settings)
        return self._build_response(500, 'Internal Server Error', {'error': 'Storage not available'})
    
    async def _handle_patch_settings(self, request):
        """PATCH /api/settings - Update settings"""
        if not request.get('body'):
            return self._build_response(400, 'Bad Request', {'error': 'Request body required'})
        
        if self.app and hasattr(self.app, 'storage'):
            # Load current settings
            settings = self.app.storage.load_settings()
            # Update with new values
            settings.update(request['body'])
            # Save
            self.app.storage.save_settings(settings)
            return self._build_response(200, 'OK', settings)
        return self._build_response(500, 'Internal Server Error', {'error': 'Storage not available'})
    
    async def _handle_request(self, client_socket, client_addr):
        """
        Handle a single client request
        
        Args:
            client_socket: Client socket
            client_addr: Client address
        """
        try:
            # Receive request
            request_data = b''
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                request_data += chunk
                # Check if we've received the full request
                if b'\r\n\r\n' in request_data:
                    # For POST/PATCH, check if we have the body
                    if b'Content-Length:' in request_data:
                        header_end = request_data.find(b'\r\n\r\n')
                        headers = request_data[:header_end].decode('utf-8')
                        for line in headers.split('\r\n'):
                            if line.lower().startswith('content-length:'):
                                content_length = int(line.split(':')[1].strip())
                                body_received = len(request_data) - header_end - 4
                                if body_received >= content_length:
                                    break
                    else:
                        break
            
            # Parse request
            request = self._parse_request(request_data)
            if not request:
                response = self._build_response(400, 'Bad Request', {'error': 'Invalid request'})
                client_socket.send(response.encode('utf-8'))
                client_socket.close()
                return
            
            print(f"Request: {request['method']} {request['path']}")
            
            # Find matching route
            response = None
            for (method, path_pattern), handler in self.routes.items():
                if request['method'] == method:
                    # Check if path matches (exact match or starts with for parameterized paths)
                    if request['path'] == path_pattern or request['path'].startswith(path_pattern + '/'):
                        response = await handler(request)
                        break
            
            if response is None:
                response = self._build_response(404, 'Not Found', {'error': 'Route not found'})
            
            # Send response
            client_socket.send(response.encode('utf-8'))
            client_socket.close()
            
        except Exception as e:
            print(f"Error handling request: {e}")
            try:
                response = self._build_response(500, 'Internal Server Error', {'error': str(e)})
                client_socket.send(response.encode('utf-8'))
                client_socket.close()
            except:
                pass
    
    async def start(self):
        """Start the HTTP server"""
        try:
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to address
            addr = socket.getaddrinfo(self.host, self.port)[0][-1]
            self.server_socket.bind(addr)
            self.server_socket.listen(5)
            
            # Set non-blocking
            self.server_socket.setblocking(False)
            
            self.running = True
            print(f"Web server started on http://{self.host}:{self.port}")
            
            while self.running:
                try:
                    # Accept connection
                    client_socket, client_addr = self.server_socket.accept()
                    # Handle request
                    asyncio.create_task(self._handle_request(client_socket, client_addr))
                except OSError:
                    # No connection available, yield control
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"Error starting server: {e}")
            self.running = False
    
    def stop(self):
        """Stop the HTTP server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
