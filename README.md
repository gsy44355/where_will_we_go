# 商圈查找工具

基于高德地图API的商圈查找工具，可以找出指定城市中多个品牌门店都在一定距离范围内的商圈。

## 功能特点

- 通过高德地图API搜索指定城市内的品牌门店
- 使用Haversine公式计算门店间距离
- 找出所有品牌门店都在指定距离内的商圈
- 支持JSON、HTML地图和命令行日志多种输出方式

## 安装

```bash
pip install -r requirements.txt
```

## 配置

1. 复制环境变量模板文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填写您的高德地图API密钥：
```bash
AMAP_API_KEY=your_api_key_here
```

高德地图API密钥申请地址：https://lbs.amap.com/

**注意**: `.env` 文件已添加到 `.gitignore`，不会被提交到Git仓库，确保API密钥安全。

## 使用方法

```bash
python main.py --city "北京" --brands "优衣库,丰茂烤肉" --output json,html
```

### 参数说明

- `--city`: 城市名称（必填）
- `--brands`: 品牌列表，用逗号分隔（必填）
- `--output`: 输出格式，可选：json, html, log（默认：json,log）
- `--threshold`: 距离阈值，单位：米（默认：200）

### 示例

```bash
# 查找北京地区优衣库和丰茂烤肉的商圈
python main.py --city "北京" --brands "优衣库,丰茂烤肉"

# 指定300米距离阈值，并生成HTML地图
python main.py --city "上海" --brands "星巴克,麦当劳" --threshold 300 --output json,html
```

## 输出说明

- **JSON输出**: 返回结构化的商圈数据
- **HTML输出**: 生成包含高德地图的HTML文件，标注所有找到的商圈
- **日志输出**: 在命令行显示详细的查找过程和结果

## 项目结构

```
where_will_we_go/
├── config.py              # 配置文件
├── amap_api.py           # 高德地图API封装
├── distance.py            # 距离计算
├── cluster_finder.py      # 商圈查找算法
├── output.py              # 结果输出
├── main.py                # 主程序
└── requirements.txt       # 依赖包
```

