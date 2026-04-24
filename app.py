import streamlit as st
import yaml

# 页面配置
st.set_page_config(page_title="Clash 订阅自动清洗工具", layout="wide")

st.title("🛠️ Clash 订阅节点精简工具")
st.caption("粘贴订阅内容 -> 选择节点 -> 生成精简版配置")

# 1. 输入区域
raw_yaml = st.text_area("1. 请粘贴完整的订阅文件内容 (YAML格式):", height=300)

if raw_yaml:
    try:
        config = yaml.safe_load(raw_yaml)
        
        if 'proxies' not in config:
            st.error("未在文件中找到 proxies 节点，请检查格式。")
        else:
            all_node_names = [p['name'] for p in config['proxies']]
            
            # 2. 交互选择区域
            st.write("---")
            st.subheader("2. 节点过滤")
            
            # 自动分类（可选增强功能：按国家代码筛选）
            keep_names = st.multiselect(
                "请选择你要保留的节点名称:",
                options=all_node_names,
                default=[]
            )

            if st.button("🚀 开始执行修改"):
                if not keep_names:
                    st.warning("请至少选择一个节点。")
                else:
                    # 核心处理逻辑
                    # A. 过滤 proxies
                    config['proxies'] = [p for p in config['proxies'] if p['name'] in keep_names]
                    
                    # B. 清洗策略组 (proxy-groups)
                    group_names = [g['name'] for g in config.get('proxy-groups', [])]
                    builtin_vals = ['DIRECT', 'REJECT', 'no-resolve']
                    
                    if 'proxy-groups' in config:
                        for group in config['proxy-groups']:
                            if 'proxies' in group:
                                # 仅保留：1.保留的节点名 2.其他策略组名 3.内置指令
                                group['proxies'] = [
                                    p for p in group['proxies'] 
                                    if p in keep_names or p in group_names or p in builtin_vals
                                ]
                    
                    # 3. 输出结果
                    st.write("---")
                    st.subheader("3. 处理结果")
                    result_yaml = yaml.dump(config, allow_unicode=True, sort_keys=False)
                    
                    st.download_button(
                        label="💾 下载精简后的配置文件",
                        data=result_yaml,
                        file_name="filtered_config.yaml",
                        mime="text/yaml"
                    )
                    st.code(result_yaml, language='yaml')

    except Exception as e:
        st.error(f"解析出错: {e}")
