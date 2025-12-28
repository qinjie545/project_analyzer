function generate_article(repo_path, user_goal):
    # 配置初始化
    llm = initialize_llm()
    context = ""
    read_files_set = {}

    # === 步骤 1: 获取项目结构 ===
    file_tree = get_file_tree(repo_path)

    # === 步骤 2: 初始文件筛选 ===
    prompt_1 = f"""
        项目结构: {file_tree}
        目标: {user_goal}
        请选择 10 个最重要的文件用于理解项目。
    """
    files_to_read = llm.invoke(prompt_1).extract_json()

    # === 步骤 3: 循环阅读与上下文构建 ===
    # 初始读取
    for file in files_to_read:
        content = read_file(file)
        if context.length + content.length > MAX_LIMIT: break
        context += format_file(file, content)
        read_files_set.add(file)

    # 补充阅读 (最多 3 轮)
    for i in 1 to 3:
        prompt_loop = f"""
            当前已读文件: {read_files_set}
            当前上下文(截断): {context[-20000:]}
            目标: {user_goal}
            还需要读取哪些文件才能达成目标？(返回空列表表示足够)
        """
        new_files = llm.invoke(prompt_loop).extract_json()
        
        if is_empty(new_files): break
        
        for file in new_files:
            if file not in read_files_set:
                content = read_file(file)
                if context.length + content.length > MAX_LIMIT: break
                context += format_file(file, content)
                read_files_set.add(file)

    # === 步骤 4: 生成详细底稿 (核心知识库) ===
    prompt_detail = f"""
        完整上下文: {context}
        目标: {user_goal}
        请写一份极其详尽的文档（约20000字），包含架构、实现细节、代码分析。
        要求：逻辑严谨，不夸张，求实。
    """
    detailed_doc = llm.invoke(prompt_detail)
    detailed_doc = sanitize_mermaid(detailed_doc) # 修复图表语法

    # === 步骤 5: 精炼成文 (最终产物) ===
    prompt_refine = f"""
        详细文档: {detailed_doc}
        目标: 将上述文档转化为一篇高质量技术文章。
        约束: 8000字以内，保留核心技术细节，逻辑通顺。
        要求：逻辑严谨，不夸张，求实。
    """
    final_article = llm.invoke(prompt_refine)
    final_article = sanitize_mermaid(final_article) # 修复图表语法

    return {
        "final_content": final_article,
        "detailed_content": detailed_doc,
        "thinking": llm.get_reasoning()
    }
