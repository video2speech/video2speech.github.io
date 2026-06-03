const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
const PORT = 3000;

// 启用CORS
app.use(cors());

// 确保uploads目录存在
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// 配置multer用于文件上传
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    // 使用原始文件名，如果没有则生成一个
    const originalName = file.originalname || `video_${Date.now()}.mp4`;
    cb(null, originalName);
  }
});

const upload = multer({ 
  storage: storage,
  limits: {
    fileSize: 100 * 1024 * 1024 // 限制文件大小为100MB
  }
});

// 上传接口
app.post('/upload', upload.single('video'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: '没有收到视频文件' });
    }

    const { sentence, timestamp, index } = req.body;
    
    console.log('收到视频上传:');
    console.log('- 文件名:', req.file.filename);
    console.log('- 文件大小:', (req.file.size / 1024 / 1024).toFixed(2), 'MB');
    console.log('- 句子:', sentence);
    console.log('- 时间:', timestamp);
    console.log('- 序号:', index);
    console.log('- 保存路径:', req.file.path);
    
    // 可以在这里添加更多处理逻辑，比如：
    // - 保存到数据库
    // - 转码视频
    // - 生成缩略图
    // - 发送到其他服务等

    res.json({
      success: true,
      message: '视频上传成功',
      filename: req.file.filename,
      size: req.file.size,
      sentence: sentence,
      timestamp: timestamp,
      index: index
    });

  } catch (error) {
    console.error('上传处理错误:', error);
    res.status(500).json({ error: '服务器内部错误' });
  }
});

// 获取已上传的视频列表
app.get('/videos', (req, res) => {
  try {
    const files = fs.readdirSync(uploadsDir);
    const videos = files
      .filter(file => file.endsWith('.mp4') || file.endsWith('.webm'))
      .map(file => {
        const filePath = path.join(uploadsDir, file);
        const stats = fs.statSync(filePath);
        return {
          filename: file,
          size: stats.size,
          created: stats.birthtime,
          modified: stats.mtime
        };
      })
      .sort((a, b) => b.created - a.created); // 按创建时间倒序

    res.json({
      success: true,
      count: videos.length,
      videos: videos
    });
  } catch (error) {
    console.error('获取视频列表错误:', error);
    res.status(500).json({ error: '获取视频列表失败' });
  }
});

// 下载视频文件
app.get('/download/:filename', (req, res) => {
  const filename = req.params.filename;
  const filePath = path.join(uploadsDir, filename);
  
  if (fs.existsSync(filePath)) {
    res.download(filePath);
  } else {
    res.status(404).json({ error: '文件不存在' });
  }
});

// 删除视频文件
app.delete('/delete/:filename', (req, res) => {
  const filename = req.params.filename;
  const filePath = path.join(uploadsDir, filename);
  
  try {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
      res.json({ success: true, message: '文件删除成功' });
    } else {
      res.status(404).json({ error: '文件不存在' });
    }
  } catch (error) {
    console.error('删除文件错误:', error);
    res.status(500).json({ error: '删除文件失败' });
  }
});

// 健康检查
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    uploadsDir: uploadsDir
  });
});

app.listen(PORT, () => {
  console.log(`\n🎥 视频上传服务器已启动`);
  console.log(`📡 服务地址: http://localhost:${PORT}`);
  console.log(`📁 上传目录: ${uploadsDir}`);
  console.log(`\n可用接口:`);
  console.log(`  POST /upload        - 上传视频`);
  console.log(`  GET  /videos        - 获取视频列表`);
  console.log(`  GET  /download/:filename - 下载视频`);
  console.log(`  DELETE /delete/:filename - 删除视频`);
  console.log(`  GET  /health        - 健康检查`);
  console.log(`\n在录制工具中使用: http://localhost:${PORT}/upload\n`);
});
