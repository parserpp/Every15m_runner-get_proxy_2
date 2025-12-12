# GitHub Token 设置指南

## 问题
`github.token` (GITHUB_TOKEN) 默认只能访问当前仓库，无法访问 `ip_ports` 仓库。

## 解决方案

### 方案 1：使用 Personal Access Token (PAT)

1. **创建 PAT Token**：
   - 访问 https://github.com/settings/tokens
   - 点击 "Generate new token (classic)"
   - 选择权限：
     - ✅ `repo` (完整仓库访问权限)
     - ✅ `workflow` (更新 GitHub Actions 工作流文件)
   - 生成并复制 Token

2. **在 Every15m_runner-get_proxy_2 仓库中设置 Secret**：
   - 进入 https://github.com/parserpp/Every15m_runner-get_proxy_2/settings/secrets/actions
   - 点击 "New repository secret"
   - Name: `GTOKEN`
   - Value: 粘贴你生成的 PAT Token
   - 点击 "Add secret"

3. **恢复工作流使用 GTOKEN**：
   ```yaml
   getproxy --in-proxy=proxy.list --out-proxy=proxy.list.out --token=${{ secrets.GTOKEN }}
   ```

### 方案 2：在 ip_ports 仓库启用 Workflow 权限

1. **在 ip_ports 仓库中**：
   - 进入 https://github.com/parserpp/ip_ports/settings/actions
   - 在 "Workflow permissions" 部分选择：
     - ✅ "Read and write permissions"
   - 勾选 "Allow GitHub Actions to access repository content and packages using the access token"

2. **修改工作流**（实验性）：
   - 需要使用 `gh` CLI 或 GitHub API
   - 较为复杂，不推荐

## 推荐
使用 **方案 1 (PAT Token)**，这是最简单、最安全的方法。