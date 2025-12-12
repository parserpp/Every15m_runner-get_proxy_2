# Proxy Validation and Upload System

## 概述

本系统自动获取代理、验证其有效性，并只上传经过验证的代理到 `ip_ports` 仓库。

## 工作流程

```
1. 克隆 parser_proxy_2 仓库
2. 运行 getproxy 生成代理列表
3. 下载 ip_ports 现有代理数据
4. 合并新旧代理数据
5. 并发测速验证所有代理
6. 只上传通过验证的代理
7. 清理本地临时文件
```

## 验证参数

- **超时时间**: 5秒
- **最大响应时间**: 3秒
- **并发线程数**: 50
- **测试URL**: http://httpbin.org/get

## 配置要求

### GitHub Token (GTOKEN)

必须在 `Every15m_runner-get_proxy_2` 仓库的 Secrets 中设置 `GTOKEN`：

1. 访问 https://github.com/settings/tokens
2. 生成新 Token (classic)，权限：
   - ✅ `repo` (完整仓库访问)
   - ✅ `workflow` (GitHub Actions)
3. 在仓库设置中添加 Secret：
   - Name: `GTOKEN`
   - Value: 你的 Token

## 文件说明

- `validate_and_upload.py` - 验证和上传脚本
- `.github/workflows/main.yml` - GitHub Actions 工作流
- `parser_proxy_2/` - 代理获取工具源码

## 输出格式

上传到 `ip_ports` 的文件：

1. **proxyinfo.json** - JSON 行格式的代理列表
2. **proxyinfo.txt** - IP:PORT 格式的纯文本列表
3. **db.json** - 按类型和匿名性分组的数据库

## 调度

工作流每 15 分钟自动运行一次 (cron: `0/15 * * * *`)。

## 特性

- ✅ 并发测速验证 (50 线程)
- ✅ 自动去重合并
- ✅ 只上传有效代理
- ✅ 完整错误处理
- ✅ 自动清理临时文件