#!/usr/bin/env python3
"""
主程序入口
"""
import argparse
import sys
from amap_api import search_brands
from cluster_finder import find_clusters
from output import output_json, output_log, output_html
from config import DEFAULT_DISTANCE_THRESHOLD, AMAP_API_KEY


def main():
    parser = argparse.ArgumentParser(
        description="商圈查找工具 - 找出多个品牌门店都在指定距离内的商圈"
    )
    parser.add_argument(
        "--city",
        type=str,
        required=True,
        help="城市名称（例如：北京、上海）"
    )
    parser.add_argument(
        "--brands",
        type=str,
        required=True,
        help="品牌列表，用逗号分隔（例如：优衣库,丰茂烤肉）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="json,log",
        help="输出格式，可选：json, html, log（用逗号分隔，默认：json,log）"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_DISTANCE_THRESHOLD,
        help=f"距离阈值，单位：米（默认：{DEFAULT_DISTANCE_THRESHOLD}）"
    )
    parser.add_argument(
        "--json-file",
        type=str,
        default=None,
        help="JSON输出文件名（默认：自动生成）"
    )
    parser.add_argument(
        "--html-file",
        type=str,
        default="map.html",
        help="HTML输出文件名（默认：map.html）"
    )
    
    args = parser.parse_args()
    
    # 检查API密钥
    if not AMAP_API_KEY or AMAP_API_KEY == "your_api_key_here":
        print("错误: 请在 .env 文件中配置高德地图API密钥")
        print("提示: 复制 .env.example 为 .env 并填写您的API密钥")
        sys.exit(1)
    
    # 解析品牌列表
    brands = [b.strip() for b in args.brands.split(",") if b.strip()]
    if not brands:
        print("错误: 请至少提供一个品牌名称")
        sys.exit(1)
    
    # 解析输出格式
    output_formats = [f.strip() for f in args.output.split(",") if f.strip()]
    if not output_formats:
        output_formats = ["json", "log"]
    
    print(f"开始搜索商圈...")
    print(f"城市: {args.city}")
    print(f"品牌: {', '.join(brands)}")
    print(f"距离阈值: {args.threshold} 米")
    print()
    
    # 1. 搜索各品牌的门店
    print("正在搜索各品牌门店...")
    brand_stores = search_brands(args.city, brands)
    
    # 检查是否有品牌没有找到门店
    brands_with_stores = [b for b in brands if brand_stores.get(b)]
    if not brands_with_stores:
        print("错误: 未找到任何品牌的门店")
        sys.exit(1)
    
    if len(brands_with_stores) < len(brands):
        missing_brands = set(brands) - set(brands_with_stores)
        print(f"警告: 以下品牌未找到门店: {', '.join(missing_brands)}")
        print(f"将继续使用找到的品牌: {', '.join(brands_with_stores)}")
    
    # 2. 查找商圈
    print("\n正在查找符合条件的商圈...")
    clusters = find_clusters(
        {brand: brand_stores[brand] for brand in brands_with_stores},
        args.threshold
    )
    
    # 3. 输出结果
    print("\n处理输出...")
    
    if "json" in output_formats:
        json_filename = args.json_file
        if not json_filename:
            json_filename = f"clusters_{args.city}_{'_'.join(brands_with_stores[:2])}.json"
        output_json(clusters, json_filename)
    
    if "log" in output_formats:
        output_log(clusters)
    
    if "html" in output_formats:
        output_html(clusters, args.city, args.html_file)
    
    print("\n完成！")


if __name__ == "__main__":
    main()

