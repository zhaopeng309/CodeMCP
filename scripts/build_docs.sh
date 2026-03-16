#!/bin/bash
# CodeMCP 文档构建脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== CodeMCP 文档构建脚本 ===${NC}"

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}警告: 未检测到虚拟环境，建议在虚拟环境中运行${NC}"
fi

# 安装文档依赖
echo -e "${GREEN}安装文档依赖...${NC}"
pip install -e ".[docs]" || {
    echo -e "${RED}依赖安装失败${NC}"
    exit 1
}

# 创建必要的目录
mkdir -p doc/api
mkdir -p doc/dev
mkdir -p doc/appendix

# 生成API文档
echo -e "${GREEN}生成API文档...${NC}"
python -c "
from codemcp.api.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from codemcp.api.schemas.block import BlockCreate, BlockUpdate, BlockResponse
from codemcp.api.schemas.system import SystemCreate, SystemUpdate, SystemResponse
print('API Schema 导入成功')
"

# 构建文档
echo -e "${GREEN}构建MkDocs文档...${NC}"
mkdocs build --clean --strict || {
    echo -e "${RED}文档构建失败${NC}"
    exit 1
}

# 检查构建结果
if [ -d "site" ]; then
    echo -e "${GREEN}文档构建成功！输出目录: site/${NC}"
    echo -e "文件数量: $(find site -type f | wc -l)"
    echo -e "总大小: $(du -sh site | cut -f1)"
else
    echo -e "${RED}错误: 未生成site目录${NC}"
    exit 1
fi

# 本地预览（可选）
if [ "$1" = "--serve" ]; then
    echo -e "${GREEN}启动本地文档服务器...${NC}"
    echo -e "访问地址: http://localhost:8000"
    mkdocs serve
fi

echo -e "${GREEN}=== 文档构建完成 ===${NC}"