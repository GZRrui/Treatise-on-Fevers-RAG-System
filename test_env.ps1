# Test script for shanghanlun-rag
Write-Host "=== Testing 《伤寒论》RAG 系统 ===" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"

# 1. Test Python
Write-Host "`n[1/6] 测试 Python 环境..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "  OK: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: Python not found" -ForegroundColor Red
    exit 1
}

# 2. Test imports
Write-Host "`n[2/6] 测试核心模块导入..." -ForegroundColor Yellow
$modules = @(
    "llama_index",
    "llama_index.core",
    "llama_index.embeddings.dashscope",
    "llama_index.llms.dashscope",
    "fastapi",
    "pydantic",
    "sqlalchemy"
)

foreach ($mod in $modules) {
    try {
        $result = python -c "import $mod; print('ok')" 2>&1
        if ($result -eq "ok") {
            Write-Host "  OK: $mod" -ForegroundColor Green
        } else {
            Write-Host "  FAIL: $mod - $result" -ForegroundColor Red
        }
    } catch {
        Write-Host "  FAIL: $mod" -ForegroundColor Red
    }
}

# 3. Test data loading
Write-Host "`n[3/6] 测试数据加载..." -ForegroundColor Yellow
try {
    $result = python -c "
import sys
sys.path.insert(0, 'D:/ragpp')
from src.data_loader import DataLoader
loader = DataLoader()
data = loader.load_raw_data()
print(f'加载成功: {len(data)} 条')
" 2>&1
    Write-Host "  OK: $result" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
}

# 4. Test data cleaning
Write-Host "`n[4/6] 测试数据清洗..." -ForegroundColor Yellow
try {
    $result = python -c "
import sys
sys.path.insert(0, 'D:/ragpp')
from src.data_loader import DataLoader
loader = DataLoader()
data = loader.load_raw_data()
clean = loader.clean_data(data)
print(f'清洗成功: {len(clean)} 条')
" 2>&1
    Write-Host "  OK: $result" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
}

# 5. Check env
Write-Host "`n[5/6] 检查环境变量..." -ForegroundColor Yellow
try {
    $result = python -c "
import sys
sys.path.insert(0, 'D:/ragpp')
from dotenv import load_dotenv
load_dotenv()
import os
key = os.getenv('DASHSCOPE_API_KEY', '')
if key and key != 'your_api_key_here':
    print(f'API Key: 已配置 (长度: {len(key)})')
else:
    print('API Key: 未配置或为示例值')
" 2>&1
    Write-Host "  $result" -ForegroundColor $(if ($result -like "*已配置*") { "Green" } else { "Yellow" })
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
}

# 6. Summary
Write-Host "`n[6/6] 测试完成" -ForegroundColor Yellow
Write-Host "`n=== 测试完成 ===" -ForegroundColor Cyan
Write-Host "如果所有测试通过，你可以运行:" -ForegroundColor White
Write-Host "  python scripts/build_index.py  # 构建索引" -ForegroundColor Cyan
Write-Host "  python scripts/interactive_qa.py  # 交互问答" -ForegroundColor Cyan