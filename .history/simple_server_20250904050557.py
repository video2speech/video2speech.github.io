#!/usr/bin/env python3
"""
简单的视频上传测试服务器
用于测试视频录制工具的服务器上传功能
"""

import os
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import cgi

class VideoUploadHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """处理POST请求 - 视频上传"""
        if self.path == '/upload':
            self.handle_upload()
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        """处理GET请求"""
        if self.path == '/health':
            self.handle_health()
        elif self.path == '/videos':
            self.handle_list_videos()
        else:
            self.send_error(404, "Not Found")

    def handle_upload(self):
        """处理视频上传"""
        try:
            # 设置CORS头
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            # 确保uploads目录存在
            uploads_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)

            # 解析multipart/form-data
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                response = json.dumps({'error': '需要multipart/form-data格式'})
                self.wfile.write(response.encode())
                return

            # 获取表单数据
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )

            # 检查是否有视频文件
            if 'video' not in form:
                response = json.dumps({'error': '没有收到视频文件'})
                self.wfile.write(response.encode())
                return

            video_field = form['video']
            if not video_field.filename:
                response = json.dumps({'error': '视频文件为空'})
                self.wfile.write(response.encode())
                return

            # 保存视频文件
            filename = video_field.filename
            file_path = os.path.join(uploads_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(video_field.file.read())

            # 获取其他表单字段
            sentence = form.getvalue('sentence', '未知句子')
            timestamp = form.getvalue('timestamp', datetime.now().isoformat())
            index = form.getvalue('index', '0')

            # 获取文件信息
            file_size = os.path.getsize(file_path)
            
            print(f"\n✅ 收到视频上传:")
            print(f"   文件名: {filename}")
            print(f"   大小: {file_size / 1024 / 1024:.2f} MB")
            print(f"   句子: {sentence}")
            print(f"   时间: {timestamp}")
            print(f"   序号: {index}")
            print(f"   保存路径: {file_path}")

            # 返回成功响应
            response = json.dumps({
                'success': True,
                'message': '视频上传成功',
                'filename': filename,
                'size': file_size,
                'sentence': sentence,
                'timestamp': timestamp,
                'index': index
            }, ensure_ascii=False)
            
            self.wfile.write(response.encode('utf-8'))

        except Exception as e:
            print(f"❌ 上传处理错误: {e}")
            response = json.dumps({'error': f'服务器内部错误: {str(e)}'})
            self.wfile.write(response.encode())

    def handle_health(self):
        """健康检查"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = json.dumps({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'server': 'Python Simple Video Upload Server'
        })
        self.wfile.write(response.encode())

    def handle_list_videos(self):
        """列出已上传的视频"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        videos = []
        
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                if filename.endswith(('.mp4', '.webm')):
                    file_path = os.path.join(uploads_dir, filename)
                    stat = os.stat(file_path)
                    videos.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        response = json.dumps({
            'success': True,
            'count': len(videos),
            'videos': sorted(videos, key=lambda x: x['created'], reverse=True)
        }, ensure_ascii=False)
        
        self.wfile.write(response.encode('utf-8'))

def run_server(port=3000):
    """启动服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, VideoUploadHandler)
    
    print(f"\n🎥 Python视频上传服务器已启动")
    print(f"📡 服务地址: http://localhost:{port}")
    print(f"📁 上传目录: {os.path.join(os.getcwd(), 'uploads')}")
    print(f"\n可用接口:")
    print(f"  POST /upload        - 上传视频")
    print(f"  GET  /videos        - 获取视频列表")
    print(f"  GET  /health        - 健康检查")
    print(f"\n在录制工具中使用: http://localhost:{port}/upload")
    print(f"\n按 Ctrl+C 停止服务器\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 服务器已停止")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()
